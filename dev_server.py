"""Local test server: serves public/ and routes /api/calculate to the same
handler Vercel uses. Run:  python3 dev_server.py   then open http://localhost:3000
"""
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "api"))
from calculate import handler as ApiHandler  # noqa: E402


class Dev(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(ROOT, "public"), **kwargs)

    def do_POST(self):
        if self.path.startswith("/api/calculate"):
            return ApiHandler.do_POST(self)
        self.send_error(404)

    def _send(self, *a, **k):  # reuse API helper for JSON replies
        return ApiHandler._send(self, *a, **k)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print(f"Open http://localhost:{port}")
    HTTPServer(("127.0.0.1", port), Dev).serve_forever()
