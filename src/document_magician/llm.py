from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(slots=True)
class OllamaClient:
    model: str
    base_url: str = "http://localhost:11434"
    temperature: float = 0.2

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": self.temperature},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        raw = json.dumps(payload).encode("utf-8")
        request = Request(
            url=f"{self.base_url.rstrip('/')}/api/chat",
            data=raw,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=300) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise RuntimeError(f"Ollama HTTP error ({exc.code}): {exc.reason}") from exc
        except URLError as exc:
            raise RuntimeError(
                f"Failed to connect to Ollama at {self.base_url}. "
                "Ensure Ollama is running locally."
            ) from exc

        try:
            return str(data["message"]["content"]).strip()
        except KeyError as exc:
            raise RuntimeError(f"Unexpected Ollama response payload: {data}") from exc
