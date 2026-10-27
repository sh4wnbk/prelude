"""The three personas: who the narration sounds like.

A persona is a voice the same facts are said in. It changes nothing about what
may be said: `app/grounding.py` reads every narration against the facts it
cited whoever wrote it, and `BANNED_PATTERNS` refuses the same words in all
three. What a persona carries is the register, which is the one thing in this
app that is a matter of taste rather than of record.

**Inspired by styles, never named after anybody.** A persona is a description
of a register (play-by-play pace, documentary calm, a partisan friend), not an
impression of a broadcaster. Naming a real commentator would be claiming a
likeness this repo has no right to and no data for, and it would put a
judgement about a person into app output, which `CLAUDE.md` keeps out.

Each persona carries five things and one that is still empty:

| Field | What it is | Where it is read |
| ----- | ---------- | ---------------- |
| `id` | the id the orchestrator picks by | `app/orchestrator_contract.py` |
| `name` | what the Profile screen calls it | Task 7 |
| `profile` | one line describing it to a fan | Task 7 |
| `style` | the register, said to the model | `build_prompt` |
| `fans_only` | whether a neutral listener may pick it | Task 7 |
| `voice` | the IBM Text to Speech voice | Phase 5, and it is `None` |

**The ids come from the contract and are not spelled again here.** `CALLER`,
`STORYTELLER` and `MATE` are declared in `app/orchestrator_contract.py`,
because the orchestrator picks a default persona and had to name them before
this file existed. Importing them is what makes a typo here a failure at
import rather than a persona nothing can select.

**The voices are `None` and unconfirmed on purpose.** A voice is picked by ear
in Phase 5, by listening to each candidate say a narration and a name, and
nothing in this repo has listened to one yet. A plausible id written down now
would be a guess wearing the look of a decision, so the field is empty and
`voice_confirmed` says why: the pair means "not chosen", and it is only a
choice when both have moved.

**`style` is prompt copy and `profile` is app output.** They are checked
differently for that reason. `profile` is a line a fan reads, so the rules
`CLAUDE.md` puts on app output apply to it and
`tests/test_personas.py::TestProfileCopy` holds it to them. `style` is said to
a model, where naming a banned word is sometimes the only way to forbid it,
which is what rule 7 of the prompt in `app/narration_prompt.py` already does.
Scanning it for those words would refuse the instruction that keeps them out
of the narration.

Standard library only, like the rest of `app/`.
"""

from dataclasses import dataclass
from typing import Mapping

from app.orchestrator_contract import CALLER, MATE, STORYTELLER


@dataclass(frozen=True)
class Persona:
    """One voice the narration can be written in.

    `id` is the id in `app/orchestrator_contract.py`, which is what the
    orchestrator returns and what a stored preference holds. `name` and
    `profile` are the Profile screen's copy. `style` is the register as it is
    said to the model, and `build_prompt` prints it above the rules.

    `fans_only` is true for a persona that only makes sense to somebody with a
    side. It is the Mate and nothing else: a partisan voice told to a neutral
    listener would be telling them they support a team they did not choose.

    `example` is the register shown rather than described: a short narration
    of a passage that never happened, in that voice, cited the way a real one
    has to be. Task 4b found that what reached a capable model was the rules
    and not the prose, with all three voices writing the same narration, so
    the styles are given something to copy rather than something to
    interpret.

    **The example is of an invented passage, and that is not decoration.** It
    uses made-up players and made-up teams so that nothing in it can be
    mistaken for a fact about the match being narrated. A model that copies a
    name out of it is refused by `app/grounding.py` like any other invention,
    which makes the failure visible rather than silent.

    `voice` is the IBM Text to Speech voice id and is `None` until Phase 5
    picks one by ear. `voice_confirmed` is false while it is a guess or absent,
    so the two fields together say "not chosen yet" rather than leaving an
    empty field to be read as an oversight.
    """

    id: str
    name: str
    profile: str
    style: str
    example: str
    fans_only: bool
    voice: str | None = None
    voice_confirmed: bool = False


#: Play-by-play energy. The pace is in the sentences rather than in the tense:
#: a buildup already happened, and `app/grounding.py` refuses a present-tense
#: verb from this persona exactly as it does from the other two, so the style
#: says where the energy comes from instead of leaving the model to find it in
#: the one place it is not allowed to.
THE_CALLER = Persona(
    id=CALLER,
    name="The Caller",
    profile="Play-by-play pace: one action a line, keeping up with the move.",
    style=(
        "Write with the energy of a radio play-by-play call. Short lines, one "
        "action each, landing in the order the move did. The pace comes from "
        "how little each sentence carries, not from excitement about it: you "
        "are reading a record of a passage that has already finished, so keep "
        "every verb in the past tense. Name the player and what they did, and "
        "go straight to the next line. Do not say how good any of it was."
    ),
    example=(
        "[4] Quillan recovered it.\n"
        "[9] Brennick was dribbled past.\n"
        "[11] Tarrow was dribbled past.\n"
        "[12] Halloway shot and scored for Westhollow."
    ),
    fans_only=False,
)

