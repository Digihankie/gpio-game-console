import unittest

from dispatcher.schema import Dispatch
from dispatcher.service import DispatchService
from dispatcher.store import PendingStore


class FakePlanner:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.queries: list[str] = []

    def chat(self, query: str) -> str:
        self.queries.append(query)
        return self.answer


FETCH_JSON = (
    '{"intent":"fetch","item":"馬克杯","dest":"客廳茶几","recipient":"Hank",'
    '"say":"機器狗去把馬克杯送到客廳給 Hank"}'
)


class ServiceTests(unittest.TestCase):
    def test_voice_from_k10_waits_for_confirm(self):
        planner = FakePlanner(FETCH_JSON)
        service = DispatchService(planner=planner, store=PendingStore(), dry_run=True)
        result = service.plan_voice("k10", "把桌上的馬克杯拿到客廳給 Hank")
        self.assertEqual(result["status"], "awaiting_confirm")
        self.assertEqual(result["pending"]["dispatch"]["target"], "dogzilla")
        self.assertEqual(result["pending"]["dispatch"]["source"], "k10")
        self.assertTrue(planner.queries[0].startswith("[助理=k10]"))

        approved = service.confirm(result["pending"]["id"], True)
        self.assertEqual(approved["status"], "ready")
        self.assertEqual(approved["calls"][0]["tool"], "dogzilla_goto")
        self.assertEqual(approved["calls"][1]["tool"], "dogzilla_grasp")

    def test_reachy_say_is_ready(self):
        planner = FakePlanner(
            '{"intent":"say","target":"reachy","confirm":false,"say":"收到，機器狗出發"}'
        )
        service = DispatchService(planner=planner, store=PendingStore(), dry_run=True)
        result = service.plan_query("跟我說一聲收到", source="reachy")
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["calls"][0]["tool"], "reachy_speak")

    def test_second_pass_json_scouts_and_verifies(self):
        planner = FakePlanner(
            '{"intent":"fetch","item":"荔枝","dest":"沙發","recipient":"貴妃",'
            '"scout":"crazyflie","verify":"yolo","say":"先探再認"}'
        )
        service = DispatchService(planner=planner, store=PendingStore(), dry_run=True)
        result = service.plan_voice("reachy", "此非荔枝，派飛鴿再探")
        self.assertEqual(result["pending"]["dispatch"]["scout"], "crazyflie")
        self.assertEqual(result["pending"]["dispatch"]["verify"], "yolo")
        self.assertEqual(result["pending"]["calls"][0]["tool"], "crazyflie_takeoff")
        self.assertEqual(result["pending"]["calls"][5]["tool"], "yolo_confirm")

    def test_empty_query(self):
        service = DispatchService(planner=FakePlanner("{}"), dry_run=True)
        with self.assertRaises(Exception):
            service.plan_query("  ")

    def test_pending_idle(self):
        service = DispatchService(planner=FakePlanner("{}"), dry_run=True)
        self.assertEqual(service.pending()["status"], "idle")

    def test_direct_submit_k10_display(self):
        service = DispatchService(planner=FakePlanner("{}"), dry_run=True)
        result = service.submit(
            Dispatch(source="k10", target="k10", intent="display", confirm=False, say="待命")
        )
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["calls"][0]["tool"], "k10_display")


if __name__ == "__main__":
    unittest.main()
