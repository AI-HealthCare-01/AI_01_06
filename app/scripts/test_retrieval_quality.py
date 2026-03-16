"""FAISS Retrieval 품질 검증 스크립트 (오프라인, 서버 기동 불필요).

사용법:
    cd app
    RAG_ENABLED=true OPENAI_API_KEY='sk-...' python -m scripts.test_retrieval_quality
    RAG_ENABLED=true OPENAI_API_KEY='sk-...' python -m scripts.test_retrieval_quality --tier 3 4

Tier 1: 직접 매칭 (약품명 + 섹션 키워드 명시)
Tier 2: 의도 추론 (섹션 키워드 없이 자연어)
Tier 3: 브랜드명 → 성분명 정규화
Tier 4: 복수 약물 + 엣지 케이스
"""

import asyncio
import os
import sys
import time

# RAG_ENABLED 강제 활성화 (서버 config 무관하게)
os.environ.setdefault("RAG_ENABLED", "true")

from app.services.retrieval_service import FAISSRetrievalService  # noqa: E402

# ── 테스트 질문 세트 ──

TIER_1: list[dict] = [
    {
        "id": "T1-1",
        "query": "아목시실린 부작용 알려줘",
        "drug_names": ["아목시실린"],
        "expect_drug": "아목시실린",
        "expect_section": "side_effects",
    },
    {
        "id": "T1-2",
        "query": "메트포르민 복용법",
        "drug_names": ["메트포르민"],
        "expect_drug": "메트포르민",
        "expect_section": "dosage",
    },
    {
        "id": "T1-3",
        "query": "아스피린 주의사항",
        "drug_names": ["아스피린"],
        "expect_drug": "아스피린",
        "expect_section": "precautions",
    },
    {
        "id": "T1-4",
        "query": "로사르탄 보관방법",
        "drug_names": ["로사르탄"],
        "expect_drug": "로사르탄",
        "expect_section": "storage",
    },
    {
        "id": "T1-5",
        "query": "와파린 효능 효과",
        "drug_names": ["와파린"],
        "expect_drug": "와파린",
        "expect_section": "efficacy",
    },
]

TIER_2: list[dict] = [
    {
        "id": "T2-1",
        "query": "이부프로펜 하루에 몇 번 먹어요?",
        "drug_names": ["이부프로펜"],
        "expect_drug": "이부프로펜",
        "expect_section": "dosage",
    },
    {
        "id": "T2-2",
        "query": "세티리진 먹으면 졸려요?",
        "drug_names": ["세티리진"],
        "expect_drug": "세티리진",
        "expect_section": "side_effects",
    },
    {
        "id": "T2-3",
        "query": "암로디핀이랑 같이 먹으면 안 되는 약 있나요?",
        "drug_names": ["암로디핀"],
        "expect_drug": "암로디핀",
        "expect_section": "interactions",
    },
    {
        "id": "T2-4",
        "query": "프레드니솔론 오래 먹어도 괜찮나요?",
        "drug_names": ["프레드니솔론"],
        "expect_drug": "프레드니솔론",
        "expect_section": "precautions",
    },
    {
        "id": "T2-5",
        "query": "졸피뎀 어디에 보관하면 되나요?",
        "drug_names": ["졸피뎀"],
        "expect_drug": "졸피뎀",
        "expect_section": "storage",
    },
]


TIER_3: list[dict] = [
    {
        "id": "T3-1",
        "query": "타이레놀 부작용",
        "drug_names": ["타이레놀"],
        "expect_drug": "아세트아미노펜",
        "expect_section": "side_effects",
    },
    {
        "id": "T3-2",
        "query": "리피토 주의사항",
        "drug_names": ["리피토"],
        "expect_drug": "아토르바스타틴",
        "expect_section": "precautions",
    },
    {
        "id": "T3-3",
        "query": "글루코파지 복용법",
        "drug_names": ["글루코파지"],
        "expect_drug": "메트포르민",
        "expect_section": "dosage",
    },
    {
        "id": "T3-4",
        "query": "노바스크 효과가 뭐예요?",
        "drug_names": ["노바스크"],
        "expect_drug": "암로디핀",
        "expect_section": "efficacy",
    },
    {
        "id": "T3-5",
        "query": "스틸녹스 부작용",
        "drug_names": ["스틸녹스"],
        "expect_drug": "졸피뎀",
        "expect_section": "side_effects",
    },
]

