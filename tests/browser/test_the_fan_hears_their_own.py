"""The words, the recording and the Moments card agree, for every fan.

Both matches, by the three answers to "Who are you with", by the three
narrator states a fan can be in: no choice, the Storyteller, the Buddy.
Eighteen fans, and for each of them three things have to be the same one slot:

- the words the moment card shows under the grounding label,
- the file the moment card's player loads,
- the file the Moments list's hero card loads.

None of the three is written down here. The slot comes from `app.api.slot_for`,
the Python copy of `Prelude.slotFor`; the words come from
`app/web/narrations.json`; the file comes from `hero.audio` in
`app/web/matches.json`. So this fails when the browser's copy of the rule
drifts from the Python one, when the card shows another slot's telling, and
when the two screens offer a fan two different voices.

Reading the file the player loaded means seeing which `new Audio` it made, so
`AUDIO_SHIM` in the conftest records every one before the page's own scripts
run and `fan.audio_loaded()` reads the list. It hands back a real audio
element, so everything downstream of it, the analyser included, is the real
thing.

The 268 px measurement is Task 29's: the narration block reserves the tallest
of the six frozen narrations plus the label at 390 px wide, so nothing below it
moves when the words land.
"""

import pytest

from tests.browser.conftest import (
    CARD_STATE, LISTENERS, MOMENTS, MOMENT_CARD, NARRATORS, PLAY_OFFERED,
)

#: The block's reserved height at 390 px wide, in pixels. Task 29 measured the
#: six frozen narrations at 216 to 268 px with the label and reserved the
#: tallest, so the player below the words does not move when they arrive.
BLOCK_PX = 268

MOMENTS_CARDS = """() => Array.from(
  document.querySelectorAll('[data-field="moments_list"] > *')
).map(card => {
  const button = card.querySelector('[data-field="moment_play"]');
  return {
    title: (card.querySelector('[data-field="title"]') || {}).textContent,
    label: button ? button.getAttribute('aria-label') : null,
    disabled: button ? button.disabled : null,
  };
})"""


def fans():
    return [
        pytest.param(listener, narrator, id="%s-%s" % (listener, narrator or "unset"))
        for listener in LISTENERS
        for narrator in NARRATORS
    ]


@pytest.mark.parametrize("listener,narrator", fans())
def test_the_card_shows_the_slot_the_rules_name(
    fan, match_ids, expected, listener, narrator
):
    for match_id in match_ids:
        want = expected(match_id, listener, narrator)
        fan.remember(match_id=match_id, listener=listener, narrator=narrator)
        fan.visit(MOMENT_CARD, match=match_id)
        fan.page.wait_for_function(PLAY_OFFERED)
        state = fan.page.evaluate(CARD_STATE)
        assert state["text"] == want["text"], (match_id, listener, narrator)
        assert state["wordsShown"] is True
        assert state["labelShown"] is True
        assert state["playDisabled"] is False
        assert state["blockHeight"] == BLOCK_PX, (match_id, state["blockHeight"])
        loaded = fan.audio_loaded()
        assert loaded == [want["file"]], (match_id, listener, narrator, loaded)
        assert not fan.errors, fan.errors


@pytest.mark.parametrize("listener,narrator", fans())
def test_the_moments_hero_card_loads_the_same_file(
    fan, match_ids, matches, expected, listener, narrator
):
    for match_id in match_ids:
        want = expected(match_id, listener, narrator)
        fan.remember(match_id=match_id, listener=listener, narrator=narrator)
        fan.visit(MOMENTS, match=match_id)
        loaded = fan.audio_loaded()
        assert loaded == [want["file"]], (match_id, listener, narrator, loaded)

        cards = fan.page.evaluate(MOMENTS_CARDS)
        moments = matches[match_id]["moments"]
        hero = matches[match_id]["hero"]["event"]
        assert len(cards) == len(moments), (match_id, len(cards))
        enabled = 0
        for card, moment in zip(cards, moments):
            assert card["title"] == moment["title"], (match_id, card)
            is_hero = (
                moment["event"]["period"], moment["event"]["minute"],
                moment["event"]["second"],
            ) == (hero["period"], hero["minute"], hero["second"])
            if is_hero:
                enabled += 1
                assert card["disabled"] is False, card
                assert card["label"] == (
                    "Play the narration for " + moment["title"]
                ), card
            else:
                assert card["disabled"] is True, card
                assert card["label"] == (
                    moment["title"] + ": no narration recorded"
                ), card
        assert enabled == 1, (match_id, enabled)
        assert not fan.errors, fan.errors


def test_the_two_screens_never_offer_two_voices(fan, match_ids, expected):
    """The same fan, both screens, one after the other in one tab.

    The two screens read the same lookup, so this would only fail if one of
    them read it at a different moment and got a different answer. It is the
    check the division of work is for, and it costs one more page load.
    """
    for match_id in match_ids:
        for listener in LISTENERS:
            want = expected(match_id, listener)
            fan.remember(match_id=match_id, listener=listener)
            fan.visit(MOMENT_CARD, match=match_id)
            fan.page.wait_for_function(PLAY_OFFERED)
            card_file = fan.audio_loaded()
            fan.visit(MOMENTS, match=match_id)
            moments_file = fan.audio_loaded()
            assert card_file == moments_file == [want["file"]], (
                match_id, listener, card_file, moments_file
            )


def test_no_screen_offers_a_recording_that_is_not_there(fan, match_ids, matches):
    """Every play button on both screens, over both matches: a button that is
    enabled has a file behind it, and `hero.audio` holds files for the hero
    goal's three slots and for nothing else."""
    for match_id in match_ids:
        hero = matches[match_id]["hero"]
        assert set(hero["audio"]) == set(hero["voice_for"].values())
        fan.remember(match_id=match_id, listener="neutral")
        fan.visit(MOMENTS, match=match_id)
        offered = fan.page.evaluate(
            """() => Array.from(document.querySelectorAll(
                 '[data-field="moments_list"] [data-field="moment_play"]'
               )).filter(b => !b.disabled).length"""
        )
        assert offered == 1, (match_id, offered)
        loaded = fan.audio_loaded()
        assert len(loaded) == 1 and loaded[0] in hero["audio"].values(), loaded
