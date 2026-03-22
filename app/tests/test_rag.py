"""RAG 기능 테스트: 섹션 감지, retrieval, context 통합"""

from unittest.mock import patch

import pytest
from tortoise import Tortoise

from app.models.chat import ChatThread
from app.models.drug_document import DrugDocument
from app.services.chat_service import build_context as _build_context
from app.services.retrieval_service import (
    KeywordRetrievalService,
    _normalize_drug_names,
    detect_sections,
    format_retrieved_docs,
)


@pytest.fixture(autouse=True)
async def _ensure_drug_document_schema():
    """conftest의 setup_db 이후 DrugDocument 스키마를 추가 생성한다."""
    conn = Tortoise.get_connection("default")
    await conn.execute_script(
        "CREATE TABLE IF NOT EXISTS drug_documents ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  drug_name VARCHAR(200) NOT NULL,"
        "  drug_name_en VARCHAR(200),"
        "  section VARCHAR(50) NOT NULL,"
        "  content TEXT NOT NULL,"
        "  source VARCHAR(100),"
        "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  UNIQUE(drug_name, section)"
        ")"
    )
    yield


@pytest.fixture
async def sample_docs():
    """테스트용 약품 문서 3건을 생성한다."""
    docs = []
    docs.append(
        await DrugDocument.create(
            drug_name="아목시실린",
            section="dosage",
            content="성인: 1회 250~500mg, 1일 3회 복용합니다.",
        )
    )
    docs.append(
        await DrugDocument.create(
            drug_name="아목시실린",
            section="side_effects",
            content="설사, 구역, 발진이 나타날 수 있습니다.",
        )
    )
    docs.append(
        await DrugDocument.create(
            drug_name="아목시실린",
            section="precautions",
            content="페니실린 알레르기가 있는 경우 복용하지 마세요.",
        )
    )
    return docs


# ─── detect_sections 테스트 ───


@pytest.mark.asyncio
async def test_detect_sections_side_effects():
    result = detect_sections("이 약 부작용이 뭐예요?")
    assert "side_effects" in result


@pytest.mark.asyncio
async def test_detect_sections_dosage():
    result = detect_sections("식후에 먹어야 하나요?")
    assert "dosage" in result


@pytest.mark.asyncio
async def test_detect_sections_interactions():
    result = detect_sections("다른 약과 같이 먹어도 되나요?")
    assert "interactions" in result


@pytest.mark.asyncio
async def test_detect_sections_precautions():
    result = detect_sections("임산부도 복용할 수 있나요?")
    assert "precautions" in result


@pytest.mark.asyncio
async def test_detect_sections_default():
    """매칭 키워드가 없으면 기본값 [dosage, precautions]을 반환한다."""
    result = detect_sections("이 약 뭐예요?")
    assert set(result) == {"dosage", "precautions"}


# ─── _normalize_drug_names 테스트 ───


@pytest.mark.asyncio
async def test_normalize_brand_to_generic():
    """브랜드명이 성분명으로 변환된다."""
    result = _normalize_drug_names(["울트라셋 이알 서방정"])
    assert "트라마돌" in result
    assert "아세트아미노펜" in result


@pytest.mark.asyncio
async def test_normalize_suffix_removal():
    """제형·용량 접미사가 제거된다."""
    result = _normalize_drug_names(["아목시실린캡슐500mg"])
    assert "아목시실린" in result


@pytest.mark.asyncio
async def test_normalize_keeps_original():
    """원본 이름도 결과에 포함된다."""
    result = _normalize_drug_names(["아스피린"])
    assert "아스피린" in result


@pytest.mark.asyncio
async def test_retrieve_partial_match(sample_docs):
    """정확 매칭 실패 시 부분 매칭으로 찾는다."""
    service = KeywordRetrievalService()
    # "아목시실린캡슐500mg"은 정확 매칭 안 되지만, 정규화 후 "아목시실린"으로 매칭
    docs = await service.retrieve(["아목시실린캡슐500mg"], "부작용이 뭐예요?")
    assert len(docs) >= 1
    assert docs[0]["drug_name"] == "아목시실린"


# ─── retrieval 테스트 ───


@pytest.mark.asyncio
async def test_retrieve_by_drug_name(sample_docs):
    service = KeywordRetrievalService()
    docs = await service.retrieve(["아목시실린"], "부작용이 뭐예요?")
    assert len(docs) == 1
    assert docs[0]["drug_name"] == "아목시실린"
    assert docs[0]["section"] == "side_effects"


@pytest.mark.asyncio
async def test_retrieve_no_match():
    """DB에 없는 약품명은 빈 결과를 반환한다."""
    service = KeywordRetrievalService()
    docs = await service.retrieve(["없는약"], "부작용이 뭐예요?")
    assert docs == []


@pytest.mark.asyncio
async def test_retrieve_default_sections(sample_docs):
    """키워드 매칭 없으면 기본 섹션(dosage, precautions)만 조회한다."""
    service = KeywordRetrievalService()
    docs = await service.retrieve(["아목시실린"], "이 약 뭐예요?")
    sections = {d["section"] for d in docs}
    assert sections == {"dosage", "precautions"}


# ─── format_retrieved_docs 테스트 ───


