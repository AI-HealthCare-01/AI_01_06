"""e약은요 OpenAPI에서 의약품 정보를 수집하여 JSON으로 저장.

사용법:
    cd app
    python -m scripts.collect_drug_data

환경변수:
    EAYAK_API_KEY: e약은요 API 인증키 (data.go.kr 발급)
"""

import asyncio
import json
import logging
import os
import re
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

API_URL = "http://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"
API_KEY = os.environ.get("EAYAK_API_KEY", "")

# 기존 seed_drugs.py 25종 기반 수집 대상
# generic: 내부 성분명, search_terms: e약은요 itemName 검색어 (성분명 + 대표 브랜드명)
TARGET_DRUGS: list[dict[str, str | list[str]]] = [
    {"generic": "아목시실린", "search_terms": ["아목시실린"]},
    {"generic": "아세트아미노펜", "search_terms": ["아세트아미노펜", "타이레놀"]},
    {"generic": "이부프로펜", "search_terms": ["이부프로펜", "부루펜"]},
    {"generic": "오메프라졸", "search_terms": ["오메프라졸", "로섹"]},
    {"generic": "메트포르민", "search_terms": ["메트포르민", "글루코파지"]},
    {"generic": "아스피린", "search_terms": ["아스피린"]},
    {"generic": "로사르탄", "search_terms": ["로사르탄", "코자"]},
    {"generic": "암로디핀", "search_terms": ["암로디핀", "노바스크"]},
    {"generic": "아토르바스타틴", "search_terms": ["아토르바스타틴", "리피토"]},
    {"generic": "세티리진", "search_terms": ["세티리진"]},
    {"generic": "로라타딘", "search_terms": ["로라타딘", "클라리틴"]},
    {"generic": "레보플록사신", "search_terms": ["레보플록사신", "크라비트"]},
    {"generic": "클라리스로마이신", "search_terms": ["클라리스로마이신", "클래리시드"]},
    {"generic": "프레드니솔론", "search_terms": ["프레드니솔론", "소론도"]},
    {"generic": "와파린", "search_terms": ["와파린", "쿠마딘"]},
    {"generic": "디곡신", "search_terms": ["디곡신"]},
    {"generic": "글리메피리드", "search_terms": ["글리메피리드", "아마릴"]},
    {"generic": "졸피뎀", "search_terms": ["졸피뎀", "스틸녹스"]},
    {"generic": "트라마돌", "search_terms": ["트라마돌"]},
    {"generic": "심바스타틴", "search_terms": ["심바스타틴", "조코"]},
    {"generic": "세팔렉신", "search_terms": ["세팔렉신", "세파렉신"]},
    {"generic": "푸로세미드", "search_terms": ["푸로세미드", "라닉스"]},
    {"generic": "판토프라졸", "search_terms": ["판토프라졸", "판토록"]},
    {"generic": "독시사이클린", "search_terms": ["독시사이클린"]},
    {"generic": "가바펜틴", "search_terms": ["가바펜틴", "뉴론틴"]},
]

# 외용제 제형 키워드 — 제품명에 포함되면 수집에서 제외
_TOPICAL_KEYWORDS: list[str] = ["크림", "연고", "겔", "로션", "액", "외용", "점안", "점이", "점비"]

# e약은요 API 필드 → 내부 section 매핑
FIELD_TO_SECTION: dict[str, str] = {
    "efcyQesitm": "efficacy",
    "useMethodQesitm": "dosage",
    "atpnWarnQesitm": "precautions",
    "atpnQesitm": "precautions",
    "intrcQesitm": "interactions",
    "seQesitm": "side_effects",
    "depositMethodQesitm": "storage",
}

MAX_CHUNK_LENGTH = 800


def _strip_html(text: str) -> str:
    """HTML 태그를 제거한다."""
    return re.sub(r"<[^>]+>", "", text).strip()


def _split_long_text(text: str, max_len: int = MAX_CHUNK_LENGTH) -> list[str]:
    """긴 텍스트를 문단 또는 마침표 기준으로 분할."""
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 1 > max_len and current:
            chunks.append(current.strip())
            current = para
        else:
            current = f"{current}\n{para}" if current else para

    if current.strip():
        chunks.append(current.strip())

    # 여전히 max_len 초과 chunk → 마침표 기준 재분할
    final: list[str] = []
    for chunk in chunks:
        if len(chunk) <= max_len:
            final.append(chunk)
        else:
            sentences = chunk.replace(". ", ".\n").split("\n")
            buf = ""
            for sent in sentences:
                if len(buf) + len(sent) + 1 > max_len and buf:
                    final.append(buf.strip())
                    buf = sent
                else:
                    buf = f"{buf} {sent}" if buf else sent
            if buf.strip():
                final.append(buf.strip())

    return final if final else [text]


