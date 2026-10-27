"""Tests for the persona config: its shape, its ids and its copy.

`app/personas.py` is configuration, so what there is to test is that it is
well formed and that it agrees with the two things that read it. The ids have
to be the ones `app/orchestrator_contract.py` declares, because the
orchestrator returns an id and a persona nothing can select is a typo nobody
would see. The copy has to obey the rules `CLAUDE.md` puts on app output,
because the Profile screen shows it.

Each test that is about all three personas loops over them and collects the
ones that failed, rather than being parametrized, so a failure names the
persona and the test keeps one node id a document can cite.

Nothing here calls a model, and nothing here asserts that a persona sounds
like anything. A voice and its prosody are judgements made by listening, which
is Phase 5, and the fields that will hold them are empty until then.
"""

import dataclasses
import re

import pytest

from app.grounding import BANNED_PATTERNS
from app.orchestrator import default_persona
from app.orchestrator_contract import (
    CALLER,
    MATE,
    NEUTRAL,
    STORYTELLER,
    TEAM_A,
    Listener,
)
from app.personas import (
    BY_ID,
    PERSONAS,
    THE_CALLER,
    THE_MATE,
    THE_STORYTELLER,
    available,
    persona,
)

#: The rules `CLAUDE.md` puts on app output that a line of copy can break.
#: Verdict nicknames and editorial epithets are the no-nicknames rule, and the
#: dashes are the no-em-dash rule. The "address to the reader" patterns are
#: deliberately left out: they exist because narration has no line spoken to
#: the fan, and Profile copy is nothing but lines spoken to the fan.
#: `scripts/scan_copy.py` scans the screens on the same footing.
OUTPUT_COPY_RULES = frozenset(
    {
        "verdict nickname",
        "editorial epithet",
        "unearned authority",
        "em dash",
        "en dash",
    }
)

#: The fields a persona carried while the prompt asked for a register. Both
#: are gone: the narration text is one text, `NARRATION_STYLE` in
#: `app/narration_prompt.py`, and a field here that nothing printed would read
#: as a register still reaching a model.
GONE_WITH_THE_REGISTER = ("style", "example")


class TestTheThreePersonas:
    """There are three, with the contract's ids, and nothing else."""

    def test_there_are_three(self):
        assert len(PERSONAS) == 3

    def test_the_ids_are_the_ones_the_contract_declares(self):
        assert {p.id for p in PERSONAS} == {CALLER, STORYTELLER, MATE}

    def test_each_id_appears_once(self):
        ids = [p.id for p in PERSONAS]
        assert len(set(ids)) == len(ids)

    def test_by_id_holds_every_persona(self):
        assert BY_ID == {p.id: p for p in PERSONAS}

    def test_the_three_are_the_caller_the_storyteller_and_the_mate(self):
        assert (THE_CALLER.id, THE_STORYTELLER.id, THE_MATE.id) == (
            CALLER,
            STORYTELLER,
            MATE,
        )


class TestEveryFieldIsFilled:
    """A persona with an empty field is a persona that cannot be used."""

    def test_every_name_and_profile_is_set(self):
        empty = [
            p.id for p in PERSONAS if not (p.name.strip() and p.profile.strip())
        ]
        assert empty == []

    def test_every_profile_is_one_line(self):
        wrapped = [p.id for p in PERSONAS if "\n" in p.profile]
        assert wrapped == []

    def test_no_persona_carries_prompt_copy(self):
        """A `style` or an `example` here would be a register again.

        Tasks 6c, 4b and 6d asked three models for three registers through
        those two fields and got one register back each time, so the
        narration text is one text and the separation moves to the audio.
        `docs/narration_eval.md` holds the numbers.
        """
        fields = {f.name for f in dataclasses.fields(PERSONAS[0])}
        assert fields.isdisjoint(GONE_WITH_THE_REGISTER)


class TestFansOnly:
    """The Mate is the only persona that needs the listener to have a side."""

    def test_only_the_mate_is_fans_only(self):
        assert {p.id for p in PERSONAS if p.fans_only} == {MATE}

    def test_a_fan_may_choose_any_of_the_three(self):
        assert available(fan=True) == PERSONAS

    def test_a_neutral_listener_is_not_offered_the_mate(self):
        assert MATE not in {p.id for p in available(fan=False)}
        assert len(available(fan=False)) == 2

    def test_the_default_for_a_neutral_listener_is_one_they_may_choose(self):
        """The orchestrator's default has to be in the config and selectable.

        `default_persona` in `app/orchestrator.py` returns an id, and nothing
        there reads this file. A default that was `fans_only` would hand a
        neutral listener a persona the Profile screen then refuses to show
        them, which is the one disagreement between the two that would not
        show up as an error.
        """
        chosen = persona(default_persona(Listener(allegiance=NEUTRAL)))
        assert chosen.fans_only is False

    def test_the_default_for_a_fan_is_in_the_config(self):
        chosen = persona(default_persona(Listener(allegiance=TEAM_A)))
        assert chosen in PERSONAS