@pytest.mark.asyncio
async def test_format_includes_drug_name():
    docs = [{"drug_name": "아목시실린", "section": "dosage", "content": "1일 3회 복용"}]
    result = format_retrieved_docs(docs)
    assert "[아목시실린 - dosage]" in result
    assert "1일 3회 복용" in result


@pytest.mark.asyncio
async def test_format_respects_max_chars():
    """2000자 cap을 초과하면 잘린다."""
    long_content = "가" * 1500
    docs = [
        {"drug_name": "약A", "section": "dosage", "content": long_content},
        {"drug_name": "약B", "section": "dosage", "content": long_content},
    ]
    with patch("app.services.retrieval_service.config") as mock_config:
        mock_config.RAG_MAX_CONTEXT_CHARS = 2000
        result = format_retrieved_docs(docs)
    assert len(result) <= 2100  # 포맷 오버헤드 감안


@pytest.mark.asyncio
async def test_format_empty_docs():
    result = format_retrieved_docs([])
    assert result == ""


# ─── _build_context 통합 테스트 ───


@pytest.mark.asyncio
async def test_build_context_rag_disabled(auth_client):
    """RAG_ENABLED=false일 때 [참고 자료]가 context에 포함되지 않는다."""
    create_resp = await auth_client.post("/api/chat/threads", json={})
    thread_id = create_resp.json()["data"]["id"]

    await auth_client.post(
        "/api/chat/messages",
        json={"thread_id": thread_id, "content": "부작용이 뭐예요?"},
    )

    thread = await ChatThread.get(id=thread_id)

    with patch("app.api.chat.config") as mock_config:
        mock_config.RAG_ENABLED = False
        mock_config.CHAT_CONTEXT_MESSAGE_COUNT = 3
        context = await _build_context(thread)

    contents = [m["content"] for m in context]
    assert not any("[참고 자료]" in c for c in contents)


@pytest.mark.asyncio
async def test_build_context_rag_enabled_no_prescription(auth_client):
    """처방전 없는 thread에서는 RAG가 활성화되어도 [참고 자료]가 삽입되지 않는다."""
    create_resp = await auth_client.post("/api/chat/threads", json={})
    thread_id = create_resp.json()["data"]["id"]

    await auth_client.post(
        "/api/chat/messages",
        json={"thread_id": thread_id, "content": "부작용이 뭐예요?"},
    )

    thread = await ChatThread.get(id=thread_id)

    with (
        patch("app.api.chat.config") as mock_chat_config,
        patch("app.services.retrieval_service.config") as mock_ret_config,
    ):
        mock_chat_config.RAG_ENABLED = True
        mock_chat_config.CHAT_CONTEXT_MESSAGE_COUNT = 3
        mock_ret_config.RAG_ENABLED = True
        mock_ret_config.RAG_MAX_CONTEXT_CHARS = 2000
        mock_ret_config.RAG_DEFAULT_SECTIONS = ["dosage", "precautions"]
        context = await _build_context(thread)

    contents = [m["content"] for m in context]
    assert not any("[참고 자료]" in c for c in contents)


@pytest.mark.asyncio
async def test_build_context_rag_enabled_with_docs(auth_client, sample_docs):
    """처방전 + DrugDocument가 있으면 [참고 자료]가 context에 삽입된다."""
    import io

    # 처방전 업로드 → medication 생성
    upload_resp = await auth_client.post(
        "/api/prescriptions",
        files={"file": ("test.png", io.BytesIO(b"fake"), "image/png")},
    )
    pid = upload_resp.json()["data"]["id"]

    # OCR dummy가 medication을 생성하지만 약품명이 다를 수 있으므로
    # 직접 아목시실린 medication을 추가
    from app.models.prescription import Medication, Prescription

    prescription = await Prescription.get(id=pid)
    await Medication.create(
        prescription=prescription,
        name="아목시실린",
        dosage="500mg",
        frequency="1일 3회",
    )

    # 처방전 연결 thread 생성
    create_resp = await auth_client.post("/api/chat/threads", json={"prescription_id": pid})
    thread_id = create_resp.json()["data"]["id"]

    # 메시지 전송
    await auth_client.post(
        "/api/chat/messages",
        json={"thread_id": thread_id, "content": "부작용이 뭐예요?"},
    )

    thread = await ChatThread.get(id=thread_id)

    with (
        patch("app.api.chat.config") as mock_chat_config,
        patch("app.services.retrieval_service.config") as mock_ret_config,
    ):
        mock_chat_config.RAG_ENABLED = True
        mock_chat_config.CHAT_CONTEXT_MESSAGE_COUNT = 3
        mock_ret_config.RAG_ENABLED = True
        mock_ret_config.RAG_MAX_CONTEXT_CHARS = 2000
        mock_ret_config.RAG_DEFAULT_SECTIONS = ["dosage", "precautions"]
        context = await _build_context(thread)

    contents = [m["content"] for m in context]
    has_ref = any("[참고 자료]" in c for c in contents)
    assert has_ref

    # drug_name이 포함되어 있는지 확인
    ref_content = [c for c in contents if "[참고 자료]" in c][0]
    assert "아목시실린" in ref_content
