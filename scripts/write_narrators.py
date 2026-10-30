"""Write or check app/web/narrators.json from the personas in app/personas.py.

Writes {"narrators": [{"id", "name", "profile"} for each persona in PERSONAS]},
in PERSONAS order, with json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
as UTF-8.

Usage:
    python scripts/write_narrators.py              # write narrators.json
    python scripts/write_narrators.py --check      # exit 1 if missing or differs, 0 if matches
    python scripts/write_narrators.py --path PATH  # use a different output file
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.personas import PERSONAS

_DEFAULT_PATH = ROOT / "app" / "web" / "narrators.json"


def _build_doc() -> dict:
    return {
        "narrators": [
            {"id": p.id, "name": p.name, "profile": p.profile}
            for p in PERSONAS
        ]
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if the file is missing or differs; exit 0 if it matches.",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=_DEFAULT_PATH,
        help="Path to narrators.json (default: app/web/narrators.json).",
    )
    args = parser.parse_args()

    path: Path = args.path
    doc = _build_doc()
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not path.exists():
            sys.exit(1)
        sys.exit(0 if path.read_text(encoding="utf-8") == text else 1)

    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
