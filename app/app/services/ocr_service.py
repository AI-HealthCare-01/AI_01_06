import abc
import base64
import json
import logging
import os
import re
import time
import uuid

import httpx
from openai import AsyncOpenAI

from app import config

logger = logging.getLogger(__name__)

_OCR_SYSTEM_PROMPT = "당신은 한국 처방전 OCR 텍스트를 분석하는 전문가입니다. 정확한 정보 추출만 수행합니다."

_OCR_EXTRACT_PROMPT = """다음은 한국 처방전 이미지에서 OCR로 추출한 텍스트 블록들입니다:

{ocr_text}

위 텍스트에서 처방전 정보를 추출하여 아래 JSON 형식으로만 응답하세요.
추출할 수 없는 항목은 null로 표시하세요.
약품이 여러 개면 medications 배열에 모두 포함하세요.

{{
  "hospital_name": "병원/의료기관명 (테이블 헤더나 양식 텍스트가 아닌 실제 기관명)",
  "doctor_name": "처방 의사 성명 (사람 이름만, 면허번호 등 제외)",
  "prescription_date": "처방일 (YYYY-MM-DD 형식)",
  "diagnosis": "질병분류기호 또는 진단명 (예: C92.1, D68.6)",
  "medications": [
    {{
      "name": "약품명 (제품코드 제외, 약품 이름만)",
      "dosage": "1회 투여량 (예: 300 MG, 1 T)",
      "frequency": "복용방법 (예: 1일 2회 아침,저녁 식후30분 복용)",
      "duration": "총투여일수 (예: 60일)",
      "instructions": "추가 지시사항"
    }}
  ]
}}"""

_MED_TABLE_HEADER = "처방의약품의명칭"
_NUM_MED_COLS = 5  # 처방의약품의명칭 | 1회투여량 | 1일투여횟수 | 총투여일수 | 용법


class OcrServiceBase(abc.ABC):
    @abc.abstractmethod
    async def extract(self, image_path: str) -> dict: ...


class DummyOcrService(OcrServiceBase):
    """Stub OCR that returns sample prescription data.
    Replace with NaverOcrService for production.
    """

    async def extract(self, image_path: str) -> dict:
        return {
            "hospital_name": "서울대학교병원",
            "doctor_name": "김의사",
            "prescription_date": "2026-02-25",
            "diagnosis": "당뇨병, 고혈압",
            "medications": [
                {
                    "name": "아스피린",
                    "dosage": "100mg",
                    "frequency": "1일 1회 아침 식후",
                    "duration": "30일",
                    "instructions": "충분한 물과 함께 복용",
                },
                {
                    "name": "메트포르민",
                    "dosage": "500mg",
                    "frequency": "1일 2회 아침/저녁 식후",
                    "duration": "30일",
                    "instructions": "식사 직후 복용",
                },
            ],
        }


