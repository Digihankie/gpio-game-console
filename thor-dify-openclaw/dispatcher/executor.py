"""Map a Dispatch onto Reachy MCP tool calls (or a stub for unwired bodies)."""

from __future__ import annotations

from typing import Any

from .schema import Dispatch

ReachyCall = dict[str, Any]


def plan_calls(dispatch: Dispatch) -> list[ReachyCall]:
    if dispatch.target == "reachy":
        return _reachy_calls(dispatch.intent, dispatch.say)
    if dispatch.target == "k10":
        return [{"tool": "k10_display", "args": {"text": dispatch.say}}]
    return [{"tool": f"{dispatch.target}_unavailable", "args": {"say": dispatch.say}}]


def _reachy_calls(intent: str, say: str) -> list[ReachyCall]:
    if intent == "status":
        return [{"tool": "reachy_status", "args": {}}]
    if intent == "say":
        return [{"tool": "reachy_speak", "args": {"text": say}}]
    if intent == "look":
        return [{"tool": "reachy_scan_for_face", "args": {}}]
    if intent == "greet":
        return [
            {"tool": "reachy_wake", "args": {}},
            {"tool": "reachy_speak", "args": {"text": say}},
            {"tool": "reachy_gesture", "args": {"name": "talking"}},
        ]
    if intent == "demo":
        return [
            {"tool": "reachy_wake", "args": {}},
            {"tool": "reachy_play_emotion", "args": {"name": "happy"}},
            {"tool": "reachy_speak", "args": {"text": say}},
        ]
    if intent == "abort":
        return [
            {"tool": "reachy_watch_stop", "args": {}},
            {"tool": "reachy_set_idle_pose", "args": {}},
        ]
    return [{"tool": "reachy_speak", "args": {"text": say}}]
