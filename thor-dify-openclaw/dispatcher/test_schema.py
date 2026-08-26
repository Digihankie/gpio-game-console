import unittest

from dispatcher.executor import plan_calls
from dispatcher.schema import DispatchError, extract_json_object, looks_like_air_delivery, normalize_dispatch


class ExtractJsonTests(unittest.TestCase):
    def test_plain_object(self):
        raw = '{"intent":"fetch","item":"杯子","dest":"客廳","recipient":"Hank","say":"去拿"}'
        self.assertEqual(extract_json_object(raw)["item"], "杯子")

    def test_fenced_markdown(self):
        raw = "好的\n```json\n{\"intent\":\"display\",\"target\":\"k10\",\"say\":\"待命\"}\n```\n"
        self.assertEqual(extract_json_object(raw)["say"], "待命")

    def test_empty(self):
        with self.assertRaises(DispatchError):
            extract_json_object("   ")


class NormalizeTests(unittest.TestCase):
    def test_fetch_forces_dogzilla_and_confirm(self):
        dispatch = normalize_dispatch(
            {
                "intent": "fetch",
                "target": "reachy",
                "confirm": False,
                "item": "紅色馬克杯",
                "dest": "會議室A",
                "recipient": "Hank",
                "say": "出發",
            },
            source="k10",
        )
        self.assertEqual(dispatch.source, "k10")
        self.assertEqual(dispatch.target, "dogzilla")
        self.assertEqual(dispatch.intent, "fetch")
        self.assertTrue(dispatch.confirm)
        self.assertEqual(dispatch.item, "紅色馬克杯")
        self.assertEqual(dispatch.dest, "會議室A")
        self.assertEqual(dispatch.recipient, "Hank")
        self.assertEqual(dispatch.scout, "none")
        self.assertEqual(dispatch.verify, "none")

    def test_incomplete_fetch_asks_again(self):
        dispatch = normalize_dispatch(
            {"intent": "fetch", "item": "杯子", "dest": "", "recipient": "Hank", "say": "x"},
            source="reachy",
        )
        self.assertEqual(dispatch.intent, "display")
        self.assertEqual(dispatch.target, "reachy")
        self.assertFalse(dispatch.confirm)
        self.assertIn("再說一次", dispatch.say)

    def test_abort_never_confirms(self):
        dispatch = normalize_dispatch(
            {"intent": "abort", "target": "dogzilla", "confirm": True, "say": "停"},
            source="reachy",
        )
        self.assertFalse(dispatch.confirm)
        self.assertEqual(dispatch.target, "dogzilla")

    def test_destination_alias(self):
        dispatch = normalize_dispatch(
            {
                "intent": "fetch",
                "item": "鑰匙",
                "destination": "門口",
                "give_to": "客人",
                "say": "送鑰匙",
            }
        )
        self.assertEqual(dispatch.dest, "門口")
        self.assertEqual(dispatch.recipient, "客人")

    def test_unknown_intent(self):
        with self.assertRaises(DispatchError):
            normalize_dispatch({"intent": "dance", "say": "x"})

    def test_air_delivery_is_not_a_fetch_body(self):
        self.assertTrue(looks_like_air_delivery("用飛機送馬克杯"))
        self.assertFalse(looks_like_air_delivery("小飛機先看一下再讓狗去拿"))

    def test_explicit_no_scout(self):
        dispatch = normalize_dispatch(
            {
                "intent": "fetch",
                "item": "杯子",
                "dest": "客廳",
                "recipient": "Hank",
                "scout": "none",
                "say": "直接放狗",
            }
        )
        self.assertEqual(dispatch.scout, "none")
        self.assertEqual(dispatch.verify, "none")

    def test_second_pass_enables_scout_and_yolo(self):
        dispatch = normalize_dispatch(
            {
                "intent": "fetch",
                "item": "嶺南荔枝",
                "dest": "沙發",
                "recipient": "貴妃",
                "scout": "crazyflie",
                "verify": "yolo",
                "say": "飛鴿先探，到點再認",
            }
        )
        self.assertEqual(dispatch.scout, "crazyflie")
        self.assertEqual(dispatch.verify, "yolo")


class ExecutorTests(unittest.TestCase):
    def test_first_pass_is_casual_horse_only(self):
        dispatch = normalize_dispatch(
            {
                "intent": "fetch",
                "item": "荔枝",
                "dest": "長安",
                "recipient": "貴妃",
                "say": "快馬加鞭",
            },
            source="reachy",
        )
        tools = [call["tool"] for call in plan_calls(dispatch)]
        self.assertEqual(
            tools,
            [
                "dogzilla_goto",
                "dogzilla_grasp",
                "dogzilla_goto",
                "dogzilla_release",
                "reachy_speak",
            ],
        )

    def test_second_pass_scouts_then_yolo_then_grasp(self):
        dispatch = normalize_dispatch(
            {
                "intent": "fetch",
                "item": "荔枝",
                "dest": "長安",
                "recipient": "貴妃",
                "scout": "crazyflie",
                "verify": "yolo",
                "say": "先探再認",
            },
            source="reachy",
        )
        tools = [call["tool"] for call in plan_calls(dispatch)]
        self.assertEqual(
            tools,
            [
                "crazyflie_takeoff",
                "crazyflie_look",
                "nvidia_vlm_locate",
                "crazyflie_land",
                "dogzilla_goto",
                "yolo_confirm",
                "dogzilla_grasp",
                "dogzilla_goto",
                "dogzilla_release",
                "reachy_speak",
            ],
        )
        self.assertEqual(plan_calls(dispatch)[2]["args"]["camera"], "crazyflie")
        self.assertEqual(plan_calls(dispatch)[5]["args"]["blessed_by"], "reachy")

    def test_k10_ingress_announces_on_k10(self):
        dispatch = normalize_dispatch(
            {
                "intent": "fetch",
                "item": "遙控器",
                "dest": "沙發",
                "recipient": "媽媽",
                "say": "送遙控器",
            },
            source="k10",
        )
        self.assertEqual(plan_calls(dispatch)[-1]["tool"], "k10_display")


if __name__ == "__main__":
    unittest.main()
