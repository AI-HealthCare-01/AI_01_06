import asyncio
import json
import logging
import math
import time
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from tortoise.functions import Count

from app import config
from app.core.deps import get_acting_patient
from app.core.redis import CHAT_STREAM_PREFIX, enqueue, subscribe_chat_stream
from app.core.response import success_response
from app.models.chat import ChatFeedback, ChatMessage, ChatThread
from app.models.prescription import Prescription
from app.models.user import User
from app.schemas.chat import FeedbackRequest, MessageSendRequest, ThreadCreateRequest
from app.services.notification_service import create_notification

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _compute_thread_status(thread: ChatThread) -> str:
    """Virtual status: active / auto_closed / ended."""
    if not thread.is_active:
        return "ended"
    now = datetime.now(UTC)
    updated = thread.updated_at
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=UTC)
    if (now - updated) > timedelta(hours=config.CHAT_AUTO_CLOSE_HOURS):
        return "auto_closed"
    return "active"


@router.post("/threads")
async def create_thread(req: ThreadCreateRequest, actors: tuple[User, User | None] = Depends(get_acting_patient)):
    current_user, patient = actors
    target_user = patient or current_user

    kwargs: dict = {"user": target_user}
    if patient:
        kwargs["acted_by"] = current_user
    if req.prescription_id is not None:
        prescription = await Prescription.get_or_none(id=req.prescription_id, user=target_user)
        if not prescription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="처방전을 찾을 수 없습니다.")
        kwargs["prescription"] = prescription

    thread = await ChatThread.create(**kwargs)

    if patient:
        await create_notification(
            user_id=patient.id,
            notification_type="CAREGIVER",
            title=f"{current_user.name}님이 AI 상담을 진행했습니다.",
        )

    return success_response(
        {
            "id": thread.id,
            "prescription_id": req.prescription_id,
            "title": thread.title,
            "is_active": thread.is_active,
            "created_at": str(thread.created_at),
        }
    )


@router.get("/threads")
async def list_threads(
    page: int = 1,
    page_size: int = config.CHAT_DEFAULT_PAGE_SIZE,
    thread_status: str = Query("all", alias="status"),
    actors: tuple[User, User | None] = Depends(get_acting_patient),
):
    current_user, patient = actors
    target_user = patient or current_user
    threads = (
        await ChatThread.filter(user=target_user)
        .annotate(message_count=Count("messages"))
        .order_by("-updated_at")
        .prefetch_related("acted_by")
    )
    # 1. Virtual status 계산 (메시지 0개인 빈 thread 제외)
    all_results = []
    for t in threads:
        if t.message_count == 0:  # type: ignore[attr-defined]
            continue
        computed = _compute_thread_status(t)
        acted_by_user = t.acted_by if t.acted_by_id else None
        all_results.append(
            {
                "id": t.id,
                "title": t.title,
                "prescription_id": t.prescription_id,
                "is_active": t.is_active,
                "status": computed,
                "created_at": str(t.created_at),
                "updated_at": str(t.updated_at),
                "acted_by_name": acted_by_user.name if acted_by_user else None,
            }
        )

    # 2. Status 필터
    if thread_status == "active":
        all_results = [r for r in all_results if r["status"] == "active"]
    elif thread_status == "ended":
        all_results = [r for r in all_results if r["status"] in ("ended", "auto_closed")]

    # 3. Total 계산
    total = len(all_results)
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    total_pages = max(1, math.ceil(total / page_size))

    # 4. Pagination slice
    start = (page - 1) * page_size
    paginated = all_results[start : start + page_size]

    return success_response(
        {
            "threads": paginated,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    )


@router.get("/threads/{thread_id}")
async def get_thread(thread_id: int, actors: tuple[User, User | None] = Depends(get_acting_patient)):
    current_user, patient = actors
    target_user = patient or current_user
    thread = await ChatThread.get_or_none(id=thread_id, user=target_user)
    if not thread:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
    return success_response(
        {
            "id": thread.id,
            "title": thread.title,
            "prescription_id": thread.prescription_id,
            "is_active": thread.is_active,
            "status": _compute_thread_status(thread),
            "created_at": str(thread.created_at),
            "updated_at": str(thread.updated_at),
        }
    )


@router.get("/threads/{thread_id}/messages")
async def list_messages(thread_id: int, actors: tuple[User, User | None] = Depends(get_acting_patient)):
    current_user, patient = actors
    target_user = patient or current_user
    thread = await ChatThread.get_or_none(id=thread_id, user=target_user)
    if not thread:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

    messages = await ChatMessage.filter(thread=thread).order_by("created_at")
    result = []
    for m in messages:
        result.append(
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "status": m.status,
                "created_at": str(m.created_at),
            }
        )
    return success_response(result)


@router.patch("/threads/{thread_id}/end")
async def end_thread(thread_id: int, actors: tuple[User, User | None] = Depends(get_acting_patient)):
    current_user, patient = actors
    target_user = patient or current_user
    thread = await ChatThread.get_or_none(id=thread_id, user=target_user)
    if not thread:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

    thread.is_active = False
    await thread.save()
    return success_response({"id": thread.id, "is_active": False})


@router.patch("/threads/{thread_id}/reactivate")
async def reactivate_thread(thread_id: int, actors: tuple[User, User | None] = Depends(get_acting_patient)):
    current_user, patient = actors
    target_user = patient or current_user
    thread = await ChatThread.get_or_none(id=thread_id, user=target_user)
    if not thread:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

    if _compute_thread_status(thread) == "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 활성 상태인 대화입니다.",
        )

    thread.is_active = True
    await thread.save()
    return success_response(
        {
            "id": thread.id,
            "title": thread.title,
            "prescription_id": thread.prescription_id,
            "is_active": True,
            "status": "active",
            "created_at": str(thread.created_at),
            "updated_at": str(thread.updated_at),
        }
    )


