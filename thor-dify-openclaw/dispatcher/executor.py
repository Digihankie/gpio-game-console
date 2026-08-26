"""Map a fetch Dispatch onto Thor NVIDIA + Dogzilla + the speaking assistant."""

from __future__ import annotations

from typing import Any

from .schema import Dispatch

ToolCall = dict[str, Any]


def plan_calls(dispatch: Dispatch) -> list[ToolCall]:
    if dispatch.intent == "fetch":
        return _fetch_calls(dispatch)
    if dispatch.intent == "abort":
        calls: list[ToolCall] = [{"tool": "crazyflie_land", "args": {}}]
        if dispatch.target == "dogzilla":
            calls.append({"tool": "dogzilla_stop", "args": {}})
            return calls
        if dispatch.target == "reachy":
            calls.extend(
                [
                    {"tool": "reachy_watch_stop", "args": {}},
                    {"tool": "reachy_set_idle_pose", "args": {}},
                ]
            )
            return calls
        calls.append({"tool": "k10_display", "args": {"text": dispatch.say}})
        return calls
    if dispatch.intent == "status" and dispatch.target == "dogzilla":
        return [{"tool": "dogzilla_status", "args": {}}]
    if dispatch.target == "reachy":
        if dispatch.intent == "status":
            return [{"tool": "reachy_status", "args": {}}]
        return [{"tool": "reachy_speak", "args": {"text": dispatch.say}}]
    return [{"tool": "k10_display", "args": {"text": dispatch.say}}]


def _fetch_calls(dispatch: Dispatch) -> list[ToolCall]:
    announce = {"tool": "reachy_speak", "args": {"text": dispatch.say}}
    if dispatch.source == "k10":
        announce = {"tool": "k10_display", "args": {"text": dispatch.say}}
    locate_camera = "dogzilla"
    prefix: list[ToolCall] = []
    if dispatch.scout == "crazyflie":
        locate_camera = "crazyflie"
        prefix = [
            {"tool": "crazyflie_takeoff", "args": {"height_m": 0.5}},
            {"tool": "crazyflie_look", "args": {"item": dispatch.item}},
        ]
    calls = prefix + [
        {
            "tool": "nvidia_vlm_locate",
            "args": {"item": dispatch.item, "camera": locate_camera},
        },
    ]
    if dispatch.scout == "crazyflie":
        calls.append({"tool": "crazyflie_land", "args": {}})
    calls.extend(
        [
            {"tool": "dogzilla_goto", "args": {"place": dispatch.item}},
            {"tool": "dogzilla_grasp", "args": {"item": dispatch.item}},
            {"tool": "dogzilla_goto", "args": {"place": dispatch.dest}},
            {"tool": "dogzilla_release", "args": {"recipient": dispatch.recipient}},
            announce,
        ]
    )
    return calls
