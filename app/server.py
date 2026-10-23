import json
import os
from pathlib import Path

from http.server import BaseHTTPRequestHandler, HTTPServer

from app.calculator import add


APP_DIR = Path(__file__).parent


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/health":
            response = {
                "status": "healthy"
            }
            content_type = "application/json"
            body = json.dumps(response).encode("utf-8")

        elif self.path == "/":
            content_type = "text/html; charset=utf-8"
            body = (APP_DIR / "ui" / "index.html").read_bytes()

        elif self.path == "/home":
            content_type = "text/html; charset=utf-8"
            body = (APP_DIR / "ui" / "home.html").read_bytes()

        elif self.path == "/calculate":
            response = {
                "result": add(2, 3)
            }
            content_type = "application/json"
            body = json.dumps(response).encode("utf-8")

        else:
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        self.wfile.write(body)


if __name__ == "__main__":

    port = int(os.environ.get("PORT", "8000"))

    server = HTTPServer(("0.0.0.0", port), Handler)

    print(f"Server running on port {port}", flush=True)

    server.serve_forever()