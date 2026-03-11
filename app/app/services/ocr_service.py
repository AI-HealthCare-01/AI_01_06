import abc
import base64
import re
import time
import uuid

import httpx

from app import config

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
        result = self._parse_fields(texts)
        result["raw_texts"] = texts
        return result

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

    def _parse_fields(self, texts: list[str]) -> dict:
        """Raw OCR 텍스트 블록을 처방전 구조화 dict로 파싱.

        Clova OCR은 텍스트를 개별 블록으로 쪼개서 반환하므로,
        블록을 공백 없이 연결(joined)해서 키워드 위치를 찾은 뒤
        원래 블록 인덱스로 역추적하여 값을 추출합니다.
        """
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

        # ──── 1) 연결 문자열 + 인덱스 매핑 구성 ────
        # joined: 모든 블록을 공백 없이 이은 문자열
        # block_starts[i]: joined 내에서 i번 블록의 시작 위치
        joined = ""
        block_starts: list[int] = []
        for t in normalized:
            block_starts.append(len(joined))
            joined += t

        def _find_block_index(pos: int) -> int:
            """joined 내의 문자 위치(pos)가 속하는 블록 인덱스를 반환."""
            for i in range(len(block_starts) - 1, -1, -1):
                if pos >= block_starts[i]:
                    return i
            return 0

        def _get_next_value(block_idx: int, skip: int = 1) -> str | None:
            """block_idx 이후 skip 번째 블록의 값을 반환."""
            target = block_idx + skip
            if target < len(normalized):
                return normalized[target]
            return None

        # ──── 2) 병원명 파싱 ────
        # "명 칭", "명칭", "요양기관명", "의료기관명", "병원명" 등의 키워드 탐색
        hospital_keywords = ["요양기관명", "의료기관명", "병원명"]
        for kw in hospital_keywords:
            pos = joined.find(kw)
            if pos != -1:
                bi = _find_block_index(pos)
                val = _get_next_value(bi)
                if val:
                    result["hospital_name"] = val
                break

        if result["hospital_name"] is None:
            # "명 칭" 또는 "명칭" → 다음 블록이 병원명
            for kw in ["명칭"]:
                pos = joined.replace(" ", "").find(kw)
                if pos != -1:
                    # joined에서 실제 위치를 찾기 위해 원본 joined에서 탐색
                    for i, t in enumerate(normalized):
                        clean = t.replace(" ", "")
                        if "명" in clean and "칭" in clean:
                            val = _get_next_value(i)
                            if val and not any(x in val for x in ["전화", "번호", "팩스"]):
                                result["hospital_name"] = val
                            break
                    break

        # ──── 3) 처방의 파싱 ────
        doctor_keywords = ["처방의사성명", "처방의성명", "의사성명"]
        for kw in doctor_keywords:
            pos = joined.find(kw)
            if pos != -1:
                bi = _find_block_index(pos)
                # 다음 블록부터 값 탐색 (라벨 건너뛰기)
                for skip in range(1, 4):
                    val = _get_next_value(bi, skip)
                    if val and not any(x in val.replace(" ", "") for x in [
                        "면허", "번호", "종별", "기호"
                    ]):
                        result["doctor_name"] = val
                        break
                break

        # ──── 4) 처방일 파싱 ────
        # "교부번호" 바로 뒤, 또는 "YYYY년 MM월 DD일" 패턴 중 첫 번째
        date_pattern = re.compile(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일")
        match = date_pattern.search(joined)
        if match:
            y, m, d = match.group(1), match.group(2).zfill(2), match.group(3).zfill(2)
            result["prescription_date"] = f"{y}-{m}-{d}"

        # ──── 5) 진단명/질병분류기호 파싱 ────
        # 처방전에서 진단코드(C92.1 등)는 "질병분류기호" 키워드 앞에 위치함
        diag_keywords_forward = ["상병명", "진단명"]
        for kw in diag_keywords_forward:
            pos = joined.find(kw)
            if pos != -1:
                bi = _find_block_index(pos)
                for skip in range(1, 4):
                    val = _get_next_value(bi, skip)
                    if val and not any(x in val.replace(" ", "") for x in [
                        "처방의", "면허", "성명", "종별"
                    ]):
                        result["diagnosis"] = val
                        break
                break

        if result["diagnosis"] is None:
            # "질병분류기호" 키워드의 앞 블록에서 진단코드 탐색
            pos = joined.find("질병분류기호")
            if pos != -1:
                bi = _find_block_index(pos)
                # 키워드 앞의 블록들 중 진단코드 패턴(알파벳+숫자+점) 탐색
                for back in range(1, 5):
                    idx = bi - back
                    if idx >= 0:
                        val = normalized[idx]
                        # 진단코드 패턴: 알파벳+숫자+점 (예: C92.1, D68.6)
                        if re.search(r"[A-Z]\d", val):
                            # 연속된 진단코드 블록 합치기
                            codes = [val]
                            for k in range(idx + 1, bi):
                                if re.search(r"[A-Z]\d", normalized[k]):
                                    codes.append(normalized[k])
                            result["diagnosis"] = " ".join(codes)
                            break

        # ──── 6) 약품 테이블 파싱 ────
        # "내복약" 키워드로 약품 데이터 시작 지점 탐색
        med_start: int | None = None
        for i, t in enumerate(normalized):
            clean = t.replace(" ", "")
            if "내복약" in clean or "외용약" in clean or "주사약" in clean:
                med_start = i + 1
                break

        # "이하여백" 또는 "이하 여백"으로 약품 데이터 종료 지점 탐색
        med_end = len(normalized)
        for i, t in enumerate(normalized):
            if "이하" in t and "여백" in t.replace(" ", ""):
                med_end = i
                break
            if "이하여백" in t.replace(" ", ""):
                med_end = i
                break

        if med_start is not None and med_start < med_end:
            # 약품 영역에서 약품 추출
            # 패턴: 약품명(여러 블록) → 제품코드(9자리 숫자) → 투약량 → 횟수 → 일수 → 총량
            med_blocks = normalized[med_start:med_end]
            code_pattern = re.compile(r"^\d{8,10}$")

            current_name_parts: list[str] = []
            i = 0
            while i < len(med_blocks):
                block = med_blocks[i]
                clean = block.replace(" ", "")

                # 제품코드 발견 → 이전까지 모은 것이 약품명
                if code_pattern.match(clean):
                    drug_name = " ".join(current_name_parts).strip()
                    current_name_parts = []

                    # 코드 다음: 1회투약량, 횟수, 일수, 총량
                    # dosage가 숫자만이고 다음 블록이 단위(MG, T, C 등)이면 합치기
                    raw_dosage = med_blocks[i + 1] if i + 1 < len(med_blocks) else None
                    next_after_dosage = med_blocks[i + 2] if i + 2 < len(med_blocks) else None

                    extra_skip = 0
                    if (raw_dosage and raw_dosage.replace(" ", "").replace(".", "").isdigit()
                            and next_after_dosage
                            and next_after_dosage.strip().upper() in ("MG", "G", "ML", "T", "C", "TAB", "CAP")):
                        dosage = f"{raw_dosage} {next_after_dosage.strip()}"
                        extra_skip = 1
                    else:
                        dosage = raw_dosage

                    frequency = med_blocks[i + 2 + extra_skip] if i + 2 + extra_skip < len(med_blocks) else None
                    duration = med_blocks[i + 3 + extra_skip] if i + 3 + extra_skip < len(med_blocks) else None

                    if drug_name:
                        result["medications"].append({
                            "name": drug_name,
                            "dosage": dosage,
                            "frequency": f"1일 {frequency}회" if frequency and frequency.isdigit() else frequency,
                            "duration": f"{duration}일" if duration and duration.isdigit() else duration,
                            "instructions": None,
                        })
                    i += 5 + extra_skip  # 코드 + 투약량(+단위) + 횟수 + 일수 + 총량 건너뛰기
                    continue

                # "**" 같은 비약품 마커 건너뛰기
                if clean in ("**", "*", "SMC"):
                    i += 1
                    continue

                # 용법 정보 (아침, 저녁, 식후 등) → 마지막 약품에 instructions 추가
                usage_keywords = ["식후", "식전", "취침", "아침", "저녁", "점심", "복용"]
                if any(uk in clean for uk in usage_keywords) and result["medications"]:
                    # 용법 블록들을 모아서 마지막 약품의 instructions에 추가
                    usage_parts = [block]
                    j = i + 1
                    while j < len(med_blocks):
                        next_clean = med_blocks[j].replace(" ", "")
                        if any(uk in next_clean for uk in usage_keywords):
                            usage_parts.append(med_blocks[j])
                            j += 1
                        else:
                            break
                    usage_text = " ".join(usage_parts)
                    # 모든 약품에 동일한 용법 적용 (처방전에서 공통 용법인 경우)
                    for med in result["medications"]:
                        if med["instructions"] is None:
                            med["instructions"] = usage_text
                    i = j
                    continue

                # 일반 텍스트 → 약품명의 일부
                current_name_parts.append(block)
                i += 1

        return result


def get_ocr_service() -> OcrServiceBase:
    if config.NAVER_OCR_SECRET and config.NAVER_OCR_URL:
        return NaverOcrService(config.NAVER_OCR_SECRET, config.NAVER_OCR_URL)
    return DummyOcrService()
