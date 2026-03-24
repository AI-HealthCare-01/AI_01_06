# Project & Sullivan

처방전 OCR 인식, LLM 기반 맞춤형 복약 가이드 생성, 실시간 AI 챗봇을 제공하는 헬스케어 서비스입니다.

---

## 주요 기능

- **처방전 OCR**: 처방전 이미지를 업로드하면 Naver Clova OCR로 텍스트를 자동 추출
- **복약 가이드 생성**: 추출된 처방 데이터와 사용자 프로필(기저질환, 알러지)을 결합하여 LLM이 맞춤형 가이드 생성
- **실시간 AI 챗봇**: 처방전 맥락을 유지하며 복약 관련 질문에 스트리밍 방식으로 응답
- **보호자 연동**: 보호자가 환자의 처방전/가이드를 대리 관리할 수 있는 초대 기반 연동
- **소셜 로그인**: 카카오, 구글 OAuth 지원

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS |
| Backend | Python 3.13, FastAPI, Tortoise ORM, aiomysql |
| AI Worker | ARQ (Redis 기반 비동기 태스크 큐) |
| AI/API | OpenAI API (gpt-4o), Naver Clova OCR |
| Database | MySQL 8.4, Redis 7 |
| Infra | Docker, Nginx, AWS EC2, Let's Encrypt |
| 패키지 관리 | uv (Python), npm (Node.js) |
| 코드 품질 | Ruff (린트/포맷), Pytest |

---

## 프로젝트 구조

```
web/          → Next.js 프론트엔드 (사용자 UI)
app/          → FastAPI 백엔드 (HTTP API, 비즈니스 로직, DB)
ai_worker/    → ARQ 비동기 워커 (OCR, LLM 호출)
infra/        → Docker, Nginx, DB 초기화, 환경변수 예시
docs/         → API 스펙, 아키텍처, 요구사항 문서
```

### 백엔드 레이어 (`app/app/`)

```
api/          → FastAPI 라우터 (요청/응답 처리)
services/     → 비즈니스 로직 (ocr_service, guide_service 등)
models/       → Tortoise ORM 모델
schemas/      → Pydantic 입출력 스키마
core/         → 공통 유틸 (database, redis, security, response)
```

### AI 워커 (`ai_worker/worker/`)

API 서버와 분리된 비동기 태스크 처리:
- `ocr_task` — Naver Clova OCR로 처방전 이미지 텍스트 추출
- `guide_task` — OpenAI API로 맞춤형 복약 가이드 생성
- `chat_task` — 처방전 맥락 기반 실시간 챗봇 응답

---

## 시작하기

### 환경변수 준비

```bash
cp infra/env/example.local.env infra/env/.local.env
# .local.env 파일을 열어 실제 API 키와 DB 비밀번호를 설정
```

### Docker Compose 실행

```bash
# 전체 스택 기동
docker compose up -d --build

# HMR(Hot Module Replacement) 포함 개발 모드
docker compose up --build --watch
```

### 개별 실행

```bash
# 백엔드 의존성 설치
cd app && uv sync

# 프론트엔드 의존성 설치
cd web && npm install && npm run dev
```

### 테스트

```bash
cd app && uv run pytest          # 백엔드 테스트
cd ai_worker && uv run pytest    # AI 워커 테스트
```

### 린트

```bash
uv run ruff check .              # 린트 검사
uv run ruff format .             # 포맷팅
```

---

## 아키텍처

```
Client ──→ Nginx (:80/:443)
              ├──→ Next.js (:3000)    ← 프론트엔드
              └──→ FastAPI (:8000)    ← API 서버
                      ├──→ MySQL 8.4  ← 데이터 저장
                      ├──→ Redis 7    ← 캐시 + 태스크 큐
                      └──→ ARQ Worker ← OCR/LLM 비동기 처리
```

---

## API 주요 엔드포인트

| 도메인 | 메서드 | 경로 | 설명 |
|--------|--------|------|------|
| Auth | POST | /api/auth/signup | 회원가입 |
| Auth | POST | /api/auth/login | 로그인 |
| Auth | POST | /api/auth/refresh | 토큰 재발급 |
| User | GET | /api/users/me | 내 정보 조회 |
| Prescription | POST | /api/prescriptions | 처방전 업로드 (OCR) |
| Guide | POST | /api/guides/{id}/generate | 복약 가이드 생성 |
| Chat | POST | /api/chat/threads | 채팅 세션 생성 |
| Chat | GET | /api/chat/threads/{id}/stream | 스트리밍 응답 |
| Caregiver | POST | /api/caregivers/invite | 보호자 초대 |

---

## 환경변수

`infra/env/example.local.env` (로컬), `infra/env/example.prod.env` (운영) 참고.

| 변수 | 설명 |
|------|------|
| DATABASE_URL | MySQL 접속 URL |
| SECRET_KEY | JWT 서명 키 |
| OPENAI_API_KEY | OpenAI API 키 |
| NAVER_OCR_SECRET | Naver Clova OCR 시크릿 |
| KAKAO_CLIENT_ID | 카카오 OAuth 클라이언트 ID |
| GOOGLE_CLIENT_ID | 구글 OAuth 클라이언트 ID |
| REDIS_URL | Redis 접속 URL |

---

## 라이선스

이 프로젝트는 학습 및 포트폴리오 목적으로 제작되었습니다.
