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

Nothing here calls a model, and nothing here asserts that a style produces a
particular register. What a persona sounds like is a judgement made by reading
narration, which is what `scripts/narration_eval.py` is for.
"""

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

#: Words below this and a style is a label rather than a register, which is
#: the one way that field can be present and useless.
STYLE_MIN_WORDS = 20


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

    def test_every_style_says_something(self):
        thin = [
            p.id for p in PERSONAS if len(p.style.split()) < STYLE_MIN_WORDS
        ]
        assert thin == []

    def test_every_profile_is_one_line(self):
        wrapped = [p.id for p in PERSONAS if "\n" in p.profile]
        assert wrapped == []

    def test_every_example_is_a_cited_narration(self):
        """Shown rather than described, in the layout the prompt asks for.

        An example without citations would be the prompt showing a model the
        one shape `app/grounding.py` refuses outright.
        """
        wrong = []
        for persona in PERSONAS:
            lines = [l for l in persona.example.splitlines() if l.strip()]
            if len(lines) < 2 or not all(
                re.match(r"\s*\[\d+\]", line) for line in lines
            ):
                wrong.append(persona.id)
        assert wrong == []


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
    """No em dashes anywhere, in the copy a fan reads or the copy a model does."""

    def test_no_em_or_en_dash_in_any_field(self):
        hits = []
        for p in PERSONAS:
            text = " ".join((p.name, p.profile, p.style, p.example))
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
