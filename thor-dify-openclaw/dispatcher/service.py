"""Application service: plan via Dify, gate on confirm, return Reachy calls."""

from __future__ import annotations

from typing import Any, Protocol

from . import executor
from .dify_client import DifyClient
from .schema import (
    Dispatch,
    DispatchError,
    extract_json_object,
    looks_like_unsupported_aircraft,
    normalize_dispatch,
    normalize_source,
)
from .store import PendingStore


class Planner(Protocol):
    def chat(self, query: str) -> str: ...


class DispatchService:
    def __init__(
        self,
        planner: Planner | None = None,
        store: PendingStore | None = None,
        dry_run: bool = True,
    ) -> None:
        self.planner = planner or DifyClient()
        self.store = store or PendingStore()
        self.dry_run = dry_run

    def health(self) -> dict[str, Any]:
        return {
            "ok": True,
            "dry_run": self.dry_run,
            "role": "dify-fetch-bridge",
            "ingress": ["reachy", "k10"],
            "body": "dogzilla",
        }

    def plan_query(self, query: str, source: str = "reachy") -> dict[str, Any]:
        query = (query or "").strip()
        source = normalize_source(source)
        if not query:
            raise DispatchError("query is required")
        if looks_like_unsupported_aircraft(query):
            dispatch = Dispatch(
                source=source,
                target="k10",
                intent="display",
                confirm=False,
                say="Crazyflie 尚未接入，這次只調度機器狗夾送",
            )
            return self._ready(dispatch, planner_source="policy")

        prompt = f"[助理={source}] {query}"
        answer = self.planner.chat(prompt)
        dispatch = normalize_dispatch(extract_json_object(answer), source=source)
        return self._ready(dispatch, planner_source="dify", raw_answer=answer)

    def plan_voice(self, source: str, text: str) -> dict[str, Any]:
        return self.plan_query(text, source=source)

    def submit(self, dispatch: Dispatch) -> dict[str, Any]:
        calls = executor.plan_calls(dispatch)
        if dispatch.confirm:
            pending = self.store.put(dispatch, calls)
            return {
                "status": "awaiting_confirm",
                "pending": self.store.snapshot(pending),
                "dry_run": self.dry_run,
            }
        return {
            "status": "ready",
            "dispatch": dispatch.to_dict(),
            "calls": calls,
            "dry_run": self.dry_run,
        }

    def pending(self) -> dict[str, Any]:
        item = self.store.latest_awaiting()
        if item is None:
            return {"status": "idle", "pending": None}
        return {"status": "awaiting_confirm", "pending": self.store.snapshot(item)}

    def confirm(self, pending_id: str, allow: bool) -> dict[str, Any]:
        try:
            item = self.store.resolve(pending_id, allow)
        except KeyError as exc:
            raise DispatchError(f"unknown pending id: {pending_id}") from exc
        payload = self.store.snapshot(item)
        if item.status == "denied":
            return {"status": "denied", "pending": payload, "dry_run": self.dry_run}
        if item.status == "expired":
            return {"status": "expired", "pending": payload, "dry_run": self.dry_run}
        if item.status != "approved":
            return {"status": item.status, "pending": payload, "dry_run": self.dry_run}
        return {
            "status": "ready",
            "dispatch": item.dispatch.to_dict(),
            "calls": item.calls,
            "pending": payload,
            "dry_run": self.dry_run,
        }

    def _ready(
        self,
        dispatch: Dispatch,
        planner_source: str,
        raw_answer: str | None = None,
    ) -> dict[str, Any]:
        result = self.submit(dispatch)
        result["planner"] = planner_source
        if raw_answer is not None:
            result["raw_answer"] = raw_answer
        return result
