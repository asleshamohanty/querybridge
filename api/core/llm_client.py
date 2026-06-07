from __future__ import annotations
from abc import ABC, abstractmethod
from api.config import settings


class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        ...


class GeminiClient(BaseLLMClient):
    MODEL = "gemini-2.5-flash"

    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        import google.generativeai as genai
        model = genai.GenerativeModel(
            model_name=self.MODEL,
            system_instruction=system_prompt,
        )
        response = model.generate_content(user_prompt)
        return response.text.strip()


class ClaudeClient(BaseLLMClient):
    MODEL = "claude-sonnet-4-5"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        import anthropic
        client = anthropic.Anthropic()
        message = client.messages.create(
            model=self.MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text.strip()


class OllamaClient(BaseLLMClient):
    MODEL = "llama3"
    BASE_URL = "http://localhost:11434"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        import httpx
        payload = {
            "model": self.MODEL,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
        }
        resp = httpx.post(f"{self.BASE_URL}/api/generate", json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["response"].strip()


_BACKENDS = {
    "gemini": GeminiClient,
    "claude": ClaudeClient,
    "ollama": OllamaClient,
}

_instance: BaseLLMClient | None = None


def get_llm_client() -> BaseLLMClient:
    global _instance
    if _instance is None:
        provider = settings.llm_provider.lower()
        if provider not in _BACKENDS:
            raise ValueError(f"Unknown LLM_PROVIDER '{provider}'. Choose from: {list(_BACKENDS)}")
        _instance = _BACKENDS[provider]()
    return _instance
