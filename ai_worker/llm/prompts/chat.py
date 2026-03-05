from .base import SYSTEM_BASE_PROMPT

CHAT_SYSTEM_PROMPT = (
    SYSTEM_BASE_PROMPT
    + """
사용자와의 실시간 대화에 친절하고 정확하게 답변해주세요. 이전 대화 맥락을 충분히 고려하여 자연스럽게 대화해야 합니다.
"""
)
