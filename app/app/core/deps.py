from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.redis import get_state_redis
from app.core.security import decode_token
from app.models.caregiver_patient import CaregiverPatientMapping
from app.models.user import User

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> User:
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    # jti가 있으면 blacklist 확인 (기존 jti 없는 토큰은 skip → 하위 호환)
    jti = payload.get("jti")
    if jti:
        redis = await get_state_redis()
        if await redis.get(f"blacklist:{jti}"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그아웃된 토큰입니다.")
    user_id = int(payload["sub"])
    user = await User.get_or_none(id=user_id, deleted_at__isnull=True)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_acting_patient(
    user: User = Depends(get_current_user),
    x_acting_for: int | None = Header(None, alias="X-Acting-For"),
) -> tuple[User, User | None]:
    """(current_user, target_patient) 튜플 반환.

    X-Acting-For 헤더가 없으면 (user, None) → 본인 모드.
    헤더가 있으면 APPROVED 매핑 검증 후 (guardian, patient) 반환.
    """
    if x_acting_for is None:
        return user, None

    if user.role != "GUARDIAN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="보호자만 대리 접근이 가능합니다.")

    mapping = await CaregiverPatientMapping.get_or_none(
        caregiver=user, patient_id=x_acting_for, status="APPROVED",
    )
    if not mapping:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="연결되지 않은 돌봄 대상입니다.")

    patient = await User.get_or_none(id=x_acting_for, deleted_at__isnull=True)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")

    return user, patient