TIER_4: list[dict] = [
    {
        "id": "T4-1",
        "query": "아스피린이랑 와파린 같이 먹어도 되나요?",
        "drug_names": ["아스피린", "와파린"],
        "expect_drug": "아스피린,와파린",
        "expect_section": "interactions",
    },
    {
        "id": "T4-2",
        "query": "아목시실린캡슐500mg 부작용",
        "drug_names": ["아목시실린캡슐500mg"],
        "expect_drug": "아목시실린",
        "expect_section": "side_effects",
    },
    {
        "id": "T4-3",
        "query": "가바펜틴 효과랑 부작용 둘 다 알려줘",
        "drug_names": ["가바펜틴"],
        "expect_drug": "가바펜틴",
        "expect_section": "efficacy,side_effects",
    },
    {
        "id": "T4-4",
        "query": "디곡신",
        "drug_names": ["디곡신"],
        "expect_drug": "디곡신",
        "expect_section": "dosage,precautions",
    },
    {
        "id": "T4-5",
        "query": "로사르탄 주의사항이랑 보관방법",
        "drug_names": ["로사르탄"],
        "expect_drug": "로사르탄",
        "expect_section": "precautions,storage",
    },
]


def _section_kr(section: str) -> str:
    return {
        "efficacy": "효능효과",
        "dosage": "용법용량",
        "precautions": "주의사항",
        "interactions": "상호작용",
        "side_effects": "부작용",
        "storage": "보관방법",
    }.get(section, section)


async def run_test(
    svc: FAISSRetrievalService, case: dict
) -> dict:
    """단일 테스트 케이스 실행 → 결과 dict 반환."""
    results = await svc.retrieve(case["drug_names"], case["query"])

    top3 = results[:3]

    # multi-section 지원: "efficacy,side_effects" → {"efficacy", "side_effects"}
    expect_sections = set(case["expect_section"].split(","))
    # multi-drug 지원
    expect_drugs = set(case.get("expect_drug", "").split(","))

    top1_hit = False
    top3_hit = False

    if top3:
        top1_hit = top3[0].get("section") in expect_sections
        top3_hit = any(r["section"] in expect_sections for r in top3)

    # multi-drug: 기대 약물이 결과에 포함되는지
    found_drugs = set(r["drug_name"] for r in results)
    drug_hit = bool(expect_drugs & found_drugs) if expect_drugs - {""} else True

    return {
        "id": case["id"],
        "query": case["query"],
        "drug_names": case["drug_names"],
        "expect_section": case["expect_section"],
        "expect_drug": case.get("expect_drug", ""),
        "total": len(results),
        "top3": [
            {
                "drug": r["drug_name"],
                "section": r["section"],
                "score": r.get("score", 0),
                "raw": r.get("_raw_score", r.get("score", 0)),
            }
            for r in top3
        ],
        "top1_hit": top1_hit,
        "top3_hit": top3_hit,
        "drug_hit": drug_hit,
        "found_drugs": sorted(found_drugs),
    }


