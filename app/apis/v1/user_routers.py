"""
USER 도메인 라우터.

기준: docs/dev/api_spec.md
  GET    /api/users/me               — 내 정보 조회 (인증 필요)
  PATCH  /api/users/me               — 내 정보 수정 (인증 필요)
  PATCH  /api/users/me/accessibility — 접근성 설정 변경 (인증 필요)
  DELETE /api/users/me               — 회원 탈퇴 (인증 필요)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.users import AccessibilityUpdateRequest, UserInfoResponse, UserUpdateRequest
from app.models.users import User
from app.services.users import UserService

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("/me", response_model=UserInfoResponse, status_code=status.HTTP_200_OK)
async def get_my_info(
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """내 정보 조회."""
    return Response(
        content=UserInfoResponse.model_validate(user).model_dump(mode="json"),
        status_code=status.HTTP_200_OK,
    )


@user_router.patch("/me", response_model=UserInfoResponse, status_code=status.HTTP_200_OK)
async def update_my_info(
    update_data: UserUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    user_service: Annotated[UserService, Depends(UserService)],
) -> Response:
    """내 정보 수정 (이름, 휴대폰 번호)."""
    updated_user = await user_service.update_me(user=user, data=update_data)
    return Response(
        content=UserInfoResponse.model_validate(updated_user).model_dump(mode="json"),
        status_code=status.HTTP_200_OK,
    )


@user_router.patch("/me/accessibility", status_code=status.HTTP_204_NO_CONTENT)
async def update_accessibility(
    update_data: AccessibilityUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    user_service: Annotated[UserService, Depends(UserService)],
) -> Response:
    """REQ-COM-001: 글자 크기 모드 토글."""
    await user_service.update_accessibility(user_id=user.id, data=update_data)
    return Response(content=None, status_code=status.HTTP_204_NO_CONTENT)


@user_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def withdraw(
    user: Annotated[User, Depends(get_request_user)],
    user_service: Annotated[UserService, Depends(UserService)],
) -> Response:
    """회원 탈퇴 (논리 삭제)."""
    await user_service.withdraw_me(user)
    resp = Response(content=None, status_code=status.HTTP_204_NO_CONTENT)
    resp.delete_cookie(key="refresh_token")
    return resp
