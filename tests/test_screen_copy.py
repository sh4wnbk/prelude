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
#: The button's own label, and the line that stands over a clipboard write
#: that resolved.
SHARE_LABEL = "SHARE"
COPIED_LABEL = "LINK COPIED"
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


class TestTheShareButtonOffersNoClip:
    """Shawn's reading of 2026-11-15: the button said it shared a clip and
    shared a link and a line of text. There is no clip in this repo and no
    code that cuts one, so the label is the thing it sends.

    The confirmation is the other half. The old fallback branch said "COPIED"
    for 1.5 seconds on every click whether anything had been copied or not,
    and a clipboard write can be refused outright. The line a fan reads now
    stands only over a write that resolved.
    """

    def test_the_label_is_the_thing_it_does(self):
        assert f'id="shareLabel">{SHARE_LABEL}<' in card()

    def test_it_no_longer_offers_a_clip(self):
        assert "SHARE CLIP" not in card()

    def test_the_banned_label_is_in_the_copy_gate(self):
        """`scripts/scan_copy.py` is what keeps it from coming back, so the
        pattern is read here rather than assumed."""
        gate = (ROOT / "scripts" / "scan_copy.py").read_text(encoding="utf-8")
        assert '("a clip the app does not have", r"SHARE CLIP")' in gate

    def test_the_confirmation_says_what_was_copied(self):
        assert f"'{COPIED_LABEL}'" in card()

    def test_the_confirmation_is_only_set_where_the_write_resolved(self):
        """`then(confirmCopied, ...)` and nothing else sets it: a rejected
        write takes the second branch, which says nothing."""
        assert "navigator.clipboard.writeText(link).then(confirmCopied" in card()
        assert card().count(COPIED_LABEL) == 1

    def test_nothing_claims_a_copy_without_a_clipboard(self):
        """`navigator.clipboard` is undefined outside a secure context, so
        reaching it at all is inside a try with an empty handler."""
        assert "try {" in card()
        assert "catch (nothingToCopyWith)" in card()


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

#: The brand file the shell inlines its mark from.
MARK = WEB / "assets" / "brand" / "prelude_mark.svg"

#: The tagline, settled with the rest of the brand on 2026-11-14. It replaces
#: "Be there. Even when you're not.", which was the launch screen's line while
#: the brand was still only in the pitch thread.
TAGLINE = "Leave your seat. Not the game."


