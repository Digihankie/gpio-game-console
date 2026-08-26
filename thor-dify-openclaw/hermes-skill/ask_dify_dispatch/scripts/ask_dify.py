#!/usr/bin/env python3
"""CLI used by the Hermes skill: plan a fleet dispatch via the local bridge."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def _post(url: str, payload: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def main(argv: list[str]) -> int:
    query = " ".join(argv[1:]).strip()
    if not query:
        print(json.dumps({"error": "usage: ask_dify.py <natural language>"}, ensure_ascii=False))
        return 2

    base = os.environ.get("DIFY_DISPATCH_URL", "http://127.0.0.1:8766").rstrip("/")
    try:
        result = _post(f"{base}/plan", {"query": query})
    except urllib.error.URLError as exc:
        print(
            json.dumps(
                {
                    "error": f"dispatch bridge unreachable at {base}: {exc.reason}",
                    "hint": "在 Thor 跑 python3 -m dispatcher 或 docker compose up dify-dispatch",
                },
                ensure_ascii=False,
            )
        )
        return 1
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(json.dumps({"error": f"HTTP {exc.code}", "detail": detail[:500]}, ensure_ascii=False))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
