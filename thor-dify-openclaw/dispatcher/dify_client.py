"""Blocking Dify Chatflow client (POST /v1/chat-messages)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class DifyError(RuntimeError):
    pass


class DifyClient:
    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
        user: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.api_url = (api_url or os.environ.get("DIFY_API_URL", "http://127.0.0.1:3080/v1")).rstrip("/")
        self.api_key = api_key if api_key is not None else os.environ.get("DIFY_API_KEY", "")
        self.user = user or os.environ.get("DIFY_USER", "dify")
        self.timeout = timeout

    def chat(self, query: str) -> str:
        if not self.api_key:
            raise DifyError("DIFY_API_KEY is empty — create a Chatflow API key in Dify")
        payload = {
            "inputs": {},
            "query": query,
            "response_mode": "blocking",
            "user": self.user,
        }
        request = urllib.request.Request(
            f"{self.api_url}/chat-messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise DifyError(f"Dify HTTP {exc.code}: {detail[:400]}") from exc
        except urllib.error.URLError as exc:
            raise DifyError(f"Dify unreachable at {self.api_url}: {exc.reason}") from exc

        answer = body.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            raise DifyError("Dify returned no answer text")
        return answer
