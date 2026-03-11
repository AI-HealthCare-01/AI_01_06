"""ICD-10 상병코드 → 한글 질병명 변환 서비스.

건강보험심사평가원 상병마스터에서 추출한 경량 JSON (코드:한글명) 사용.
"""

import json
import os
import re
from functools import lru_cache

_JSON_PATH = os.path.join(os.path.dirname(__file__), "icd_codes.json")


@lru_cache(maxsize=1)
def _load_icd_map() -> dict[str, str]:
    """JSON을 읽어 {코드: 한글명} dict 반환."""
    if not os.path.exists(_JSON_PATH):
        return {}
    with open(_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def lookup(code: str) -> str | None:
    """ICD 코드 하나를 한글 질병명으로 변환. 매핑 없으면 None."""
    icd = _load_icd_map()
    normalized = code.replace(".", "").replace(" ", "").upper()
    return icd.get(normalized)


def resolve_diagnosis(raw: str | None) -> str | None:
    """OCR 진단명을 한글 질병명으로 변환.

    한글 포함 시 원본 반환, 복수 코드 처리, 중복 제거.
    """
    if not raw:
        return raw
    if re.search(r"[가-힣]", raw):
        return raw

    codes = [c.strip() for c in re.split(r"[,\s]+", raw) if c.strip()]
    if not codes:
        return raw

    seen: set[str] = set()
    names: list[str] = []
    for code in codes:
        name = lookup(code) or code
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
    """OCR 의사명이 실제 사람 이름인지 검증. 아닌 경우 None 반환.

    유효 조건: 특수문자 제거 후 한글 2~4자, 블랙리스트 키워드 미포함.
    """
    if not name:
        return None
    clean = re.sub(r"[^가-힣]", "", name)
    if not (2 <= len(clean) <= 4):
        return None
    if any(kw in clean for kw in _DOCTOR_BLACKLIST):
        return None
    return clean
