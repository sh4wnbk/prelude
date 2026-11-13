"""A fan arriving with nothing stored, and a fan coming back to a new tab.

The first load is the state a judge sees, and it is the one a browser run is
most likely to skip, because writing the fan's answers into storage is how
every other check here gets to the screen it wants. So this one writes nothing.

What has to be true of it, which is Task 26's rule and Task 28's:

- **Prelude does not choose the match.** The list opens with no card selected
  and the confirm button disabled, and its header pill is hidden, because a
  pill that names a match and says it is live has nothing true to say before
  the fan has chosen one.
- **A screen that is about one match sends the fan to the list.** The five
  screens in `MATCH_REQUIRED` reached with no `match` in the URL replace
  themselves with the list, so Back does not return to them. A match the app
  does not hold does the same.
- **The list and the scanner are whole without a match**, so neither of them
  redirects and neither renders one.
- **The narrator outlives the tab and the allegiance does not.** The narrator
  is a standing preference in `localStorage`; "Who are you with" and the name
  are answers about tonight and stay in `sessionStorage`. Closing the tab and
  opening another is what tells the two apart.
"""

import pytest

from tests.browser.conftest import (
    LIVE, MATCH_REQUIRED, MOMENT_CARD, MOMENTS, PICKER, PROFILE, SCANNER,
)

#: The header pill, which only the list ships hidden and so only the list
#: marks: `renderChip` shows it there once a match is chosen, and on every
#: other screen it is in the markup and shown. `shown` is read off whichever
#: of the two the screen has.
CHIP = """() => {
  const chip = document.querySelector('[data-field=chip]');
  const marked = document.querySelector('[data-field=chip_pill]');
  const pill = marked || (chip && chip.parentElement);
  return {
    marked: marked !== null,
    shown: pill ? getComputedStyle(pill).display !== 'none' : null,
    text: chip ? chip.textContent.trim() : null,
  };
}"""


def test_the_list_chooses_no_match(fan):
    page = fan.goto(PICKER)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(400)
    assert page.evaluate(
        "() => document.querySelectorAll('.event-card[aria-checked=true]').length"
    ) == 0
    assert page.evaluate("() => document.getElementById('confirm-btn').disabled") is True
    assert not fan.errors, fan.errors


def test_the_lists_pill_is_hidden_until_a_match_is_chosen(fan, match_ids):
    page = fan.goto(PICKER)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(400)
    chip = page.evaluate(CHIP)
    assert chip["marked"] is True, chip
    assert chip["shown"] is False, chip
    assert chip["text"] == "", chip


def test_the_pill_names_the_match_once_there_is_one(fan, match_ids, matches):
    """And on a screen that is about one match it is in the markup and shown,
    which is the shape every screen but the list and the scanner has."""
    for match_id in match_ids:
        page = fan.visit(LIVE, match=match_id)
        chip = page.evaluate(CHIP)
        assert chip["marked"] is False, (match_id, chip)
        assert chip["shown"] is True, (match_id, chip)
        assert chip["text"] == (
            matches[match_id]["label"] + " · LIVE"
        ), chip

    # And on the list, once a match is chosen, the pill it ships hidden is
    # shown and names that match.
    for match_id in match_ids:
        page = fan.visit(PICKER, match=match_id)
        chip = page.evaluate(CHIP)
        assert chip["marked"] is True, (match_id, chip)
        assert chip["shown"] is True, (match_id, chip)
        assert chip["text"] == (
            matches[match_id]["label"] + " · LIVE"
        ), chip


@pytest.mark.parametrize("screen", MATCH_REQUIRED)
def test_a_match_screen_with_no_match_sends_the_fan_to_the_list(fan, screen):
    page = fan.goto(screen)
    page.wait_for_url("**/" + PICKER + "*")
    assert PICKER in page.url, page.url
    assert not fan.errors, fan.errors


@pytest.mark.parametrize("screen", MATCH_REQUIRED)
def test_a_match_the_app_does_not_hold_sends_the_fan_to_the_list(fan, screen):
    page = fan.goto(screen, match=1)
    page.wait_for_url("**/" + PICKER + "*")
    assert PICKER in page.url, page.url


def test_back_does_not_return_to_a_screen_the_fan_never_chose(fan):
    """`replace` rather than `assign`: the screen that sent the fan away is
    not a step in the history."""
    page = fan.goto(PICKER)
    page.wait_for_load_state("domcontentloaded")
    page.goto(fan.server.url(MOMENT_CARD))
    page.wait_for_url("**/" + PICKER + "*")
    page.go_back()
    page.wait_for_load_state("domcontentloaded")
    assert MOMENT_CARD not in page.url, page.url


