from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.core.response import success_response
from app.models.user import User
from app.schemas.user import UserUpdateRequest

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return success_response({
        "id": user.id,
        "email": user.email,
        "nickname": user.nickname,
        "name": user.name,
        "role": user.role,
        "birth_date": str(user.birth_date) if user.birth_date else None,
        "gender": user.gender,
        "phone": user.phone,
        "height": user.height,
        "weight": user.weight,
        "allergies": user.allergies,
        "conditions": user.conditions,
    })


@router.patch("/me")
async def update_me(req: UserUpdateRequest, user: User = Depends(get_current_user)):
    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await user.save()
    return success_response({"message": "정보가 수정되었습니다."})
