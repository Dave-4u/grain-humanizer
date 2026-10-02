import os
import unittest

os.environ.pop("OPENAI_API_KEY", None)  # always test the local engine

from fastapi.testclient import TestClient  # noqa: E402

from engine import humanize, local_humanize  # noqa: E402
from main import app  # noqa: E402

SAMPLE = (
    "In today's world, it is important to note that artificial intelligence plays a crucial role "
    "in the digital landscape. Furthermore, organizations must delve into this tapestry of innovation "
    "to leverage cutting-edge solutions."
)


class EngineTests(unittest.TestCase):
    def test_removes_classic_tells(self):
        out = local_humanize(SAMPLE, mode="casual", strength=2).output.lower()
        for tell in ["delve", "tapestry", "it is important to note", "furthermore"]:
            self.assertNotIn(tell, out)
        self.assertIn("artificial intelligence", out)  # meaning kept

    def test_all_modes_and_strengths_return_text(self):
        for mode in ["casual", "professional", "academic-light"]:
            for strength in (1, 2, 3):
                r = humanize(SAMPLE, mode=mode, strength=strength, prefer_llm=False)
                self.assertTrue(r.output.strip())
                self.assertIsInstance(r.changes, list)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")

    def test_ui_served(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Grain", r.text)

    def test_humanize_endpoint(self):
        r = self.client.post("/api/humanize", json={"text": SAMPLE, "mode": "professional", "strength": 3})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["output"])

    def test_validation(self):
        self.assertEqual(self.client.post("/api/humanize", json={"text": "x", "mode": "pirate"}).status_code, 422)
        self.assertEqual(self.client.post("/api/humanize", json={"text": "   "}).json()["output"], "")


if __name__ == "__main__":
    unittest.main()
