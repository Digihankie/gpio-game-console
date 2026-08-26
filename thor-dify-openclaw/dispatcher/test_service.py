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


class ServiceTests(unittest.TestCase):
    def test_safe_say_is_ready(self):
        planner = FakePlanner(
            '{"target":"reachy","intent":"say","confirm":false,"say":"午安"}'
        )
        service = DispatchService(planner=planner, store=PendingStore(), dry_run=True)
        result = service.plan_query("請 Reachy 說午安")
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["dispatch"]["intent"], "say")
        self.assertEqual(result["calls"][0]["tool"], "reachy_speak")
        self.assertTrue(result["dry_run"])

    def test_greet_waits_for_k10(self):
        planner = FakePlanner(
            '{"target":"reachy","intent":"greet","confirm":false,"say":"大家好"}'
        )
        service = DispatchService(planner=planner, store=PendingStore(), dry_run=True)
        result = service.plan_query("跟大家打招呼")
        self.assertEqual(result["status"], "awaiting_confirm")
        pending_id = result["pending"]["id"]

        denied = service.confirm(pending_id, False)
        self.assertEqual(denied["status"], "denied")

        result = service.plan_query("再打一次招呼")
        approved = service.confirm(result["pending"]["id"], True)
        self.assertEqual(approved["status"], "ready")
        self.assertEqual(approved["calls"][0]["tool"], "reachy_wake")

    def test_crazyflie_blocked_without_dify(self):
        planner = FakePlanner("should not be called")
        service = DispatchService(planner=planner, store=PendingStore(), dry_run=True)
        result = service.plan_query("Crazyflie 起飛")
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["dispatch"]["target"], "k10")
        self.assertEqual(planner.queries, [])

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
            Dispatch(target="k10", intent="display", confirm=False, say="待命")
        )
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["calls"][0]["tool"], "k10_display")


if __name__ == "__main__":
    unittest.main()
