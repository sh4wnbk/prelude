"""Tests for the narration pipeline: generate, check, retry, fall back.

No model is called. A `Script` provider returns lines written in the test, which
is what lets a test say "the model drifts twice and then behaves" and assert on
what the pipeline did about it. `tests/conftest.py` fails any test that opens a
connection, so the no-network guarantee does not rest on these stubs being used
correctly.

The rule under test is whole-narration. A failing line is not dropped, because
a narration with a hole in it tells a different story: a run recorded as past
one defender, then another, then the goalkeeper reads as something else with
the middle removed. Nor is a failing line kept unlabelled. The whole narration
fails together, is regenerated, and falls back to the template if it keeps
failing.

Narration carries a citation tag per sentence, which is what the check reads.
The tags come off before anything is shown or voiced, so `Narrated.text` is the
stripped paragraph and `Narrated.tagged_text` is what passed the check.
"""

import pytest

from app.narration import (
    GROUNDING_LABEL,
    MAX_RETRIES,
    MODEL,
    TEMPLATE,
    NarrationNotGrounded,
    narrate,
    pass_rate,
)
from app.grounding import strip_citations
from app.narration_prompt import facts_from_buildup, template_narration
from app.narration_provider import Narration
from app.statsbomb_event_feed import StatsBombEventFeed

MATCH_1986 = 3750191
GOAL_1986 = (54, 18)

# Narration as a model writes it, each sentence citing the facts it used. Fact
# 22 is Maradona's last Dribble and fact 24 is his shot; the numbers are read
# out of data/raw/ and written down, like the ones in tests/test_grounding.py.
GROUNDED = "Maradona dribbles and shoots, and scores for Argentina. [22, 24]"
INVENTED_PLAYER = "Maradona passes to Valdano, who scores for Argentina. [6, 7]"
INVENTED_PENALTY = "Maradona scores the penalty for Argentina. [24]"
SAYS_NOTHING = "He turns away from two, then goes again. [8]"

# The same narration as it is shown and voiced.
GROUNDED_SHOWN = "Maradona dribbles and shoots, and scores for Argentina."


class Script:
    """A narration provider that reads from a list written in the test.

    Satisfies the same interface as the real backends. It records the prompts
    it was given, so a test can check the pipeline asked the same question each
    time rather than quietly changing it between retries.
    """

    name = "script"
    model = "script"

    def __init__(self, *lines: str):
        self._lines = list(lines)
        self.prompts: list[str] = []

    def narrate(self, prompt: str) -> Narration:
        self.prompts.append(prompt)
        if not self._lines:
            raise AssertionError("the pipeline asked for more attempts than expected")
        return Narration(
            text=self._lines.pop(0), provider=self.name, model=self.model
        )


@pytest.fixture(scope="module")
def feed():
    return StatsBombEventFeed()


@pytest.fixture(scope="module")
def moment(feed):
    return next(
        m for m in feed.defining_moments(MATCH_1986)
        if (m.minute, m.second) == GOAL_1986
    )


def narrate_with(feed, moment, *lines, **kwargs):
    provider = Script(*lines)
    result = narrate(feed, MATCH_1986, moment, narration_provider=provider, **kwargs)
    return result, provider


class TestFirstAttemptPasses:
    def test_it_keeps_the_model_narration(self, feed, moment):
        narrated, provider = narrate_with(feed, moment, GROUNDED)
        assert narrated.text == GROUNDED_SHOWN
        assert narrated.tagged_text == GROUNDED
        assert narrated.source == MODEL
        assert not narrated.used_fallback
        assert len(provider.prompts) == 1

    def test_it_is_labelled(self, feed, moment):
        narrated, _ = narrate_with(feed, moment, GROUNDED)
        assert narrated.labelled
        assert narrated.label == GROUNDING_LABEL == "Verified from play data"

    def test_one_attempt_is_recorded_and_it_passed(self, feed, moment):
        narrated, _ = narrate_with(feed, moment, GROUNDED)
        assert len(narrated.attempts) == 1
        assert narrated.attempts[0].grounded
        assert narrated.attempts[0].failures == ()
        assert narrated.first_attempt_grounded
        assert narrated.failure_log == ()


