r"""Check that the docs still describe the code they quote.

Every doc in this repo points at code: `docs/DESIGN.md` cites a screen and a
class string in it, `docs/bob_brief.md` quotes live test output and a test
count, `README.md` lists what runs, and `docs/HARNESS.md`,
`docs/VERIFICATION.md`, `docs/GOVERNANCE.md` and `docs/IBM_STACK.md` put a file
and a test beside nearly every statement they make. All of that is correct when
written and goes stale silently the next time the code moves. Nothing
re-validates it, which is how a citation survived a file shrinking by twenty
lines and how the brief kept quoting a failure message that had been rewritten.

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

# Markup is not only in the screens any more. manual-entry.js builds the manual
# ticket form, so a component documented from it cites `js` the way a component
# in a screen cites `01`.
SHARED_MARKUP = {"js": ROOT / "app" / "web" / "manual-entry.js"}

SOURCES = dict(SCREENS, **SHARED_MARKUP)

DOCS = [
    ROOT / "README.md",
    ROOT / "HANDOFF.md",
    ROOT / "CLAUDE.md",
    # The six long sections `README.md` used to carry inline. Task 37 moved
    # them out so the README could be a page a judge skims; they are checked
    # exactly as they were while they were in it.
    ROOT / "docs" / "CAPABILITIES.md",
    ROOT / "docs" / "THE_LABEL.md",
    ROOT / "docs" / "HOSTED_API.md",
    ROOT / "docs" / "DOCUMENTS.md",
    ROOT / "docs" / "CREDENTIALS.md",
    ROOT / "docs" / "DATA.md",
    ROOT / "docs" / "DESIGN.md",
    ROOT / "docs" / "GOVERNANCE.md",
    ROOT / "docs" / "HARNESS.md",
    ROOT / "docs" / "IBM_STACK.md",
    ROOT / "docs" / "VERIFICATION.md",
    ROOT / "docs" / "bob_brief.md",
    ROOT / "docs" / "data_check.md",
    ROOT / "docs" / "narration.md",
    ROOT / "docs" / "narration_eval.md",
    ROOT / "docs" / "VOICE.md",
    ROOT / "docs" / "orchestrate_agent.md",
    ROOT / "bob_sessions" / "README.md",
    ROOT / "scripts" / "brand" / "README.md",
]

# The archived task records, which `HANDOFF.md` used to hold inline. They are
# globbed rather than listed, so folding a record into `docs/history/` at the
# end of a task needs no edit here and cannot quietly escape the checks.
#
# They get every check the text got while it was in `HANDOFF.md`: the paths it
# names still have to exist, the tests it cites still have to be collected, the
# counts it claims are still read against the suite, and it still may hold no
# em dash. A record is evidence, so a record pointing at something that no
# longer exists is the same defect it was before the move.
HISTORY = sorted((ROOT / "docs" / "history").glob("*.md"))

DOCS += HISTORY

# Paths the docs name on purpose while they do not exist. Each one is described
# in the docs as not yet built, so an absent file is the correct state. The
# check runs in both directions: when one of them is built, this line fails
# until the plan entry is rewritten as built work, which is what stops a plan
# quietly outliving the thing it planned.
#
# `docs/narration_eval.md` came off this list when Task 4a built it,
# `app/orchestrator_contract.py` and `tests/test_orchestrator.py` when Task 5
# wrote them, and `app/orchestrator.py` when Bob built it in Task 4. Add a path
# here when a doc names one before it is written.
#
# `bob_sessions/phase4_task5_header.md` came off it when Bob's Task 5 session
# was run and the export was committed.
#
# `scripts/write_headers.py` came off it when Bob built Task 6, and that
# session's export when it was committed in `95341d1`, and Task 7's export when
# it was committed in `76e0d15`, and Task 8's after it, and Task 11's export
# when it was committed in `076e914`, and Task 13's export when it was
# committed in `473b98e`, and Task 14's export when it was committed in
# `9f98e91`.
#
# Task 15's export went back on it when the brief was written, and came off on
# 2026-11-07 when the session was run and the export committed.
#
# It holds the other direction too, which Task 33 was the first to need: a
# path a task record names because the file existed when that record was
# written, and a later task removed. A record is not edited as the code moves
# on, so the record goes on saying `scripts/make_mark.py` and this says the
# file is gone on purpose. The check still runs both ways: writing that script
# again fails here until this line goes.
DELIBERATELY_ABSENT: set[str] = {"scripts/make_mark.py"}

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


# A code span may wrap across lines in the prose, so newlines are allowed inside
# one and squeezed out before matching.
CODE_SPAN = re.compile(r"`([^`]+)`")
SCREEN_CITE = re.compile(r"`(0[1-4]|js)`")

# Anchors shorter than this match too much to prove anything.
MIN_ANCHOR = 10


def squeeze(s):
    """Drop all whitespace, so a class string wrapped across lines in the prose
    still matches the markup, and `foo: bar` here matches minified `foo:bar`."""
    return "".join(s.split())


def block_anchors(block):
    """The backticked strings in a block that could identify an element.

    A span containing an ellipsis is an explicit elision, never a verbatim
    quote, so it is not an anchor.
    """
    return [s for s in CODE_SPAN.findall(block)
            if len(squeeze(s)) >= MIN_ANCHOR
            and "..." not in s
            and not re.fullmatch(r"0[1-4]|js", s.strip())]


def design_blocks(doc):
    """A paragraph, bullet or table row: citation and anchor sit together."""
    return re.split(r"\n\s*\n|\n(?=[-*|] )", doc)


def check_design_citations(fail):
    """DESIGN.md cites a screen, and the class string beside it must be in it.

    This used to cite file and line. A line number is correct when written and
    wrong after the next markup change, which happened three times, and once a
    repair pointed a citation at the wrong element without anything noticing. A
    class string travels with the element it names, so the only way to break
    this is to change the markup the doc describes, which is exactly when the
    doc should be updated.
    """
    doc = (ROOT / "docs" / "DESIGN.md").read_text(encoding="utf-8")
    text = {k: squeeze(v.read_text(encoding="utf-8")) for k, v in SOURCES.items()}

    anchored = unanchored = 0
    for block in design_blocks(doc):
        cites = sorted(set(SCREEN_CITE.findall(block)))
        if not cites:
            continue
        anchors = block_anchors(block)
        if not anchors:
            unanchored += len(cites)
            continue
        # Every anchor must be in at least one screen the block cites. Without
        # this a renamed class slips through whenever a sibling anchor in the
        # same block still matches.
        for a in anchors:
            if not any(squeeze(a) in text[key] for key in cites):
                fail("DESIGN.md",
                     f"quotes {a.strip()[:70]!r} beside {', '.join(cites)}, but it is in "
                     "none of them")
        # And every cited screen must carry at least one of them.
        for key in cites:
            if any(squeeze(a) in text[key] for a in anchors):
                anchored += 1
            else:
                fail("DESIGN.md",
                     f"cites {key} ({SOURCES[key].name}), but none of its anchors is "
                     f"there: {anchors[:3]}")
    if not anchored and not unanchored:
        fail("DESIGN.md", "no screen citations found; has the format changed?")
    print(f"  DESIGN.md: {anchored} citations anchored in their screen, {unanchored} without an anchor")


# Two structural landmarks every screen has exactly once, cited for all four.
# Checking them by name keeps a deterministic tripwire on the app shell.
LANDMARKS = [
    ("- **Header**:", "fixed top-0 w-full z-50 pt-safe"),
    ("- **Bottom nav**:", "fixed bottom-0 w-full z-50 pb-safe"),
]


def check_design_landmarks(fail):
    """The header and nav bullets must cite all four screens, and be right."""
    doc = (ROOT / "docs" / "DESIGN.md").read_text(encoding="utf-8")
    text = {k: v.read_text(encoding="utf-8") for k, v in SCREENS.items()}

    checked = 0
    for bullet, needle in LANDMARKS:
        start = doc.find(bullet)
        if start < 0:
            fail("DESIGN.md", f"could not find the {bullet!r} bullet; has the format changed?")
            continue
        block = doc[start:doc.find("\n- ", start + 1)]
        cites = sorted(set(SCREEN_CITE.findall(block)))
        if len(cites) != len(SCREENS):
            fail("DESIGN.md", f"{bullet!r} cites {cites}, expected all four screens")
        for key in cites:
            checked += 1
            if needle not in text[key]:
                fail("DESIGN.md", f"{bullet} cites {key}, but {needle!r} is not in "
                                  f"{SCREENS[key].name}")
    print(f"  DESIGN.md: {checked} structural landmarks verified")


def check_quoted_pytest_result(fail):
    """bob_brief.md quotes the result the suite actually prints.

    While the module was reserved this quoted the failure message all 14 tests
    shared. The module is built, so it quotes the passing summary instead. The
    claim being checked did not change: what the brief prints as live output
    has to still be live output.
    """
    brief = (ROOT / "docs" / "bob_brief.md").read_text(encoding="utf-8")
    block = re.search(r"`pytest -q` reports:\s*```\s*(.*?)\s*```", brief, re.S)
    if block is None:
        fail("bob_brief.md", "could not find the quoted pytest result block")
        return
    quoted = " ".join(block.group(1).split())
    live = " ".join(run_pytest("-q").split())
    if quoted not in live:
        fail(
            "bob_brief.md",
            "the quoted pytest result no longer matches pytest output.\n"
            f"      quoted: {quoted}",
        )
    else:
        print("  bob_brief.md: quoted pytest result matches live output")


# A test target named in a doc, written the way pytest addresses it: a test
# file, one class inside one, or one test. A target scopes a count claim beside
# it, and `check_cited_tests` resolves every one of them whether a count is
# beside it or not.
#
# There is more than one test file now, so a bare count has to be read as a
# count of something, and one file can hold tests in two states at once:
# `tests/test_event_feed.py` holds the built EventFeed contract and the pending
# buildup contract together, so the only honest counts are the file's total and
# the per-class breakdown.
TEST_NODE_CITE = re.compile(
    r"`(tests/test_[A-Za-z0-9_]+\.py(?:::[A-Za-z0-9_]+){0,2})`"
)

# A class or a test named on its own, which the docs do where the sentence
# around it makes the file obvious. Anchored on the opening backtick, so a name
# inside a longer span such as `tests/test_grounding.py` is not read as one.
BARE_TEST_CITE = re.compile(r"`(test_[a-z0-9_]+|Test[A-Za-z0-9_]*)`")

_COLLECTED = None
_BROWSER = None


def browser_collected():
    """Every node id in `tests/browser/`, which the default run leaves out.

    `norecursedirs` keeps the browser suite out of `pytest`, so the collection
    `collected()` does is the unit suite and its total is the number the count
    claims are about. The browser suite is still a place a doc cites a test
    by name, so it is collected separately and read by the citation check and
    by nothing else: a count claim stays a claim about the unit suite.
    """
    global _BROWSER
    if _BROWSER is not None:
        return _BROWSER
    _BROWSER = tuple(
        line.strip().replace("\\", "/")
        for line in run_pytest("tests/browser", "--collect-only", "-q").splitlines()
        if "::" in line
    )
    return _BROWSER


def targets_for(nodes):
    """The three ways pytest addresses a test, for every node id given: the
    file, the class in the file, and the node itself."""
    found = set()
    for node in nodes:
        path, _, rest = node.partition("::")
        found.add(path)
        if "::" in rest:
            found.add(f"{path}::{rest.split('::', 1)[0]}")
        found.add(node)
        found.add(node.split("[")[0])
    return found


def collected():
    """(counts by target, suite total, every node id), from pytest itself.

    `counts` is keyed by test file, by file::class, and by full node id, so one
    lookup answers both "how many tests does this target hold" and "is this a
    target at all". Kept after the first call, because three checks read it and
    a collection pass over the suite is not free.
    """
    global _COLLECTED
    if _COLLECTED is not None:
        return _COLLECTED

    nodes = [
        line.strip().replace("\\", "/")
        for line in run_pytest("--collect-only", "-q").splitlines()
        if "::" in line
    ]
    counts = {}
    for node in nodes:
        path, _, rest = node.partition("::")
        counts[path] = counts.get(path, 0) + 1
        if "::" in rest:
            target = f"{path}::{rest.split('::', 1)[0]}"
            counts[target] = counts.get(target, 0) + 1
        # The node id itself holds one test, which is what makes a count claim
        # beside a single cited test scope to that test.
        counts[node] = 1
    _COLLECTED = (counts, len(nodes), tuple(nodes))
    return _COLLECTED


def claimed_counts(block):
    """The test counts a block claims.

    The "all N pass" pattern is case-insensitive. It was not, and a sentence
    opening "All 14 failing with ..." went unchecked for that reason, which is
    the one position in a sentence the phrase is most likely to appear in.
    """
    return {
        int(n)
        for n in re.findall(r"(\d+)\s+(?:acceptance\s+)?tests?\b", block)
        + re.findall(r"all\s+(\d+)\s+(?:fail|pass)", block, re.IGNORECASE)
    }


def check_test_count(fail):
    """Counts like "14 tests" and "all 14 pass" must match what pytest collects.

    A claim that names one test target, a file or one class in a file, is
    checked against that target. A claim that names none is about the suite and
    is checked against the total. Before there was a second test file the two
    were the same number, and reading every claim as a claim about the whole
    suite would now report a correct per-file sentence as stale.
    """
    counts, total, _ = collected()
    if not total:
        fail("tests", "pytest collected no tests")
        return

    checked = 0
    for doc in [
        ROOT / "docs" / "bob_brief.md",
        ROOT / "HANDOFF.md",
        ROOT / "README.md",
        # The per-file "all N pass" claims moved here with the capability
        # list; the check moved with them.
        ROOT / "docs" / "CAPABILITIES.md",
        ROOT / "docs" / "HARNESS.md",
    ] + HISTORY:
        for block in design_blocks(doc.read_text(encoding="utf-8")):
            claims = claimed_counts(block)
            if not claims:
                continue
            cited = sorted(set(TEST_NODE_CITE.findall(block)))
            if len(cited) == 1:
                scope, expected = cited[0], counts.get(cited[0], 0)
            else:
                scope, expected = "the suite", total
            for n in claims:
                checked += 1
                if n != expected:
                    fail(doc.name, f"claims {n} tests for {scope}, pytest collects "
                                   f"{expected}")
    files = sum(1 for key in counts if "::" not in key)
    print(f"  test count: {checked} claim(s) checked, "
          f"{total} collected across {files} file(s)")


def check_cited_tests(fail):
    """A test a doc cites is one pytest collects.

    `docs/HARNESS.md`, `docs/VERIFICATION.md`, `docs/GOVERNANCE.md` and
    `docs/IBM_STACK.md` put a file and a test beside nearly every statement they
    make, which is the only thing that makes those documents evidence rather
    than description. A renamed test would leave them pointing at nothing while
    still reading as evidence, so a citation is checked the way a path is: it
    resolves, or the gate fails.

    Both forms are checked. A node id is resolved against what pytest collects,
    in any of the three ways pytest addresses one: a file, a class in a file, or
    a single test. A class or test named on its own is resolved against the
    names pytest collected, for the places where the file is obvious from the
    sentence around it.
    """
    counts, total, nodes = collected()
    if not total:
        fail("tests", "pytest collected no tests")
        return

    # The browser suite joins the names and node ids a citation may resolve
    # against, and not the total: a count claim is about the unit suite, which
    # is what `pytest` with no path runs.
    browser = browser_collected()
    if not browser:
        fail("tests", "pytest collected nothing in tests/browser")
        return
    everything = tuple(nodes) + browser
    targets = set(counts) | targets_for(browser)
    classes = {part for node in everything for part in node.split("::")[1:-1]}
    names = {node.split("::")[-1].split("[")[0] for node in everything}

    checked = 0
    for doc in DOCS:
        text = doc.read_text(encoding="utf-8")
        for cite in sorted(set(TEST_NODE_CITE.findall(text))):
            # A planned test file is named by the Plan section before it is
            # written, so it is exempt here for the same reason it is exempt
            # from the path check. The exemption is only ever as wide as that
            # one list, and the path check fails the moment the file appears.
            if cite in DELIBERATELY_ABSENT:
                continue
            checked += 1
            if cite not in targets:
                fail(doc.name, f"cites {cite}, which pytest does not collect")
        for cite in sorted(set(BARE_TEST_CITE.findall(text))):
            checked += 1
            if cite.startswith("test_"):
                if cite not in names:
                    fail(doc.name,
                         f"cites the test {cite}, which pytest does not collect")
            elif cite not in classes:
                fail(doc.name,
                     f"cites the test class {cite}, which pytest does not collect")
    print(f"  tests cited: {checked} citation(s) resolved against "
          f"{total} collected and {len(browser)} in tests/browser")


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
    r"\"([^\"]{10,})\"\s*\(((?:`(?:0[1-4]|removed)`(?:,\s*)?)+)\)"
)
QUOTE_CITATION = re.compile(r"`(0[1-4])`|`(removed)`")

#: Screen copy a task record quotes with the screen it was on, and a later
#: task took off that screen. The record stands as it was written and this
#: says the line is gone; the check reads it both ways, so a line here that
#: comes back to a screen fails until this entry goes.
#:
#: Task 33 removed the moment card's broadcast quote: nothing read it out of
#: the data, and the 2022 one was wrong about the play.
SINCE_REMOVED = {
    "\u00ab...Maradona, inside his own half, past Beardsley, past Butcher, "
    "past Fenwick, rounds Shilton, and finishes.\u00bb",
}


def check_quoted_screen_copy(fail):
    """A doc that quotes screen copy says which screen it is on.

    A quote followed by `NN` must appear in that screen. A quote followed by
    `removed` must appear in no screen at all, which keeps "we took this out"
    claims honest in both directions. Quotes with no citation are prose and are
    not checked, so commit messages and rule text can be quoted freely.

    `HANDOFF.md` was the only doc that used the convention, and the records
    carrying most of those quotes are now under `docs/history/`. Both are read,
    and the total is what has to be non-zero: a convention that disappeared
    from every doc at once is a convention that has quietly changed.

    A record is not edited as the code moves on, so a record quoting a line
    that a later task removed would fail here for being right about the day it
    was written. `SINCE_REMOVED` is where that is recorded instead, and it is
    read in both directions: writing one of those lines back into a screen
    fails until the entry goes.
    """
    sources = [ROOT / "HANDOFF.md"] + HISTORY
    text = {k: " ".join(v.read_text(encoding="utf-8").split()) for k, v in SCREENS.items()}

    for gone in SINCE_REMOVED:
        still = [k for k, body in text.items() if gone in body]
        if still:
            fail("the screens", f"{gone[:50]!r} is recorded as removed but is in "
                                f"{', '.join(still)}")

    found = 0
    for doc in sources:
        flat = " ".join(doc.read_text(encoding="utf-8").split())
        for quote, cites in QUOTED_SCREEN_COPY.findall(flat):
            wanted = " ".join(quote.split())
            for key, removed in QUOTE_CITATION.findall(cites):
                found += 1
                if removed:
                    still = [k for k, body in text.items() if wanted in body]
                    if still:
                        fail(doc.name,
                             f"{wanted[:50]!r} is marked removed but is still in "
                             f"{', '.join(still)}")
                elif wanted in SINCE_REMOVED:
                    continue
                elif wanted not in text[key]:
                    fail(doc.name, f"{wanted[:50]!r} is not in {SCREENS[key].name}")
    if not found:
        fail("the docs", "no cited screen copy found; has the convention changed?")
    print(f"  screen copy: {found} cited quote(s) checked across "
          f"{len(sources)} doc(s)")


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
        check_quoted_pytest_result,
        check_test_count,
        check_cited_tests,
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