async def _validate_thread_for_message(thread: ChatThread | None) -> None:
    """메시지 전송 전 스레드 상태 검증 및 stale stream 정리."""
    if not thread:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

    if not thread.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="종료된 대화에는 메시지를 보낼 수 없습니다."
        )

    if _compute_thread_status(thread) == "auto_closed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="장시간 미활동으로 자동 종료된 대화입니다. 대화 이어가기를 이용해주세요.",
        )

    stale = await ChatMessage.filter(thread=thread, status__in=["streaming", "pending"]).first()
    if stale:
        elapsed = time.time() - stale.created_at.timestamp()
        if elapsed < config.CHAT_STREAMING_TIMEOUT_SECONDS:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이전 응답이 생성 중입니다.")
        stale.status = "failed"
        await stale.save()


@router.post("/messages")
async def send_message(req: MessageSendRequest, actors: tuple[User, User | None] = Depends(get_acting_patient)):
    current_user, patient = actors
    target_user = patient or current_user
    thread = await ChatThread.get_or_none(id=req.thread_id, user=target_user)
    await _validate_thread_for_message(thread)

    await ChatMessage.create(thread=thread, role="user", content=req.content, status="completed")

    if not thread.title:
        thread.title = req.content[:40]
        await thread.save()

    assistant_msg = await ChatMessage.create(thread=thread, role="assistant", content="", status="pending")

    await enqueue("chat_task", assistant_msg.id)

    return success_response({"message_id": assistant_msg.id, "status": "pending"})


def _sse_done(msg: ChatMessage) -> str:
    return f"data: {json.dumps({'type': 'done', 'content': msg.content, 'message_id': msg.id}, ensure_ascii=False)}\n\n"


def _sse_error(message: str = "응답 생성에 실패했습니다.") -> str:
    return f"data: {json.dumps({'type': 'error', 'message': message}, ensure_ascii=False)}\n\n"


_SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


async def _sse_relay(msg: ChatMessage, message_id: int):  # noqa: C901
    pubsub, sub_redis = await subscribe_chat_stream(message_id)
    try:
        deadline = time.time() + config.CHAT_STREAMING_TIMEOUT_SECONDS
        while time.time() < deadline:
            raw = await pubsub.get_message(ignore_subscribe_messages=True, timeout=15.0)
            if raw is None:
                yield ": keepalive\n\n"
                await msg.refresh_from_db()
                if msg.status == "completed":
                    yield _sse_done(msg)
                    return
                if msg.status == "failed":
                    yield _sse_error()
                    return
                continue

            if raw["type"] != "message":
                continue

            event = json.loads(raw["data"])
            if event["t"] == "c":
                yield f"data: {json.dumps({'type': 'chunk', 'content': event['d']}, ensure_ascii=False)}\n\n"
            elif event["t"] == "done":
                await msg.refresh_from_db()
                yield _sse_done(msg)
                return
            elif event["t"] == "error":
                yield _sse_error(event.get("d", "오류 발생"))
                return
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(f"{CHAT_STREAM_PREFIX}{message_id}")
        await pubsub.aclose()
        await sub_redis.aclose()


@router.get("/messages/{message_id}/stream")
async def stream_message(message_id: int, actors: tuple[User, User | None] = Depends(get_acting_patient)):
    """Redis Pub/Sub에서 워커의 LLM 응답을 구독하여 SSE로 클라이언트에 relay한다."""
    current_user, patient = actors
    target_user = patient or current_user

    msg = await ChatMessage.get_or_none(id=message_id)
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="메시지를 찾을 수 없습니다.")

    thread = await ChatThread.get_or_none(id=msg.thread_id, user=target_user)
    if not thread:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

    if msg.status == "completed":

        async def completed_gen():
            yield _sse_done(msg)

        return StreamingResponse(completed_gen(), media_type="text/event-stream", headers=_SSE_HEADERS)

    if msg.status == "failed":

        async def failed_gen():
            yield _sse_error()

        return StreamingResponse(failed_gen(), media_type="text/event-stream", headers=_SSE_HEADERS)

    return StreamingResponse(_sse_relay(msg, message_id), media_type="text/event-stream", headers=_SSE_HEADERS)


@router.post("/feedback")
async def send_feedback(req: FeedbackRequest, actors: tuple[User, User | None] = Depends(get_acting_patient)):
    current_user, patient = actors
    target_user = patient or current_user
    kwargs: dict = {"feedback_type": req.feedback_type}

    if req.thread_id:
        thread = await ChatThread.get_or_none(id=req.thread_id, user=target_user)
        if not thread:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        kwargs["thread"] = thread

    if req.message_id:
        message = await ChatMessage.get_or_none(id=req.message_id)
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="메시지를 찾을 수 없습니다.")
        msg_thread = await ChatThread.get_or_none(id=message.thread_id, user=target_user)
        if not msg_thread:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        kwargs["message"] = message

    if req.reason:
        kwargs["reason"] = req.reason
    if req.reason_text:
        kwargs["reason_text"] = req.reason_text

    feedback = await ChatFeedback.create(**kwargs)
    return success_response({"id": feedback.id, "feedback_type": feedback.feedback_type})
