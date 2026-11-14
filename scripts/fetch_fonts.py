r"""Download the screens' fonts and write `app/web/fonts.css` beside them.

The screens loaded four stylesheets from `fonts.googleapis.com` and their
font files from `fonts.gstatic.com`. Two things were wrong with that. The
site is a demo a judge opens once, so a slow or blocked Google is a demo that
renders in Times New Roman; and `tests/browser/` could not hold the screens
to loading nothing from outside, because they did, which is the allowance
Task 30 recorded under "Found, not fixed".

So the files are in the repo. This script is what puts them there, and it is
the only thing that reaches Google: it asks for exactly the two stylesheets
the screens used to ask for, downloads every `.woff2` they name, and writes
`app/web/fonts.css` as those stylesheets with the `src` URLs pointing at
`app/web/assets/fonts/` instead.

**Every subset is kept, not only latin.** Google answers with one `@font-face`
per weight per subset, each with its own `unicode-range`, and a browser
downloads only the subsets the text on the page needs. Dropping the others
would be smaller and would change what a fan sees: the name a fan types goes
into the header, and a name outside latin and latin-ext would fall back to a
system font. Keeping all of them is what makes "no screen looks different"
true rather than nearly true.

**Nothing but the `src` lines is rewritten.** The subset comments, the weights,
the `font-display` and every `unicode-range` come through as Google wrote
them, so the stylesheet a browser applies is the one it applied before.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\fetch_fonts.py --plan
    .\.venv-prelude\Scripts\python.exe -I scripts\fetch_fonts.py --confirm

`--plan` asks Google for the two stylesheets, prints what it would download
and writes nothing. `--confirm` downloads and writes. Standard library only.
"""

import argparse
import hashlib
import re
import sys
import urllib.request
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
FONT_DIR = WEB / "assets" / "fonts"
FONTS_CSS = WEB / "fonts.css"

#: The two stylesheet requests the screens carried, unchanged. The first is
#: the three text families with the weights `docs/DESIGN.md` records; the
#: second is the icon font with the two axes the screens set inline.
#:
#: **Six of the seven screens asked for a third**, a static instance of the
#: icon font at `opsz,wght,FILL,GRAD@24,400,0,0`, immediately before the
#: variable one. It is not here, and that is not a change to what a fan sees.
#: Two `@font-face` rules naming one family are resolved by the later one, the
#: variable rule covers `font-weight: 100 700` so it matches wherever the
#: static rule did, and the `.material-symbols-outlined` rule the two
#: responses carry is byte-identical. So the static file was downloaded by
#: nobody and overridden everywhere, and leaving it out keeps 1.1 MB of
#: unreachable font out of the repo. The moment card never carried it, which
#: is why `docs/DESIGN.md` records the variable axes and cites that screen.
REQUESTS = (
    (
        "the three text families",
        "https://fonts.googleapis.com/css2"
        "?family=Hanken+Grotesk:wght@400;500;600;700"
        "&family=JetBrains+Mono:wght@400;500;600"
        "&family=Syne:wght@600;700"
        "&display=swap",
    ),
    (
        "the icon font",
        "https://fonts.googleapis.com/css2"
        "?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1"
        "&display=swap",
    ),
)

#: Google serves `woff2` only to a client that says it can read it, and a
#: plain urllib request is answered with `ttf`. This is a browser's own
#: string and carries nothing about this machine or this project.
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

#: The first four bytes of a woff2 file. A stylesheet or an error page
#: arriving where a font was asked for would otherwise be committed as one.
WOFF2_MAGIC = b"wOF2"

SRC = re.compile(r"url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)")
FAMILY = re.compile(r"font-family:\s*'([^']+)'")

HEADER = """/* The screens' fonts, served from this repo rather than from Google.
 *
 * Written by scripts/fetch_fonts.py, which is the only thing that reaches
 * fonts.googleapis.com. Do not edit by hand: every line but the src URLs is
 * Google's own answer to the two requests the screens used to make, and the
 * point of the file is that a browser applies exactly what it applied before.
 *
 * Run it again with --confirm to refresh; the font files are in
 * app/web/assets/fonts/.
 */
"""


