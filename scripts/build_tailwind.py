r"""Compile the screens' shared Tailwind config into `app/web/tailwind.css`.

The screens used to load `https://cdn.tailwindcss.com`, which is 407 KB of
JavaScript that reads the DOM, reads the `tailwind-config` block beside it and
writes a stylesheet at run time. Three things were wrong with that. A blocked
or slow CDN is a demo with no styling at all; the browser suite could not hold
the screens to loading nothing from outside, which is the allowance Task 30
recorded under "Found, not fixed"; and the Play CDN re-runs on every DOM
change, so the Moments screen, which `match-content.js` rebuilds, repainted
after its own list was built.

So the stylesheet is compiled once and committed. This script is what compiles
it.

**The config is still the block in the screens.** `HANDOFF.md` records that
the `<script id="tailwind-config">` block is one block, byte-identical across
every screen, and that the design system rests on it; `docs/DESIGN.md` cites
it for every token and `scripts/check_docs.py` holds those citations to the
screens. None of that changes. This script reads the block out of the screens,
refuses to run if the copies disagree, and hands it to the Tailwind CLI.

**The block no longer executes.** It carries `type="text/tailwind-config"`, so
a browser parses it and does not run it: with no Tailwind on the page,
`tailwind.config = {...}` would throw a `ReferenceError` and the browser suite
counts a console error against the screen. The bytes inside the tag are
unchanged.

**The version is pinned to the one the CDN was serving**, 3.4.17, read out of
the bundle it used to load. A different minor would be a different stylesheet
for the same config.

Needs `npx`, which comes with Node. Nothing else in this repo does, and CI
does not run this: `app/web/tailwind.css` is committed, and the step in
`.github/workflows/ci.yml` that fails on a dirty tree is what catches a
stylesheet that no longer matches the config it was built from.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\build_tailwind.py --plan
    .\.venv-prelude\Scripts\python.exe -I scripts\build_tailwind.py --confirm

Standard library only.
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
OUT = WEB / "tailwind.css"

#: The Tailwind the Play CDN bundled, read out of the bundle the screens used
#: to load, and the two plugins five of them asked it for. All three are
#: pinned: the same config compiled by a different minor is a different
#: stylesheet.
VERSION = "3.4.17"
PLUGINS = (
    ("@tailwindcss/forms", "0.5.9"),
    ("@tailwindcss/container-queries", "0.1.1"),
)

#: The plugins are in, and that is a decision rather than a copy. Five
#: screens loaded `cdn.tailwindcss.com?plugins=forms,container-queries` and
#: two, the event list and the moment card, loaded the CDN bare, so the app
#: was running two stylesheets. One compiled file cannot keep both, and the
#: forms plugin is load-bearing: `docs/DESIGN.md` records that the match
#: select "takes the forms plugin's own chevron rather than a drawn one", and
#: that select is built by `app/web/manual-entry.js` and mounted on the event
#: list, which is one of the two screens that was not loading the plugin. So
#: the documented design is the one with the plugins and the event list is
#: what was wrong. The container queries plugin adds variants and no base
#: rules, and no screen uses an `@container` class, so it changes nothing; it
#: is kept because five screens asked for it.
#:
#: Where the compiler looks for class names. The screens and the scripts
#: beside them, because `match-content.js`, `listener-card.js` and
#: `manual-entry.js` build markup and the picker's own script holds the
#: selected and unselected card styles as literals. The data files are not
#: scanned: nothing in them is a class.
CONTENT = ("*.html", "*.js")

#: The whole of the input stylesheet. The three directives, in Tailwind's own
#: order, and nothing of ours: every rule the screens add is already in their
#: own `<style>` blocks or in `app/web/phone-frame.css`.
INPUT_CSS = "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n"

BLOCK = re.compile(
    r'<script id="tailwind-config"[^>]*>(.*?)</script>', re.S
)

HEADER = """/* The screens' Tailwind stylesheet, compiled and committed.
 *
 * Written by scripts/build_tailwind.py from the <script id="tailwind-config">
 * block the screens share, with Tailwind {version} and the forms and container
 * queries plugins, which is the version and the plugin set the Play CDN was
 * serving when this replaced it. Do not edit by hand: change the block in the
 * screens and run the script again.
 *
 * The classes in it are the ones found in app/web/*.html and app/web/*.js, so
 * a class used only somewhere this does not scan will not be in here.
 */
