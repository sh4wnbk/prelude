r"""Generate one demo ticket QR code per match, and prove each one decodes.

The payload is a URL: `<site>/?ticket=<match_id>:<section>:<row>:<seat>`, built
from the seat fields in `app/web/matches.json`. Those fields are the same ones
the Live screen renders, so a ticket code and the ticket line a fan reads on
screen cannot drift apart: this refuses to write anything if they disagree.

It is a URL because a phone's own camera app only offers to open what it can
recognise. The bare `prelude:...` string these codes used to carry read back as
text with nothing to do, so the code worked only from inside Prelude's own
scanner. A https URL opens the app at that ticket from any camera app. The
scanner still reads the old form, so a code printed earlier keeps working.

Writing an image is not evidence that it holds the payload, so every code is
read back off the PNG with a real decoder and compared byte for byte. A
mismatch, or a code that will not decode at all, exits non-zero.

The seats are demo fixture data, not play data. `HANDOFF.md` records why: the
seat is the fan's own ticket, not a claim about the match, so it carries no
grounding obligation. Nothing here reads `data/raw/`.

Decoding needs the dev dependencies (`zxing-cpp` and `pillow`). Run:

    .\.venv-prelude\Scripts\python.exe -I scripts\make_tickets.py
"""

import json
import sys
from pathlib import Path

import segno

ROOT = Path(__file__).resolve().parent.parent
MATCHES = ROOT / "app" / "web" / "matches.json"
OUT_DIR = ROOT / "app" / "web" / "assets" / "tickets"

SEAT_FIELDS = ("section", "row", "seat")
DOT = "·"

# Where the codes point. Changing this means regenerating both images, because
# the URL is inside them; the README and HANDOFF.md name the same site.
SITE = "https://sh4wnbk.github.io/prelude/"

# Medium recovers from roughly 15% damage, which is what a ticket shown on a
# phone screen or printed and creased actually needs. Black on white, because a
# themed code is a code that sometimes does not scan.
ERROR_LEVEL = "m"
SCALE = 8
BORDER = 4


def require_seat_fields(match):
    """Every part of the payload has to be in the data, not supplied here."""
    seat = match["live_seated"]
    missing = [f for f in SEAT_FIELDS if not seat.get(f)]
    if missing:
        raise SystemExit(
            f"match {match['match_id']} has no {', '.join(missing)} in matches.json; "
            "the payload cannot be built from data that is not there"
        )


def payload_for(match):
    """`<site>/?ticket=<match_id>:<section>:<row>:<seat>` for one match."""
    seat = match["live_seated"]
    return "{}?ticket={}:{}:{}:{}".format(
        SITE, match["match_id"], seat["section"], seat["row"], seat["seat"]
    )


def check_ticket_line(match):
    """The code and the line on Live have to describe the same seat."""
    seat = match["live_seated"]
    expected = (f"Sec {seat['section']} {DOT} Row {seat['row']} "
                f"{DOT} Seat {seat['seat']}")
    if seat["ticket"] != expected:
        raise SystemExit(
            f"match {match['match_id']}: the ticket line {seat['ticket']!r} does not "
            f"match its seat fields, which read {expected!r}. Fix matches.json before "
            "generating a code that claims a different seat."
        )


def decode(path):
    """Read the payload back off the written PNG, or None if nothing decodes."""
    try:
        import zxingcpp
        from PIL import Image
    except ModuleNotFoundError as exc:
        raise SystemExit(
            f"cannot verify the codes: {exc.name} is missing. Install the dev "
            "dependencies with `uv sync --dev`. Tickets are not written without "
            "a decode check."
        ) from exc

    with Image.open(path) as img:
        result = zxingcpp.read_barcode(img.convert("L"))
    return result.text if result else None


def main():
    doc = json.loads(MATCHES.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    failures = []
    for match in doc["matches"]:
        require_seat_fields(match)
        check_ticket_line(match)
        payload = payload_for(match)
        path = OUT_DIR / f"{match['match_id']}.png"

        segno.make(payload, error=ERROR_LEVEL).save(
            path, kind="png", scale=SCALE, border=BORDER
        )

        decoded = decode(path)
        rel = path.relative_to(ROOT).as_posix()
        if decoded == payload:
            print(f"{rel}  {path.stat().st_size:,} bytes")
            print(f"  encoded {payload!r}")
            print(f"  decoded {decoded!r}  exact match")
        else:
            failures.append(rel)
            print(f"{rel}  DOES NOT ROUND TRIP")
            print(f"  encoded {payload!r}")
            print(f"  decoded {decoded!r}")

    print(f"\n{len(doc['matches'])} ticket(s) written to "
          f"{OUT_DIR.relative_to(ROOT).as_posix()}, {len(failures)} failed to decode")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
