"""Scan the web screens for banned copy and report every hit with file and line.

Exit code is 1 if anything is found, so this can gate a commit. Run:

    .\\.venv-prelude\\Scripts\\python.exe -I scripts\\scan_copy.py
"""

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# The screens, plus matches.json, which holds display copy, plus the scripts,
# since manual-entry.js builds its own markup and copy is screen copy wherever
# it happens to be written.
SCREENS = (sorted((ROOT / "app" / "web").glob("*.html"))
           + sorted((ROOT / "app" / "web").glob("*.json"))
           + sorted((ROOT / "app" / "web").glob("*.js")))

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
    # Four lines that claimed more than the code does, removed in Task 32.
    # Each is here so it cannot come back, and each pattern is the copy as it
    # stood. Five patterns for four lines: the confirm button said two things
    # in sequence. The space around a separator is matched rather than written
    # out, so a hit does not depend on how the copy is spaced.
    ("GPS the app does not read", r"AT VENUE\s*·\s*GPS"),
    ("live audio that does not exist", r"LIVE AUDIO SYNC"),
    ("a connection and a readiness neither of which is checked",
     r"Play data connected\s*·\s*AI narration ready"),
    ("a synchronisation that does not happen", r"Synchronizing Play Data"),
    ("a venue feed that does not exist", r"Connected to Venue Feed"),
]

COMPILED = [(label, re.compile(pattern, re.IGNORECASE)) for label, pattern in BANNED]


# --- The grounding label -----------------------------------------------------
#
# CLAUDE.md allows "Verified from play data" only over narration whose claims
# trace back to the event data. That is a placement rule, not a banned string,
# so the regex sweep above cannot see a violation: the words are correct, the
# position is not. This check reads the markup as a tree and asks what the label
# is actually sitting over.
#
# The label was once on the Live standby pipeline card, where it sat above rows
# reporting whether the step-away trigger and the narration were switched on.
# Those rows are app state, not a claim read from the feed, so the label was
# making a grounding promise about something the data never said.

GROUNDING_LABEL = "Verified from play data"

# Elements that hold narration. A label is grounded when it shares a card with
# one of these. If Phase 5 adds another narration field, add it here too, or a
# correct placement will be reported as a violation.
NARRATION_FIELDS = {"hero_quote", "hero_narration"}

# Walking out of the card and into the page shell would let any label anywhere
# on a screen count as grounded, so the walk stops at these.
SHELL_TAGS = {"#root", "html", "body", "main"}

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "param", "source", "track", "wbr"}


class Markup(HTMLParser):
    """A parent-linked tree, enough to ask what encloses what."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = {"tag": "#root", "attrs": {}, "children": [], "parent": None,
                     "text": "", "line": 0}
        self.stack = [self.root]

    def _node(self, tag, attrs):
        node = {"tag": tag, "attrs": dict(attrs), "children": [],
                "parent": self.stack[-1], "text": "", "line": self.getpos()[0]}
        self.stack[-1]["children"].append(node)
        return node

    def handle_starttag(self, tag, attrs):
        node = self._node(tag, attrs)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self._node(tag, attrs)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1]["text"] += data


def walk(node):
    yield node
    for child in node["children"]:
        yield from walk(child)


def squeeze(s):
    return " ".join(s.split())


def holds_narration(node):
    return any(n["attrs"].get("data-field") in NARRATION_FIELDS for n in walk(node))


def grounded(label):
    """True when the label shares a card with a narration element."""
    parent = label["parent"]
    while parent is not None and parent["tag"] not in SHELL_TAGS:
        if holds_narration(parent):
            return True
        parent = parent["parent"]
    return False


def check_grounding(path, rel):
    """Report every grounding label that is not sitting over narration."""
    if path.suffix != ".html":
        # A .json copy file carries no markup, so nothing there can establish
        # that the label sits over narration. The label belongs in the screens.
        if GROUNDING_LABEL in path.read_text(encoding="utf-8"):
            print(f"{rel}  [ungrounded label] {GROUNDING_LABEL!r}")
            print("    ...copy data cannot place the label over narration...")
            return 1
        return 0

    tree = Markup()
    tree.feed(path.read_text(encoding="utf-8"))
    hits = 0
    for node in walk(tree.root):
        if GROUNDING_LABEL not in squeeze(node["text"]):
            continue
        if grounded(node):
            continue
        hits += 1
        # What the label is actually sitting over: the nearest enclosing card
        # that says something other than the label itself.
        near = "(nothing but the label)"
        enclosing = node["parent"]
        while enclosing is not None and enclosing["tag"] not in SHELL_TAGS:
            alongside = squeeze(" ".join(
                n["text"] for n in walk(enclosing)
                # Material Symbol spans hold an icon ligature, not copy.
                if "material-symbols" not in n["attrs"].get("class", "")))
            alongside = squeeze(alongside.replace(GROUNDING_LABEL, " "))
            if alongside:
                near = alongside[:70]
                break
            enclosing = enclosing["parent"]
        print(f"{rel}:{node['line']}  [ungrounded label] {GROUNDING_LABEL!r}")
        print(f"    ...sits over {near!r}, not over narration "
              f"({', '.join(sorted(NARRATION_FIELDS))})...")
    return hits


def main():
    if not SCREENS:
        raise SystemExit(f"no screens found under {ROOT / 'app' / 'web'}")

    hits = 0
    grounding_hits = 0
    for path in SCREENS:
        rel = path.relative_to(ROOT).as_posix()
        grounding_hits += check_grounding(path, rel)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for label, pattern in COMPILED:
                for match in pattern.finditer(line):
                    hits += 1
                    start = max(0, match.start() - 50)
                    end = min(len(line), match.end() + 50)
                    print(f"{rel}:{lineno}  [{label}] {match.group(0)!r}")
                    print(f"    ...{line[start:end].strip()}...")

    total = hits + grounding_hits
    print(f"\nscanned {len(SCREENS)} screens, {hits} banned-copy hit(s), "
          f"{grounding_hits} ungrounded label(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
