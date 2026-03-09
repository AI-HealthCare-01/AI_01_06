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

- [x] 3-1. (행위) Redis 연결 + arq enqueue 헬퍼
- [x] 3-2. (행위) prescriptions.py: OCR 직접호출 → 태스크 발행
- [x] 3-3. (행위) guides.py: LLM 직접호출 → 태스크 발행
- [x] 3-4. (행위) ai_worker 태스크 구현 (ocr_task, guide_task)
- [x] 3-5. (행위) DB: SQLite → MySQL (프로덕션), 테스트는 SQLite 유지

## Phase 4: 프론트엔드 대응

- [x] 4-1. (행위) 프론트에서 비동기 상태(processing/generating) 폴링 처리

## Phase 5: 스트리밍 챗봇 — 구조 변경

- [x] 5-1. (구조) ChatThread / ChatMessage / ChatFeedback 모델 + DB/conftest/worker 모듈 등록
- [x] 5-2. (구조) ChatService ABC + DummyService + OpenAIService + factory
- [x] 5-3. (구조) Pydantic 스키마 + Chat API 라우터 + config 추가
- [x] 5-4. (구조) nginx SSE 설정 추가
- [x] 5-5. (구조) 프론트엔드 API 클라이언트 채팅 메서드 + SSE 헬퍼

## Phase 6: 스트리밍 챗봇 — 행위 변경

- [x] 6-1. (행위) Thread CRUD + 제목 자동 생성
- [x] 6-2. (행위) 메시지 전송 + SSE 스트리밍 + 상태 관리
- [x] 6-3. (행위) LLM 컨텍스트 구성 (completed만 포함, failed/streaming 제외)
- [x] 6-4. (행위) OpenAIChatService 구현
- [x] 6-5. (행위) 메시지 피드백 + 세션 종료 피드백
- [x] 6-6. (행위) 메시지 목록 조회

## Phase 7: 프론트엔드 채팅 UI

- [x] 7-1. (행위) 채팅 페이지 전면 개편 (SSE 스트리밍 + 퀵 액션 + 상태 관리)
- [ ] 7-2. (행위) 대화 종료 피드백 모달
- [ ] 7-3. (행위) 대화 기록 페이지
- [ ] 7-4. (행위) 대화 상세 조회 페이지
