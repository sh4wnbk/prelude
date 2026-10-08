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


def check_design_citations(fail):
    """DESIGN.md cites `NN:MMM`. The line must exist and must not be blank."""
    doc = (ROOT / "docs" / "DESIGN.md").read_text(encoding="utf-8")
    cites = sorted(set(re.findall(r"`(0[1-4]):(\d+)`", doc)))
    if not cites:
        fail("DESIGN.md", "no citations found at all; has the format changed?")
        return
    for key, number in cites:
        lines = SCREENS[key].read_text(encoding="utf-8").splitlines()
        n = int(number)
        name = SCREENS[key].name
        if n > len(lines):
            fail("DESIGN.md", f"cites {key}:{n} but {name} has {len(lines)} lines")
        elif not lines[n - 1].strip():
            fail("DESIGN.md", f"cites {key}:{n} but that line in {name} is blank")
    print(f"  DESIGN.md: {len(cites)} citations checked")


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
        check_quoted_failure,
        check_test_count,
        check_referenced_paths,
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