class NaverOcrService(OcrServiceBase):
    """Naver Clova OCR integration."""

    def __init__(self, secret: str, url: str) -> None:
        self.secret = secret
        self.url = url

    async def extract(self, image_path: str) -> dict:
        texts = await self._call_clova_api(image_path)

        # LLM 파싱 우선, 실패 시 기존 규칙 파싱 fallback
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if api_key:
            try:
                result = await self._parse_with_llm(texts, api_key)
                result["raw_texts"] = texts
                return result
            except Exception:
                logger.warning("LLM OCR 파싱 실패, 규칙 파싱으로 fallback", exc_info=True)

        result = self._parse_fields(texts)
        result["raw_texts"] = texts
        return result

    @staticmethod
    async def _parse_with_llm(texts: list[str], api_key: str) -> dict:
        """OCR 텍스트를 LLM으로 구조화."""
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        client = AsyncOpenAI(api_key=api_key)

        ocr_text = "\n".join(f"[{i}] {t}" for i, t in enumerate(texts))
        prompt = _OCR_EXTRACT_PROMPT.format(ocr_text=ocr_text)

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _OCR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        parsed = json.loads(response.choices[0].message.content)

        # 정규화: medications가 없으면 빈 리스트
        if "medications" not in parsed or not isinstance(parsed["medications"], list):
            parsed["medications"] = []

        return parsed

    async def _call_clova_api(self, image_path: str) -> list[str]:
        """Naver Clova OCR API 호출 후 인식된 텍스트 블록 리스트 반환."""
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        ext = image_path.rsplit(".", 1)[-1].lower()
        payload = {
            "version": "V2",
            "requestId": str(uuid.uuid4()),
            "timestamp": int(time.time() * 1000),
            "lang": "ko",
            "images": [{"format": ext, "name": "prescription", "data": image_data}],
        }
        headers = {
            "X-OCR-SECRET": self.secret,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()

        fields = response.json()["images"][0].get("fields", [])
        return [f["inferText"] for f in fields if f.get("inferText")]

    @staticmethod
    def _build_joined(normalized: list[str]) -> tuple[str, list[int]]:
        """블록 리스트를 공백 없이 연결한 문자열과 각 블록의 시작 위치를 반환."""
        joined = ""
        block_starts: list[int] = []
        for t in normalized:
            block_starts.append(len(joined))
            joined += t
        return joined, block_starts

    @staticmethod
    def _find_block_index(pos: int, block_starts: list[int]) -> int:
        """joined 내 문자 위치(pos)가 속하는 블록 인덱스를 반환."""
        for i in range(len(block_starts) - 1, -1, -1):
            if pos >= block_starts[i]:
                return i
        return 0

    @staticmethod
    def _get_next_value(normalized: list[str], block_idx: int, skip: int = 1) -> str | None:
        """block_idx 이후 skip 번째 블록의 값을 반환."""
        target = block_idx + skip
        if target < len(normalized):
            return normalized[target]
        return None

    def _extract_hospital_name(self, normalized: list[str], joined: str, block_starts: list[int]) -> str | None:
        """병원명 파싱."""
        for kw in ("요양기관명", "의료기관명", "병원명"):
            pos = joined.find(kw)
            if pos != -1:
                bi = self._find_block_index(pos, block_starts)
                val = self._get_next_value(normalized, bi)
                if val:
                    return val
                break

        # "명칭" 폴백
        if joined.replace(" ", "").find("명칭") != -1:
            for i, t in enumerate(normalized):
                clean = t.replace(" ", "")
                if "명" in clean and "칭" in clean:
                    val = self._get_next_value(normalized, i)
                    if val and not any(x in val for x in ("전화", "번호", "팩스")):
                        return val
                    break
        return None

    def _extract_doctor_name(self, normalized: list[str], joined: str, block_starts: list[int]) -> str | None:
        """처방의 성명 파싱."""
        for kw in ("처방의사성명", "처방의성명", "의사성명"):
            pos = joined.find(kw)
            if pos != -1:
                bi = self._find_block_index(pos, block_starts)
                for skip in range(1, 4):
                    val = self._get_next_value(normalized, bi, skip)
                    if val and not any(x in val.replace(" ", "") for x in ("면허", "번호", "종별", "기호")):
                        return val
                break
        return None

    @staticmethod
    def _extract_date(joined: str) -> str | None:
        """처방일 파싱 (YYYY년 MM월 DD일 또는 YYYY-MM-DD 패턴)."""
        match = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", joined)
        if match:
            y, m, d = match.group(1), match.group(2).zfill(2), match.group(3).zfill(2)
            return f"{y}-{m}-{d}"
        match = re.search(r"(\d{4}-\d{2}-\d{2})", joined)
        if match:
            return match.group(1)
        return None

    def _extract_diagnosis(self, normalized: list[str], joined: str, block_starts: list[int]) -> str | None:
        """진단명/질병분류기호 파싱."""
        for kw in ("상병명", "진단명"):
            pos = joined.find(kw)
            if pos != -1:
                bi = self._find_block_index(pos, block_starts)
                for skip in range(1, 4):
                    val = self._get_next_value(normalized, bi, skip)
                    if val and not any(x in val.replace(" ", "") for x in ("처방의", "면허", "성명", "종별")):
                        return val
                break

        # 질병분류기호 앞 블록에서 진단코드(알파벳+숫자) 탐색
        pos = joined.find("질병분류기호")
        if pos != -1:
            bi = self._find_block_index(pos, block_starts)
            for back in range(1, 5):
                idx = bi - back
                if idx >= 0 and re.search(r"[A-Z]\d", normalized[idx]):
                    codes = [normalized[idx]]
                    for k in range(idx + 1, bi):
                        if re.search(r"[A-Z]\d", normalized[k]):
                            codes.append(normalized[k])
                    return " ".join(codes)
        return None

    @staticmethod
    def _med_block_range(normalized: list[str]) -> tuple[int | None, int, bool]:
        """약품 테이블의 시작/종료 인덱스와 단순 포맷 여부를 반환.

        단순 포맷(simple=True): "처방의약품의명칭" 헤더 기반, _NUM_MED_COLS 열 그룹으로 파싱.
        코드 포맷(simple=False): "내복약" 등 마커 기반, 제품코드로 약품 경계 탐색.
        """
        med_start: int | None = None
        simple = False
        for i, t in enumerate(normalized):
            clean = t.replace(" ", "")
            if _MED_TABLE_HEADER in clean:
                med_start = i + _NUM_MED_COLS  # 헤더행 (_NUM_MED_COLS 개) 건너뛰기
                simple = True
                break
            if any(kw in clean for kw in ("내복약", "외용약", "주사약")):
                med_start = i + 1
                break
        med_end = len(normalized)
        for i, t in enumerate(normalized):
            clean = t.replace(" ", "")
            if ("이하" in t and "여백" in clean) or "이하여백" in clean:
                med_end = i
                break
        return med_start, med_end, simple

    @staticmethod
    def _parse_medications_simple(med_blocks: list[str]) -> list[dict]:
        """단순 포맷: _NUM_MED_COLS 블록 단위 그룹으로 약품 파싱."""
        medications = []
        i = 0
        while i + _NUM_MED_COLS <= len(med_blocks):
            name, dosage, freq, dur, instr = med_blocks[i : i + _NUM_MED_COLS]
            medications.append(
                {
                    "name": name,
                    "dosage": dosage,
                    "frequency": f"1일 {freq}회" if freq and freq.isdigit() else freq,
                    "duration": f"{dur}일" if dur and dur.isdigit() else dur,
                    "instructions": instr or None,
                }
            )
            i += _NUM_MED_COLS
        return medications

    @staticmethod
    def _parse_dosage(med_blocks: list[str], i: int) -> tuple[str | None, int]:
        """투약량과 단위 병합 여부를 반환. (dosage, extra_skip)"""
        raw_dosage = med_blocks[i + 1] if i + 1 < len(med_blocks) else None
        next_after = med_blocks[i + 2] if i + 2 < len(med_blocks) else None
        _units = ("MG", "G", "ML", "T", "C", "TAB", "CAP")
        if (
            raw_dosage
            and raw_dosage.replace(" ", "").replace(".", "").isdigit()
            and next_after
            and next_after.strip().upper() in _units
        ):
            return f"{raw_dosage} {next_after.strip()}", 1
        return raw_dosage, 0

    @staticmethod
    def _apply_usage(med_blocks: list[str], i: int, medications: list[dict], usage_keywords: tuple) -> int:
        """용법 블록들을 마지막 약품 instructions에 추가하고 다음 인덱스를 반환."""
        usage_parts = [med_blocks[i]]
        j = i + 1
        while j < len(med_blocks) and any(uk in med_blocks[j].replace(" ", "") for uk in usage_keywords):
            usage_parts.append(med_blocks[j])
            j += 1
        usage_text = " ".join(usage_parts)
        for med in medications:
            if med["instructions"] is None:
                med["instructions"] = usage_text
        return j

    @staticmethod
    def _extract_medications(normalized: list[str]) -> list[dict]:
        """약품 테이블 파싱."""
        med_start, med_end, simple = NaverOcrService._med_block_range(normalized)
        if med_start is None or med_start >= med_end:
            return []

        med_blocks = normalized[med_start:med_end]
        if simple:
            return NaverOcrService._parse_medications_simple(med_blocks)

        code_pattern = re.compile(r"^\d{8,10}$")
        usage_keywords = ("식후", "식전", "취침", "아침", "저녁", "점심", "복용")
        medications: list[dict] = []
        current_name_parts: list[str] = []
        i = 0

        while i < len(med_blocks):
            block = med_blocks[i]
            clean = block.replace(" ", "")

            if code_pattern.match(clean):
                drug_name = " ".join(current_name_parts).strip()
                current_name_parts = []
                dosage, extra_skip = NaverOcrService._parse_dosage(med_blocks, i)
                frequency = med_blocks[i + 2 + extra_skip] if i + 2 + extra_skip < len(med_blocks) else None
                duration = med_blocks[i + 3 + extra_skip] if i + 3 + extra_skip < len(med_blocks) else None
                if drug_name:
                    medications.append(
                        {
                            "name": drug_name,
                            "dosage": dosage,
                            "frequency": f"1일 {frequency}회" if frequency and frequency.isdigit() else frequency,
                            "duration": f"{duration}일" if duration and duration.isdigit() else duration,
                            "instructions": None,
                        }
                    )
                i += 5 + extra_skip
                continue

            if clean in ("**", "*", "SMC"):
                i += 1
                continue

            if any(uk in clean for uk in usage_keywords) and medications:
                i = NaverOcrService._apply_usage(med_blocks, i, medications, usage_keywords)
                continue

            current_name_parts.append(block)
            i += 1

        return medications

    def _parse_fields(self, texts: list[str]) -> dict:
        """Raw OCR 텍스트 블록을 처방전 구조화 dict로 파싱."""
        normalized = [t.strip() for t in texts if t.strip()]
        result: dict = {
            "hospital_name": None,
            "doctor_name": None,
            "prescription_date": None,
            "diagnosis": None,
            "medications": [],
        }
        if not normalized:
            return result

        joined, block_starts = self._build_joined(normalized)
        result["hospital_name"] = self._extract_hospital_name(normalized, joined, block_starts)
        result["doctor_name"] = self._extract_doctor_name(normalized, joined, block_starts)
        result["prescription_date"] = self._extract_date(joined)
        result["diagnosis"] = self._extract_diagnosis(normalized, joined, block_starts)
        result["medications"] = self._extract_medications(normalized)
        return result


def get_ocr_service() -> OcrServiceBase:
    if config.NAVER_OCR_SECRET and config.NAVER_OCR_URL:
        return NaverOcrService(config.NAVER_OCR_SECRET, config.NAVER_OCR_URL)
    return DummyOcrService()
