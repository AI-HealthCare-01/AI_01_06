from openai import AsyncOpenAI


def get_openai_client(api_key: str) -> AsyncOpenAI:
    return AsyncOpenAI(api_key=api_key)
