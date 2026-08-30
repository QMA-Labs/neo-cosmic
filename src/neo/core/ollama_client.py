from __future__ import annotations

import json
from dataclasses import dataclass
from threading import Event

import httpx


@dataclass(frozen=True, slots=True)
class OllamaStatus:
    reachable: bool
    models: tuple[str, ...] = ()
    error: str | None = None


class ChatCancelled(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: str, timeout: float = 3.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def status(self) -> OllamaStatus:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            response.raise_for_status()
            models = tuple(
                item["name"] for item in response.json().get("models", []) if "name" in item
            )
            return OllamaStatus(True, models)
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            return OllamaStatus(False, error=str(exc))

    def has_model(self, model: str) -> bool:
        status = self.status()
        wanted = model.removesuffix(":latest")
        return status.reachable and any(
            name.removesuffix(":latest") == wanted for name in status.models
        )

    def chat(
        self,
        model: str,
        prompt: str,
        *,
        context_size: int = 8192,
        gpu_layers: int = 0,
        keep_alive: str = "5m",
        cancel_event: Event | None = None,
    ) -> str:
        chunks: list[str] = []
        with httpx.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
                "think": False,
                "keep_alive": keep_alive,
                "options": {"num_ctx": context_size, "num_gpu": gpu_layers},
            },
            timeout=httpx.Timeout(connect=8.0, read=None, write=30.0, pool=8.0),
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if cancel_event is not None and cancel_event.is_set():
                    raise ChatCancelled("پاسخ توسط کاربر متوقف شد")
                if not line:
                    continue
                payload = json.loads(line)
                chunks.append(str(payload.get("message", {}).get("content", "")))
        return "".join(chunks).strip()

    def chat_with_image(
        self,
        model: str,
        prompt: str,
        image_base64: str,
        *,
        context_size: int = 8192,
        cancel_event: Event | None = None,
    ) -> str:
        chunks: list[str] = []
        with httpx.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt, "images": [image_base64]}],
                "stream": True,
                "think": False,
                "options": {"num_ctx": context_size},
            },
            timeout=httpx.Timeout(connect=8.0, read=None, write=60.0, pool=8.0),
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if cancel_event is not None and cancel_event.is_set():
                    raise ChatCancelled("تحلیل صفحه توسط کاربر متوقف شد")
                if not line:
                    continue
                payload = json.loads(line)
                chunks.append(str(payload.get("message", {}).get("content", "")))
        return "".join(chunks).strip()
