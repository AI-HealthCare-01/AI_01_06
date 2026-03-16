"""수집된 약품 데이터 + 시드 데이터를 임베딩하여 FAISS 인덱스 생성.

e약은요 수집 데이터가 있으면 우선 사용하고, 없는 약품/섹션은
기존 seed_drugs.py 데이터로 보충합니다.

사용법:
    cd app
    python -m scripts.build_faiss_index

환경변수:
    OPENAI_API_KEY: OpenAI API 키 (임베딩 생성용)
    EMBEDDING_MODEL: 임베딩 모델 (기본값: text-embedding-3-small)
"""

import json
import os
import sys
from pathlib import Path

import faiss
import numpy as np
from openai import OpenAI

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM = 1536  # text-embedding-3-small 차원
BATCH_SIZE = 100

DATA_DIR = Path("data")
FAISS_DIR = DATA_DIR / "faiss"

SECTION_KR: dict[str, str] = {
    "efficacy": "효능효과",
    "dosage": "용법용량",
    "precautions": "주의사항",
    "interactions": "상호작용",
    "side_effects": "부작용",
    "storage": "보관방법",
}


def load_chunks() -> list[dict]:
    """e약은요 수집 데이터 + 시드 데이터를 통합 로드.

    e약은요 데이터가 있으면 우선, 없는 약품/섹션은 시드로 보충.
    """
    chunks: list[dict] = []

    # 1) e약은요 수집 데이터
    raw_path = DATA_DIR / "raw_drug_chunks.json"
    if raw_path.exists():
        raw_data = json.loads(raw_path.read_text())
        chunks.extend(raw_data)
        print(f"e약은요 데이터: {len(raw_data)} chunks 로드")
    else:
        print("e약은요 수집 데이터 없음 (data/raw_drug_chunks.json)")
        print("  → seed 데이터만 사용합니다.")
        print("  → e약은요 데이터 수집: python -m scripts.collect_drug_data")

    # 2) 시드 데이터 보충 (중복 방지)
    try:
        from scripts.seed_drugs import SEED_DATA
    except ImportError:
        print("시드 데이터 import 실패 — e약은요 데이터만 사용")
        return chunks

    seen = {(c["drug_name"], c["section"]) for c in chunks}
    seed_added = 0

    for drug in SEED_DATA:
        for section, content in drug["sections"].items():
            if (drug["drug_name"], section) not in seen:
                chunks.append(
                    {
                        "drug_name": drug["drug_name"],
                        "drug_name_en": drug.get("drug_name_en", ""),
                        "section": section,
                        "content": content,
                        "source": drug.get("source", "의약품안전나라"),
                        "item_seq": None,
                    }
                )
                seed_added += 1

    print(f"시드 데이터 보충: {seed_added} chunks 추가")

    # 3) 동일 drug_name+section 중복 제거 (가장 긴 content 1개만 유지)
    best: dict[tuple[str, str], dict] = {}
    for c in chunks:
        key = (c["drug_name"], c["section"])
        if key not in best or len(c["content"]) > len(best[key]["content"]):
            best[key] = c
    before = len(chunks)
    chunks = list(best.values())
    print(f"중복 제거: {before} → {len(chunks)} chunks ({before - len(chunks)}건 제거)")

    return chunks


def create_embedding_text(chunk: dict) -> str:
    """임베딩용 텍스트 생성.

    약품명+섹션 한글명을 prefix로 추가하여
    검색 시 약품/섹션 컨텍스트를 반영한다.
    """
    sec_label = SECTION_KR.get(chunk["section"], chunk["section"])
    return f"{chunk['drug_name']} {sec_label}: {chunk['content']}"


def embed_batches(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """OpenAI 배치 임베딩. BATCH_SIZE 단위로 나눠 호출."""
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        resp = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        batch_embeddings = [d.embedding for d in resp.data]
        all_embeddings.extend(batch_embeddings)
        print(f"  임베딩 진행: {i + len(batch)}/{len(texts)}")

    return all_embeddings


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY 환경변수를 설정하세요.")
        print("  export OPENAI_API_KEY='sk-...'")
        sys.exit(1)

    FAISS_DIR.mkdir(parents=True, exist_ok=True)

    # 데이터 로드
    chunks = load_chunks()
    if not chunks:
        print("\n임베딩할 데이터가 없습니다.")
        print("다음 중 하나를 먼저 실행하세요:")
        print("  1) python -m scripts.collect_drug_data  (e약은요 수집)")
        print("  2) python -m scripts.seed_drugs          (시드 데이터 투입)")
        sys.exit(1)

    print(f"\n총 {len(chunks)} chunks 임베딩 시작 (model={EMBEDDING_MODEL})")

    # 임베딩 텍스트 생성
    texts = [create_embedding_text(c) for c in chunks]

    # 배치 임베딩
    client = OpenAI(api_key=api_key)
    all_embeddings = embed_batches(client, texts)

    # FAISS 인덱스 생성
    # cosine similarity = L2 정규화 후 내적 (IndexFlatIP)
    vectors = np.array(all_embeddings, dtype=np.float32)
    faiss.normalize_L2(vectors)

    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    index.add(vectors)

    # 인덱스 저장
    index_path = FAISS_DIR / "drug_index.faiss"
    faiss.write_index(index, str(index_path))

    # 메타데이터 저장
    metadata = []
    for i, chunk in enumerate(chunks):
        metadata.append(
            {
                "chunk_id": i,
                "drug_name": chunk["drug_name"],
                "drug_name_en": chunk.get("drug_name_en", ""),
                "section": chunk["section"],
                "content": chunk["content"],
                "source": chunk.get("source", ""),
                "item_seq": chunk.get("item_seq"),
            }
        )

    meta_path = FAISS_DIR / "drug_metadata.json"
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2))

    print("\nFAISS 인덱스 생성 완료:")
    print(f"  벡터 수: {index.ntotal}")
    print(f"  차원:   {EMBEDDING_DIM}")
    print(f"  모델:   {EMBEDDING_MODEL}")
    print(f"  인덱스:     {index_path}")
    print(f"  메타데이터: {meta_path}")


if __name__ == "__main__":
    main()
