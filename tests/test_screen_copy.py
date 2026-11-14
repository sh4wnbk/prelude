"""Acceptance tests for the screen copy Shawn settled on 2026-10-29.

Copy that told the fan they had been away goes, because the opener rule in
`docs/VOICE.md` keeps the absence out of everything said after it. Copy that
repeated "buildup" on screens that already say it goes too. The lines that
replace them are Shawn's, written out here as literals. `docs/bob_brief.md`
carries the brief as Task 7.

Kept on purpose, and not tested here: the Live helper shown before the fan
leaves ("Prelude keeps track while you're away.") and the "STEPPED AWAY"
state label. The tagline in the Moments footer was on this list until
Shawn's decision of 2026-11-13 took it off the screen; see
`TestTheMomentsFooterCarriesNoTagline`.
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


class TestTheMomentsFooterCarriesNoTagline:
    """Shawn's decision on 2026-11-13: "The moment you missed deserves an
    encore!" is marketing language, not app copy. It told the fan they had
    missed something on a screen they can reach without ever having stepped
    away, and "deserves an encore" is a judgement rather than a description."""

    TAGLINE = "The moment you missed deserves an encore!"

    def test_the_moments_screen_does_not_carry_it(self):
        markup = (WEB / "prelude_04_moments.html").read_text(encoding="utf-8")
        assert self.TAGLINE not in markup

    def test_no_screen_or_copy_file_carries_it(self):
        for path in sorted(WEB.glob("*.html")) + sorted(WEB.glob("*.js")) + [MATCHES]:
            text = path.read_text(encoding="utf-8")
            assert self.TAGLINE not in text, path.name

    def test_nothing_in_app_web_says_deserves_an_encore(self):
        """The phrase and not just the sentence, so a reworded version of the
        same claim does not slip back in."""
        for path in sorted(WEB.glob("*.html")) + sorted(WEB.glob("*.js")) + [MATCHES]:
            text = path.read_text(encoding="utf-8").lower()
            assert "deserves an encore" not in text, path.name


#: The shell, which is the only page that carries the launch screen.
SHELL = WEB / "index.html"

#: Shawn's wording of 2026-11-14, as two literals.
WORDMARK = "Prelude."
LAUNCH_LINE = "Be there. Even when you're not."


class TestTheLaunchScreen:
    """The first frame of a visit: the wordmark over the line, and nothing else.

    It is in `app/web/index.html` and nowhere else, because the shell is what
    a visit opens on and what the manifest's `start_url` names. A screen
    opened on its own is a developer's path and shows no launch screen.

    **It claims nothing.** There is no match on it, no clock, no score, no
    data and no label: the only two lines are the app's own name and the line
    Shawn settled on. `tests/browser/test_the_launch_screen.py` is what holds
    its behaviour, the first frame, the fade, the cap and the one visit.
    """

    def shell(self):
        return SHELL.read_text(encoding="utf-8")

    def test_the_wordmark(self):
        assert '<div id="launch-mark">Prelude<span id="launch-stop">.</span></div>' in (
            self.shell()
        )

    def test_the_line(self):
        assert '<p id="launch-line">%s</p>' % LAUNCH_LINE in self.shell()

    def test_it_is_announced_as_prelude(self):
        assert '<div aria-label="Prelude" id="launch" role="img">' in self.shell()

    def test_the_wordmark_is_syne(self):
        """The same family the icon's two glyphs are drawn from, so the
        launch screen and the home screen icon are one letterform."""
        block = self.shell().split("#launch-mark {")[1].split("}")[0]
        assert '"Syne"' in block
        assert "font-weight: 700" in block

    def test_the_stop_is_the_amber_and_the_word_is_not(self):
        shell = self.shell()
        assert "#launch-stop { color: #ffb703; }" in shell
        assert "color: #e1e2ea;" in shell.split("#launch-mark {")[1].split("}")[0]

    def test_the_line_is_the_amber(self):
        block = self.shell().split("#launch-line {")[1].split("}")[0]
        assert "color: #ffb703;" in block

    def test_it_sits_on_the_app_background(self):
        block = self.shell().split("#launch {")[1].split("}")[0]
        assert "background-color: #101319;" in block

    def test_it_claims_nothing(self):
        """Every word on it, which is the app's name and one line."""
        shell = self.shell()
        start = shell.index('id="launch"')
        body = shell[start:shell.index("</div>", shell.index("launch-line"))]
        words = " ".join(body.split())
        for banned in ("LIVE", "Verified", "goal", "match", "data", "narration"):
            assert banned.lower() not in words.lower(), banned

    def test_it_is_on_the_shell_and_on_no_screen(self):
        for path in sorted(WEB.glob("prelude_*.html")):
            text = path.read_text(encoding="utf-8")
            assert 'id="launch"' not in text, path.name
            assert LAUNCH_LINE not in text, path.name

    def test_it_honours_a_request_for_less_motion(self):
        shell = self.shell()
        at = shell.index("@media (prefers-reduced-motion: reduce)")
        block = shell[at:shell.index("}", shell.index("{", at + 40)) + 1]
        assert "#launch" in block
        assert "transition: none" in block

    def test_whether_it_paints_is_decided_before_the_body(self):
        """A class on `<html>`, set in the head. Decided in the body it would
        be a flash of one state before the other, and `CLAUDE.md` counts the
        frames before any script has run as a state a fan can see."""
        shell = self.shell()
        decided = shell.index("prelude.launched")
        parsed = shell.index('id="launch"')
        assert decided < parsed, "the decision is made after the element exists"
        assert "html.launched #launch { display: none; }" in shell

    def test_the_visit_is_a_session(self):
        """`sessionStorage`, so a new tab is a new visit and a reload is not.
        Blocked storage shows it rather than hiding it, which the shell says."""
        shell = self.shell()
        assert "window.sessionStorage.getItem('prelude.launched')" in shell
        assert "window.sessionStorage.setItem('prelude.launched', '1')" in shell
        assert "localStorage" not in shell.split('id="frame"')[0]
