"""날씨 tool – 사용자 질문에서 날씨 의도 + 도시명을 감지하고 OpenWeatherMap API를 호출한다.

설계 원칙:
- 판별은 매우 보수적 (명시적 날씨 키워드만)
- 도시명이 없으면 None 반환 → 호출자가 기존 LLM fallback
- API 실패 시 예외 → 호출자가 기존 LLM fallback
"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

# ── 날씨 키워드 (보수적: 명시적 날씨 표현만) ──
_WEATHER_KEYWORDS: list[str] = [
    "날씨",
    "기온",
    "강수확률",
    "강수량",
    "비 오나",
    "비오나",
    "비 올까",
    "비올까",
    "눈 오나",
    "눈오나",
    "눈 올까",
    "눈올까",
    "기상예보",
    "일기예보",
    "최고기온",
    "최저기온",
    "체감온도",
]

# ── 한국어 도시 → OpenWeatherMap 도시명 매핑 ──
_CITY_MAP: dict[str, str] = {
    "서울": "Seoul",
    "부산": "Busan",
    "대구": "Daegu",
    "인천": "Incheon",
    "광주": "Gwangju",
    "대전": "Daejeon",
    "울산": "Ulsan",
    "세종": "Sejong",
    "수원": "Suwon",
    "성남": "Seongnam",
    "고양": "Goyang",
    "용인": "Yongin",
    "창원": "Changwon",
    "청주": "Cheongju",
    "전주": "Jeonju",
    "천안": "Cheonan",
    "제주": "Jeju",
    "포항": "Pohang",
    "김해": "Gimhae",
    "춘천": "Chuncheon",
    "목포": "Mokpo",
    "여수": "Yeosu",
    "강릉": "Gangneung",
    "원주": "Wonju",
    "경주": "Gyeongju",
    "안동": "Andong",
    "속초": "Sokcho",
    "평택": "Pyeongtaek",
    "파주": "Paju",
    "김포": "Gimpo",
    "화성": "Hwaseong",
    "안양": "Anyang",
    "안산": "Ansan",
    "의정부": "Uijeongbu",
    "구미": "Gumi",
    "거제": "Geoje",
    "양산": "Yangsan",
    "진주": "Jinju",
    "익산": "Iksan",
    "군산": "Gunsan",
    "남원": "Namwon",
    "통영": "Tongyeong",
    "논산": "Nonsan",
    "서산": "Seosan",
    "당진": "Dangjin",
    "충주": "Chungju",
    "제천": "Jecheon",
    "영주": "Yeongju",
    "상주": "Sangju",
    "문경": "Mungyeong",
    "김천": "Gimcheon",
    "영천": "Yeongcheon",
    "광양": "Gwangyang",
    "나주": "Naju",
    "순천": "Suncheon",
}

# ── 영어 도시명도 직접 인식 ──
_ENGLISH_CITIES: set[str] = {
    "seoul",
    "busan",
    "daegu",
    "incheon",
    "gwangju",
    "daejeon",
    "ulsan",
    "jeju",
    "tokyo",
    "osaka",
    "new york",
    "london",
    "paris",
    "beijing",
    "shanghai",
    "bangkok",
    "singapore",
    "sydney",
    "los angeles",
    "san francisco",
    "chicago",
    "seattle",
}

# 날씨 설명 한국어 매핑
_WEATHER_DESC_KR: dict[str, str] = {
    "clear sky": "맑음",
    "few clouds": "구름 조금",
    "scattered clouds": "구름 약간",
    "broken clouds": "구름 많음",
    "overcast clouds": "흐림",
    "light rain": "가벼운 비",
    "moderate rain": "비",
    "heavy intensity rain": "강한 비",
    "light snow": "가벼운 눈",
    "snow": "눈",
    "mist": "안개",
    "fog": "안개",
    "haze": "연무",
    "thunderstorm": "천둥번개",
    "drizzle": "이슬비",
}


def is_weather_query(text: str) -> bool:
    """명시적 날씨 키워드가 포함되어 있는지 판별한다 (보수적)."""
    text_lower = text.lower().strip()
    return any(kw in text_lower for kw in _WEATHER_KEYWORDS)


def extract_city(text: str) -> str | None:
    """사용자 메시지에서 도시명을 추출한다. 없으면 None."""
    # 한국어 도시명 매칭 (긴 이름 우선)
    for kr_name in sorted(_CITY_MAP, key=len, reverse=True):
        if kr_name in text:
            return _CITY_MAP[kr_name]

    # 영어 도시명 매칭
    text_lower = text.lower()
    for en_name in sorted(_ENGLISH_CITIES, key=len, reverse=True):
        if en_name in text_lower:
            # API에 보낼 때 타이틀케이스
            return en_name.title()

    return None


async def fetch_weather(city: str, api_key: str) -> dict:
    """OpenWeatherMap Current Weather API를 호출한다.

    실패 시 예외를 발생시킨다 (호출자가 fallback 처리).
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
        "lang": "kr",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


def format_weather_response(data: dict, city_kr: str | None = None) -> str:
    """OpenWeatherMap 응답을 사용자 친화적 한국어 메시지로 포맷한다."""
    city_name = city_kr or data.get("name", "")
    main = data.get("main", {})
    weather_list = data.get("weather", [])
    wind = data.get("wind", {})

    temp = main.get("temp", "—")
    feels_like = main.get("feels_like", "—")
    humidity = main.get("humidity", "—")
    temp_min = main.get("temp_min", "—")
    temp_max = main.get("temp_max", "—")
    wind_speed = wind.get("speed", "—")

    desc_en = weather_list[0].get("description", "") if weather_list else ""
    desc = _WEATHER_DESC_KR.get(desc_en, desc_en)

    lines = [
        f"🌤️ **{city_name} 현재 날씨**\n",
        f"- 날씨: {desc}",
        f"- 현재 기온: {temp}°C (체감 {feels_like}°C)",
        f"- 최저/최고: {temp_min}°C / {temp_max}°C",
        f"- 습도: {humidity}%",
        f"- 풍속: {wind_speed} m/s",
        "",
        "※ 이 정보는 실시간 기상 데이터를 기반으로 제공됩니다.",
    ]
    return "\n".join(lines)


def _find_korean_city_name(english_city: str) -> str | None:
    """영어 도시명에 대응하는 한국어 도시명을 찾는다."""
    reverse_map = {v.lower(): k for k, v in _CITY_MAP.items()}
    return reverse_map.get(english_city.lower())


# ── 통합 함수: chat_task에서 호출 ──


async def try_weather_response(user_query: str, api_key: str) -> str | None:
    """날씨 질문이면 응답 문자열을 반환, 아니면 None.

    - 날씨 키워드 없음 → None
    - 도시명 없음 → None (기존 LLM fallback)
    - API 실패 → None (기존 LLM fallback)
    """
    if not api_key:
        return None

    if not is_weather_query(user_query):
        return None

    city = extract_city(user_query)
    if city is None:
        logger.info("[Weather] 날씨 질문이나 도시명 없음 → LLM fallback")
        return None

    city_kr = _find_korean_city_name(city) or city

    try:
        data = await fetch_weather(city, api_key)
        response = format_weather_response(data, city_kr)
        logger.info("[Weather] %s 날씨 응답 생성 완료", city_kr)
        return response
    except Exception:
        logger.exception("[Weather] API 호출 실패 → LLM fallback")
        return None
