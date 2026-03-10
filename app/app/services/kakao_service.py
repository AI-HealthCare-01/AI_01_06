import httpx

from app import config


class KakaoService:
    _token_url = "https://kauth.kakao.com/oauth/token"
    _user_info_url = "https://kapi.kakao.com/v2/user/me"

    async def exchange_code(self, code: str) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                self._token_url,
                data={
                    "grant_type": "authorization_code",
                    "client_id": config.KAKAO_CLIENT_ID,
                    "client_secret": config.KAKAO_CLIENT_SECRET,
                    "redirect_uri": config.KAKAO_REDIRECT_URI,
                    "code": code,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            return resp.json()

    async def get_user_info(self, access_token: str) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                self._user_info_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            return resp.json()


def get_kakao_service() -> KakaoService:
    return KakaoService()
