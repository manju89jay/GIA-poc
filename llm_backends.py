import os
from abc import ABC, abstractmethod
from typing import Optional
import requests
from openai import OpenAI


class LLMError(Exception):
    pass


class LLMClient(ABC):
    def __init__(self, model: str = "gpt-5", temperature: float = 0.0):
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


def get_backend(name: str, model: str, temperature: float) -> LLMClient:
    name = name or "openai"
    if name == "openai":
        return CloudLLM(model=model, temperature=temperature)
    if name == "offline":
        return OfflineLLM(model=model, temperature=temperature)
    raise ValueError("unknown backend")
