"""Parse and validate the thin Dify fleet-dispatch JSON."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any

TARGETS = ("reachy", "k10", "m3", "dogzilla")
INTENTS = ("status", "say", "look", "greet", "demo", "abort", "display")
UNWIRED_TARGETS = ("m3", "dogzilla")
REJECTED_KEYWORDS = ("crazyflie", "crazyradio", "cflib")

# Motion / locomotion that must wait for K10 A even if the model forgot confirm.
FORCE_CONFIRM = {
    ("reachy", "greet"),
    ("reachy", "demo"),
    ("m3", "demo"),
    ("dogzilla", "demo"),
}

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


class DispatchError(ValueError):
    """Invalid planner output."""


@dataclass(frozen=True)
class Dispatch:
    target: str
    intent: str
    confirm: bool
    say: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def extract_json_object(text: str) -> dict[str, Any]:
    if text is None:
        raise DispatchError("empty Dify answer")
    blob = text.strip()
    if not blob:
        raise DispatchError("empty Dify answer")

    fenced = _FENCE_RE.findall(blob)
    if fenced:
        blob = fenced[0].strip()

    try:
        parsed = json.loads(blob)
    except json.JSONDecodeError:
        start = blob.find("{")
        end = blob.rfind("}")
        if start < 0 or end <= start:
            raise DispatchError("Dify answer is not JSON") from None
        try:
            parsed = json.loads(blob[start : end + 1])
        except json.JSONDecodeError as exc:
            raise DispatchError(f"Dify answer is not JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise DispatchError("Dify JSON must be an object")
    return parsed


def normalize_dispatch(raw: dict[str, Any]) -> Dispatch:
    target = str(raw.get("target", "")).strip().lower()
    intent = str(raw.get("intent", "")).strip().lower()
    say = str(raw.get("say", "")).strip()
    confirm = _as_bool(raw.get("confirm", False))

    if target not in TARGETS:
        raise DispatchError(f"unknown target: {target or '(empty)'}")
    if intent not in INTENTS:
        raise DispatchError(f"unknown intent: {intent or '(empty)'}")
    if not say:
        raise DispatchError("say is required")

    if target in UNWIRED_TARGETS and intent != "status":
        return Dispatch(
            target="k10",
            intent="display",
            confirm=False,
            say=f"{target} 尚未接入 Hermes，改為顯示：{say}",
        )

    if intent == "abort":
        confirm = False
    elif (target, intent) in FORCE_CONFIRM:
        confirm = True

    return Dispatch(target=target, intent=intent, confirm=confirm, say=say)


def looks_like_unsupported_aircraft(query: str) -> bool:
    q = (query or "").lower()
    return any(word in q for word in REJECTED_KEYWORDS)


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False