"""


def screens() -> list:
    return sorted(WEB.glob("prelude_*.html"))


def shared_config() -> str:
    """The config block every screen carries, or a refusal naming the odd one.

    The byte-identity is the decision this reads: a screen with its own config
    is the defect Bob's Task 10 introduced once already, where one screen's
    `primary-container` was `#5c3d00` and its whole amber read as disabled.
    `tests/test_profile.py` holds the screens to it too; this refuses to
    compile from a set that disagrees, so the stylesheet is never built from
    one screen's private idea of the tokens.
    """
    found = {}
    for path in screens():
        match = BLOCK.search(path.read_text(encoding="utf-8"))
        if not match:
            raise SystemExit(
                "{} carries no tailwind-config block, so there is no shared "
                "config to compile".format(path.name)
            )
        found.setdefault(match.group(1), []).append(path.name)
    if len(found) != 1:
        groups = sorted(found.values(), key=len, reverse=True)
        raise SystemExit(
            "the screens do not share one config: {}. Nothing was "
            "compiled.".format(
                "; ".join("{} screen(s) agree ({})".format(
                    len(names), ", ".join(names)) for names in groups)
            )
        )
    return next(iter(found))


def config_module(block: str) -> str:
    """The block as a CommonJS config the Tailwind CLI can require.

    The block assigns to `tailwind.config`, which is how the Play CDN took it.
    The object literal is lifted out unchanged and `content` is added beside
    it: where to look for class names is this script's business and not a
    design token, so it is not in the block the screens carry.
    """
    marker = "tailwind.config"
    at = block.index(marker)
    literal = block[block.index("=", at) + 1:].strip().rstrip(";")
    paths = ",\n    ".join(
        '"{}"'.format((WEB / pattern).as_posix()) for pattern in CONTENT
    )
    plugins = ",\n    ".join(
        'require("{}")'.format(name) for name, _ in PLUGINS
    )
    return (
        "/* Generated by scripts/build_tailwind.py. Not committed: this is\n"
        " * written into a temporary directory for one CLI run. The config\n"
        " * itself is the <script id=\"tailwind-config\"> block in the\n"
        " * screens, lifted out unchanged; content and plugins are added\n"
        " * beside it. */\n"
        "const shared = {};\n"
        "module.exports = Object.assign({{}}, shared, {{\n"
        "  content: [\n    {},\n  ],\n"
        "  plugins: [\n    {},\n  ],\n}});\n".format(literal, paths, plugins)
    )


def compile_css(block: str) -> str:
    """Install the pinned compiler in a temporary directory and run it.

    The packages go into the temporary directory rather than the repo, which
    is why this is `npm install` and not `npx`: the config has to `require`
    the two plugins, and `require` resolves against the config's own
    directory. Nothing is left behind and the repo carries no `package.json`.
    """
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm:
        raise SystemExit(
            "npm is not on PATH, so the Tailwind CLI cannot be installed. It "
            "comes with Node; app/web/tailwind.css is committed, so nothing "
            "else in this repo needs it."
        )
    wanted = ["tailwindcss@" + VERSION] + [
        "{}@{}".format(name, version) for name, version in PLUGINS
    ]
    with tempfile.TemporaryDirectory(prefix="prelude-tailwind-") as tmp:
        work = Path(tmp)
        (work / "package.json").write_text(
            '{ "name": "prelude-tailwind-build", "private": true }\n',
            encoding="utf-8", newline="\n",
        )
        print("install  {}".format(", ".join(wanted)))
        installed = subprocess.run(
            [npm, "install", "--silent", "--no-audit", "--no-fund",
             "--no-package-lock"] + wanted,
            cwd=str(work), capture_output=True, text=True,
        )
        for line in (installed.stderr or "").splitlines():
            print("  npm  {}".format(line.rstrip()))
        if installed.returncode != 0:
            raise SystemExit(
                "npm install exited {}; nothing was written".format(
                    installed.returncode
                )
            )
        (work / "tailwind.config.js").write_text(
            config_module(block), encoding="utf-8", newline="\n"
        )
        (work / "input.css").write_text(INPUT_CSS, encoding="utf-8", newline="\n")
        cli = work / "node_modules" / ".bin" / (
            "tailwindcss.cmd" if sys.platform == "win32" else "tailwindcss"
        )
        if not cli.is_file():
            raise SystemExit(
                "the install left no Tailwind CLI at {}; nothing was "
                "written".format(cli)
            )
        done = subprocess.run(
            [
                str(cli),
                "--config", str(work / "tailwind.config.js"),
                "--input", str(work / "input.css"),
                "--output", str(work / "out.css"),
            ],
            cwd=str(work),
            capture_output=True,
            text=True,
        )
        # The CLI writes its progress to stderr and says nothing on stdout.
        for line in (done.stderr or "").splitlines():
            print("  cli  {}".format(line.rstrip()))
        if done.returncode != 0:
            raise SystemExit(
                "the Tailwind CLI exited {}; nothing was written".format(
                    done.returncode
                )
            )
        written = work / "out.css"
        if not written.is_file():
            raise SystemExit("the CLI wrote no stylesheet; nothing was written")
        return written.read_text(encoding="utf-8")


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--plan",
        action="store_true",
        help="print what would be compiled and write nothing",
    )
    parser.add_argument(
        "--confirm", action="store_true", help="compile and write the stylesheet"
    )
    args = parser.parse_args(argv)

    block = shared_config()
    print("config   the tailwind-config block, shared by {} screen(s), "
          "{} chars".format(len(screens()), len(block)))
    print("version  tailwindcss@{}, with {}".format(
        VERSION,
        ", ".join("{}@{}".format(name, v) for name, v in PLUGINS),
    ))
    print("content  {}".format(", ".join(
        (WEB / pattern).relative_to(ROOT).as_posix() for pattern in CONTENT
    )))
    print("output   {}".format(OUT.relative_to(ROOT).as_posix()))
    print()
    if args.plan or not args.confirm:
        print("nothing was written. --confirm is what writes it.")
        return 0

    css = compile_css(block)
    OUT.write_text(
        HEADER.format(version=VERSION) + "\n" + css.lstrip("\n"),
        encoding="utf-8",
        newline="\n",
    )
    print()
    print("wrote {} ({:,} bytes, {} rule(s))".format(
        OUT.relative_to(ROOT).as_posix(), OUT.stat().st_size, css.count("{")
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