class TestTheVoicesAreNotChosenYet:
    """Phase 5 picks a voice by ear. Until then the field is empty and says so."""

    def test_every_voice_is_null(self):
        assert [p.id for p in PERSONAS if p.voice is not None] == []

    def test_every_voice_is_marked_unconfirmed(self):
        assert [p.id for p in PERSONAS if p.voice_confirmed] == []

    def test_a_null_voice_is_never_confirmed(self):
        """The pair cannot say "confirmed nothing", which is the broken state.

        `voice_confirmed` is what stops an empty field being read as an
        oversight. A persona claiming a confirmed voice while holding none
        would be the field saying the opposite of the truth.
        """
        assert [
            p.id for p in PERSONAS if p.voice_confirmed and p.voice is None
        ] == []


class TestTheProsodyIsNotSetYet:
    """The four numbers that separate the voices, and they are empty too.

    Shawn sets them by ear in Phase 5: a rate, a pitch, and the pauses that
    let each sentence land. Comprehension comes first, so the Caller's energy
    is pitch and emphasis with a rate only modestly above the Storyteller's,
    and words per minute is measured from the real audio rather than guessed
    at here.
    """

    def test_every_prosody_field_is_null(self):
        assert [
            p.id for p in PERSONAS if any(v is not None for v in p.prosody)
        ] == []

    def test_every_persona_is_marked_unconfirmed(self):
        assert [p.id for p in PERSONAS if p.prosody_confirmed] == []

    def test_the_four_fields_are_the_prosody(self):
        """`prosody` is the four, in the order they are set.

        A caller asking whether a persona has a delivery yet asks once. If a
        fifth field is added, this is what says it has to join the tuple.
        """
        for p in PERSONAS:
            assert p.prosody == (
                p.rate, p.pitch, p.sentence_break, p.goal_break
            )

    def test_an_empty_prosody_is_never_confirmed(self):
        """The same broken state as a confirmed null voice, four fields over.

        They are set in one sitting, because a rate heard without the breaks
        around it is not a judgement anybody can make, so one flag covers the
        four and a true flag means all four are set.
        """
        assert [
            p.id
            for p in PERSONAS
            if p.prosody_confirmed and any(v is None for v in p.prosody)
        ] == []


class TestProfileCopy:
    """The Profile lines are app output, so `CLAUDE.md` governs them."""

    def test_no_verdict_nickname_or_epithet(self):
        hits = []
        for p in PERSONAS:
            copy = f"{p.name} {p.profile}".lower()
            hits += [
                f"{p.id}: {label} {pattern}"
                for label, pattern in BANNED_PATTERNS
                if label in OUTPUT_COPY_RULES and re.search(pattern, copy)
            ]
        assert hits == []

    def test_no_persona_is_named_after_a_person(self):
        """A name is a register, not a likeness.

        The three are named for what they do, which is what keeps the config
        from claiming a resemblance to a real broadcaster. "The" plus one
        common noun is the shape, and it is cheap to hold it to that.
        """
        odd = [
            p.name for p in PERSONAS if not re.fullmatch(r"The [A-Z][a-z]+", p.name)
        ]
        assert odd == []


class TestNoDashes:
    """No em dashes in the copy a fan reads. Nothing here is read by a model."""

    def test_no_em_or_en_dash_in_any_field(self):
        hits = []
        for p in PERSONAS:
            text = " ".join((p.name, p.profile))
            hits += [
                f"{p.id}: {name}"
                for name, dash in (("em dash", "—"), ("en dash", "–"))
                if dash in text
            ]
        assert hits == []


class TestLookup:
    """One way in, and a failure that names what exists."""

    def test_every_persona_is_found_by_its_id(self):
        assert [persona(p.id) for p in PERSONAS] == list(PERSONAS)

    def test_an_unknown_id_names_the_three_that_exist(self):
        with pytest.raises(KeyError) as failure:
            persona("commentator")
        message = str(failure.value)
        for known in (CALLER, STORYTELLER, MATE):
            assert known in message
