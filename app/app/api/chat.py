import json
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app import config
from app.core.deps import get_current_user
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


@router.post("/threads")
async def create_thread(req: ThreadCreateRequest, user: User = Depends(get_current_user)):
    kwargs: dict = {"user": user}
    if req.prescription_id is not None:
        prescription = await Prescription.get_or_none(id=req.prescription_id, user=user)
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
async def list_threads(user: User = Depends(get_current_user)):
    threads = await ChatThread.filter(user=user).order_by("-updated_at")
    result = []
    for t in threads:
        result.append(
            {
                "id": t.id,
                "title": t.title,
                "prescription_id": t.prescription_id,
                "is_active": t.is_active,
                "created_at": str(t.created_at),
                "updated_at": str(t.updated_at),
            }
        )
    return success_response(result)


@router.get("/threads/{thread_id}/messages")
async def list_messages(thread_id: int, user: User = Depends(get_current_user)):
    thread = await ChatThread.get_or_none(id=thread_id, user=user)
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
async def end_thread(thread_id: int, user: User = Depends(get_current_user)):
    thread = await ChatThread.get_or_none(id=thread_id, user=user)
    if not thread:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

    thread.is_active = False
    await thread.save()
    return success_response({"id": thread.id, "is_active": False})


RAG_INSTRUCTION = (
    "\n\n[근거 기반 답변 원칙]\n"
    "- [참고 자료]가 제공된 경우 해당 내용을 근거로 답변하세요.\n"
    "- 참고 자료에 없는 내용은 솔직히 '해당 정보가 없다'고 안내하세요.\n"
    "- 약품명, 용량, 횟수 등 수치는 자료에 있는 그대로만 사용하세요."
)


async def _build_retrieved_context(
    thread: ChatThread, medications: list, user_query: str
) -> list[dict]:
    """처방전 약품 기반 RAG 검색 결과를 system message로 반환한다.

    retrieval 실패 시 빈 리스트를 반환하여 기존 채팅 흐름을 유지한다.
    """
    try:
        drug_names = [m.name for m in medications]
        logger.info("[RAG] drug_names=%s, query=%s", drug_names, user_query[:50])
        print(f"[RAG-DEBUG] drug_names={drug_names}")
        if not drug_names:
            return []

        retrieval_service = get_retrieval_service()
        print(f"[RAG-DEBUG] service_type={type(retrieval_service).__name__}")
        docs = await retrieval_service.retrieve(drug_names, user_query)
        logger.info("[RAG] retrieved %d docs", len(docs))
        print(f"[RAG-DEBUG] retrieved_docs={len(docs)}")
        if not docs:
            print("[RAG-DEBUG] 0 docs retrieved — no matching DrugDocument found")
            return []

        ref_text = format_retrieved_docs(docs)
        logger.info("[RAG] context length=%d chars", len(ref_text))
        print(f"[RAG-DEBUG] context_length={len(ref_text)} chars")
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
        print("[RAG-DEBUG] EXCEPTION in retrieval — see logger.exception above")
        return []


async def _build_context(thread: ChatThread) -> list[dict]:
    """LLM에 전달할 메시지 컨텍스트를 구성합니다."""
    system_content = SYSTEM_PROMPT
    if config.RAG_ENABLED:
        system_content += RAG_INSTRUCTION
    messages: list[dict] = [{"role": "system", "content": system_content}]

    # 처방전 요약
    medications = []
    if thread.prescription_id:
        prescription = await Prescription.get(id=thread.prescription_id)
        user = await User.get(id=thread.user_id)
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
    logger.info("[RAG] enabled=%s, medications=%d, recent=%d",
                config.RAG_ENABLED, med_count, recent_count)
    print(f"[RAG-DEBUG] enabled={config.RAG_ENABLED}, medications={med_count}, recent={recent_count}")

    if config.RAG_ENABLED and medications and recent_list:
        # 가장 최근 user 메시지에서 질문 추출
        user_query = ""
        for m in reversed(recent_list):
            if m.role == "user":
                user_query = m.content
                break

        print(f"[RAG-DEBUG] user_query={user_query[:80]!r}")
        if user_query:
            retrieved = await _build_retrieved_context(thread, medications, user_query)
            print(f"[RAG-DEBUG] retrieved_context_count={len(retrieved)}")
            messages.extend(retrieved)
    else:
        if not config.RAG_ENABLED:
            print("[RAG-DEBUG] SKIPPED: RAG_ENABLED is False")
        elif not medications:
            print("[RAG-DEBUG] SKIPPED: no medications (prescription_id may be null)")
        elif not recent_list:
            print("[RAG-DEBUG] SKIPPED: no recent messages")

    for m in recent_list:
        messages.append({"role": m.role, "content": m.content})

    return messages


@router.post("/messages")
async def send_message(req: MessageSendRequest, user: User = Depends(get_current_user)):
    thread = await ChatThread.get_or_none(id=req.thread_id, user=user)
    if not thread:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

    if not thread.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="종료된 대화에는 메시지를 보낼 수 없습니다."
        )

    # 동시 streaming 방지: stale streaming 정리
    stale = await ChatMessage.filter(thread=thread, status="streaming").first()
    if stale:
        elapsed = time.time() - stale.created_at.timestamp()
        if elapsed < config.CHAT_STREAMING_TIMEOUT_SECONDS:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이전 응답이 생성 중입니다.")
        stale.status = "failed"
        await stale.save()

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
            yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_msg.id})}\n\n"

        except Exception:
            assistant_msg.content = accumulated
            assistant_msg.status = "failed"
            await assistant_msg.save()
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
async def send_feedback(req: FeedbackRequest, user: User = Depends(get_current_user)):
    kwargs: dict = {"feedback_type": req.feedback_type}

    if req.thread_id:
        thread = await ChatThread.get_or_none(id=req.thread_id, user=user)
        if not thread:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        kwargs["thread"] = thread

    if req.message_id:
        message = await ChatMessage.get_or_none(id=req.message_id)
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="메시지를 찾을 수 없습니다.")
        msg_thread = await ChatThread.get_or_none(id=message.thread_id, user=user)
        if not msg_thread:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        kwargs["message"] = message

    if req.reason:
        kwargs["reason"] = req.reason
    if req.reason_text:
        kwargs["reason_text"] = req.reason_text

    feedback = await ChatFeedback.create(**kwargs)
    return success_response({"id": feedback.id, "feedback_type": feedback.feedback_type})
