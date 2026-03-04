"""
AUTH 도메인 라우터.

기준: docs/dev/api_spec.md
  POST /api/auth/signup  — 회원가입 (인증 불필요)
  POST /api/auth/login   — 로그인 (인증 불필요)
  POST /api/auth/refresh — 토큰 재발급 (인증 불필요)
  POST /api/auth/logout  — 로그아웃 (인증 필요)
"""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from fastapi.responses import ORJSONResponse as Response

from app.core import config
from app.core.config import Env
from app.dependencies.security import get_request_user
from app.dtos.auth import LoginRequest, LoginResponse, SignUpRequest, TokenRefreshResponse
from app.models.users import User
from app.services.auth import AuthService
from app.services.jwt import JwtService

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignUpRequest,
    auth_service: Annotated[AuthService, Depends(AuthService)],
) -> Response:
    """REQ-USR-001: 이메일, 비밀번호, 이름, 성별, 생년월일, 휴대폰 번호 등 기본 폼 입력."""
    await auth_service.signup(request)
    return Response(
        content={"detail": "회원가입이 성공적으로 완료되었습니다."},
        status_code=status.HTTP_201_CREATED,
    )


@auth_router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(AuthService)],
) -> Response:
    """REQ-USR-008: 이메일과 비밀번호를 통한 로그인."""
    user = await auth_service.authenticate(request)
    tokens = await auth_service.login(user)
    resp = Response(
        content=LoginResponse(
            access_token=str(tokens["access_token"]),
            role=user.role,
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )
    resp.set_cookie(
        key="refresh_token",
        value=str(tokens["refresh_token"]),
        httponly=True,
        secure=(config.ENV == Env.PROD),
        samesite="lax",
        domain=config.COOKIE_DOMAIN or None,
        expires=tokens["refresh_token"].payload["exp"],
    )
    return resp


@auth_router.post("/refresh", response_model=TokenRefreshResponse, status_code=status.HTTP_200_OK)
async def token_refresh(
    jwt_service: Annotated[JwtService, Depends(JwtService)],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> Response:
    """refresh_token 쿠키를 이용해 access_token을 재발급합니다."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token이 없습니다.",
        )
    access_token = jwt_service.refresh_jwt(refresh_token)
    return Response(
        content=TokenRefreshResponse(access_token=str(access_token)).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    _: Annotated[User, Depends(get_request_user)],
) -> Response:
    """로그아웃: 클라이언트 쿠키의 refresh_token을 만료 처리합니다."""
    resp = Response(content=None, status_code=status.HTTP_204_NO_CONTENT)
    resp.delete_cookie(key="refresh_token")
    return resp
