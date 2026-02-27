# 개발 가이드

이 문서는 AI Healthcare 프로젝트에 새로운 기능을 추가하거나 기존 코드를 수정할 때 참고하는 실무 가이드입니다.

---

## 목차

1. [프로젝트 구조 이해](#1-프로젝트-구조-이해)
2. [환경 설정](#2-환경-설정)
3. [API 추가 가이드](#3-api-추가-가이드)
4. [DB 모델 추가 가이드](#4-db-모델-추가-가이드)
5. [AI Worker 로직 추가 가이드](#5-ai-worker-로직-추가-가이드)
6. [인증 및 보안](#6-인증-및-보안)
7. [테스트 작성 가이드](#7-테스트-작성-가이드)
8. [코드 품질 관리](#8-코드-품질-관리)
9. [배포 가이드](#9-배포-가이드)

---

## 1. 프로젝트 구조 이해

```
.
├── app/                        # FastAPI 서버
│   ├── apis/v1/                # API 라우터
│   ├── core/config.py          # 서버 설정 (환경변수 로드)
│   ├── db/databases.py         # Tortoise ORM 초기화
│   ├── dependencies/security.py # 인증 의존성 (JWT)
│   ├── dtos/                   # 요청/응답 스키마 (Pydantic)
│   ├── models/                 # DB 테이블 정의 (Tortoise)
│   ├── repositories/           # DB 쿼리 레이어
│   ├── services/               # 비즈니스 로직
│   ├── utils/                  # 공통 유틸리티 (JWT 등)
│   ├── validators/             # 입력값 검증 로직
│   └── tests/                  # 테스트 코드
├── ai_worker/                  # AI 추론/학습 워커
│   ├── core/config.py          # 워커 설정
│   ├── schemas/                # 워커용 데이터 스키마
│   └── tasks/                  # 실제 처리 작업 정의
├── envs/                       # 환경변수 파일
├── nginx/                      # Nginx 설정
└── scripts/                    # 배포 및 CI 스크립트
```

### 레이어 구조 (app/)

```
Router (apis/) → Service (services/) → Repository (repositories/) → Model (models/)
```

- **Router**: HTTP 요청 수신, DTO 검증, Service 호출
- **Service**: 비즈니스 로직 처리
- **Repository**: DB 쿼리 전담
- **Model**: Tortoise ORM 테이블 정의

---

## 2. 환경 설정

### 환경변수 파일 구조

| 파일 | 용도 |
|------|------|
| `envs/example.local.env` | 로컬 환경 예시 |
| `envs/example.prod.env` | 운영 환경 예시 |
| `envs/.local.env` | 실제 로컬 환경변수 (git 제외) |
| `envs/.prod.env` | 실제 운영 환경변수 (git 제외) |

### 주요 환경변수

```env
# FastAPI 서버
ENV=local                   # local | dev | prod
SECRET_KEY=your-secret-key
COOKIE_DOMAIN=localhost

# DB
DB_HOST=localhost
DB_PORT=3306
DB_USER=ozcoding
DB_PASSWORD=pw1234
DB_NAME=ai_health

# Docker 이미지 버전 관리
APP_VERSION=v1.0.0
AI_WORKER_VERSION=v1.0.0
```

### Config 클래스 (`app/core/config.py`)

`pydantic-settings`의 `BaseSettings`를 사용하여 `.env` 파일에서 자동으로 환경변수를 로드합니다.

```python
from app.core import config

# 사용 예시
config.DB_HOST
config.SECRET_KEY
config.ENV  # Env.LOCAL | Env.DEV | Env.PROD
```

새로운 환경변수가 필요하면 `Config` 클래스에 필드를 추가하고 `.env` 파일에도 값을 추가합니다.

---

## 3. API 추가 가이드

### 순서: DTO → Service → Repository → Router → 등록

### Step 1. DTO 정의 (`app/dtos/`)

요청/응답 스키마를 Pydantic 모델로 정의합니다.

```python
# app/dtos/health.py
from pydantic import BaseModel

class HealthRecordCreateRequest(BaseModel):
    user_id: int
    bpm: int
    recorded_at: str

class HealthRecordResponse(BaseModel):
    id: int
    bpm: int
    recorded_at: str

    model_config = {"from_attributes": True}
```

### Step 2. Repository 작성 (`app/repositories/`)

DB 쿼리만 담당합니다. 비즈니스 로직은 포함하지 않습니다.

```python
# app/repositories/health_repository.py
from app.models.health import HealthRecord

class HealthRepository:
    async def create(self, user_id: int, bpm: int, recorded_at: str) -> HealthRecord:
        return await HealthRecord.create(user_id=user_id, bpm=bpm, recorded_at=recorded_at)

    async def get_by_user(self, user_id: int) -> list[HealthRecord]:
        return await HealthRecord.filter(user_id=user_id).all()
```

### Step 3. Service 작성 (`app/services/`)

비즈니스 로직을 처리합니다. Repository를 통해 DB에 접근합니다.

```python
# app/services/health.py
from app.repositories.health_repository import HealthRepository
from app.dtos.health import HealthRecordCreateRequest

class HealthService:
    def __init__(self):
        self.repo = HealthRepository()

    async def create_record(self, request: HealthRecordCreateRequest):
        return await self.repo.create(
            user_id=request.user_id,
            bpm=request.bpm,
            recorded_at=request.recorded_at,
        )
```

### Step 4. Router 작성 (`app/apis/v1/`)

```python
# app/apis/v1/health_routers.py
from typing import Annotated
from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.health import HealthRecordCreateRequest, HealthRecordResponse
from app.services.health import HealthService

health_router = APIRouter(prefix="/health", tags=["health"])

@health_router.post("/records", status_code=status.HTTP_201_CREATED)
async def create_health_record(
    request: HealthRecordCreateRequest,
    user: Annotated[..., Depends(get_request_user)],
    health_service: Annotated[HealthService, Depends(HealthService)],
) -> Response:
    record = await health_service.create_record(request)
    return Response(HealthRecordResponse.model_validate(record).model_dump(), status_code=status.HTTP_201_CREATED)
```

### Step 5. Router 등록 (`app/apis/v1/__init__.py`)

```python
from app.apis.v1.health_routers import health_router

v1_routers.include_router(health_router)
```

---

## 4. DB 모델 추가 가이드

### Step 1. Tortoise 모델 정의 (`app/models/`)

```python
# app/models/health.py
from tortoise import fields
from tortoise.models import Model

class HealthRecord(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="health_records")
    bpm = fields.IntField()
    recorded_at = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "health_records"
```

### Step 2. TORTOISE_APP_MODELS에 등록 (`app/db/databases.py`)

```python
TORTOISE_APP_MODELS = [
    "aerich.models",
    "app.models.users",
    "app.models.health",  # 추가
]
```

### Step 3. 마이그레이션 실행

```bash
# 마이그레이션 파일 생성
uv run aerich migrate --name add_health_record

# 마이그레이션 적용
uv run aerich upgrade
```

> 최초 설정 시: `uv run aerich init-db`

---

## 5. AI Worker 로직 추가 가이드

### Step 1. 스키마 정의 (`ai_worker/schemas/`)

워커가 처리할 데이터의 입출력 스키마를 정의합니다.

```python
# ai_worker/schemas/prediction.py
from pydantic import BaseModel

class PredictionInput(BaseModel):
    user_id: int
    features: list[float]

class PredictionOutput(BaseModel):
    user_id: int
    result: float
    label: str
```

### Step 2. Task 작성 (`ai_worker/tasks/`)

실제 모델 추론 또는 학습 로직을 작성합니다.

```python
# ai_worker/tasks/prediction.py
from ai_worker.schemas.prediction import PredictionInput, PredictionOutput

async def run_prediction(input_data: PredictionInput) -> PredictionOutput:
    # 모델 로드 및 추론 로직
    features = input_data.features
    result = sum(features) / len(features)  # 예시
    label = "정상" if result < 0.5 else "이상"
    return PredictionOutput(user_id=input_data.user_id, result=result, label=label)
```

### Step 3. `ai_worker/main.py`에서 호출

```python
# ai_worker/main.py
import asyncio
from ai_worker.tasks.prediction import run_prediction
from ai_worker.schemas.prediction import PredictionInput

async def main():
    sample = PredictionInput(user_id=1, features=[0.1, 0.4, 0.3])
    result = await run_prediction(sample)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 6. 인증 및 보안

### JWT 인증 흐름

```
로그인 → access_token (응답 body) + refresh_token (HttpOnly Cookie)
         ↓
인증 필요 API → Authorization: Bearer <access_token>
         ↓
토큰 만료 → GET /api/v1/auth/token/refresh (쿠키의 refresh_token 사용)
```

### 인증이 필요한 API 작성

`get_request_user` 의존성을 주입하면 자동으로 JWT를 검증하고 현재 유저 객체를 반환합니다.

```python
from app.dependencies.security import get_request_user
from app.models.users import User

@router.get("/protected")
async def protected_endpoint(
    user: Annotated[User, Depends(get_request_user)],
):
    return {"user_id": user.id}
```

### 토큰 설정 (`app/core/config.py`)

| 설정 | 기본값 | 설명 |
|------|--------|------|
| `JWT_ALGORITHM` | `HS256` | JWT 서명 알고리즘 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | 액세스 토큰 만료 시간 |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | `20160` (14일) | 리프레시 토큰 만료 시간 |

---

## 7. 테스트 작성 가이드

### 테스트 구조

```
app/tests/
├── conftest.py          # 공통 픽스처 (테스트 클라이언트, DB 설정)
├── auth_apis/           # 인증 API 테스트
│   ├── test_login_api.py
│   ├── test_signup_api.py
│   └── test_token_api.py
└── user_apis/           # 유저 API 테스트
    └── test_user_me_apis.py
```

### 테스트 작성 예시

```python
# app/tests/health_apis/test_health_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_health_record(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/health/records",
        json={"bpm": 72, "recorded_at": "2025-01-01T00:00:00"},
        headers=auth_headers,
    )
    assert response.status_code == 201
```

### 테스트 실행

```bash
./scripts/ci/run_test.sh
# 또는
uv run pytest app/tests/ -v
```

---

## 8. 코드 품질 관리

### 사용 도구

| 도구 | 역할 | 설정 |
|------|------|------|
| **Ruff** | 린팅 + 포맷팅 | `pyproject.toml [tool.ruff]` |
| **Mypy** | 정적 타입 검사 | `pyproject.toml` |
| **Pytest** | 테스트 실행 | `pyproject.toml [tool.pytest]` |

### 스크립트 실행

```bash
# 코드 포맷팅 검사 및 자동 수정
./scripts/ci/code_fommatting.sh

# 타입 검사
./scripts/ci/check_mypy.sh

# 테스트
./scripts/ci/run_test.sh
```

### Ruff 주요 규칙 (`pyproject.toml`)

- 라인 길이: 120자
- `E`, `W`: pycodestyle
- `F`: pyflakes (미사용 import 등)
- `I`: isort (import 정렬)
- `B`: flake8-bugbear (잠재적 버그)
- `N`: pep8-naming (네이밍 컨벤션)

---

## 9. 배포 가이드

### 로컬 전체 스택 실행

```bash
# .env 파일 준비
cp envs/example.local.env envs/.local.env
ln -sf envs/.local.env .env  # 또는 직접 .env 생성

# 전체 서비스 실행 (MySQL, Redis, FastAPI, AI Worker, Nginx)
docker-compose up -d --build
```

접속 주소:
- Swagger UI: http://localhost/api/docs
- API: http://localhost/api/v1/

### EC2 운영 배포

```bash
# 배포 스크립트 실행
chmod +x scripts/deployment.sh
./scripts/deployment.sh
```

스크립트 실행 시 입력 항목:
1. Docker Hub 계정 (Username / PAT)
2. Docker Repository 이름
3. 배포할 서비스 선택 (FastAPI / AI Worker) 및 버전
4. EC2 SSH 키 파일명 및 IP 주소
5. HTTP / HTTPS 선택 (HTTPS 선택 시 도메인 입력)

### HTTPS 설정 (Let's Encrypt)

```bash
chmod +x scripts/certbot.sh
./scripts/certbot.sh
```

### Docker 이미지 버전 관리

이미지 태그 형식: `{docker_user}/{repo}:{service}-{version}`

| 서비스 | 태그 예시 |
|--------|-----------|
| FastAPI | `ozcodingschool/ai-health:app-v1.0.0` |
| AI Worker | `ozcodingschool/ai-health:ai-v1.0.0` |

버전은 `envs/.prod.env`의 `APP_VERSION`, `AI_WORKER_VERSION`으로 관리합니다.

---

## 자주 쓰는 명령어 모음

```bash
# 의존성 설치
uv sync                    # 전체
uv sync --group app        # FastAPI만
uv sync --group ai         # AI Worker만

# 서버 실행 (로컬)
uv run uvicorn app.main:app --reload

# AI Worker 실행 (로컬)
uv run python -m ai_worker.main

# DB 마이그레이션
uv run aerich migrate --name <이름>
uv run aerich upgrade

# Docker
docker-compose up -d --build
docker-compose down
docker-compose logs -f fastapi
```
