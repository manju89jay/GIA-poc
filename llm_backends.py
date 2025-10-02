import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import requests
from openai import OpenAI


class LLMError(Exception):
    pass


class LLMClient(ABC):
    def __init__(self, model: Optional[str] = None, temperature: float = 0.0):
        self.model = model
        self.temperature = temperature

    @abstractmethod
    def generate(self, system: str, user: str) -> str:
        raise NotImplementedError


class CloudLLM(LLMClient):
    def __init__(self, model: str = "gpt-5", temperature: float = 0.0):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMError("missing OPENAI_API_KEY")
        super().__init__(model, temperature)
        self.client = OpenAI(api_key=api_key)

    def generate(self, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=self.temperature,
        )
        return resp.choices[0].message.content


class OfflineLLM(LLMClient):
    def __init__(self, model: str = "gpt-5", temperature: float = 0.0):
        endpoint = os.getenv("OFFLINE_LLM_ENDPOINT")
        if not endpoint:
            raise LLMError("missing OFFLINE_LLM_ENDPOINT")
        super().__init__(model, temperature)
        self.endpoint = endpoint

    def generate(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "prompt": f"{system}\n{user}",
        }
        r = requests.post(self.endpoint, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict):
            return (
                data.get("content")
                or data.get("text")
                or data.get("choices", [{}])[0].get("text", "")
            )
        return str(data)


class LocalLlamaLLM(LLMClient):
    """LLM backend that runs llama.cpp locally on a downloaded checkpoint."""

    def __init__(self, model: Optional[str] = None, temperature: float = 0.0):
        super().__init__(model=model, temperature=temperature)
        candidate = model
        if not candidate or candidate == "gpt-5":
            candidate = os.getenv("LLAMA_MODEL_PATH")
        if not candidate:
            raise LLMError("missing LLAMA_MODEL_PATH or model path override")
        model_path = Path(candidate).expanduser()
        if not model_path.exists():
            raise LLMError(f"local model not found: {model_path}")
        self.model_path = model_path
        self.model = str(model_path)
        self._client = None

    def _ensure_client(self):
        if self._client is not None:
            return
        try:
            from llama_cpp import Llama  # type: ignore
        except ImportError as exc:
            raise LLMError(
                "llama-cpp-python is not installed; install it to use the local backend"
            ) from exc
        try:
            self._client = Llama(model_path=str(self.model_path))
        except Exception as exc:  # pragma: no cover - surface informative error
            raise LLMError(f"failed to initialise llama.cpp backend: {exc}") from exc

    def generate(self, system: str, user: str) -> str:
        self._ensure_client()
        assert self._client is not None  # for type checkers
        try:
            response = self._client.create_chat_completion(
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=self.temperature,
            )
        except Exception as exc:  # pragma: no cover - runtime error surfaced to caller
            raise LLMError(f"llama.cpp generation failed: {exc}") from exc

        if hasattr(response, "model_dump"):
            response = response.model_dump()
        elif hasattr(response, "dict"):
            response = response.dict()
        if not isinstance(response, dict):
            raise LLMError("unexpected response from llama.cpp")
        choices = response.get("choices") or []
        if not choices:
            raise LLMError("llama.cpp returned no choices")
        message = choices[0].get("message", {}) or {}
        content = message.get("content")
        if isinstance(content, list):
            content = "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            )
        if not isinstance(content, str) or not content.strip():
            raise LLMError("llama.cpp returned empty content")
        return content


def get_backend(name: str, model: Optional[str], temperature: float) -> LLMClient:
    name = name or "openai"
    if name == "openai":
        return CloudLLM(model=model or "gpt-5", temperature=temperature)
    if name == "offline":
        return OfflineLLM(model=model or "gpt-5", temperature=temperature)
    if name in {"local", "local-llama", "llama"}:
        return LocalLlamaLLM(model=model, temperature=temperature)
    raise ValueError("unknown backend")
