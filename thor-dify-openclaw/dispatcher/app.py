"""Stdlib HTTP front for the Dify ↔ Hermes dispatch bridge."""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from .schema import DispatchError, normalize_dispatch
from .service import DispatchService


def build_service() -> DispatchService:
    dry_run = os.environ.get("DRY_RUN", "1").strip().lower() not in {"0", "false", "no"}
    return DispatchService(dry_run=dry_run)


class Handler(BaseHTTPRequestHandler):
    service: DispatchService

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/", "/health"}:
            self._json(200, self.service.health())
            return
        if path == "/pending":
            self._json(200, self.service.pending())
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            body = self._read_json()
        except DispatchError as exc:
            self._json(400, {"error": str(exc)})
            return

        try:
            if path == "/plan":
                query = str(body.get("query") or body.get("text") or "")
                self._json(200, self.service.plan_query(query))
                return
            if path == "/dispatch":
                if "query" in body or "text" in body:
                    query = str(body.get("query") or body.get("text") or "")
                    self._json(200, self.service.plan_query(query))
                    return
                dispatch = normalize_dispatch(body)
                self._json(200, self.service.submit(dispatch))
                return
            if path == "/confirm":
                pending_id = str(body.get("id") or "")
                allow = bool(body.get("allow"))
                if not pending_id:
                    raise DispatchError("id is required")
                self._json(200, self.service.confirm(pending_id, allow))
                return
        except DispatchError as exc:
            self._json(400, {"error": str(exc)})
            return
        except Exception as exc:  # noqa: BLE001 — return planner/network errors as 502
            self._json(502, {"error": str(exc)})
            return

        self._json(404, {"error": "not found"})

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        if not raw:
            return {}
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise DispatchError(f"invalid JSON body: {exc}") from exc
        if not isinstance(parsed, dict):
            raise DispatchError("JSON body must be an object")
        return parsed

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def make_handler(service: DispatchService):
    class Bound(Handler):
        pass

    Bound.service = service
    return Bound


def serve(host: str | None = None, port: int | None = None, service: DispatchService | None = None) -> None:
    host = host or os.environ.get("DISPATCH_BIND", "0.0.0.0")
    port = port if port is not None else int(os.environ.get("DISPATCH_PORT", "8766"))
    httpd = ThreadingHTTPServer((host, port), make_handler(service or build_service()))
    print(f"dify-dispatch listening on {host}:{port}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    # Allow `python3 -m dispatcher.app` from thor-dify-openclaw/
    if __package__ is None:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from dispatcher.app import serve as _serve

        _serve()
    else:
        serve()
