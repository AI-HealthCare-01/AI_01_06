# AI 헬스케어 파이널 프로젝트 (ai-health-example)

이 프로젝트는 클라이언트 요청을 처리하는 프론트엔드 및 API 서버와 프롬프트 처리 및 OCR 분석을 전담하는 AI 워커로 구성된 AI 헬스케어 서비스 템플릿입니다. 처방전 및 의료 기록을 바탕으로 개인 맞춤형 복약 지도와 생활 습관 가이드를 생성하며, 실시간 챗봇 기능을 제공합니다.

## 주요 기술 스택

### 프론트엔드 (Frontend)
- 프레임워크: Next.js

### 백엔드 (Backend)
- 언어: Python 3.13 이상
- 프레임워크: FastAPI
- 데이터베이스 및 ORM: MySQL, Tortoise ORM (비동기 지원)
- 캐시 및 비동기 작업: Redis

### AI 및 외부 API (AI & 3rd Party API)
- LLM: OpenAI API (Local/Dev 환경: gpt-4o-mini, Prod 환경: gpt-4o)
  - 용도: OCR 처방전 인식 결과 기반 가이드 생성 및 실시간 챗봇 응답 처리
- OCR: Naver Clova OCR
  - 용도: 처방전 데이터 추출 및 텍스트 변환

### 인프라 및 배포 (Infrastructure & DevOps)
- 컨테이너화: Docker, Docker-Compose
- 웹 서버/리버스 프록시: Nginx
- 패키지 관리: uv
- 코드 품질 관리: Ruff (포매팅/린트), Mypy (정적 타입 검사), Pytest (테스트)

## 프로젝트 구조

프로젝트는 역할에 따라 다음과 같이 분리되어 있습니다.

- `web/`: Next.js 기반의 프론트엔드 애플리케이션. 사용자 인터페이스 및 클라이언트 사이드 로직을 담당합니다.
- `app/`: FastAPI 기반의 API 서버. HTTP 요청 처리, 비즈니스 로직, DB 통신을 담당합니다.
- `ai_worker/`: AI API 워커. 처방전 OCR 이미지 처리 및 LLM 기반 가이드 생성, 챗봇 응답 등 외부 AI API 호출과 연산을 API 서버와 분리하여 처리합니다.
- `envs/`: 로컬(`.local.env`) 및 배포(`.prod.env`) 환경 변수 관리 디렉토리입니다.
- `nginx/`: Nginx 리버스 프록시 및 SSL 설정 파일이 위치합니다.
- `scripts/`: CI/CD, EC2 배포, 코드 품질 관리 자동화를 위한 쉘 스크립트 모음입니다.
- `pyproject.toml`: `uv`를 활용한 Python 의존성 관리 및 코드 품질 도구 설정 파일입니다.
- `docker-compose.yml` & `docker-compose.prod.yml`: 전체 서비스 스택(Web, API, AI Worker, DB, Redis, Nginx) 컨테이너 실행 설정 파일입니다.

## 실행 및 배포 모델

### 1. 개발 환경 (Local Development)
- `uv sync`를 통해 백엔드 및 AI 워커의 의존성을 분리하여 설치할 수 있습니다.
- `docker-compose up -d --build` 명령어로 전체 스택을 로컬에 구축합니다.
- 비용 및 응답 속도 최적화를 위해 LLM은 `gpt-4o-mini`를 사용합니다.

### 2. 운영 환경 (Production & EC2 Deployment)
- `scripts/deployment.sh`를 통해 도커 이미지 빌드 및 AWS EC2 자동 배포를 수행합니다.
- `scripts/certbot.sh`를 활용해 Let's Encrypt 기반 HTTPS를 적용합니다.
- 높은 추론 성능과 정확한 가이드 생성을 위해 LLM은 `gpt-4o`를 사용합니다.