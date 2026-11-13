"""Acceptance tests for the screen copy Shawn settled on 2026-10-29.

Copy that told the fan they had been away goes, because the opener rule in
`docs/VOICE.md` keeps the absence out of everything said after it. Copy that
repeated "buildup" on screens that already say it goes too. The lines that
replace them are Shawn's, written out here as literals. `docs/bob_brief.md`
carries the brief as Task 7.

Kept on purpose, and not tested here: the Live helper shown before the fan
leaves ("Prelude keeps track while you're away."), the "STEPPED AWAY" state
label, and the tagline in the Moments footer.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
MATCHES = WEB / "matches.json"
MOMENT_CARD = WEB / "prelude_03_moment_card.html"
LIVE = WEB / "prelude_02_live_seated.html"

SHARE_TITLE = "Listen on Prelude."
SHARE_TEXT = {
    3750191: "Maradona's solo goal as it happened.",
    3869685: "Di María's counter goal as it happened.",
}
READY = "Ready when you are."
SEATED_CAPTION = (
    "You're in your seat. We'll catch the buildup if you step away."
)


def matches():
    doc = json.loads(MATCHES.read_text(encoding="utf-8"))
    return {entry["match_id"]: entry for entry in doc["matches"]}


def card():
    return MOMENT_CARD.read_text(encoding="utf-8")


class TestTheMomentCardLabel:
    def test_the_label_no_longer_says_you_stepped_away(self):
        assert "YOU STEPPED AWAY" not in card()

    def test_the_label_still_says_the_buildup(self):
        assert ">THE BUILDUP</span>" in card()


class TestTheLiveScreenAfterHeadingOut:
    def test_the_1986_helper_line(self):
        assert matches()[3750191]["live_seated"]["after"]["help"] == READY

    def test_the_2022_helper_line(self):
        assert matches()[3869685]["live_seated"]["after"]["help"] == READY


class TestTheShareSheet:
    def test_the_title(self):
        assert f"title: '{SHARE_TITLE}'" in card()

    def test_the_old_title_is_gone(self):
        assert "The buildup you missed." not in card()

    def test_the_1986_share_text(self):
        assert matches()[3750191]["hero"]["share_text"] == SHARE_TEXT[3750191]

    def test_the_2022_share_text(self):
        assert matches()[3869685]["hero"]["share_text"] == SHARE_TEXT[3869685]

    def test_the_inline_share_text_is_the_1986_line(self):
        """The button carries the default match's text before the renderer
        runs, as every other inline field on the card does."""
        assert f'data-share-text="{SHARE_TEXT[3750191]}"' in card()


class TestNothingSaysYouMissedIt:
    def test_no_screen_or_copy_file_says_the_buildup_you_missed(self):
        for path in sorted(WEB.glob("*.html")) + [MATCHES]:
            assert "buildup you missed" not in path.read_text(encoding="utf-8"), path.name


class TestTheSeatedCaptionPromisesOnlyTheBuildup:
    """Shawn's decision on 2026-11-12: the old line ("We'll catch anything you
    miss.") promised coverage of the whole match, and the demo narrates one
    goal per match. The caption now names the one thing the app does."""

    def test_the_1986_caption(self):
        assert matches()[3750191]["live_seated"]["caption"] == SEATED_CAPTION

    def test_the_2022_caption(self):
        assert matches()[3869685]["live_seated"]["caption"] == SEATED_CAPTION

    def test_the_live_screen_carries_it_inline(self):
        markup = LIVE.read_text(encoding="utf-8")
        assert f'data-field="caption">{SEATED_CAPTION}</span>' in markup

    def test_no_screen_or_copy_file_promises_to_catch_anything_you_miss(self):
        for path in sorted(WEB.glob("*.html")) + [MATCHES]:
            text = path.read_text(encoding="utf-8")
            assert "anything you miss" not in text, path.name
