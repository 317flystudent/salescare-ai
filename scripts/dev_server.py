from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import threading
import time


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
sys.path.insert(0, str(BACKEND_DIR))

from config import CHATBOT_HOST, CHATBOT_PORT  # noqa: E402
from database import init_db  # noqa: E402
from server import ApiHandler  # noqa: E402


class FrontendHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("frontend - - [%s] %s" % (self.log_date_time_string(), fmt % args))


def serve(name, httpd):
    print(f"{name} running at http://{httpd.server_address[0]}:{httpd.server_address[1]}")
    httpd.serve_forever()


def main():
    init_db()
    frontend_port = 5173
    api_server = ThreadingHTTPServer((CHATBOT_HOST, CHATBOT_PORT), ApiHandler)
    frontend_handler = partial(FrontendHandler, directory=str(FRONTEND_DIR))
    frontend_server = ThreadingHTTPServer((CHATBOT_HOST, frontend_port), frontend_handler)

    threads = [
        threading.Thread(target=serve, args=("backend", api_server), daemon=True),
        threading.Thread(target=serve, args=("frontend", frontend_server), daemon=True),
    ]
    for thread in threads:
        thread.start()

    print("Press Ctrl+C to stop both services.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping services...")
        api_server.shutdown()
        frontend_server.shutdown()


if __name__ == "__main__":
    main()

