import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from dispatcher.app import make_handler
from dispatcher.service import DispatchService
from dispatcher.store import PendingStore


class FakePlanner:
    def chat(self, query: str) -> str:
        return '{"target":"reachy","intent":"say","confirm":false,"say":"%s"}' % query


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        service = DispatchService(planner=FakePlanner(), store=PendingStore(), dry_run=True)
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(service))
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def _json(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"} if payload is not None else {},
        )
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def test_health(self):
        status, body = self._json("GET", "/health")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["role"], "dify-hermes-bridge")

    def test_plan_and_pending(self):
        status, body = self._json("POST", "/plan", {"query": "午安"})
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ready")
        self.assertEqual(body["calls"][0]["args"]["text"], "午安")

        status, body = self._json("GET", "/pending")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "idle")


if __name__ == "__main__":
    unittest.main()
