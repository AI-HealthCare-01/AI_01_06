"""e약은요 API 응답 디버그 스크립트.

각 약물의 search_terms별로 실제 API 호출 → 응답 구조를 직접 확인한다.
수집 실패 원인(검색어 문제 / API 응답 구조 / 외용제 필터)을 판별한다.

사용법:
    cd app
    EAYAK_API_KEY='...' python -m scripts.debug_eayak_api
"""

import asyncio
import os
import sys

import httpx

API_URL = "http://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"
API_KEY = os.environ.get("EAYAK_API_KEY", "")

# 외용제 필터 (collect_drug_data.py와 동일)
TOPICAL_KEYWORDS = ["크림", "연고", "겔", "로션", "액", "외용", "점안", "점이", "점비"]

# 디버그 대상: 미수집 약물 중심 + 프레드니솔론(외용제 필터 확인)
DEBUG_TARGETS: list[dict] = [
    {"generic": "암로디핀", "search_terms": ["암로디핀", "노바스크"]},
    {"generic": "메트포르민", "search_terms": ["메트포르민", "글루코파지"]},
    {"generic": "아토르바스타틴", "search_terms": ["아토르바스타틴", "리피토"]},
    {"generic": "와파린", "search_terms": ["와파린", "쿠마딘"]},
    {"generic": "졸피뎀", "search_terms": ["졸피뎀", "스틸녹스"]},
    {"generic": "프레드니솔론", "search_terms": ["프레드니솔론", "소론도"]},
    {"generic": "오메프라졸", "search_terms": ["오메프라졸", "로섹"]},
    {"generic": "디곡신", "search_terms": ["디곡신"]},
    # 수집 성공 약물 1개 (비교용)
    {"generic": "아스피린", "search_terms": ["아스피린"]},
]


async def debug_search(client: httpx.AsyncClient, term: str) -> dict:
    """단일 검색어로 API 호출 → raw 응답 반환."""
    params = {
        "serviceKey": API_KEY,
        "itemName": term,
        "type": "json",
        "numOfRows": "5",
        "pageNo": "1",
    }
    try:
        resp = await client.get(API_URL, params=params, timeout=30)
        status = resp.status_code
        raw = resp.text[:500]

        if status != 200:
            return {"status": status, "error": raw, "items": []}

        data = resp.json()
        # e약은요 API 응답 구조 확인
        body = data.get("body", data)
        items = body.get("items", [])
        total = body.get("totalCount", "?")

        if not isinstance(items, list):
            items = []

        return {"status": status, "total": total, "items": items, "raw_keys": list(data.keys())}
    except Exception as e:
        return {"status": -1, "error": str(e), "items": []}


_SECTION_FIELDS: dict[str, str] = {
    "efcyQesitm": "효능",
    "useMethodQesitm": "용법",
    "atpnWarnQesitm": "주의(경고)",
    "atpnQesitm": "주의(일반)",
    "intrcQesitm": "상호작용",
    "seQesitm": "부작용",
    "depositMethodQesitm": "보관",
}


def _print_item_detail(i: int, item: dict) -> None:
    """단일 API 응답 item의 상세 정보를 출력한다."""
    item_name = item.get("itemName", "?")
    item_seq = item.get("itemSeq", "?")
    entp = item.get("entpName", "?")

    is_topical = any(kw in item_name for kw in TOPICAL_KEYWORDS)
    topical_mark = " [외용제-필터됨]" if is_topical else ""

    form_hints = []
    dosage = item.get("useMethodQesitm", "")
    if dosage:
        if "바르" in dosage:
            form_hints.append("바르는약")
        if "복용" in dosage or "먹" in dosage:
            form_hints.append("경구제")
    form_str = f" ({', '.join(form_hints)})" if form_hints else ""

    print(f"\n  [{i + 1}] {item_name}{topical_mark}{form_str}")
    print(f"      seq={item_seq}, 제조={entp}")

    for field, label in _SECTION_FIELDS.items():
        val = item.get(field, "")
        if val and isinstance(val, str):
            clean_len = len(val.replace("<p>", "").replace("</p>", "").strip())
            print(f"      {label:8s}: {clean_len:4d}자")
        else:
            print(f"      {label:8s}: (없음)")


async def main() -> None:
    if not API_KEY:
        print("EAYAK_API_KEY 환경변수를 설정하세요.")
        sys.exit(1)

    print("e약은요 API 디버그")
    print(f"API URL: {API_URL}")
    print(f"API KEY: {API_KEY[:8]}...{API_KEY[-4:]}")
    print()

    async with httpx.AsyncClient() as client:
        for drug in DEBUG_TARGETS:
            generic = drug["generic"]
            print(f"{'=' * 60}")
            print(f" {generic}")
            print(f"{'=' * 60}")

            for term in drug["search_terms"]:
                result = await debug_search(client, term)
                items = result["items"]

                print(f'\n  검색어: "{term}"')
                print(f"  HTTP {result['status']}, totalCount={result.get('total', '?')}, items={len(items)}")

                if result.get("error"):
                    print(f"  ERROR: {result['error'][:200]}")
                    continue

                if not items:
                    print("  -> 결과 없음")
                    continue

                for i, item in enumerate(items):
                    _print_item_detail(i, item)

            print()


if __name__ == "__main__":
    asyncio.run(main())
