import abc
import json
import logging
import re
from pathlib import Path

import numpy as np
from openai import AsyncOpenAI
from tortoise.expressions import Q

from app import config
from app.models.drug_document import DrugDocument

logger = logging.getLogger(__name__)

# ── FAISS 인덱스 경로 ──
_FAISS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "faiss"

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


# ── e약은요 기반 브랜드 매핑 (파일 기반, 모듈 로드 시 1회) ──
def _load_brand_map() -> dict[str, str]:
    """data/faiss/drug_name_map.json에서 브랜드→성분 매핑 로드."""
    path = _FAISS_DIR / "drug_name_map.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            logger.warning("브랜드 매핑 파일 로드 실패", exc_info=True)
    return {}


_BRAND_MAP_EAYAK: dict[str, str] = _load_brand_map()


def _normalize_drug_names_v2(raw_names: list[str]) -> list[str]:
    """v2: 기존 하드코딩 매핑 + e약은요 매핑 병합.

    기존 _normalize_drug_names 결과에 e약은요 브랜드→성분 매핑을 추가.
    """
    result = set(_normalize_drug_names(raw_names))

    for raw in raw_names:
        for brand, generic in _BRAND_MAP_EAYAK.items():
            if brand in raw or raw in brand:
                result.add(generic)

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
    async def retrieve(self, drug_names: list[str], query: str) -> list[dict]:
        """약품명 목록과 사용자 질문을 받아 관련 문서를 반환한다.

        Returns:
            [{"drug_name": str, "section": str, "content": str}, ...]
        """
        ...

    async def retrieve_all(self, drug_names: list[str]) -> list[dict]:
        """약품명 목록의 전체 섹션을 반환한다 (가이드 생성용).

        기본 구현은 빈 query로 retrieve를 호출한다.
        서브클래스에서 최적화된 구현으로 오버라이드 가능.
        """
        return await self.retrieve(drug_names, "")


class KeywordRetrievalService(RetrievalServiceBase):
    """v1: 약품명 정규화 + 부분 매칭 + 섹션 키워드 매칭"""

    async def retrieve(self, drug_names: list[str], query: str) -> list[dict]:
        sections = detect_sections(query)

        # 1) 약품명 정규화 (브랜드→성분, 접미사 제거)
        normalized = _normalize_drug_names(drug_names)
        logger.info("[RAG] normalized_names=%s (from %s)", normalized, drug_names)
        print(f"[RAG-DEBUG] normalized={normalized}, sections={sections}")

        # 2) 정확 매칭 시도
        docs = await DrugDocument.filter(drug_name__in=normalized, section__in=sections)
        print(f"[RAG-DEBUG] exact_match={len(docs)} docs")

        # 3) 정확 매칭 0건이면 부분 매칭(icontains) 시도
        if not docs:
            q = Q()
            for name in normalized:
                if len(name) >= 2:  # 너무 짧은 문자열 제외
                    q |= Q(drug_name__icontains=name)
            if q:
                docs = await DrugDocument.filter(q, section__in=sections)
                print(f"[RAG-DEBUG] partial_match={len(docs)} docs")
                logger.info("[RAG] partial match found %d docs", len(docs))

        return [{"drug_name": d.drug_name, "section": d.section, "content": d.content} for d in docs]

    async def retrieve_all(self, drug_names: list[str]) -> list[dict]:
        """전 섹션 조회 (가이드 생성용)."""
        normalized = _normalize_drug_names(drug_names)
        docs = await DrugDocument.filter(drug_name__in=normalized)
        if not docs:
            q = Q()
            for name in normalized:
                if len(name) >= 2:
                    q |= Q(drug_name__icontains=name)
            if q:
                docs = await DrugDocument.filter(q)
        return [{"drug_name": d.drug_name, "section": d.section, "content": d.content} for d in docs]


# ── FAISS 벡터 검색 서비스 ──

_faiss_instance: "FAISSRetrievalService | None" = None