def print_result(r: dict) -> None:
    print(f"\n┌─ {r['id']} ──────────────────────────────────────")
    print(f"│ 질문: {r['query']}")
    print(f"│ 입력 약물: {r['drug_names']}")
    print(f"│ 기대 섹션: {r['expect_section']} ({_section_kr(r['expect_section'])})")
    print(f"│ 반환 chunk 수: {r['total']}")
    print("│")

    if not r["top3"]:
        print("│ ⚠ 결과 없음 (0건)")
    else:
        for i, t in enumerate(r["top3"], 1):
            marker = "✓" if t["section"] == r["expect_section"] else " "
            raw_str = f" (raw={t['raw']:.4f})" if t["raw"] != t["score"] else ""
            print(
                f"│ Top-{i}: {t['drug']} / {t['section']}"
                f" ({_section_kr(t['section'])}) / score={t['score']:.4f}{raw_str} {marker}"
            )

    verdict = "PASS" if r["top1_hit"] else ("PASS(top3)" if r["top3_hit"] else "FAIL")
    drug_info = ""
    if r.get("expect_drug") and "," in r.get("expect_drug", ""):
        drug_info = f" | 약물매칭: {r.get('found_drugs', [])}"
    elif r.get("expect_drug") and r.get("found_drugs"):
        found = r["found_drugs"]
        expected = r["expect_drug"]
        if expected not in found:
            drug_info = f" | 약물매칭 실패: 기대={expected}, 결과={found}"
    print(f"│")
    print(f"│ 판정: {verdict}{drug_info}")
    print(f"└───────────────────────────────────────────────")


def print_scorecard(
    tier_name: str,
    results: list[dict],
    target_top1: int,
    target_top3: int,
) -> tuple[int, int]:
    top1_pass = sum(1 for r in results if r["top1_hit"])
    top3_pass = sum(1 for r in results if r["top3_hit"])
    total = len(results)

    print(f"\n{'='*50}")
    print(f" {tier_name} 스코어카드")
    print(f"{'='*50}")
    print(f"  Section Accuracy @1: {top1_pass}/{total}  (목표 {target_top1}/{total})")
    print(f"  Section Accuracy @3: {top3_pass}/{total}  (목표 {target_top3}/{total})")

    t1_ok = top1_pass >= target_top1
    t3_ok = top3_pass >= target_top3
    status = "PASS" if (t1_ok and t3_ok) else "FAIL"
    print(f"  판정: {status}")

    # 실패 케이스 요약
    fails = [r for r in results if not r["top3_hit"]]
    if fails:
        print(f"\n  실패 케이스:")
        for f in fails:
            scores = [t["score"] for t in f["top3"]] if f["top3"] else []
            print(f"    - {f['id']}: 기대={f['expect_section']}, scores={scores}")

    return top1_pass, top3_pass