async def fetch_drug_info(client: httpx.AsyncClient, drug_name: str) -> list[dict]:
    """단일 성분명으로 e약은요 검색."""
    if not API_KEY:
        logger.error("EAYAK_API_KEY 환경변수가 설정되지 않았습니다.")
        return []

    params = {
        "serviceKey": API_KEY,
        "itemName": drug_name,
        "type": "json",
        "numOfRows": "5",
        "pageNo": "1",
    }
    try:
        resp = await client.get(API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("body", {}).get("items", [])
        return items if isinstance(items, list) else []
    except Exception:
        logger.exception("e약은요 API 호출 실패: %s", drug_name)
        return []


def extract_chunks(items: list[dict], drug_name: str) -> tuple[list[dict], dict[str, str]]:
    """API 응답을 section별 chunk 리스트로 변환. 브랜드 매핑도 수집."""
    chunks: list[dict] = []
    brand_map: dict[str, str] = {}
    seen_content: set[str] = set()

    for item in items:
        item_seq = item.get("itemSeq", "")
        brand_name = item.get("itemName", "")

        # 외용제 제품 제외
        if any(kw in brand_name for kw in _TOPICAL_KEYWORDS):
            continue

        # 브랜드 → 성분 매핑 수집
        if brand_name and brand_name != drug_name:
            brand_map[brand_name] = drug_name

        for api_field, section in FIELD_TO_SECTION.items():
            content = item.get(api_field, "")
            if not content or not isinstance(content, str):
                continue

            content = _strip_html(content).strip()
            if len(content) < 10:
                continue

            # 중복 제거 (동일 약품·섹션·앞부분 80자)
            content_hash = f"{drug_name}:{section}:{content[:80]}"
            if content_hash in seen_content:
                continue
            seen_content.add(content_hash)

            # 긴 텍스트 분할
            text_parts = _split_long_text(content)
            for idx, part in enumerate(text_parts):
                chunks.append(
                    {
                        "drug_name": drug_name,
                        "drug_name_en": "",
                        "section": section,
                        "content": part,
                        "source": "e약은요",
                        "item_seq": item_seq,
                        "brand_name": brand_name,
                        "chunk_part": idx if len(text_parts) > 1 else None,
                    }
                )

    return chunks, brand_map


async def main() -> None:
    if not API_KEY:
        print("EAYAK_API_KEY 환경변수를 설정한 뒤 실행하세요.")
        print("  export EAYAK_API_KEY='your-api-key-here'")
        return

    output_dir = Path("data")
    faiss_dir = output_dir / "faiss"
    output_dir.mkdir(parents=True, exist_ok=True)
    faiss_dir.mkdir(parents=True, exist_ok=True)

    all_chunks: list[dict] = []
    all_brand_map: dict[str, str] = {}

    print(f"e약은요 데이터 수집 시작 (대상: {len(TARGET_DRUGS)}종)")
    print()

    async with httpx.AsyncClient() as client:
        for drug in TARGET_DRUGS:
            generic = drug["generic"]
            search_terms = drug["search_terms"]

            # search_terms를 순차 시도하여 결과 합산
            all_items: list[dict] = []
            seen_seqs: set[str] = set()
            for term in search_terms:
                items = await fetch_drug_info(client, term)
                for item in items:
                    seq = item.get("itemSeq", "")
                    if seq not in seen_seqs:
                        seen_seqs.add(seq)
                        all_items.append(item)

            if not all_items:
                print(f"  {generic}: API 결과 없음 (seed 데이터만 사용)")
                continue
            chunks, brand_map = extract_chunks(all_items, generic)
            all_chunks.extend(chunks)
            all_brand_map.update(brand_map)
            print(f"  {generic}: {len(chunks)} chunks from {len(all_items)} items (검색어: {search_terms})")

    # 수집 결과 저장
    raw_path = output_dir / "raw_drug_chunks.json"
    raw_path.write_text(json.dumps(all_chunks, ensure_ascii=False, indent=2))
    print(f"\n총 {len(all_chunks)} chunks → {raw_path}")

    # 브랜드 매핑 저장
    map_path = faiss_dir / "drug_name_map.json"
    map_path.write_text(json.dumps(all_brand_map, ensure_ascii=False, indent=2))
    print(f"브랜드 매핑 {len(all_brand_map)}건 → {map_path}")


if __name__ == "__main__":
    asyncio.run(main())