class FAISSRetrievalService(RetrievalServiceBase):
    """v2: FAISS 벡터 검색 + 처방 약품 메타데이터 필터링.

    FAISS 인덱스와 메타데이터 JSON을 로드하여
    사용자 질문의 의미적 유사도 기반으로 약품 정보를 검색한다.
    검색 결과는 처방 약품명으로 필터링되어 반환된다.
    """

    def __init__(self) -> None:
        import faiss as _faiss

        self._faiss = _faiss

        index_path = _FAISS_DIR / "drug_index.faiss"
        meta_path = _FAISS_DIR / "drug_metadata.json"

        if not index_path.exists() or not meta_path.exists():
            raise FileNotFoundError(
                f"FAISS 인덱스를 찾을 수 없습니다: {_FAISS_DIR}. "
                "python -m scripts.build_faiss_index 를 먼저 실행하세요."
            )

        self.index = _faiss.read_index(str(index_path))
        self.metadata: list[dict] = json.loads(meta_path.read_text())
        self._client: AsyncOpenAI | None = None

        # drug_name 기준 메타데이터 인덱스 (retrieve_all 최적화)
        self._meta_by_drug: dict[str, list[dict]] = {}
        for meta in self.metadata:
            self._meta_by_drug.setdefault(meta["drug_name"], []).append(meta)

        logger.info("[FAISS] 인덱스 로드 완료: %d vectors, %d drugs", self.index.ntotal, len(self._meta_by_drug))

    def _get_client(self) -> AsyncOpenAI:
        """AsyncOpenAI 클라이언트를 lazy 초기화하여 반환."""
        if self._client is None:
            self._client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        return self._client

    async def _embed_query(self, query: str) -> np.ndarray:
        """사용자 질문을 임베딩 벡터로 변환."""
        client = self._get_client()
        resp = await client.embeddings.create(
            model=config.EMBEDDING_MODEL,
            input=query,
        )
        vec = np.array([resp.data[0].embedding], dtype=np.float32)
        self._faiss.normalize_L2(vec)
        return vec

    async def retrieve(self, drug_names: list[str], query: str) -> list[dict]:
        """의미 기반 벡터 검색 + 처방 약품명 필터."""
        # 1) 약품명 정규화 (하드코딩 + e약은요 매핑)
        normalized = _normalize_drug_names_v2(drug_names)
        normalized_set = set(normalized)
        logger.info("[FAISS-RAG] normalized=%s", normalized)

        # 2) 쿼리 임베딩
        query_vec = await self._embed_query(query)

        # 3) top-k 검색
        k = min(config.RAG_FAISS_TOP_K, self.index.ntotal)
        scores, indices = self.index.search(query_vec, k)

        # 4) 처방 약품 필터 + 유사도 임계값
        results: list[dict] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            meta = self.metadata[idx]

            # 처방 약품에 해당하는 문서만 통과
            if meta["drug_name"] not in normalized_set:
                continue

            # 유사도 임계값 미만은 무관한 내용
            if score < config.RAG_SIMILARITY_THRESHOLD:
                continue

            results.append(
                {
                    "drug_name": meta["drug_name"],
                    "section": meta["section"],
                    "content": meta["content"],
                    "score": float(score),
                }
            )

        # 5) 점수 내림차순 정렬
        results.sort(key=lambda x: x["score"], reverse=True)
        logger.info("[FAISS-RAG] %d results (from %d candidates)", len(results), k)
        return results

    async def retrieve_all(self, drug_names: list[str]) -> list[dict]:
        """전 섹션 메타데이터 직접 조회 (벡터 검색 불필요, 가이드 생성용).

        _meta_by_drug dict index를 사용하여 O(1) 조회.
        """
        normalized = _normalize_drug_names_v2(drug_names)
        results: list[dict] = []

        for name in normalized:
            for meta in self._meta_by_drug.get(name, []):
                results.append(
                    {
                        "drug_name": meta["drug_name"],
                        "section": meta["section"],
                        "content": meta["content"],
                    }
                )

        logger.info("[FAISS-RAG] retrieve_all: %d docs for %s", len(results), drug_names)
        return results


class DummyRetrievalService(RetrievalServiceBase):
    """테스트용 더미 검색 서비스. 빈 결과를 반환한다."""

    async def retrieve(self, drug_names: list[str], query: str) -> list[dict]:
        return []

    async def retrieve_all(self, drug_names: list[str]) -> list[dict]:
        return []


def get_retrieval_service() -> RetrievalServiceBase:
    """RAG 서비스 인스턴스를 반환한다.

    - RAG_ENABLED=true이고 FAISS 인덱스가 존재하면 FAISSRetrievalService (싱글톤)
    - FAISS 인덱스가 없으면 KeywordRetrievalService로 폴백
    - RAG_ENABLED=false이면 DummyRetrievalService
    """
    global _faiss_instance

    if config.RAG_ENABLED:
        # FAISS 싱글톤: 인덱스를 한 번만 로드
        if _faiss_instance is not None:
            return _faiss_instance
        try:
            _faiss_instance = FAISSRetrievalService()
            return _faiss_instance
        except (FileNotFoundError, ImportError) as e:
            logger.warning("[RAG] FAISS 사용 불가 (%s) — 키워드 검색으로 폴백", e)
            return KeywordRetrievalService()
    return DummyRetrievalService()