class TestRetries:
    def test_a_failing_narration_is_regenerated_whole(self, feed, moment):
        """Not repaired, not trimmed: asked for again."""
        narrated, provider = narrate_with(feed, moment, INVENTED_PLAYER, GROUNDED)
        assert narrated.text == GROUNDED_SHOWN
        assert narrated.source == MODEL
        assert len(provider.prompts) == 2
        assert provider.prompts[0] == provider.prompts[1]

    def test_no_part_of_a_failing_narration_survives(self, feed, moment):
        """The failing attempt is recorded, never spliced into the result."""
        narrated, _ = narrate_with(feed, moment, INVENTED_PLAYER, GROUNDED)
        assert "Valdano" not in narrated.text
        assert narrated.attempts[0].text == INVENTED_PLAYER

    def test_the_first_attempt_is_still_marked_failed(self, feed, moment):
        """A retry must not hide that the first attempt drifted."""
        narrated, _ = narrate_with(feed, moment, INVENTED_PLAYER, GROUNDED)
        assert not narrated.first_attempt_grounded
        assert narrated.attempts[0].number == 1

    def test_it_retries_at_most_twice(self, feed, moment):
        """Three attempts in all, which is what MAX_RETRIES means."""
        narrated, provider = narrate_with(
            feed, moment, INVENTED_PLAYER, INVENTED_PENALTY, SAYS_NOTHING
        )
        assert MAX_RETRIES == 2
        assert len(provider.prompts) == 3
        assert narrated.used_fallback

    def test_the_retry_budget_can_be_set(self, feed, moment):
        narrated, provider = narrate_with(
            feed, moment, INVENTED_PLAYER, GROUNDED, max_retries=0
        )
        assert len(provider.prompts) == 1
        assert narrated.used_fallback


class TestFallback:
    def test_it_falls_back_after_the_retries_are_spent(self, feed, moment):
        narrated, _ = narrate_with(
            feed, moment, INVENTED_PLAYER, INVENTED_PENALTY, SAYS_NOTHING
        )
        assert narrated.source == TEMPLATE
        assert narrated.used_fallback

    def test_the_fallback_is_the_template_narration(self, feed, moment):
        facts = facts_from_buildup(feed.buildup(MATCH_1986, moment))
        narrated, _ = narrate_with(
            feed, moment, INVENTED_PLAYER, INVENTED_PENALTY, SAYS_NOTHING
        )
        assert narrated.tagged_text == template_narration(facts)
        assert narrated.text == strip_citations(template_narration(facts))

    def test_the_fallback_is_checked_like_any_other_narration(self, feed, moment):
        """"Grounded by construction" is a claim worth testing, so the pipeline
        runs the check over the fallback too and records the result."""
        narrated, _ = narrate_with(
            feed, moment, INVENTED_PLAYER, INVENTED_PENALTY, SAYS_NOTHING
        )
        last = narrated.attempts[-1]
        assert last.source == TEMPLATE
        assert last.grounded
        assert last.number == 4

    def test_the_fallback_is_labelled(self, feed, moment):
        narrated, _ = narrate_with(
            feed, moment, INVENTED_PLAYER, INVENTED_PENALTY, SAYS_NOTHING
        )
        assert narrated.labelled
        assert narrated.label == GROUNDING_LABEL

    def test_nothing_ungrounded_is_ever_returned(self, feed, moment):
        """The point of the whole module. Whatever the model does, the text
        that comes back passed the check.

        The cited version is what is re-checked. The stripped paragraph cannot
        pass, because a sentence with no citation has nothing to be read
        against, which is why both are kept.
        """
        from app.grounding import check

        facts = facts_from_buildup(feed.buildup(MATCH_1986, moment))
        for lines in (
            (GROUNDED,),
            (INVENTED_PLAYER, GROUNDED),
            (INVENTED_PLAYER, INVENTED_PENALTY, GROUNDED),
            (INVENTED_PLAYER, INVENTED_PENALTY, SAYS_NOTHING),
        ):
            narrated, _ = narrate_with(feed, moment, *lines)
            assert check(narrated.tagged_text, facts).grounded, narrated.tagged_text

    def test_an_ungroundable_fallback_raises_rather_than_voicing_it(
        self, feed, moment, monkeypatch
    ):
        """If the fallback itself ever failed, there would be nothing safe to
        say, so this raises instead of handing back something unlabelled."""
        monkeypatch.setattr(
            "app.narration.template_narration",
            lambda facts: "Valdano scores the penalty of the century. [24]",
        )
        with pytest.raises(NarrationNotGrounded) as raised:
            narrate_with(
                feed, moment, INVENTED_PLAYER, INVENTED_PENALTY, SAYS_NOTHING
            )
        assert "nothing safe to voice" in str(raised.value)


