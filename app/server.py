import json
import os

from http.server import BaseHTTPRequestHandler, HTTPServer

from app.calculator import add


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/health":
            response = {
                "status": "healthy"
            }

        elif self.path == "/":
            response = {
                "message": "Hello from Jenkins CI/CD!",
                "result": add(2, 3)
            }

        else:
            self.send_error(404)
            return

        body = json.dumps(response).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        self.wfile.write(body)


if __name__ == "__main__":

    port = int(os.environ.get("PORT", "8000"))

    server = HTTPServer(("0.0.0.0", port), Handler)

    print(f"Server running on port {port}", flush=True)

    server.serve_forever()