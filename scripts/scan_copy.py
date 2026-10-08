"""Scan the web screens for banned copy and report every hit with file and line.

Exit code is 1 if anything is found, so this can gate a commit. Run:

    .\\.venv-prelude\\Scripts\\python.exe -I scripts\\scan_copy.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# The screens, plus matches.json, which holds display copy and so is subject to
# the same rules as copy written into the markup.
SCREENS = sorted((ROOT / "app" / "web").glob("*.html")) + sorted((ROOT / "app" / "web").glob("*.json"))

# (label, regex). Word boundaries where a bare substring would false-positive:
# "BOS" inside "boston"-like tokens, "dB" inside words, "official" inside
# "officially" is still a hit and is meant to be.
BANNED = [
    ("basketball term", r"\bKnicks\b"),
    ("basketball term", r"\bCeltics\b"),
    ("basketball term", r"\bNYK\b"),
    ("basketball term", r"\bBOS\b"),
    ("basketball term", r"\bQ3\b"),
    ("basketball term", r"\bBrunson\b"),
    ("basketball term", r"3-pointer"),
    ("basketball term", r"Madison Square Garden"),
    ("verdict nickname", r"Goal of the Century"),
    ("verdict nickname", r"Hand of God"),
    ("verdict nickname", r"Controvers\w*"),
    ("unearned authority", r"\bofficial\w*"),
    ("60-second framing", r"60 seconds"),
    ("60-second framing", r"60-Second"),
    ("invented hardware", r"\bUWB\b"),
    ("invented hardware", r"\bhaptic\w*"),
    ("invented hardware", r"\bdB\b"),
    ("em dash", r"—"),
]

COMPILED = [(label, re.compile(pattern, re.IGNORECASE)) for label, pattern in BANNED]


def main():
    if not SCREENS:
        raise SystemExit(f"no screens found under {ROOT / 'app' / 'web'}")

    hits = 0
    for path in SCREENS:
        rel = path.relative_to(ROOT).as_posix()
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for label, pattern in COMPILED:
                for match in pattern.finditer(line):
                    hits += 1
                    start = max(0, match.start() - 50)
                    end = min(len(line), match.end() + 50)
                    print(f"{rel}:{lineno}  [{label}] {match.group(0)!r}")
                    print(f"    ...{line[start:end].strip()}...")

    print(f"\nscanned {len(SCREENS)} screens, {hits} hit(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
