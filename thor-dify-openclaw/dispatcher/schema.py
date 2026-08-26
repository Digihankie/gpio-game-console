"""Parse the thin Dify fetch-planner JSON: item / dest / recipient."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any

SOURCES = ("reachy", "k10")
TARGETS = ("dogzilla", "reachy", "k10")
INTENTS = ("fetch", "abort", "status", "say", "display")
SCOUTS = ("crazyflie", "none")
# 飛機只准當眼睛。把「用飛機送東西」講成要夾送時，仍走狗，scout 開著。
AIR_DELIVERY_HINTS = ("用飛機送", "飛過去拿", "空投", "drone delivery")

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


class DispatchError(ValueError):
    """Invalid planner output."""


@dataclass(frozen=True)
class Dispatch:
    source: str
    target: str
    intent: str
    confirm: bool
    say: str
    item: str = ""
    dest: str = ""
    recipient: str = ""
    scout: str = "none"
    verify: str = "none"

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


def normalize_source(value: Any, default: str = "reachy") -> str:
    source = str(value or default).strip().lower()
    return source if source in SOURCES else default


def normalize_dispatch(raw: dict[str, Any], source: str | None = None) -> Dispatch:
    ingress = normalize_source(source if source is not None else raw.get("source"))
    intent = str(raw.get("intent", "")).strip().lower()
    target = str(raw.get("target", "")).strip().lower()
    say = str(raw.get("say", "")).strip()
    item = str(raw.get("item", "")).strip()
    dest = str(raw.get("dest") or raw.get("destination") or "").strip()
    recipient = str(raw.get("recipient") or raw.get("give_to") or "").strip()
    confirm = _as_bool(raw.get("confirm", False))
    scout = str(raw.get("scout", "")).strip().lower()

    if intent not in INTENTS:
        raise DispatchError(f"unknown intent: {intent or '(empty)'}")

    if intent == "fetch":
        if not (item and dest and recipient):
            return Dispatch(
                source=ingress,
                target=ingress,
                intent="display",
                confirm=False,
                say="請再說一次：要拿什麼、送到哪裡、給誰",
            )
        if scout not in SCOUTS:
            scout = "none"
        verify = str(raw.get("verify", "")).strip().lower()
        if verify not in ("none", "yolo"):
            verify = "yolo" if scout == "crazyflie" else "none"
        return Dispatch(
            source=ingress,
            target="dogzilla",
            intent="fetch",
            confirm=True,
            say=say or _fetch_say(item, dest, recipient, scout, verify),
            item=item,
            dest=dest,
            recipient=recipient,
            scout=scout,
            verify=verify,
        )

    if intent == "abort":
        if target not in TARGETS:
            target = "dogzilla"
        return Dispatch(
            source=ingress,
            target=target,
            intent="abort",
            confirm=False,
            say=say or "停止目前任務",
            scout="crazyflie",
        )

    if target not in TARGETS:
        raise DispatchError(f"unknown target: {target or '(empty)'}")
    if not say:
        raise DispatchError("say is required")

    return Dispatch(
        source=ingress,
        target=target,
        intent=intent,
        confirm=False,
        say=say,
        item=item,
        dest=dest,
        recipient=recipient,
        scout="none",
        verify="none",
    )


def looks_like_air_delivery(query: str) -> bool:
    q = query or ""
    return any(hint in q for hint in AIR_DELIVERY_HINTS)


def _fetch_say(item: str, dest: str, recipient: str, scout: str, verify: str) -> str:
    if scout == "crazyflie" and verify == "yolo":
        return f"飛鴿先探{item}，驛馬到點後以 YOLO 確認，再送到{dest}給{recipient}"
    if scout == "crazyflie":
        return f"小飛機先看{item}在哪，再讓機器狗送到{dest}給{recipient}"
    return f"驛馬快去把{item}送到{dest}給{recipient}"


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False
