"""What a screen reader says a control is called.

Every icon in `app/web/` is a Material Symbols ligature: a span whose text is
the glyph's name, `sensors` or `replay_10` or `ios_share`, rendered as a
picture by the icon font. A reader does not see the picture. It sees the word,
and because the span sits inside the control, the word used to be part of the
control's accessible name: the bottom nav read "sensors LIVE", "auto_awesome_motion
MOMENTS", "tune PROFILE", and the moment card's second button read "replay_10
REPLAY 10S". Task 34 hid the two spans in that button deck and
`HANDOFF.md` carried the rest as "Found, not fixed" through Tasks 35 and 36.

Every one of those spans is `aria-hidden="true"` now, so a control's name is
the label a fan reads and nothing else.

**This asks the browser, not the markup.** The names below are the ones
Chromium computed from the live tree, through `aria_snapshot`, which is the
same computation a reader does. An icon the renderer built rather than the
file would be in that tree too.

Three things are asked of every screen, on both matches, for all three
listeners and all three narrator states:

- every Material Symbols span is hidden from the tree, read off the live DOM
  rather than off the file;
- no ligature appears in any accessible name on the screen, with the
  ligatures read off that same DOM so nothing is written down twice;
- the bottom nav, where it is, is named by its three labels.

And the moment card, which is the one screen with a button deck, is asked for
its four buttons by name.
"""

import re

import pytest

from tests.browser.conftest import (
    ALL_SCREENS, LISTENERS, MATCH_REQUIRED, MOMENT_CARD, NARRATORS,
)

#: The bottom nav's three labels, in the order the markup puts them. Written
#: down because they are the nav's own copy, which is what this is about;
#: `tests/test_screen_copy.py` holds the markup to the same three strings.
NAV_NAMES = ("LIVE", "MOMENTS", "PROFILE")

#: The moment card's four buttons, by accessible name. Three are the label a
#: fan reads; the play button carries an `aria-label`, because its label is
#: the glyph and a glyph is not a name.
CARD_BUTTONS = (
    "MATCH STREAM",
    "Play buildup narration",
    "REPLAY 10S",
    "SHARE",
)

#: Every icon span on the page, with the ligature it holds and whether the
#: tree can see it. Read off the live DOM, so an icon built by
#: `app/web/match-content.js` counts the same as one in the file.
ICON_SPANS = """() => Array.from(
  document.querySelectorAll('span.material-symbols-outlined')
).map(span => ({
  ligature: (span.textContent || '').trim(),
  hidden: span.getAttribute('aria-hidden') === 'true',
}))"""

#: One line of an aria snapshot that carries a name: a role, then the name in
#: double quotes. `- button "SHARE"` and `- link "LIVE":` both match; a
#: `- text: ...` line, which is content rather than a name, does not.
NAMED_NODE = re.compile(r'^\s*-\s+[a-z]+(?:-[a-z]+)*\s+"((?:[^"\\]|\\.)*)"')


def names_in(snapshot):
    """Every accessible name in one aria snapshot, in tree order."""
    return [
        NAMED_NODE.match(line).group(1)
        for line in snapshot.splitlines()
        if NAMED_NODE.match(line)
    ]


def open_screen(fan, screen, match_id, listener, narrator):
    """One screen, settled, for one fan.

    The five screens that are about a match are waited for by their render
    flag; the list and the scanner render nothing of a match, so
    `domcontentloaded` is as settled as they get.
    """
    fan.remember(match_id=match_id, listener=listener, narrator=narrator)
    if screen in MATCH_REQUIRED:
        fan.visit(screen, match=match_id)
    else:
        fan.goto(screen, match=match_id)
        fan.page.wait_for_load_state("domcontentloaded")
    return fan.page


@pytest.mark.parametrize("narrator", NARRATORS)
@pytest.mark.parametrize("listener", LISTENERS)
def test_a_control_is_named_by_its_label_and_not_by_its_glyph(
    fan, match_ids, listener, narrator
):
    """Both matches, every screen: no ligature reaches a name."""
    for match_id in match_ids:
        for screen in ALL_SCREENS:
            where = (screen, match_id, listener, narrator)
            page = open_screen(fan, screen, match_id, listener, narrator)

            icons = page.evaluate(ICON_SPANS)
            assert icons, where
            showing = [one["ligature"] for one in icons if not one["hidden"]]
            assert not showing, (showing, where)

            names = names_in(page.locator("body").aria_snapshot())
            assert names, where
            ligatures = sorted({one["ligature"] for one in icons})
            leaked = [
                (ligature, name)
                for ligature in ligatures
                for name in names
                if re.search(r"\b%s\b" % re.escape(ligature), name)
            ]
            assert not leaked, (leaked, where)

            nav = page.locator("nav[data-active-classes]")
            if nav.count():
                assert tuple(names_in(nav.aria_snapshot())) == NAV_NAMES, (
                    names_in(nav.aria_snapshot()), where,
                )

            if screen == MOMENT_CARD:
                buttons = names_in(page.locator("main").aria_snapshot())
                for wanted in CARD_BUTTONS:
                    assert wanted in buttons, (wanted, buttons, where)
