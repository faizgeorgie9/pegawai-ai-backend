import http.server
import json
import socketserver
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent / "evidence" / "ui_demos_20261109"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/save":
            self.send_error(404)
            return
        name = parse_qs(parsed.query).get("name", [""])[0]
        safe = Path(name).name
        if not safe:
            self.send_error(400, "missing name")
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        (ROOT / safe).write_bytes(body)
        payload = json.dumps({"saved": safe, "bytes": len(body)}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


with socketserver.TCPServer(("127.0.0.1", 8099), Handler) as httpd:
    httpd.serve_forever()
