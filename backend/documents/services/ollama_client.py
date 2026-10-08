"""HTTP client for the local Ollama language model."""

import requests
from django.conf import settings


class OllamaError(Exception):
    """Raised when an Ollama request fails."""


class OllamaClient:
    """Generate text using a locally hosted Ollama model."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 120,
        session=None,
    ):
        self.base_url = (
            base_url
            or getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        ).rstrip("/")
        self.model = model or getattr(settings, "OLLAMA_MODEL", "qwen3:1.7b")
        self.timeout = timeout
        self.session = session if session is not None else requests.Session()

    def generate(self, prompt: str) -> str:
        """Generate an answer from a prompt."""

        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {
                "num_predict": 512,
            },
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

        except (requests.RequestException, ValueError) as exc:
            raise OllamaError("Failed to communicate with Ollama.") from exc

        answer = data.get("response")

        if not isinstance(answer, str) or not answer.strip():
            raise OllamaError("Ollama returned an empty or invalid response.")

        return answer.strip()