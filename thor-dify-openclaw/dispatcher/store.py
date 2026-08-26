"""In-memory pending confirms for the K10 A/B gate."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .schema import Dispatch


@dataclass
class Pending:
    id: str
    dispatch: Dispatch
    calls: list[dict[str, Any]]
    created_at: float
    status: str = "awaiting_confirm"
    result: dict[str, Any] | None = None


class PendingStore:
    def __init__(self, ttl_seconds: float = 90.0) -> None:
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._items: dict[str, Pending] = {}

    def put(self, dispatch: Dispatch, calls: list[dict[str, Any]]) -> Pending:
        self.expire()
        item = Pending(
            id=uuid.uuid4().hex[:12],
            dispatch=dispatch,
            calls=calls,
            created_at=time.time(),
        )
        with self._lock:
            self._items[item.id] = item
        return item

    def get(self, pending_id: str) -> Pending | None:
        self.expire()
        with self._lock:
            return self._items.get(pending_id)

    def latest_awaiting(self) -> Pending | None:
        self.expire()
        with self._lock:
            waiting = [item for item in self._items.values() if item.status == "awaiting_confirm"]
        if not waiting:
            return None
        return max(waiting, key=lambda item: item.created_at)

    def resolve(self, pending_id: str, allow: bool) -> Pending:
        item = self.get(pending_id)
        if item is None:
            raise KeyError(pending_id)
        if item.status != "awaiting_confirm":
            return item
        item.status = "approved" if allow else "denied"
        return item

    def expire(self) -> None:
        now = time.time()
        with self._lock:
            for item in list(self._items.values()):
                if item.status == "awaiting_confirm" and now - item.created_at > self.ttl_seconds:
                    item.status = "expired"

    def snapshot(self, item: Pending) -> dict[str, Any]:
        return {
            "id": item.id,
            "status": item.status,
            "dispatch": item.dispatch.to_dict(),
            "calls": item.calls,
            "created_at": item.created_at,
            "result": item.result,
        }
