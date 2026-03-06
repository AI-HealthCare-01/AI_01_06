# Plan: Docker Compose + Worker 분리

## Phase 1: 긴급 코드 수정 (현 구조, 이동 전)

- [x] 1-1. (행위) python-jose → PyJWT, sha256 → bcrypt 직접 사용
- [x] 1-2. (구조) Tortoise pk=True → primary_key=True

## Phase 2: 디렉토리 구조 변경 (구조만)

- [x] 2-1. (구조) backend/ → app/, frontend/ → web/
- [x] 2-2. (구조) ai_worker/ 스캐폴딩 + services 이동
- [x] 2-3. (구조) uv workspace 설정 (루트 pyproject.toml)
- [x] 2-4. (구조) 인프라 파일 생성 (Dockerfile, docker-compose, nginx, envs)

## Phase 3: 행위 변경 (Redis + 비동기 태스크)

- [ ] 3-1. (행위) Redis 연결 + arq enqueue 헬퍼
- [ ] 3-2. (행위) prescriptions.py: OCR 직접호출 → 태스크 발행
- [ ] 3-3. (행위) guides.py: LLM 직접호출 → 태스크 발행
- [ ] 3-4. (행위) ai_worker 태스크 구현 (ocr_task, guide_task)
- [ ] 3-5. (행위) DB: SQLite → MySQL (프로덕션), 테스트는 SQLite 유지

## Phase 4: 프론트엔드 대응

- [ ] 4-1. (행위) 프론트에서 비동기 상태(processing/generating) 폴링 처리
