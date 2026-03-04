"""
파일 저장소 유틸리티 (B담당)

로컬 디스크에 처방전 이미지를 저장하고 정적 URL을 반환합니다.

확장 포인트:
  - S3 등으로 교체 시 이 모듈만 수정하면 됩니다.
  - `save_upload_file()` 함수의 시그니처는 유지하고 내부 구현만 바꾸세요.
"""

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core import config

# 허용 MIME 타입
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf"}


def _get_upload_root() -> Path:
    """업로드 루트 디렉토리 (없으면 자동 생성)"""
    root = Path(config.UPLOAD_DIR)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _make_user_dir(user_id: int) -> Path:
    """사용자별 업로드 디렉토리 생성"""
    user_dir = _get_upload_root() / "prescriptions" / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


async def save_upload_file(file: UploadFile, user_id: int) -> tuple[str, str]:
    """
    처방전 이미지를 로컬 디스크에 저장합니다.

    Returns:
        (file_url, mime_type)
          - file_url  : 정적 접근 URL  (예: /static/prescriptions/1/uuid.jpg)
          - mime_type : 파일 MIME 타입 (예: image/jpeg)

    Raises:
        HTTPException 400 : 허용되지 않는 파일 형식
        HTTPException 413 : 파일 크기 초과
    """
    # MIME 타입 검증
    mime_type = file.content_type or "application/octet-stream"
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"허용되지 않는 파일 형식입니다: {mime_type}. 허용: {', '.join(ALLOWED_MIME_TYPES)}",
        )

    # 파일 내용 읽기
    contents = await file.read()

    # 파일 크기 검증
    max_bytes = config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"파일 크기가 {config.MAX_UPLOAD_SIZE_MB}MB를 초과합니다.",
        )

    # 확장자 결정
    original_name = file.filename or "file"
    ext = Path(original_name).suffix.lower()
    if not ext:
        # MIME에서 확장자 추론
        ext_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "application/pdf": ".pdf",
        }
        ext = ext_map.get(mime_type, ".bin")

    # UUID 파일명 생성
    filename = f"{uuid.uuid4().hex}{ext}"

    # 저장
    save_path = _make_user_dir(user_id) / filename
    save_path.write_bytes(contents)

    # 정적 URL 경로
    file_url = f"{config.STATIC_URL_PREFIX}/prescriptions/{user_id}/{filename}"

    return file_url, mime_type


def get_file_path_from_url(file_url: str) -> Path:
    """
    정적 URL → 실제 파일 경로 변환 (디버깅·삭제용).

    예: /static/prescriptions/1/abc.jpg → ./uploads/prescriptions/1/abc.jpg
    """
    # /static/ 접두사 제거
    relative = file_url.removeprefix(config.STATIC_URL_PREFIX).lstrip("/")
    return _get_upload_root() / relative
