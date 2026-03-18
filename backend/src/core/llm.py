"""Shared LLM instance factory."""

import os
from langchain_openai import ChatOpenAI


def get_llm(temperature: float = 0.3) -> ChatOpenAI:
    return ChatOpenAI(
        model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        temperature=temperature,
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