#: Documentary calm. The plainest of the three, and the closest to the voice
#: `docs/VOICE.md` describes, which is why it is what a neutral listener gets
#: by default: `default_persona` in `app/orchestrator.py` returns it.
THE_STORYTELLER = Persona(
    id=STORYTELLER,
    name="The Storyteller",
    profile="Calm and unhurried: a documentary record of the passage.",
    style=(
        "Write in the calm, even voice of a documentary narrator. Measured "
        "sentences, told in the past tense, one step of the passage at a "
        "time. The facts carry it, so add no colour and no atmosphere the "
        "records do not hold: no weather, no crowd, no reading of anybody's "
        "intentions. Let the plainness be the register."
    ),
    example=(
        "[4] Quillan recovered the ball for Westhollow.\n"
        "[9] Brennick was dribbled past.\n"
        "[11] Tarrow was dribbled past.\n"
        "[12] Halloway shot and scored for Westhollow."
    ),
    fans_only=False,
)

#: Partisan, and the only persona that needs to know who is listening. The
#: listener's side is a prompt input for this one alone: `persona_block` in
#: `app/narration_prompt.py` prints it for a `fans_only` persona and for no
#: other, and `check` in `app/grounding.py` admits "we", "our" and "us" from
#: one, in a sentence citing at least one fact recorded against that side.
#:
#: **One cited fact, not every cited fact.** That is the same shape as a name
#: claim, which is grounded when some cited fact holds it. Requiring all of
#: them would refuse "[10, 11] We dribbled past Beardsley", which cites the
#: two records of one dribble and is true for an Argentina listener.
#:
#: "You" stays refused here as it is everywhere: the narration is not
#: addressed to the fan, which is what the ending rule in `docs/VOICE.md`
#: keeps out.
THE_MATE = Persona(
    id=MATE,
    name="The Mate",
    profile="Partisan and warm, like a friend in the next seat.",
    style=(
        "Write as a supporter sitting one seat along, telling a friend what "
        "they missed. Warm and partisan, in the past tense, and on the "
        "listener's side throughout. Call that side \"we\", \"our\" or "
        "\"us\", and only ever over a fact about that side: a sentence about "
        "the other team names them as the facts name them and never says "
        "\"we\". Do not speak to the listener: no \"you\" and no \"your\". "
        "Partisan is about whose side the telling is on, not about saying the "
        "goal was good, so still say only what the facts record."
    ),
    # Written for a listener on Westhollow. "We" and "our" stand for the side
    # and never sit beside a player's name: "We recovered it through
    # Quillan", never "We, Quillan, recovered it". A model given the second
    # writes the first person as a label on a name, which is what
    # `openai/gpt-oss-120b` did in Task 4b without an example to copy.
    #
    # "Recovered" rather than "won it back", which `app/grounding.py` reads
    # as a claim about a `Foul Won` event. The first draft of these examples
    # said "won it back" and
    # `tests/test_narration_prompt.py::TestTheWorkedExamples::test_each_example_passes_the_real_grounding_check`
    # refused it, which is the prompt being held to the rules it states.
    example=(
        "[4] We recovered it through Quillan.\n"
        "[9] Brennick was dribbled past.\n"
        "[11] Tarrow was dribbled past.\n"
        "[12] Halloway shot and scored for us."
    ),
    fans_only=True,
)

#: The three, in the order the Profile screen lists them.
PERSONAS: tuple[Persona, ...] = (THE_CALLER, THE_STORYTELLER, THE_MATE)

#: By id, which is how every caller reaches one: the orchestrator returns an
#: id, and a stored preference holds one.
BY_ID: Mapping[str, Persona] = {persona.id: persona for persona in PERSONAS}


def persona(persona_id: str) -> Persona:
    """The persona with this id, or `KeyError` naming the three that exist.

    An unknown id is a bug rather than a thing to recover from: there are
    three personas, they are declared here, and a caller holding a fourth id
    read it from somewhere that has drifted.
    """
    try:
        return BY_ID[persona_id]
    except KeyError:
        known = ", ".join(sorted(BY_ID))
        raise KeyError(
            f"{persona_id!r} is not a persona; the three are {known}"
        ) from None


def available(fan: bool) -> tuple[Persona, ...]:
    """The personas a listener may choose from.

    A fan may choose any of the three. A neutral listener may not choose a
    `fans_only` persona, because there is no side for it to be partisan
    about. This is what the Profile screen in Task 7 lists, and it is here
    rather than there so the rule has one home.
    """
    if fan:
        return PERSONAS
    return tuple(p for p in PERSONAS if not p.fans_only)
