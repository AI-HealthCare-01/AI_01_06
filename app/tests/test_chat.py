"""채팅 기능 테스트: Thread CRUD, SSE 스트리밍, 피드백"""

import io
import json

import pytest
from httpx import AsyncClient

from app.models.chat import ChatMessage, ChatThread
from app.services.chat_service import build_context


@pytest.mark.asyncio
async def test_create_thread(auth_client: AsyncClient):
    resp = await auth_client.post("/api/chat/threads", json={})
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["id"] is not None
    assert body["data"]["is_active"] is True


@pytest.mark.asyncio
async def test_create_thread_with_prescription(auth_client: AsyncClient):
    upload_resp = await auth_client.post(
        "/api/prescriptions",
        files={"file": ("test.png", io.BytesIO(b"fake"), "image/png")},
    )
    pid = upload_resp.json()["data"]["id"]

    resp = await auth_client.post("/api/chat/threads", json={"prescription_id": pid})
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["prescription_id"] == pid


@pytest.mark.asyncio
async def test_list_threads_own_only(auth_client: AsyncClient, client: AsyncClient):
    # auth_client로 thread 생성
    await auth_client.post("/api/chat/threads", json={})

    # 다른 유저 생성
    await client.post(
        "/api/auth/signup",
        json={
            "email": "other@test.com",
            "password": "Test1234!",
            "nickname": "다른유저",
            "name": "이영희",
            "role": "PATIENT",
            "terms_of_service": True,
            "privacy_policy": True,
        },
    )
    login_resp = await client.post(
        "/api/auth/login",
        json={
            "email": "other@test.com",
            "password": "Test1234!",
        },
    )
    other_token = login_resp.json()["data"]["access_token"]

    # 다른 유저의 thread 목록은 비어있어야 함
    resp = await client.get(
        "/api/chat/threads",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_end_thread(auth_client: AsyncClient):
    create_resp = await auth_client.post("/api/chat/threads", json={})
    thread_id = create_resp.json()["data"]["id"]

    resp = await auth_client.patch(f"/api/chat/threads/{thread_id}/end")
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["is_active"] is False


@pytest.mark.asyncio
async def test_send_message_auto_title(auth_client: AsyncClient):
    create_resp = await auth_client.post("/api/chat/threads", json={})
    thread_id = create_resp.json()["data"]["id"]

    long_message = "이것은 40자를 초과하는 매우 긴 메시지입니다. 제목이 잘려야 합니다. 이렇게 길면 안됩니다."
    await auth_client.post(
        "/api/chat/messages",
        json={"thread_id": thread_id, "content": long_message},
    )

    thread = await ChatThread.get(id=thread_id)
    assert thread.title is not None
    assert len(thread.title) <= 40


@pytest.mark.asyncio
async def test_send_message_to_ended_thread_returns_400(auth_client: AsyncClient):
    create_resp = await auth_client.post("/api/chat/threads", json={})
    thread_id = create_resp.json()["data"]["id"]

    await auth_client.patch(f"/api/chat/threads/{thread_id}/end")

    resp = await auth_client.post(
        "/api/chat/messages",
        json={"thread_id": thread_id, "content": "hello"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_send_message_to_others_thread_returns_403(auth_client: AsyncClient, client: AsyncClient):
    create_resp = await auth_client.post("/api/chat/threads", json={})
    thread_id = create_resp.json()["data"]["id"]

    # 다른 유저
    await client.post(
        "/api/auth/signup",
        json={
            "email": "other2@test.com",
            "password": "Test1234!",
            "nickname": "다른유저2",
            "name": "박철수",
            "role": "PATIENT",
            "terms_of_service": True,
            "privacy_policy": True,
        },
    )
    login_resp = await client.post(
        "/api/auth/login",
        json={
            "email": "other2@test.com",
            "password": "Test1234!",
        },
    )
    other_token = login_resp.json()["data"]["access_token"]

    resp = await client.post(
        "/api/chat/messages",
        json={"thread_id": thread_id, "content": "hello"},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_messages(auth_client: AsyncClient):
    create_resp = await auth_client.post("/api/chat/threads", json={})
    thread_id = create_resp.json()["data"]["id"]

    await auth_client.post(
        "/api/chat/messages",
        json={"thread_id": thread_id, "content": "테스트 질문"},
    )

    resp = await auth_client.get(f"/api/chat/threads/{thread_id}/messages")
    body = resp.json()
    assert body["success"] is True
    assert len(body["data"]) == 2  # user + assistant
    assert body["data"][0]["role"] == "user"
    assert body["data"][1]["role"] == "assistant"
    assert body["data"][1]["status"] == "completed"


@pytest.mark.asyncio
async def test_context_excludes_failed_messages(auth_client: AsyncClient):
    """failed 메시지가 컨텍스트에서 제외되는지 확인"""
    create_resp = await auth_client.post("/api/chat/threads", json={})
    thread_id = create_resp.json()["data"]["id"]

    # 정상 메시지 1개
    await auth_client.post(
        "/api/chat/messages",
        json={"thread_id": thread_id, "content": "첫 번째 질문"},
    )

    # failed 메시지 수동 생성
    thread = await ChatThread.get(id=thread_id)
    await ChatMessage.create(thread=thread, role="assistant", content="미완성", status="failed")

    # 새 user 메시지를 completed로 저장 후 컨텍스트 빌더 확인
    await ChatMessage.create(thread=thread, role="user", content="새 질문", status="completed")
    context = await build_context(thread)

    # failed 메시지("미완성")가 컨텍스트에 포함되어서는 안 됨
    contents = [m["content"] for m in context]
    assert "미완성" not in contents
    assert "새 질문" in contents


@pytest.mark.asyncio
async def test_send_feedback(auth_client: AsyncClient):
    create_resp = await auth_client.post("/api/chat/threads", json={})
    thread_id = create_resp.json()["data"]["id"]

    await auth_client.post(
        "/api/chat/messages",
        json={"thread_id": thread_id, "content": "질문"},
    )

    # 메시지 목록에서 assistant 메시지 ID 가져오기
    msgs_resp = await auth_client.get(f"/api/chat/threads/{thread_id}/messages")
    assistant_msg_id = msgs_resp.json()["data"][1]["id"]

    # thumbs_up 피드백
    resp = await auth_client.post(
        "/api/chat/feedback",
        json={
            "message_id": assistant_msg_id,
            "feedback_type": "thumbs_up",
        },
    )
    assert resp.json()["success"] is True

    # session_negative 피드백
    resp = await auth_client.post(
        "/api/chat/feedback",
        json={
            "thread_id": thread_id,
            "feedback_type": "session_negative",
            "reason": "inaccurate",
            "reason_text": "정보가 틀렸어요",
        },
    )
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_send_message_returns_message_id(auth_client: AsyncClient):
    """send_message가 SSE가 아닌 JSON {message_id, status} 를 반환한다."""
    create_resp = await auth_client.post("/api/chat/threads", json={})
    thread_id = create_resp.json()["data"]["id"]

    resp = await auth_client.post(
        "/api/chat/messages",
        json={"thread_id": thread_id, "content": "약을 식전에 먹어야 하나요?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "message_id" in body["data"]
    assert body["data"]["status"] == "pending"


@pytest.mark.asyncio
async def test_message_stream_completed(auth_client: AsyncClient):
    """완료된 메시지의 stream SSE 조회 시 즉시 done 이벤트를 반환한다."""
    create_resp = await auth_client.post("/api/chat/threads", json={})
    thread_id = create_resp.json()["data"]["id"]

    send_resp = await auth_client.post(
        "/api/chat/messages",
        json={"thread_id": thread_id, "content": "테스트 질문"},
    )
    msg_id = send_resp.json()["data"]["message_id"]

    async with auth_client.stream("GET", f"/api/chat/messages/{msg_id}/stream") as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        lines = []
        async for line in response.aiter_lines():
            lines.append(line)

    data_lines = [line for line in lines if line.startswith("data: ")]
    assert len(data_lines) == 1
    event = json.loads(data_lines[0][6:])
    assert event["type"] == "done"
    assert event["message_id"] == msg_id
    assert len(event["content"]) > 0


@pytest.mark.asyncio
async def test_message_stream_wrong_user(auth_client: AsyncClient, client: AsyncClient):
    """다른 사용자의 메시지 stream 조회 시 403 반환."""
    create_resp = await auth_client.post("/api/chat/threads", json={})
    thread_id = create_resp.json()["data"]["id"]

    send_resp = await auth_client.post(
        "/api/chat/messages",
        json={"thread_id": thread_id, "content": "테스트"},
    )
    msg_id = send_resp.json()["data"]["message_id"]

    await client.post(
        "/api/auth/signup",
        json={
            "email": "stream_other@test.com",
            "password": "Test1234!",
            "nickname": "스트림다른유저",
            "name": "최스트림",
            "role": "PATIENT",
            "terms_of_service": True,
            "privacy_policy": True,
        },
    )
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "stream_other@test.com", "password": "Test1234!"},
    )
    other_token = login_resp.json()["data"]["access_token"]

    resp = await client.get(
        f"/api/chat/messages/{msg_id}/stream",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 403
