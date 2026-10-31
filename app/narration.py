"""Narrate one moment: generate, check, retry, and fall back if it still drifts.

The rule this implements is whole-narration, not per-line. A line that fails
the grounding check does not get dropped, because a narration with a hole in it
tells a different story: a run recorded as past one defender, then another,
then the goalkeeper reads as something else entirely with the middle removed.
Nor does a failing line get kept unlabelled, because the app says only what the
play data proves. So the whole narration fails together.

What happens then:

1. The narration is generated and checked.
2. If it is not grounded, it is generated again, up to `MAX_RETRIES` times.
3. If it still is not grounded, the fallback in `app/narration_prompt.py`
   assembles a short plain narration straight from the events. That is grounded
   by construction, and it is checked anyway.
4. Nothing ungrounded is ever returned as narration or labelled.

Every attempt is recorded, with the claims that failed, so a model that drifts
leaves a trace. `Narrated.first_attempt_grounded` is the one a pass rate should
be measured on: counting retries would hide how often the first attempt was
wrong, which is the number that says whether the prompt and the model are
working.

The narration a model writes carries a citation tag per sentence, naming the
facts that sentence used, and the check needs them. They are machinery, not
copy, so `Narrated.text` has them stripped and is what a screen shows and a
voice reads; `Narrated.tagged_text` keeps the cited version, which is the one
the check passed and the one a reader can audit sentence by sentence.

The fallback is the last resort, and if it somehow fails the check too, this
raises rather than returning something unlabelled. There is no path here that
hands back narration the data does not support.
"""

from dataclasses import dataclass
from typing import Sequence

from app.event_feed import EventFeed, Moment
from app.grounding import Claim, check, strip_citations
from app.narration_prompt import (
    DEFAULT_SENTENCES,
    build_prompt,
    facts_from_buildup,
    template_narration,
)
from app.narration_provider import NarrationProvider, provider as default_provider
from app.recorded_names import recorded_nicknames
from app.personas import Persona

#: Regenerations allowed after the first attempt, so three attempts at most.
MAX_RETRIES = 2

#: What produced a narration.
MODEL = "model"
TEMPLATE = "template"

#: The label `CLAUDE.md` governs. Written once, here, so no caller spells it
#: differently or softens it.
GROUNDING_LABEL = "Verified from play data"


class NarrationNotGrounded(RuntimeError):
    """Even the fallback failed the grounding check.

    This should not happen: the fallback copies its every name, number and
    action out of the events. If it is raised, either the fallback or the check
    has a bug, and the right response is to fix it rather than to voice
    something unverified.
    """


@dataclass(frozen=True)
class Attempt:
    """One go at narrating a moment, grounded or not.

    `number` counts from 1. `source` is `MODEL` or `TEMPLATE`. `text` is the
    attempt exactly as it was written, citation tags included, because that is
    what was checked and a failure report has to be recognisable against it.
    `failures` is empty when the attempt was grounded, and otherwise holds every
    claim that could not be pointed at.
    """

    number: int
    source: str
    text: str
    grounded: bool
    failures: tuple[Claim, ...]

    @property
    def summary(self) -> str:
        if self.grounded:
            return f"attempt {self.number} ({self.source}): grounded"
        return (
            f"attempt {self.number} ({self.source}): not grounded, "
            + "; ".join(str(failure) for failure in self.failures)
        )


@dataclass(frozen=True)
class Narrated:
    """The narration for one moment, and the record of how it was arrived at.

    `text` is the narration to show and to voice: one paragraph, with the
    citation tags taken off. `tagged_text` is the same narration as it was
    checked, each sentence still naming the facts it used, which is what an
    audit of a line reads.

    `labelled` says whether the text may carry "Verified from play data". It is
    true whenever there is text at all, because nothing ungrounded is returned;
    it is kept as a field so a caller reads the permission rather than assuming
    it.
    """

    moment: Moment
    text: str
    tagged_text: str
    source: str
    labelled: bool
    attempts: tuple[Attempt, ...]

    @property
    def first_attempt_grounded(self) -> bool:
        """Whether the first attempt passed. The pass-rate number."""
        return self.attempts[0].grounded

    @property
    def used_fallback(self) -> bool:
        return self.source == TEMPLATE

    @property
    def label(self) -> str:
        """The grounding label, or an empty string if it is not earned."""
        return GROUNDING_LABEL if self.labelled else ""

    @property
    def failure_log(self) -> tuple[str, ...]:
        """Every attempt that failed, with its claims. For the record."""
        return tuple(a.summary for a in self.attempts if not a.grounded)


