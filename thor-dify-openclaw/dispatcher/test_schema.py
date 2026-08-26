import unittest

from dispatcher.executor import plan_calls
from dispatcher.schema import DispatchError, extract_json_object, looks_like_unsupported_aircraft, normalize_dispatch


class ExtractJsonTests(unittest.TestCase):
    def test_plain_object(self):
        raw = '{"target":"reachy","intent":"say","confirm":false,"say":"你好"}'
        self.assertEqual(extract_json_object(raw)["target"], "reachy")

    def test_fenced_markdown(self):
        raw = "好的\n```json\n{\"target\":\"k10\",\"intent\":\"display\",\"confirm\":false,\"say\":\"待命\"}\n```\n"
        self.assertEqual(extract_json_object(raw)["say"], "待命")

    def test_prose_around_object(self):
        raw = '調度如下：{"target":"reachy","intent":"status","confirm":false,"say":"狀態"} 結束'
        self.assertEqual(extract_json_object(raw)["intent"], "status")

    def test_empty(self):
        with self.assertRaises(DispatchError):
            extract_json_object("   ")


class NormalizeTests(unittest.TestCase):
    def test_force_confirm_on_greet(self):
        dispatch = normalize_dispatch(
            {"target": "Reachy", "intent": "greet", "confirm": False, "say": "大家好"}
        )
        self.assertTrue(dispatch.confirm)
        self.assertEqual(dispatch.target, "reachy")

    def test_abort_never_confirms(self):
        dispatch = normalize_dispatch(
            {"target": "reachy", "intent": "abort", "confirm": True, "say": "停"}
        )
        self.assertFalse(dispatch.confirm)

    def test_unwired_m3_demo_becomes_k10_display(self):
        dispatch = normalize_dispatch(
            {"target": "m3", "intent": "demo", "confirm": True, "say": "前進"}
        )
        self.assertEqual(dispatch.target, "k10")
        self.assertEqual(dispatch.intent, "display")
        self.assertFalse(dispatch.confirm)
        self.assertIn("尚未接入", dispatch.say)

    def test_unknown_target(self):
        with self.assertRaises(DispatchError):
            normalize_dispatch({"target": "drone", "intent": "say", "say": "x"})

    def test_missing_say(self):
        with self.assertRaises(DispatchError):
            normalize_dispatch({"target": "reachy", "intent": "say", "say": ""})

    def test_crazyflie_query_detected(self):
        self.assertTrue(looks_like_unsupported_aircraft("讓 Crazyflie 起飛"))
        self.assertFalse(looks_like_unsupported_aircraft("讓 Reachy 揮手"))


class ExecutorTests(unittest.TestCase):
    def test_greet_uses_wake_speak_gesture(self):
        dispatch = normalize_dispatch(
            {"target": "reachy", "intent": "greet", "confirm": True, "say": "你好"}
        )
        tools = [call["tool"] for call in plan_calls(dispatch)]
        self.assertEqual(tools, ["reachy_wake", "reachy_speak", "reachy_gesture"])

    def test_status_is_read_only(self):
        dispatch = normalize_dispatch(
            {"target": "reachy", "intent": "status", "confirm": False, "say": "查狀態"}
        )
        self.assertEqual(plan_calls(dispatch)[0]["tool"], "reachy_status")


if __name__ == "__main__":
    unittest.main()
