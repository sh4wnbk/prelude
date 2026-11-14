r"""Download the one third-party script the app runs, into `app/web/assets/`.

The scanner reads a QR code with `BarcodeDetector` where the browser has it
and with jsQR where it does not, which on iPhone Safari and on Edge for
Windows is always. jsQR was loaded from `cdn.jsdelivr.net` at a pinned version
with a Subresource Integrity hash.

That is the last thing a screen fetched from somewhere else. Task 32 compiled
the stylesheet and brought the fonts into the repo so
`tests/browser/test_every_screen.py` could assert that no screen leaves its
own origin, and this file is what the assertion found: the hash made the
script safe to load and did not make it present. A blocked CDN left the
scanner with no reader on exactly the browsers that need one.

**The integrity hash is still the check.** It is not an attribute on a
same-origin script tag any more; it is checked here, before the file is
written, against the hash the scanner carried. A download that does not match
is refused and nothing is written, so the committed copy is the same bytes the
pinned version served.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\fetch_vendor.py --plan
    .\.venv-prelude\Scripts\python.exe -I scripts\fetch_vendor.py --confirm

Standard library only.
"""

import argparse
import base64
import hashlib
import sys
import urllib.request
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "app" / "web" / "assets" / "vendor"

#: (name, url, integrity, filename). The URL and the integrity hash are the
#: ones `app/web/prelude_05_scan.html` carried before it loaded this copy.
WANTED = (
    (
        "jsQR 1.4.0",
        "https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js",
        "sha384-b5Ya4Bq3qCyz39m2ISh+4DxjAIljdeFwK/BsXLuj9gugaNwAcj/ia15fxNZL9Nlx",
        "jsQR.js",
    ),
)

UA = "Mozilla/5.0 (compatible; prelude-build)"


def integrity_of(body: bytes, algorithm: str) -> str:
    digest = hashlib.new(algorithm, body).digest()
    return algorithm + "-" + base64.b64encode(digest).decode("ascii")


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--plan", action="store_true",
        help="print what would be downloaded and write nothing",
    )
    parser.add_argument(
        "--confirm", action="store_true", help="download and write the files",
    )
    args = parser.parse_args(argv)

    for name, url, integrity, filename in WANTED:
        print("{:<12} {}".format(name, url))
        print("{:<12} {}".format("integrity", integrity))
        print("{:<12} {}".format(
            "into", (VENDOR / filename).relative_to(ROOT).as_posix()
        ))
    print()
    if args.plan or not args.confirm:
        print("nothing was written. --confirm is what writes it.")
        return 0

    VENDOR.mkdir(parents=True, exist_ok=True)
    for name, url, integrity, filename in WANTED:
        request = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(request, timeout=60) as answer:
            body = answer.read()
        algorithm = integrity.split("-", 1)[0]
        got = integrity_of(body, algorithm)
        if got != integrity:
            raise SystemExit(
                "{} does not match the pinned integrity hash. Wanted {}, got "
                "{}. Nothing was written.".format(name, integrity, got)
            )
        (VENDOR / filename).write_bytes(body)
        print("  {:>7,} bytes  {}  ({} matches)".format(
            len(body), filename, algorithm
        ))
    print()
    print("wrote {}".format(VENDOR.relative_to(ROOT).as_posix()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
