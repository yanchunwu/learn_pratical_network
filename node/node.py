import os
import socketserver
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path


NODE_NAME = os.environ.get("NODE_NAME", "unknown")
LOG_PATH = Path("/data/states.log")
LISTEN_PORT = 9000


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class EchoHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        self.rfile.readline()
        self.wfile.write(f"{NODE_NAME} {utc_now()}\n".encode("utf-8"))


class ThreadedTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


def start_server() -> None:
    with ThreadedTCPServer(("0.0.0.0", LISTEN_PORT), EchoHandler) as server:
        server.daemon_threads = True
        server.serve_forever()


def maintain_state_log() -> None:
    entries: deque[tuple[float, str]] = deque()

    while True:
        now = time.time()
        line = f"{NODE_NAME} {utc_now()}"
        entries.append((now, line))

        cutoff = now - 60
        while entries and entries[0][0] < cutoff:
            entries.popleft()

        LOG_PATH.write_text("\n".join(item for _, item in entries) + "\n", encoding="utf-8")
        time.sleep(1)


def main() -> None:
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    maintain_state_log()


if __name__ == "__main__":
    main()