def ask(url: str) -> str:
    """One stylesheet, as a browser would be given it."""
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=60) as answer:
        if answer.status != 200:
            raise SystemExit("{} answered {}".format(url, answer.status))
        return answer.read().decode("utf-8")


def slug(css: str, url: str, at: int) -> str:
    """A readable, deterministic filename for one `@font-face`'s font file.

    The family comes out of the block the URL sits in and the subset out of
    the comment above it, with eight hex digits of the URL to keep two blocks
    that agree on both apart. The weight is deliberately not in the name: all
    four of these are variable fonts, so Google answers every requested weight
    of one subset with the same file, and 41 `@font-face` blocks name 14
    files. A weight in the name would read as a promise the file does not
    make.
    """
    block_start = css.rfind("@font-face", 0, at)
    block = css[block_start:at]
    family = FAMILY.search(block)
    comment = re.findall(r"/\*\s*([^*]+?)\s*\*/", css[:block_start])
    parts = [
        re.sub(r"[^a-z0-9]+", "-", (family.group(1) if family else "font").lower()),
        re.sub(r"[^a-z0-9]+", "-", comment[-1].lower()) if comment else "all",
        hashlib.sha256(url.encode("utf-8")).hexdigest()[:8],
    ]
    return "-".join(parts) + ".woff2"


def plan(stylesheets: Sequence[tuple]) -> list:
    """Every font file the two stylesheets name, with the name it will take."""
    wanted = []
    seen = set()
    for label, url, css in stylesheets:
        for match in SRC.finditer(css):
            remote = match.group(1)
            if remote in seen:
                continue
            seen.add(remote)
            wanted.append((label, remote, slug(css, remote, match.start())))
    return wanted


def rewrite(css: str, names: dict) -> str:
    """The stylesheet with its `src` URLs pointing at the committed files."""

    def local(match):
        return 'url("assets/fonts/{}")'.format(names[match.group(1)])

    return SRC.sub(local, css)


def download(remote: str, into: Path) -> int:
    request = urllib.request.Request(remote, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=60) as answer:
        body = answer.read()
    if not body.startswith(WOFF2_MAGIC):
        raise SystemExit(
            "{} did not answer with a woff2 file (first bytes {!r}); nothing "
            "was written".format(remote, body[:8])
        )
    into.write_bytes(body)
    return len(body)


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--plan",
        action="store_true",
        help="print what would be downloaded and write nothing",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="download the font files and write app/web/fonts.css",
    )
    args = parser.parse_args(argv)

    stylesheets = []
    for label, url in REQUESTS:
        css = ask(url)
        print("asked    {} ({} chars, {} @font-face)".format(
            label, len(css), css.count("@font-face")
        ))
        stylesheets.append((label, url, css))

    wanted = plan(stylesheets)
    print("files    {} woff2 to download".format(len(wanted)))
    print()
    if args.plan or not args.confirm:
        for label, remote, name in wanted:
            print("  {}  <-  {}".format(name, remote.rsplit("/", 1)[-1]))
        print()
        print("nothing was written. --confirm is what writes it.")
        return 0

    FONT_DIR.mkdir(parents=True, exist_ok=True)
    names = {}
    total = 0
    for label, remote, name in wanted:
        size = download(remote, FONT_DIR / name)
        names[remote] = name
        total += size
        print("  {:>7,} bytes  {}".format(size, name))

    pieces = [HEADER]
    for label, url, css in stylesheets:
        pieces.append("\n/* {}: {} */\n".format(label, url))
        pieces.append(rewrite(css, names).strip() + "\n")
    FONTS_CSS.write_text("".join(pieces), encoding="utf-8", newline="\n")

    print()
    print("wrote {} ({:,} bytes of fonts in {})".format(
        FONTS_CSS.relative_to(ROOT), total, FONT_DIR.relative_to(ROOT)
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
