"""A local HTTP server for `app/web/`, with ranges and a delay the tests set.

Two things the browser suite needs that `http.server` does not give.

**Range requests.** The waveform is a scrubber, so a drag asks the audio
element for a position it may not have buffered, and the element asks the
server for those bytes. `SimpleHTTPRequestHandler` answers a `Range:` request
with the whole file and `200`, which Chromium accepts but which means a seek is
never exercised over a real range. GitHub Pages answers `206` with
`Accept-Ranges: bytes`, so this does too, and the suite sees the behaviour the
deployed site has. `docs/HARNESS.md` records the difference.

**A delay, and a failure, decided per request path.** The one thing Task 29
learned the hard way: a `time.sleep` inside a Playwright route handler blocks
the driver's own event loop, so the page's state is read after it has already
moved on. The delay has to be the server's. Each request is served on its own
thread here, so a sleep holds that one response and nothing else: the driver
keeps running and the page is read while the fetch is still in the air.

`Plan` is what a test sets. Every field is keyed by the file name alone, with
no query string, because the screens ask for `narrations.json?v=<deploy>` when
a version is stamped in and for `narrations.json` when it is not.

    plan.delay["narrations.json"] = 2.0      # answer, two seconds late
    plan.status["narrations.json"] = 503     # refuse
    plan.hang.add("narrations.json")         # never answer at all

Nothing here writes to the tree it serves, and it binds to 127.0.0.1 on a port
the operating system chooses, so two of these can run at once.
"""

import http.server
import os
import re
import socketserver
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

#: Long enough that a test watching a page is finished before the response
#: lands, short enough that a hung request cannot outlive the suite.
HANG_SECONDS = 120.0

#: What a browser is told it may cache. Nothing: a test that reloads a page
#: with a new plan has to see the plan, not the last answer.
NO_STORE = "no-store, no-cache, must-revalidate"

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".mp3": "audio/mpeg",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".ico": "image/x-icon",
    ".svg": "image/svg+xml",
    ".woff2": "font/woff2",
    ".webmanifest": "application/manifest+json",
}

RANGE = re.compile(r"^bytes=(\d*)-(\d*)$")


@dataclass
class Plan:
    """How the server answers, which a test changes between page loads."""

    delay: dict = field(default_factory=dict)
    status: dict = field(default_factory=dict)
    hang: set = field(default_factory=set)
    #: Every file name asked for, in order, for a test that wants to know
    #: whether a fetch happened at all.
    asked: list = field(default_factory=list)

    def clear(self):
        self.delay.clear()
        self.status.clear()
        self.hang.clear()
        del self.asked[:]


class Handler(http.server.BaseHTTPRequestHandler):
    """One request. `directory` and `plan` come from the server object."""

    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        """Quiet. A failing test says what it saw; the access log does not."""

    # The two verbs a page needs. HEAD is what Chromium sometimes sends for an
    # audio element before it asks for bytes.
    def do_GET(self):
        self.answer(body=True)

    def do_HEAD(self):
        self.answer(body=False)

    def answer(self, body):
        name = self.path.lstrip("/").split("?")[0]
        plan = self.server.plan
        plan.asked.append(name)

        if name in plan.hang:
            # Hold the connection and answer nothing. The test reads the page
            # while this waits, and clearing the plan at the end of the test
            # lets the thread go rather than leaving it to the process.
            waited = 0.0
            while name in plan.hang and waited < HANG_SECONDS:
                time.sleep(0.05)
                waited += 0.05
            return
        if name in plan.delay:
            time.sleep(plan.delay[name])
        if name in plan.status:
            self.fail(plan.status[name])
            return

        path = self.resolve(name)
        if path is None:
            self.fail(404)
            return

        data = path.read_bytes()
        kind = CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream")
        start, end = self.wanted(len(data))
        if start is None:
            self.send_response(416)
            self.send_header("Content-Range", "bytes */%d" % len(data))
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        partial = (start, end) != (0, len(data) - 1)
        self.send_response(206 if partial else 200)
        self.send_header("Content-Type", kind)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", NO_STORE)
        self.send_header("Content-Length", str(end - start + 1))
        if partial:
            self.send_header(
                "Content-Range", "bytes %d-%d/%d" % (start, end, len(data))
            )
        self.end_headers()
        if body:
            self.wfile.write(data[start:end + 1])

    def fail(self, code):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Cache-Control", NO_STORE)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def resolve(self, name):
        """The file `name` asks for, or None.

        A name that climbs out of the served directory is not resolved, which
        matters because the suite points a page at this with URLs it builds
        itself and a mistake should be a 404 rather than a read of the repo.
        """
        if not name:
            name = "index.html"
        root = self.server.directory.resolve()
        try:
            path = (root / name).resolve()
        except OSError:
            return None
        if root not in path.parents and path != root:
            return None
        return path if path.is_file() else None

    def wanted(self, size):
        """(start, end) inclusive, from the Range header, or the whole file.

        (None, None) means the range cannot be satisfied, which is a 416.
        """
        header = self.headers.get("Range")
        if not header or size == 0:
            return 0, max(0, size - 1)
        found = RANGE.match(header.strip())
        if not found:
            return 0, size - 1
        first, last = found.group(1), found.group(2)
        if first == "":
            if last == "":
                return None, None
            length = min(int(last), size)
            return size - length, size - 1
        start = int(first)
        if start >= size:
            return None, None
        end = size - 1 if last == "" else min(int(last), size - 1)
        if end < start:
            return None, None
        return start, end


class Server(socketserver.ThreadingTCPServer):
    """The server. One thread per request, which is what the delay needs."""

    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        """A client that walked away is not an error worth printing.

        Every state this suite is about involves a page being navigated away
        from or a fetch being abandoned, so a half-written response is the
        normal case here. Anything else is raised the usual way.
        """
        kind = sys.exc_info()[0]
        if kind is not None and issubclass(kind, (ConnectionError, BrokenPipeError)):
            return
        super().handle_error(request, client_address)

    def __init__(self, directory):
        self.directory = Path(directory)
        self.plan = Plan()
        super().__init__(("127.0.0.1", 0), Handler)

    @property
    def base(self):
        host, port = self.server_address[:2]
        return "http://%s:%d" % (host, port)

    def url(self, screen, **query):
        """A URL for one screen, with the query a test wants on it."""
        parts = "&".join("%s=%s" % (k, v) for k, v in query.items() if v is not None)
        return "%s/%s%s" % (self.base, screen, ("?" + parts) if parts else "")


def serve(directory):
    """A started server, on its own daemon thread. Close it with `shutdown`."""
    server = Server(directory)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


if __name__ == "__main__":   # pragma: no cover - a hand run, for looking
    web = Path(__file__).resolve().parent.parent.parent / "app" / "web"
    running = serve(web)
    print("serving %s at %s" % (web, running.base))
    print("ctrl-c to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        running.shutdown()
        os._exit(0)
