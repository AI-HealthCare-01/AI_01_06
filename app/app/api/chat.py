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
from app.core.response import success_response
from app.models.chat import ChatFeedback, ChatMessage, ChatThread
from app.models.patient_profile import PatientProfile
from app.models.prescription import Medication, Prescription
from app.models.user import User
from app.schemas.chat import FeedbackRequest, MessageSendRequest, ThreadCreateRequest
from app.services.chat_service import SYSTEM_PROMPT, get_chat_service
from app.services.retrieval_service import format_retrieved_docs, get_retrieval_service

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


RAG_INSTRUCTION = (
    "\n\n[근거 기반 답변 원칙]\n"
    "- [참고 자료]가 제공된 경우 해당 내용을 근거로 답변하세요.\n"
    "- 참고 자료에 없는 내용은 솔직히 '해당 정보가 없다'고 안내하세요.\n"
    "- 약품명, 용량, 횟수 등 수치는 자료에 있는 그대로만 사용하세요."
)


async def _build_retrieved_context(thread: ChatThread, medications: list, user_query: str) -> list[dict]:
    """처방전 약품 기반 RAG 검색 결과를 system message로 반환한다.

    retrieval 실패 시 빈 리스트를 반환하여 기존 채팅 흐름을 유지한다.
    """
    try:
        drug_names = [m.name for m in medications]
        logger.info("[RAG] drug_names=%s, query=%s", drug_names, user_query[:50])
        if not drug_names:
            return []

        retrieval_service = get_retrieval_service()
        docs = await retrieval_service.retrieve(drug_names, user_query)
        logger.info("[RAG] retrieved %d docs", len(docs))
        if not docs:
            return []

        ref_text = format_retrieved_docs(docs)
        logger.info("[RAG] context length=%d chars", len(ref_text))
        if not ref_text:
            return []

        return [
            {
                "role": "system",
                "content": (
                    "[참고 자료]\n"
                    "아래는 처방된 약품의 공식 정보입니다. "
                    "답변 시 이 정보를 근거로 활용하세요.\n\n" + ref_text
                ),
            }
        ]
    except Exception:
        logger.exception("[RAG] retrieval failed")
        return []


async def _build_context(thread: ChatThread) -> list[dict]:  # noqa: C901
    """LLM에 전달할 메시지 컨텍스트를 구성합니다."""
    system_content = SYSTEM_PROMPT
    if config.RAG_ENABLED:
        system_content += RAG_INSTRUCTION
    messages: list[dict] = [{"role": "system", "content": system_content}]

    # 처방전 요약
    medications = []
    if thread.prescription_id:
        prescription = await Prescription.get(id=thread.prescription_id)
        medications = await Medication.filter(prescription=prescription)

        summary_parts = []
        if prescription.hospital_name:
            summary_parts.append(f"병원: {prescription.hospital_name}")
        if prescription.diagnosis:
            summary_parts.append(f"진단: {prescription.diagnosis}")
        if medications:
            med_names = ", ".join(m.name for m in medications)
            summary_parts.append(f"처방 약물: {med_names}")

        profile = await PatientProfile.get_or_none(user_id=thread.user_id)
        if profile and profile.allergy_details:
            summary_parts.append(f"알러지: {profile.allergy_details}")
        if profile and profile.disease_details:
            summary_parts.append(f"기저질환: {profile.disease_details}")

        if summary_parts:
            messages.append(
                {
                    "role": "system",
                    "content": "[처방전 요약]\n" + "\n".join(summary_parts),
                }
            )

    # 최근 completed 메시지 (현재 사용자 메시지 포함)
    recent = (
        await ChatMessage.filter(thread=thread, status="completed")
        .order_by("-created_at")
        .limit(config.CHAT_CONTEXT_MESSAGE_COUNT)
    )
    recent_list = list(reversed(recent))

    # RAG: 처방전이 연결된 경우에만 검색 수행
    med_count = len(medications)
    recent_count = len(recent_list)
    logger.info("[RAG] enabled=%s, medications=%d, recent=%d", config.RAG_ENABLED, med_count, recent_count)

    if config.RAG_ENABLED and medications and recent_list:
        # 가장 최근 user 메시지에서 질문 추출
        user_query = ""
        for m in reversed(recent_list):
            if m.role == "user":
                user_query = m.content
                break

        if user_query:
            retrieved = await _build_retrieved_context(thread, medications, user_query)
            messages.extend(retrieved)

    for m in recent_list:
        messages.append({"role": m.role, "content": m.content})

    return messages


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

    stale = await ChatMessage.filter(thread=thread, status="streaming").first()
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

    # user 메시지 저장
    await ChatMessage.create(thread=thread, role="user", content=req.content, status="completed")

    # 첫 메시지면 제목 자동 생성
    if not thread.title:
        thread.title = req.content[:40]
        await thread.save()

    # assistant 메시지 생성 (streaming 상태)
    assistant_msg = await ChatMessage.create(thread=thread, role="assistant", content="", status="streaming")

    # 컨텍스트 구성
    context = await _build_context(thread)

    async def sse_generator():
        chat_service = get_chat_service()
        accumulated = ""
        start_time = time.time()

        try:
            stream = chat_service.stream_reply(context)
            async for token in stream:
                # 전체 timeout 체크
                if time.time() - start_time > config.CHAT_STREAMING_TIMEOUT_SECONDS:
                    break

                accumulated += token
                yield f"data: {json.dumps({'type': 'chunk', 'content': token}, ensure_ascii=False)}\n\n"

            # 정상 완료
            assistant_msg.content = accumulated
            assistant_msg.status = "completed"
            await assistant_msg.save()
            await thread.save()  # updated_at 갱신
            yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_msg.id})}\n\n"

        except Exception:
            assistant_msg.content = accumulated
            assistant_msg.status = "failed"
            await assistant_msg.save()
            await thread.save()  # updated_at 갱신
            yield f"data: {json.dumps({'type': 'error', 'message': '응답 생성 중 오류가 발생했습니다.'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


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
