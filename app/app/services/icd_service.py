"""ICD-10 상병코드 → 한글 질병명 변환 서비스.

조회 우선순위 (4-Layer):
1. curated_common.json  — 통상명 (감기, 고혈압 등 환자 친화적 표현)
2. icd_codes.json       — HIRA 공식 한글명 (21,299개)
3. NLM Clinical Tables  — 무료·무키 영문명 fallback
4. LLM 간소화          — 복잡한 공식명 → 쉬운 한국어 (OpenAI)
"""

import json
import logging
import os
import re
from functools import lru_cache

import httpx

logger = logging.getLogger(__name__)

_DIR = os.path.dirname(__file__)
_JSON_PATH = os.path.join(_DIR, "icd_codes.json")
_COMMON_PATH = os.path.join(_DIR, "curated_common.json")

# 간소화가 필요한 접두 패턴 (공식명에 붙는 수식어)
_VERBOSE_PREFIXES = re.compile(
    r"^(상세불명의|부위가 명시되지 않은|달리 분류되지 않은|기타|상세불명|"
    r"본태성\(원발성\)|본태성|원발성|이차성|특발성)\s+"
)


@lru_cache(maxsize=1)
def _load_icd_map() -> dict[str, str]:
    if not os.path.exists(_JSON_PATH):
        return {}
    with open(_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_common_map() -> dict[str, str]:
    if not os.path.exists(_COMMON_PATH):
        return {}
    with open(_COMMON_PATH, encoding="utf-8") as f:
        return json.load(f)


def _normalize_code(code: str) -> str:
    return code.replace(".", "").replace(" ", "").upper()


def lookup(code: str) -> str | None:
    """Layer 2: HIRA icd_codes.json에서 공식 한글명 조회."""
    return _load_icd_map().get(_normalize_code(code))


def lookup_common(code: str) -> str | None:
    """Layer 1: curated_common.json에서 통상명 조회."""
    return _load_common_map().get(_normalize_code(code))


def _strip_verbose_prefix(name: str) -> str:
    """공식명의 불필요한 수식어 제거: '상세불명의 위염' → '위염'."""
    return _VERBOSE_PREFIXES.sub("", name).strip()


async def _nlm_lookup(code: str) -> str | None:
    """Layer 3: NLM Clinical Tables — 무료, 키 없음, 영문명 반환."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(
                "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search",
                params={"sf": "code,name", "terms": code, "count": 3},
            )
            data = r.json()
            # 응답 형식: [totalCount, [codes], {}, [[code, name], ...]]
            if data[0] > 0 and data[3]:
                for row in data[3]:
                    if row[0].replace(".", "").upper() == _normalize_code(code):
                        return row[1]  # 영문명
    except Exception:
        logger.debug("NLM lookup failed for %s", code, exc_info=True)
    return None


async def _llm_simplify(name: str) -> str:
    """Layer 4: OpenAI로 복잡한 공식명 → 환자가 이해하기 쉬운 한국어 통상명."""
    from app import config

    if not config.OPENAI_API_KEY:
        return name
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "다음 의학 진단명을 환자가 이해하기 쉬운 한국어 통상명으로 변환하세요. "
                        "10자 이내로 간결하게, 의학 용어는 일반 표현으로 바꾸세요. "
                        "명칭만 출력하고 다른 설명은 하지 마세요."
                    ),
                },
                {"role": "user", "content": name},
            ],
            max_tokens=30,
            temperature=0,
        )
        simplified = resp.choices[0].message.content.strip()
        return simplified if simplified else name
    except Exception:
        logger.debug("LLM simplify failed for '%s'", name, exc_info=True)
        return name


async def lookup_with_fallback(code: str) -> str:
    """4단계 fallback으로 ICD 코드 → 통상명 반환."""
    # Layer 1: 통상명 (curated)
    common = lookup_common(code)
    if common:
        return common

    # Layer 2: HIRA 공식 한글명
    official = lookup(code)
    if official:
        stripped = _strip_verbose_prefix(official)
        # 공식명이 충분히 간결하면 그대로, 복잡하면 LLM 간소화
        if len(stripped) <= 12:
            return stripped
        return await _llm_simplify(stripped)

    # Layer 3: NLM Clinical Tables (영문 fallback)
    eng = await _nlm_lookup(code)
    if eng:
        # Layer 4: 영문명을 한국어로 간소화
        return await _llm_simplify(eng)

    return code  # 변환 실패 시 원본 코드 반환


async def resolve_diagnosis(raw: str | None) -> str | None:
    """OCR 진단명을 통상명으로 변환 (비동기).

    - 이미 한글이면: 수식어 제거만 적용
    - ICD 코드이면: 4단계 fallback으로 한글 통상명으로 변환
    - 복수 코드 지원, 중복 제거
    """
    if not raw:
        return raw

    # 이미 한글 포함 → 수식어만 제거
    if re.search(r"[가-힣]", raw):
        return _strip_verbose_prefix(raw)

    codes = [c.strip() for c in re.split(r"[,\s]+", raw) if c.strip()]
    if not codes:
        return raw

    seen: set[str] = set()
    names: list[str] = []
    for code in codes:
        name = await lookup_with_fallback(code)
        if name not in seen:
            seen.add(name)
            names.append(name)

    return ", ".join(names)


def normalize_dosage(dosage: str | None) -> str | None:
    """용량 단위를 소문자로 정규화: '300 MG' → '300 mg'."""
    if not dosage:
        return dosage
    return re.sub(
        r"\b(MG|ML|MCG|UG|IU)\b",
        lambda m: m.group().lower(),
        dosage,
        flags=re.IGNORECASE,
    )


_DOCTOR_BLACKLIST = frozenset(
    [
        "환자",
        "요구",
        "기관",
        "의료",
        "처방",
        "조제",
        "약국",
        "번호",
        "면허",
        "종별",
        "기호",
        "성명",
        "진료",
    ]
)


def validate_doctor_name(name: str | None) -> str | None:
    """OCR 의사명이 실제 사람 이름인지 검증. 아닌 경우 None 반환."""
    if not name:
        return None
    clean = re.sub(r"[^가-힣]", "", name)
    if not (2 <= len(clean) <= 4):
        return None
    if any(kw in clean for kw in _DOCTOR_BLACKLIST):
        return None
    return clean