class TestTheLaunchScreen:
    """Every load of the shell: the mark over the tagline, and nothing else.

    It is in `app/web/index.html` and nowhere else, because the shell is what
    a visit opens on and what the manifest's `start_url` names. A screen
    opened on its own is a developer's path and shows no launch screen.

    **It claims nothing.** There is no match on it, no clock, no score, no
    data and no label: the mark and the tagline are all of it.
    `tests/browser/test_the_launch_screen.py` is what holds its behaviour,
    the first frame, the layout, the fade and the cap.
    """

    def shell(self):
        return SHELL.read_text(encoding="utf-8")

    def test_the_mark_is_the_brand_file_inlined(self):
        """The paths out of `app/web/assets/brand/prelude_mark.svg`, so the
        mark on the launch screen and the mark the brand carries cannot
        drift. It is inline rather than fetched because the first frame of a
        visit is before any request of its own has been answered."""
        drawn = MARK.read_text(encoding="utf-8")
        inside = drawn[drawn.index("</title>") + len("</title>"):drawn.rindex("</svg>")]
        assert inside in self.shell()

    def test_the_mark_carries_no_second_name(self):
        """The brand file is an image in its own right, with a title and a
        label. Inlined inside something already named, those would be a
        second name for one thing, so they come off."""
        shell = self.shell()
        at = shell.index('id="launch-mark"')
        tag = shell[shell.rindex("<", 0, at):shell.index(">", at) + 1]
        assert 'aria-hidden="true"' in tag, tag
        assert "aria-label" not in tag, tag
        assert "<title>" not in shell[at:shell.index("</svg>", at)]

    def test_the_tagline(self):
        assert '<p id="launch-line">%s</p>' % TAGLINE in self.shell()

    def test_it_is_announced_as_the_mark_and_the_tagline(self):
        assert (
            '<div aria-label="Prelude. %s" id="launch" role="img">' % TAGLINE
        ) in self.shell()

    def test_the_tagline_is_hanken_grotesk(self):
        """The family the brand file sets it in, which is also the family the
        screens use for body copy."""
        block = self.shell().split("#launch-line {")[1].split("}")[0]
        assert '"Hanken Grotesk"' in block
        assert "font-weight: 500" in block
        assert "font-size: 16px" in block

    def test_the_tagline_is_the_amber(self):
        block = self.shell().split("#launch-line {")[1].split("}")[0]
        assert "color: #ffb703;" in block

    def test_the_mark_is_the_width_the_brand_file_draws_it(self):
        block = self.shell().split("#launch-mark {")[1].split("}")[0]
        assert "width: 300px;" in block

    def test_it_sits_on_the_app_background(self):
        block = self.shell().split("#launch {")[1].split("}")[0]
        assert "background-color: #101319;" in block
        assert "gap: 20px;" in block

    def test_it_claims_nothing(self):
        """Every word on it, which is the tagline and nothing else: the mark
        is a picture and carries no text at all."""
        shell = self.shell()
        start = shell.index('id="launch"')
        body = shell[start:shell.index("</div>", shell.index("launch-line"))]
        words = " ".join(body.split())
        for banned in ("LIVE", "Verified", "goal", "match", "narration"):
            assert banned.lower() not in words.lower(), banned

    def test_it_is_on_the_shell_and_on_no_screen(self):
        for path in sorted(WEB.glob("prelude_*.html")):
            text = path.read_text(encoding="utf-8")
            assert 'id="launch"' not in text, path.name
            assert TAGLINE not in text, path.name

    def test_the_fade_is_kept_for_a_fan_who_asked_for_less_motion(self):
        """An opacity fade is not motion, so there is no rule under
        `prefers-reduced-motion` and no branch in the script.

        The spec for Task 34 said no fade under `reduce` and that was wrong:
        nothing on this screen or on the list behind it moves, scales, slides
        or spins, and what a fan who asked for less motion got instead was a
        hard cut from the mark to the list, which is the one thing in the
        sequence that reads as a jolt. Shawn saw that cut on an iPhone XR on
        2026-11-15, with Reduce Motion on.
        """
        shell = self.shell()
        # No rule, and the reasoning is written down where the rule was.
        assert "@media (prefers-reduced-motion" not in shell
        assert "prefers-reduced-motion" in shell
        # And no branch: the script asked `matchMedia` and took the fade away.
        assert "matchMedia" not in shell
        assert "transition: opacity 300ms ease;" in shell

    def test_it_is_up_before_any_script_has_run(self):
        """The markup ships visible and nothing decides whether to paint it,
        so the frames before any script has run have it in them. It used to
        be decided in the head out of `sessionStorage`."""
        shell = self.shell()
        assert "html.launched" not in shell
        assert "prelude.launched" not in shell
        body = shell[shell.index('id="launch"'):]
        assert "hidden" not in body[:body.index(">")], body[:body.index(">")]

    def test_the_shell_reads_no_storage_at_all(self):
        """The one decision it used to make out of storage is gone, so a
        cleared, blocked or full storage changes nothing about this page.
        The words still appear in a comment, which is the point: what was
        there and why it went."""
        shell = self.shell()
        for call in ("sessionStorage.getItem", "sessionStorage.setItem",
                     "localStorage.getItem", "localStorage.setItem"):
            assert call not in shell, call

    def test_the_old_line_is_gone_from_every_screen(self):
        for path in sorted(WEB.glob("*.html")) + sorted(WEB.glob("*.js")):
            assert "Be there. Even when" not in path.read_text(encoding="utf-8"), path.name