def narrate(
    feed: EventFeed,
    match_id: int,
    moment: Moment,
    narration_provider: NarrationProvider | None = None,
    sentences: int = DEFAULT_SENTENCES,
    max_retries: int = MAX_RETRIES,
    persona: Persona | None = None,
    side: str | None = None,
    beats: bool = True,
    hero: bool = False,
) -> Narrated:
    """Narrate `moment`, returning grounded text or raising.

    `narration_provider` defaults to the one `app/narration_provider.py`
    chooses, which is Ollama. Pass one in to use a different backend or, in a
    test, to replay a recorded response.

    `persona` is the voice, from `app/personas.py`, and `side` is the team the
    listener is on. Both go to the check and neither goes to the prompt: the
    narration text is one text in every voice, and the persona decides how it
    is spoken in Phase 5. What the check does with them is admit the first
    person from a partisan voice over that side's facts, which is a guard
    rather than something the prompt asks for; a partisan persona with no side
    raises there.

    `hero` asks the prompt for the shape the recordings speak: the whole move
    in order naming every player who touched the ball, the clock once at the
    start, and a last sentence that says the shot scored. It is off
    everywhere but `scripts/freeze_narrations.py` and the candidate run
    behind it, because the pass rates in `docs/narration_eval.md` were
    measured without it. It reaches the prompt and not the check: all three
    of those are things `app/grounding.py` already accepted, which
    `tests/test_grounding.py::TestTheHeroShape` holds it to.

    **The names are the recorded ones, short where a short one is recorded.**
    The facts print `player_nickname` from the lineups file wherever it holds
    one, so the prompt asks for "Lionel Messi" rather than "Lionel Andrés
    Messi Cuccittini". A player the file records no nickname for keeps their
    full name: see `app/recorded_names.py`, which also says why no surname is
    picked out of a full name here.

    `beats` prints the key beats of the passage in the prompt. It is true
    everywhere but in one arm of the paid comparison, which measures what the
    block costs on a model that may not need it: Task 4c added it because
    `granite4:micro` would not reach the beats without it, and that is a
    statement about a three billion parameter model rather than about every
    model.

    **The fallback is not the model's narration.** It is assembled by code
    out of the facts, sentence per fact, so a narration that reaches it is not
    what the model wrote. It is still checked, because the check is what
    decides whether anything may be labelled, and
    `scripts/narration_eval.py` counts a fallback as a failure for that
    reason rather than as a narration the model produced.
    """
    facts = facts_from_buildup(
        feed.buildup(match_id, moment), recorded_nicknames(match_id)
    )
    chosen = narration_provider or default_provider()
    prompt = build_prompt(
        facts, sentences=sentences, beats=beats, hero=hero
    )

    attempts: list[Attempt] = []
    for number in range(1, max_retries + 2):
        text = chosen.narrate(prompt).text.strip()
        result = check(text, facts, persona=persona, side=side)
        attempts.append(
            Attempt(
                number=number,
                source=MODEL,
                text=text,
                grounded=result.grounded,
                failures=result.failures,
            )
        )
        if result.grounded:
            return _narrated(moment, text, MODEL, attempts)

    fallback = template_narration(facts)
    result = check(fallback, facts, persona=persona, side=side)
    attempts.append(
        Attempt(
            number=len(attempts) + 1,
            source=TEMPLATE,
            text=fallback,
            grounded=result.grounded,
            failures=result.failures,
        )
    )
    if not result.grounded:
        raise NarrationNotGrounded(
            "the fallback narration failed the grounding check, so there is "
            "nothing safe to voice for this moment: " + result.summary
        )
    return _narrated(moment, fallback, TEMPLATE, attempts)


def _narrated(
    moment: Moment, text: str, source: str, attempts: Sequence[Attempt]
) -> Narrated:
    """Wrap the narration that passed, stripped for showing and kept for audit.

    `text` is what passed the check with its citations taken off. Nothing is
    re-checked here: the stripped text cannot pass the check, because a sentence
    with no citation has nothing to be read against, which is why the tagged
    version is the one kept beside it.
    """
    return Narrated(
        moment=moment,
        text=strip_citations(text),
        tagged_text=text,
        source=source,
        labelled=True,
        attempts=tuple(attempts),
    )


def pass_rate(narrations: Sequence[Narrated]) -> tuple[int, int]:
    """(first attempts grounded, total) across several narrations.

    First attempts only, on purpose. A rate that counted retries would say the
    model is doing better than it is.
    """
    grounded = sum(1 for n in narrations if n.first_attempt_grounded)
    return grounded, len(narrations)