class TestCitations:
    """The tags are machinery for the check, not copy.

    `CLAUDE.md` governs what the app says, and "[22, 24]" is not something a
    screen displays or a voice reads aloud, so it comes off before either. What
    passed the check is kept beside it, because that is the version a reader can
    audit sentence by sentence.
    """

    def test_the_narration_that_is_shown_carries_no_tags(self, feed, moment):
        for lines in (
            (GROUNDED,),
            (INVENTED_PLAYER, GROUNDED),
            (INVENTED_PLAYER, INVENTED_PENALTY, SAYS_NOTHING),
        ):
            narrated, _ = narrate_with(feed, moment, *lines)
            assert "[" not in narrated.text, narrated.text
            assert "]" not in narrated.text, narrated.text

    def test_the_narration_that_is_shown_is_one_paragraph(self, feed, moment):
        """The prompt asks for one sentence per line, which is how the tags are
        read. The voice does not want the line breaks."""
        narrated, _ = narrate_with(
            feed, moment, INVENTED_PLAYER, INVENTED_PENALTY, SAYS_NOTHING
        )
        assert "\n" not in narrated.text
        assert narrated.text.startswith(f"Minute {moment.minute}.")

    def test_the_cited_version_is_kept(self, feed, moment):
        narrated, _ = narrate_with(feed, moment, GROUNDED)
        assert narrated.tagged_text == GROUNDED
        assert strip_citations(narrated.tagged_text) == narrated.text

    def test_an_attempt_is_recorded_as_the_model_wrote_it(self, feed, moment):
        """A failure report has to be recognisable against what was checked."""
        narrated, _ = narrate_with(feed, moment, INVENTED_PLAYER, GROUNDED)
        assert narrated.attempts[0].text == INVENTED_PLAYER


class TestFailureLog:
    def test_every_failure_is_recorded_with_its_claims(self, feed, moment):
        narrated, _ = narrate_with(
            feed, moment, INVENTED_PLAYER, INVENTED_PENALTY, GROUNDED
        )
        assert len(narrated.failure_log) == 2
        assert "Valdano" in narrated.failure_log[0]
        assert "Open Play" in narrated.failure_log[1]

    def test_the_log_names_the_claim_kind(self, feed, moment):
        narrated, _ = narrate_with(feed, moment, INVENTED_PENALTY, GROUNDED)
        assert "shot_type" in narrated.attempts[0].summary

    def test_a_grounded_run_logs_no_failures(self, feed, moment):
        narrated, _ = narrate_with(feed, moment, GROUNDED)
        assert narrated.failure_log == ()

    def test_every_attempt_is_numbered_in_order(self, feed, moment):
        narrated, _ = narrate_with(
            feed, moment, INVENTED_PLAYER, INVENTED_PENALTY, SAYS_NOTHING
        )
        assert [a.number for a in narrated.attempts] == [1, 2, 3, 4]
        assert [a.source for a in narrated.attempts] == [MODEL] * 3 + [TEMPLATE]


class TestPassRate:
    def test_it_counts_first_attempts_only(self, feed, moment):
        """A rate that counted retries would say the model is doing better
        than it is, which is the number Task 4 reports."""
        straight = narrate_with(feed, moment, GROUNDED)[0]
        retried = narrate_with(feed, moment, INVENTED_PLAYER, GROUNDED)[0]
        fell_back = narrate_with(
            feed, moment, INVENTED_PLAYER, INVENTED_PENALTY, SAYS_NOTHING
        )[0]

        assert pass_rate([straight]) == (1, 1)
        assert pass_rate([retried]) == (0, 1)
        assert pass_rate([straight, retried, fell_back]) == (1, 3)

    def test_a_retried_narration_is_not_counted_as_a_pass(self, feed, moment):
        retried = narrate_with(feed, moment, INVENTED_PLAYER, GROUNDED)[0]
        assert retried.text == GROUNDED_SHOWN
        assert not retried.first_attempt_grounded
        assert pass_rate([retried]) == (0, 1)