@pytest.mark.parametrize("screen", [PICKER, SCANNER])
def test_the_list_and_the_scanner_are_whole_without_a_match(fan, screen):
    page = fan.goto(screen)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(500)
    assert screen in page.url, page.url
    assert page.evaluate(
        "() => document.documentElement.getAttribute('data-match-rendered')"
    ) is None
    assert not fan.errors, fan.errors


def test_the_moment_card_offers_nothing_before_a_match_is_chosen(fan):
    """It is not reached at all, so there is no button and no label to be
    wrong: the fan is on the list before anything of it is painted."""
    page = fan.goto(MOMENT_CARD)
    page.wait_for_url("**/" + PICKER + "*")
    assert page.evaluate("() => document.getElementById('playBtn')") is None


def test_the_narrator_outlives_the_tab(fan, match_ids, expected):
    """Chosen in one tab, still theirs in the next, and the slot follows it.

    The allegiance does not: it is an answer about tonight, so the new tab is
    a fan with no side, and the slot the narrator reaches is the one a fan
    with no side gets.
    """
    match_id = match_ids[0]
    fan.remember(match_id=match_id, listener="team_b", name="Olivia",
                 narrator="storyteller")
    page = fan.visit(MOMENT_CARD, match=match_id)
    page.wait_for_function("() => !document.getElementById('playBtn').disabled")
    chosen = expected(match_id, "team_b", "storyteller")
    assert fan.audio_loaded() == [chosen["file"]]

    page = fan.reopen()
    page.goto(fan.server.url(PICKER))
    page.wait_for_load_state("domcontentloaded")
    held = page.evaluate(
        """() => ({
             narrator: localStorage.getItem('prelude.narrator'),
             listener: sessionStorage.getItem('prelude.listener.%d'),
             name: sessionStorage.getItem('prelude.name'),
           })""" % match_id
    )
    assert held["narrator"] == "storyteller", held
    assert held["listener"] is None, held
    assert held["name"] is None, held

    fan.visit(MOMENT_CARD, match=match_id)
    fan.page.wait_for_function(
        "() => !document.getElementById('playBtn').disabled"
    )
    after = expected(match_id, "neutral", "storyteller")
    assert fan.audio_loaded() == [after["file"]]
    assert fan.page.evaluate(
        "() => document.querySelector('[data-field=hero_narration]').textContent"
    ) == after["text"]


def test_the_narrator_is_chosen_by_tapping_and_then_outlives_the_tab(
    fan, match_ids, expected, narrators
):
    """The same thing, with nothing written into storage by the harness: the
    narrator is picked on Profile the way a fan picks one.

    One of the three cards is already current for this fan and
    `renderNarrators` attaches no click handler to the current card, which
    Task 29 recorded as the picker's existing behaviour. So the card tapped
    here is chosen for not being the current one.
    """
    match_id = match_ids[1]
    fan.remember(match_id=match_id, listener="team_a")
    page = fan.visit(PROFILE, match=match_id)
    page.wait_for_selector("[data-field='narrator_list'] button")

    current = expected(match_id, "team_a")["slot"].split("_")[0]
    cards = page.evaluate(
        """() => Array.from(
             document.querySelectorAll("[data-field='narrator_list'] button")
           ).map(b => ({
             name: b.querySelector('span').textContent,
             current: b.getAttribute('aria-current') === 'true',
             off: b.getAttribute('aria-disabled') === 'true',
           }))"""
    )
    choosable = [card for card in cards if not card["current"] and not card["off"]]
    assert choosable, cards
    name = choosable[0]["name"]
    wanted = {entry["name"]: entry["id"] for entry in narrators}[name]
    assert wanted != current, (wanted, current)

    page.get_by_role("button", name=name).first.click()
    page.wait_for_timeout(300)
    stored = page.evaluate("() => localStorage.getItem('prelude.narrator')")
    assert stored == wanted, (stored, wanted, cards)

    page = fan.reopen()
    page.goto(fan.server.url(PICKER))
    page.wait_for_load_state("domcontentloaded")
    assert page.evaluate("() => localStorage.getItem('prelude.narrator')") == stored

    fan.visit(MOMENTS, match=match_id)
    after = expected(match_id, "neutral", stored)
    assert fan.audio_loaded() == [after["file"]]
