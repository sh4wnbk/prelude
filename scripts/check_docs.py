r"""Check that the docs still describe the code they quote.

Every doc in this repo points at code: `docs/DESIGN.md` cites file and line,
`docs/bob_brief.md` quotes live test output and a test count, `README.md` lists
what runs. All of that is correct when written and goes stale silently the next
time the code moves. Nothing re-validates it, which is how a citation survived a
file shrinking by twenty lines and how the brief kept quoting a failure message
that had been rewritten.

This checks the quotable claims. It does not check prose. Exit code is 1 if
anything has drifted, so it can gate a commit. Run:

    .\.venv-prelude\Scripts\python.exe -I scripts\check_docs.py
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SCREENS = {
    "01": ROOT / "app" / "web" / "prelude_01_picker.html",
    "02": ROOT / "app" / "web" / "prelude_02_live_seated.html",
    "03": ROOT / "app" / "web" / "prelude_03_moment_card.html",
    "04": ROOT / "app" / "web" / "prelude_04_moments.html",
}

DOCS = [
    ROOT / "README.md",
    ROOT / "HANDOFF.md",
    ROOT / "CLAUDE.md",
    ROOT / "docs" / "DESIGN.md",
    ROOT / "docs" / "bob_brief.md",
    ROOT / "docs" / "data_check.md",
    ROOT / "bob_sessions" / "README.md",
]

# Paths the docs name on purpose while they do not exist. Each one is described
# in the docs as not yet built, so an absent file is the correct state.
DELIBERATELY_ABSENT = {"app/statsbomb_event_feed.py"}

PATH_IN_BACKTICKS = re.compile(
    r"`((?:app|docs|scripts|tests|bob_sessions)/[A-Za-z0-9_./-]+)`"
)


def run_pytest(*args):
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return result.stdout + result.stderr


CODE_SPAN = re.compile(r"`([^`\n]+)`")
CITE = re.compile(r"`(0[1-4]):(\d+)`")
SHIFT_RANGE = range(-6, 7)


def check_design_citations(fail):
    """DESIGN.md cites `NN:MMM`. Check the line exists, and that the set of
    citations has not drifted as a block.

    Range alone is too weak: inserting one line near the top of a screen shifts
    every citation below it, and each one still points at a real, non-blank
    line, so a range check stays green while the whole file is wrong. That
    happened once, when the phone-frame stylesheet link was added.

    Matching each citation individually against nearby markup is too noisy the
    other way: anchors go through HTML entity escaping, describe a container on
    a neighbouring line, or name a utility by how it is used rather than where
    it is declared. All three produce false alarms.

    So this scores the citations per screen. Each citation that sits beside a
    backticked code span found in that screen votes for the offset at which its
    anchor lands. If some non-zero offset explains more citations than zero
    does, the citations for that screen have drifted together, which is the
    failure worth reporting.
    """
    doc = (ROOT / "docs" / "DESIGN.md").read_text(encoding="utf-8")
    lines_by = {k: v.read_text(encoding="utf-8").splitlines() for k, v in SCREENS.items()}

    votes = {k: [] for k in SCREENS}
    total = 0
    for block in re.split(r"\n\s*\n|\n(?=[-*|] )", doc):
        cites = CITE.findall(block)
        if not cites:
            continue
        anchors = [s for s in CODE_SPAN.findall(block)
                   if len(s) >= 10 and not re.fullmatch(r"0[1-4]:\d+", s)]
        for key, number in cites:
            total += 1
            n = int(number)
            lines = lines_by[key]
            if n > len(lines):
                fail("DESIGN.md", f"cites {key}:{n} but {SCREENS[key].name} has {len(lines)} lines")
                continue
            if not lines[n - 1].strip():
                fail("DESIGN.md", f"cites {key}:{n} but that line is blank")
                continue
            usable = [a for a in anchors if any(a in l for l in lines)]
            if usable:
                votes[key].append((n, usable))

    anchored = 0
    for key, cites in votes.items():
        if not cites:
            continue
        lines = lines_by[key]

        def score(offset):
            hit = 0
            for n, anchors in cites:
                i = n - 1 + offset
                if 0 <= i < len(lines) and any(a in lines[i] for a in anchors):
                    hit += 1
            return hit

        at_zero = score(0)
        anchored += at_zero
        best = max(SHIFT_RANGE, key=lambda o: (score(o), -abs(o)))
        if best != 0 and score(best) > at_zero:
            fail(
                "DESIGN.md",
                f"citations for screen {key} look shifted by {best:+d}: "
                f"{score(best)} of {len(cites)} anchors land at that offset, "
                f"only {at_zero} land where cited",
            )
    print(f"  DESIGN.md: {total} citations, {anchored} anchored to their line")

def check_quoted_failure(fail):
    """bob_brief.md quotes the message the suite actually prints."""
    brief = (ROOT / "docs" / "bob_brief.md").read_text(encoding="utf-8")
    block = re.search(
        r"fail with the same message:\s*```\s*(.*?)\s*```", brief, re.S
    )
    if block is None:
        fail("bob_brief.md", "could not find the quoted failure message block")
        return
    quoted = " ".join(block.group(1).split())
    live = " ".join(run_pytest("-q").split())
    if quoted not in live:
        fail(
            "bob_brief.md",
            "the quoted failure message no longer matches pytest output.\n"
            f"      quoted: {quoted}",
        )
    else:
        print("  bob_brief.md: quoted failure message matches live output")


def check_test_count(fail):
    """Counts like "14 tests" and "all 14 fail" must match what pytest collects."""
    collected = len(
        [l for l in run_pytest("--collect-only", "-q").splitlines() if "::" in l]
    )
    if not collected:
        fail("tests", "pytest collected no tests")
        return
    for doc in (ROOT / "docs" / "bob_brief.md", ROOT / "HANDOFF.md", ROOT / "README.md"):
        text = doc.read_text(encoding="utf-8")
        claimed = {
            int(n)
            for n in re.findall(r"(\d+)\s+(?:acceptance\s+)?tests?\b", text)
            + re.findall(r"all\s+(\d+)\s+fail", text)
        }
        for n in claimed:
            if n != collected:
                fail(doc.name, f"claims {n} tests, pytest collects {collected}")
    print(f"  test count: {collected} collected, matches the docs")


def check_referenced_paths(fail):
    """A path named in backticks exists, or is on the deliberately absent list."""
    checked = 0
    for doc in DOCS:
        for match in sorted(set(PATH_IN_BACKTICKS.findall(doc.read_text(encoding="utf-8")))):
            if match.startswith("data/raw"):
                continue  # gitignored and rebuilt by fetch_statsbomb.py
            checked += 1
            if match in DELIBERATELY_ABSENT:
                if (ROOT / match).exists():
                    fail(doc.name, f"{match} now exists but is listed as absent")
            elif not (ROOT / match).exists():
                fail(doc.name, f"references {match}, which does not exist")
    print(f"  paths: {checked} references checked")


QUOTED_SCREEN_COPY = re.compile(
    r"\"([^\"]{10,})\"\s*\(((?:`(?:0[1-4]:\d+|removed)`(?:,\s*)?)+)\)"
)
CITATION = re.compile(r"`(0[1-4]):(\d+)`|`(removed)`")



# Two structural landmarks that every screen has exactly once, and that DESIGN.md
# cites for all four. They are the citations that move when anything is inserted
# above them, so checking them by content is a deterministic tripwire for drift,
# with none of the noise of matching arbitrary prose anchors to arbitrary lines.
LANDMARKS = [
    ("- **Header**:", "fixed top-0 w-full z-50 pt-safe"),
    ("- **Bottom nav**:", "fixed bottom-0 w-full z-50 pb-safe"),
]


def check_design_landmarks(fail):
    """The header and nav citations in DESIGN.md must land on those elements."""
    doc = (ROOT / "docs" / "DESIGN.md").read_text(encoding="utf-8")
    lines_by = {k: v.read_text(encoding="utf-8").splitlines() for k, v in SCREENS.items()}

    checked = 0
    for bullet, needle in LANDMARKS:
        start = doc.find(bullet)
        if start < 0:
            fail("DESIGN.md", f"could not find the {bullet!r} bullet; has the format changed?")
            continue
        block = doc[start:doc.find("\n- ", start + 1)]
        cites = CITE.findall(block)
        if len(cites) != len(SCREENS):
            fail("DESIGN.md", f"{bullet!r} cites {len(cites)} screens, expected {len(SCREENS)}")
        for key, number in cites:
            checked += 1
            n, lines = int(number), lines_by[key]
            if not (1 <= n <= len(lines)) or needle not in lines[n - 1]:
                got = lines[n - 1][:60] if 1 <= n <= len(lines) else "<out of range>"
                fail("DESIGN.md", f"{bullet} cites {key}:{n}, but {needle!r} is not there: {got!r}")
    print(f"  DESIGN.md: {checked} structural landmarks verified")

def check_quoted_screen_copy(fail):
    """HANDOFF quotes screen copy and cites where it lives.

    A quote followed by `NN:MMM` must appear on that line of that screen. A
    quote followed by `removed` must appear on no screen at all, which keeps
    "we took this out" claims honest. Quotes with no citation are prose and are
    not checked, so commit messages and rule text can be quoted freely.
    """
    doc = (ROOT / "HANDOFF.md").read_text(encoding="utf-8")
    flat = " ".join(doc.split())
    screens = {k: " ".join(v.read_text(encoding="utf-8").split()) for k, v in SCREENS.items()}
    lines = {k: v.read_text(encoding="utf-8").splitlines() for k, v in SCREENS.items()}

    found = 0
    for quote, cites in QUOTED_SCREEN_COPY.findall(flat):
        wanted = " ".join(quote.split())
        for key, number, removed in CITATION.findall(cites):
            found += 1
            if removed:
                hit = [k for k, text in screens.items() if wanted in text]
                if hit:
                    fail("HANDOFF.md", f"{wanted[:50]!r} is marked removed but is still on {', '.join(hit)}")
            else:
                n = int(number)
                if n > len(lines[key]):
                    fail("HANDOFF.md", f"cites {key}:{n} but that screen has {len(lines[key])} lines")
                elif wanted not in " ".join(lines[key][n - 1].split()):
                    fail("HANDOFF.md", f"{wanted[:50]!r} is not on {key}:{n}")
    if not found:
        fail("HANDOFF.md", "no cited screen copy found; has the convention changed?")
    print(f"  HANDOFF.md: {found} cited screen quotes checked")


def check_no_em_dashes(fail):
    """CLAUDE.md bans em dashes in docs. Scripts are exempt; they may hold one
    as a search pattern."""
    for doc in DOCS:
        text = doc.read_text(encoding="utf-8")
        for char, label in (("—", "em dash"), ("–", "en dash")):
            if char in text:
                fail(doc.name, f"contains {text.count(char)} {label}(s)")
    print(f"  dashes: {len(DOCS)} docs checked")


def main():
    failures = []

    def fail(where, message):
        failures.append(f"  {where}: {message}")

    print("checking docs against the code they describe")
    for check in (
        check_design_citations,
        check_design_landmarks,
        check_quoted_failure,
        check_test_count,
        check_referenced_paths,
        check_quoted_screen_copy,
        check_no_em_dashes,
    ):
        check(fail)

    if failures:
        print(f"\n{len(failures)} stale claim(s):")
        print("\n".join(failures))
        return 1
    print("\nall doc claims match the code")
    return 0


if __name__ == "__main__":
    sys.exit(main())