async def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY 환경변수를 설정하세요.")
        sys.exit(1)

    # FAISS 서비스 초기화
    try:
        svc = FAISSRetrievalService()
    except FileNotFoundError as e:
        print(f"FAISS 인덱스 없음: {e}")
        sys.exit(1)

    print(f"FAISS 인덱스 로드 완료: {svc.index.ntotal} vectors")
    print(f"임베딩 모델: {os.environ.get('EMBEDDING_MODEL', 'text-embedding-3-small')}")
    print(f"threshold={float(os.environ.get('RAG_SIMILARITY_THRESHOLD', '0.2'))}, "
          f"top_k={int(os.environ.get('RAG_FAISS_TOP_K', '50'))}")

    # ── Tier 1 실행 ──
    print(f"\n{'#'*50}")
    print(f" Tier 1: 직접 매칭 (5개)")
    print(f"{'#'*50}")

    t1_results = []
    for case in TIER_1:
        r = await run_test(svc, case)
        t1_results.append(r)
        print_result(r)

    t1_top1, t1_top3 = print_scorecard("Tier 1 (직접 매칭)", t1_results, 5, 5)

    # ── Tier 2 실행 ──
    print(f"\n{'#'*50}")
    print(f" Tier 2: 의도 추론 (5개)")
    print(f"{'#'*50}")

    t2_results = []
    for case in TIER_2:
        r = await run_test(svc, case)
        t2_results.append(r)
        print_result(r)

    t2_top1, t2_top3 = print_scorecard("Tier 2 (의도 추론)", t2_results, 3, 4)

    # ── Tier 3-4 (옵션) ──
    tiers_to_run = set()
    if "--tier" in sys.argv:
        idx = sys.argv.index("--tier")
        for arg in sys.argv[idx + 1 :]:
            if arg.isdigit():
                tiers_to_run.add(int(arg))
            else:
                break
    run_all = not tiers_to_run  # --tier 없으면 1-2만 실행
    run_extended = bool(tiers_to_run & {3, 4})

    t3_top1 = t3_top3 = t4_top1 = t4_top3 = 0
    t3_results: list[dict] = []
    t4_results: list[dict] = []

    if 3 in tiers_to_run:
        print(f"\n{'#'*50}")
        print(f" Tier 3: 브랜드명 → 성분명 정규화 (5개)")
        print(f"{'#'*50}")
        for case in TIER_3:
            r = await run_test(svc, case)
            t3_results.append(r)
            print_result(r)
        t3_top1, t3_top3 = print_scorecard("Tier 3 (브랜드 정규화)", t3_results, 4, 4)

    if 4 in tiers_to_run:
        print(f"\n{'#'*50}")
        print(f" Tier 4: 복수 약물 + 엣지 케이스 (5개)")
        print(f"{'#'*50}")
        for case in TIER_4:
            r = await run_test(svc, case)
            t4_results.append(r)
            print_result(r)
        t4_top1, t4_top3 = print_scorecard("Tier 4 (복합/엣지)", t4_results, 3, 4)

    # ── 종합 스코어카드 ──
    all_results = t1_results + t2_results + t3_results + t4_results
    total = len(all_results)
    all_top1 = sum(1 for r in all_results if r["top1_hit"])
    all_top3 = sum(1 for r in all_results if r["top3_hit"])

    # score 분포
    all_scores = []
    for r in all_results:
        for t in r["top3"]:
            all_scores.append(t["score"])

    print(f"\n{'='*50}")
    print(f" 종합 스코어카드")
    print(f"{'='*50}")
    print(f"  Tier 1 @1: {t1_top1}/5  |  Tier 1 @3: {t1_top3}/5")
    print(f"  Tier 2 @1: {t2_top1}/5  |  Tier 2 @3: {t2_top3}/5")
    if t3_results:
        print(f"  Tier 3 @1: {t3_top1}/5  |  Tier 3 @3: {t3_top3}/5")
    if t4_results:
        print(f"  Tier 4 @1: {t4_top1}/5  |  Tier 4 @3: {t4_top3}/5")
    print(f"  전체  @1: {all_top1}/{total}  |  전체  @3: {all_top3}/{total}")

    if all_scores:
        print(f"\n  Score 분포:")
        print(f"    min={min(all_scores):.4f}  max={max(all_scores):.4f}"
              f"  avg={sum(all_scores)/len(all_scores):.4f}")

    overall = "PASS" if (t1_top1 >= 5 and t2_top3 >= 4) else "FAIL"
    print(f"\n  Tier 1-2 판정: {overall}")

    if run_extended:
        print()
        if t3_results:
            drug_hits = sum(1 for r in t3_results if r.get("drug_hit"))
            print(f"  Tier 3 약물 정규화 성공: {drug_hits}/5")
        if t4_results:
            drug_hits = sum(1 for r in t4_results if r.get("drug_hit"))
            print(f"  Tier 4 약물 매칭 성공: {drug_hits}/5")

    print()


if __name__ == "__main__":
    start = time.time()
    asyncio.run(main())
    elapsed = time.time() - start
    total_queries = len(TIER_1) + len(TIER_2)
    if "--tier" in sys.argv:
        idx = sys.argv.index("--tier")
        for arg in sys.argv[idx + 1 :]:
            if arg == "3":
                total_queries += len(TIER_3)
            elif arg == "4":
                total_queries += len(TIER_4)
            else:
                break
    print(f"총 소요 시간: {elapsed:.1f}초 (임베딩 API 호출 {total_queries}회)")
