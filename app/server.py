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
            content_type = "application/json"
            body = json.dumps(response).encode("utf-8")

        elif self.path == "/":
            response = {
                "message": "Deployed automatically with Jenkins and Argo CD and exposed to vnet!",
                "result": add(2, 3)
            }
            content_type = "application/json"
            body = json.dumps(response).encode("utf-8")

        elif self.path == "/home":
            content_type = "text/html; charset=utf-8"
            body = b"""<!doctype html>
                    <html lang="fr">
                    <head>
                        <meta charset="utf-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        <title>Jenkins Python Lab</title>
                    </head>
                    <body>
                        <h1>Bienvenue</h1>
                        <p>La page web est servie par Python.</p>
                    </body>
                    </html>
                    """

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