from .base import SYSTEM_BASE_PROMPT

GUIDE_SYSTEM_PROMPT = (
    SYSTEM_BASE_PROMPT
    + """
제공된 처방전 데이터와 사용자의 기저질환, 알러지 정보를 바탕으로 안전하고 이해하기 쉬운 복약 가이드를 생성해주세요.
"""
)
