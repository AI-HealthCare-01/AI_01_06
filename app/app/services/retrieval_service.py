import abc
import logging
import re

from tortoise.expressions import Q

from app import config
from app.models.drug_document import DrugDocument

logger = logging.getLogger(__name__)

# ── 제품명 → 성분명(generic) 매핑 (MVP용 하드코딩) ──
# OCR 결과에 등장하는 제품명/브랜드명을 성분명으로 변환한다.
# key는 제품명에 포함될 수 있는 부분 문자열(소문자 비교 불필요, 한글).
_BRAND_TO_GENERIC: dict[str, list[str]] = {
    "울트라셋": ["트라마돌", "아세트아미노펜"],
    "타이레놀": ["아세트아미노펜"],
    "판콜": ["아세트아미노펜"],
    "게보린": ["아세트아미노펜", "이부프로펜"],
    "애드빌": ["이부프로펜"],
    "부루펜": ["이부프로펜"],
    "탁센": ["아세트아미노펜"],
    "낙센": ["이부프로펜"],
    "오메가드": ["오메프라졸"],
    "로섹": ["오메프라졸"],
    "넥시움": ["오메프라졸"],
    "판토록": ["판토프라졸"],
    "글루코파지": ["메트포르민"],
    "다이아벡스": ["메트포르민"],
    "바이엘아스피린": ["아스피린"],
    "코자": ["로사르탄"],
    "노바스크": ["암로디핀"],
    "리피토": ["아토르바스타틴"],
    "지르텍": ["세티리진"],
    "클라리틴": ["로라타딘"],
    "클래리시드": ["클라리스로마이신"],
    "크라비트": ["레보플록사신"],
    "소론도": ["프레드니솔론"],
    "쿠마딘": ["와파린"],
    "라닉스": ["푸로세미드"],
    "바이브라마이신": ["독시사이클린"],
    "뉴론틴": ["가바펜틴"],
    "스틸녹스": ["졸피뎀"],
    "아마릴": ["글리메피리드"],
    "조코": ["심바스타틴"],
    "타시그나": [],  # 닐로티닙 — 시드 데이터에 아직 없음
}


def _normalize_drug_names(raw_names: list[str]) -> list[str]:
    """OCR 제품명을 성분명(generic name)으로 변환한다.

    1) 브랜드 매핑에 해당하면 성분명으로 치환
    2) 제품명에서 제형·용량 접미사를 제거하여 핵심 약품명 추출
    3) 원본도 함께 반환 (시드 데이터에 제품명이 있을 수 있으므로)
    """
    result: set[str] = set()

    for raw in raw_names:
        result.add(raw)  # 원본 유지

        # 브랜드 → 성분 매핑
        for brand, generics in _BRAND_TO_GENERIC.items():
            if brand in raw:
                result.update(generics)

        # 제형·용량 접미사 제거: "아목시실린캡슐500mg" → "아목시실린"
        cleaned = re.sub(
            r"(정|캡슐|서방정|필름코팅정|산|시럽|현탁액|주사|크림|연고|겔)"
            r"[\s]*[\d.]*\s*(mg|g|ml|mcg|iu|%)?.*$",
            "",
            raw,
            flags=re.IGNORECASE,
        ).strip()
        if cleaned and cleaned != raw:
            result.add(cleaned)

    return list(result)


# 사용자 질문에서 섹션을 추론하기 위한 키워드 매핑
_SECTION_KEYWORDS: dict[str, list[str]] = {
    "side_effects": ["부작용", "졸리", "졸음", "어지러", "메스꺼", "구역", "설사", "두통", "발진"],
    "dosage": ["식전", "식후", "복용", "먹는 방법", "용량", "용법", "몇 알", "몇 번"],
    "interactions": ["같이 먹", "함께 복용", "상호작용", "병용", "술", "음주", "자몽"],
    "precautions": ["주의", "임산부", "임신", "수유", "금기", "조심", "어린이", "노인", "고령"],
    "efficacy": ["효과", "효능", "어디에 쓰", "무슨 약", "뭐에 좋"],
    "storage": ["보관", "냉장", "유통기한", "상온"],
}


def detect_sections(query: str) -> list[str]:
    """사용자 질문에서 관련 섹션을 키워드 매칭으로 추출한다.

    매칭되는 섹션이 없으면 기본값(dosage, precautions)을 반환한다.
    """
    matched: set[str] = set()
    for section, keywords in _SECTION_KEYWORDS.items():
        for kw in keywords:
            if kw in query:
                matched.add(section)
                break
    return list(matched) if matched else list(config.RAG_DEFAULT_SECTIONS)


def format_retrieved_docs(docs: list[dict]) -> str:
    """검색된 문서 목록을 LLM context용 텍스트로 포맷팅한다.

    각 문서는 "[약품명 - 섹션]\\n내용" 형태로 출력된다.
    전체 길이가 RAG_MAX_CONTEXT_CHARS를 초과하면 해당 지점에서 중단한다.
    """
    parts: list[str] = []
    total_len = 0
    max_chars = config.RAG_MAX_CONTEXT_CHARS

    for doc in docs:
        entry = f"[{doc['drug_name']} - {doc['section']}]\n{doc['content']}"
        entry_len = len(entry)

        if total_len + entry_len > max_chars:
            remaining = max_chars - total_len
            if remaining > 50:
                parts.append(entry[:remaining] + "...")
            break

        parts.append(entry)
        total_len += entry_len

    return "\n\n".join(parts)


class RetrievalServiceBase(abc.ABC):
    @abc.abstractmethod
    async def retrieve(
        self, drug_names: list[str], query: str
    ) -> list[dict]:
        """약품명 목록과 사용자 질문을 받아 관련 문서를 반환한다.

        Returns:
            [{"drug_name": str, "section": str, "content": str}, ...]
        """
        ...


class KeywordRetrievalService(RetrievalServiceBase):
    """v1: 약품명 정규화 + 부분 매칭 + 섹션 키워드 매칭"""

    async def retrieve(
        self, drug_names: list[str], query: str
    ) -> list[dict]:
        sections = detect_sections(query)

        # 1) 약품명 정규화 (브랜드→성분, 접미사 제거)
        normalized = _normalize_drug_names(drug_names)
        logger.info("[RAG] normalized_names=%s (from %s)", normalized, drug_names)

        # 2) 정확 매칭 시도
        docs = await DrugDocument.filter(
            drug_name__in=normalized, section__in=sections
        )

        # 3) 정확 매칭 0건이면 부분 매칭(icontains) 시도
        if not docs:
            q = Q()
            for name in normalized:
                if len(name) >= 2:  # 너무 짧은 문자열 제외
                    q |= Q(drug_name__icontains=name)
            if q:
                docs = await DrugDocument.filter(q, section__in=sections)
                logger.info("[RAG] partial match found %d docs", len(docs))

        return [
            {"drug_name": d.drug_name, "section": d.section, "content": d.content}
            for d in docs
        ]


class DummyRetrievalService(RetrievalServiceBase):
    """테스트용 더미 검색 서비스. 빈 결과를 반환한다."""

    async def retrieve(
        self, drug_names: list[str], query: str
    ) -> list[dict]:
        return []


def get_retrieval_service() -> RetrievalServiceBase:
    if config.RAG_ENABLED:
        return KeywordRetrievalService()
    return DummyRetrievalService()
