from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import threading
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "loadtest.py"


class LoadTestTests(unittest.TestCase):
    def run_load_test(self, status, body):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(status)
                self.end_headers()
                self.wfile.write(json.dumps(body).encode())

            def log_message(self, *args):
                pass

        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                return subprocess.run(
                    [
                        sys.executable, str(SCRIPT),
                        f"http://127.0.0.1:{server.server_port}",
                        "--duration", "1", "--concurrency", "1",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            finally:
                server.shutdown()
                thread.join()

    def test_healthy_replica_succeeds(self):
        result = self.run_load_test(200, {"status": "ok", "hostname": "replica-one"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("replica-one:", result.stdout)

    def test_failed_health_check_fails_with_diagnostics(self):
        for status in (200, 503):
            with self.subTest(status=status):
                result = self.run_load_test(status, {"status": "error", "hostname": "replica-one"})
                self.assertEqual(result.returncode, 1)
                self.assertNotIn("replica-one:", result.stdout)
                self.assertIn("ValueError" if status == 200 else "HTTPError", result.stderr)

    def test_non_positive_arguments_are_rejected(self):
        for argument, value in (("--duration", "0"), ("--concurrency", "-1")):
            with self.subTest(argument=argument):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "http://127.0.0.1:1", argument, value],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("must be greater than zero", result.stderr)


if __name__ == "__main__":
    unittest.main()
