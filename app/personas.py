"""The three personas: what the narration sounds like.

A persona is a sound. It changes nothing about what may be said and nothing
about how the words are written: `app/grounding.py` reads every narration
against the facts it cited whoever asked for it, and
`NARRATION_STYLE` in `app/narration_prompt.py` is the one style every
narration is written in. What a persona carries is the delivery, which is the
one thing in this app that is a matter of taste rather than of record.

**The personas are separated by sound because text did not separate them.**
Three measured attempts are in `docs/narration_eval.md`: the register
described to `granite4:micro` (Task 6c), the register described to
`openai/gpt-oss-120b` (Task 4b), and the register shown to it as a worked
example (Task 6d). Words per sentence spread 0.6, 2.1 and 1.9 across the
voices, and on the 54:18 goal the three wrote the same five sentences. The
grounding rules are narrow enough that there is no room for a writing style
inside them, so the style field and the worked examples are gone and Phase 5
separates the voices in the audio instead.

**Comprehension comes first.** The Caller is the quick one, and its energy
comes from emphasis and pitch rather than from speed: the rate sits only
modestly above the Storyteller's and has a ceiling. Breaks between sentences
let each beat land, with a slightly longer one before the goal sentence. The
numbers are set by ear in Phase 5, words per minute is measured from the real
audio, and the measured ceiling goes into config.

Each persona carries four things and five that are still empty:

| Field | What it is | Where it is read |
| ----- | ---------- | ---------------- |
| `id` | the id the orchestrator picks by | `app/orchestrator_contract.py` |
| `name` | what the Profile screen calls it | Task 7 |
| `profile` | one line describing the voice to a fan | Task 7 |
| `fans_only` | whether a neutral listener may pick it | Task 7 |
| `voice` | the IBM Text to Speech voice | Phase 5, and it is `None` |
| `rate` | the SSML speaking rate | Phase 5, and it is `None` |
| `pitch` | the SSML pitch | Phase 5, and it is `None` |
| `sentence_break` | the pause between sentences | Phase 5, and it is `None` |
| `goal_break` | the pause before the goal sentence | Phase 5, and it is `None` |

**The ids come from the contract and are not spelled again here.** `CALLER`,
`STORYTELLER` and `MATE` are declared in `app/orchestrator_contract.py`,
because the orchestrator picks a default persona and had to name them before
this file existed. Importing them is what makes a typo here a failure at
import rather than a persona nothing can select.

**The five empty fields are empty on purpose.** A voice is picked by ear in
Phase 5, by listening to each candidate say a narration and a name, and the
prosody is set the same way; nothing in this repo has listened to one yet. A
plausible value written down now would be a guess wearing the look of a
decision, so the fields are empty and `voice_confirmed` and
`prosody_confirmed` say why: a pair means "not chosen", and it is only a
choice when both have moved.

**`profile` is app output.** It is a line a fan reads, so the rules
`CLAUDE.md` puts on app output apply to it and
`tests/test_personas.py::TestProfileCopy` holds it to them. Nothing in this
file is said to a model any more, which is what the style field was.

Standard library only, like the rest of `app/`.
"""

from dataclasses import dataclass
from typing import Mapping

from app.orchestrator_contract import CALLER, MATE, STORYTELLER


@dataclass(frozen=True)
class Persona:
    """One voice the narration can be spoken in.

    `id` is the id in `app/orchestrator_contract.py`, which is what the
    orchestrator returns and what a stored preference holds. `name` and
    `profile` are the Profile screen's copy, and `profile` describes a sound
    rather than a way of writing: the narration text is the same in all three.

    `fans_only` is true for a persona that only makes sense to somebody with a
    side. It is the Mate and nothing else: a partisan voice told to a neutral
    listener would be telling them they support a team they did not choose.

    `voice` is the IBM Text to Speech voice id. `rate` and `pitch` are SSML
    prosody values as that markup writes them, such as a percentage; it is a
    string because that is what goes into the attribute. `sentence_break` and
    `goal_break` are pauses in milliseconds, so the one before the goal can be
    read against the one between sentences rather than compared as text.

    All five are `None` until Phase 5 sets them by ear. `voice_confirmed`
    covers the voice and `prosody_confirmed` covers the four prosody fields,
    which are set together in one sitting: a rate heard without the breaks
    around it is not a judgement anybody can make. A flag that is false says
    the fields beside it are not chosen rather than overlooked.
    """

    id: str
    name: str
    profile: str
    fans_only: bool
    voice: str | None = None
    rate: str | None = None
    pitch: str | None = None
    sentence_break: int | None = None
    goal_break: int | None = None
    voice_confirmed: bool = False
    prosody_confirmed: bool = False

    @property
    def prosody(self) -> tuple[str | None, str | None, int | None, int | None]:
        """The four prosody fields, in the order they are set.

        One accessor so a caller that wants to know whether this persona has
        a delivery yet asks once rather than naming four fields, and so
        `prosody_confirmed` has something to be about.
        """
        return (self.rate, self.pitch, self.sentence_break, self.goal_break)


#: The quick one. Its energy is emphasis and pitch rather than speed: a rate
#: far above the Storyteller's would cost a listener the names and the clock,
#: which are the whole of what the narration carries, so Phase 5 gives this
#: one a ceiling.
THE_CALLER = Persona(
    id=CALLER,
    name="The Caller",
    profile="Quick play-by-play, keeping up with the move.",
    fans_only=False,
)

#: The plainest of the three, and the closest to the voice `docs/VOICE.md`
#: describes, which is why it is what a neutral listener gets by default:
#: `default_persona` in `app/orchestrator.py` returns it. Its rate is the one
#: the other two are set against.
THE_STORYTELLER = Persona(
    id=STORYTELLER,
    name="The Storyteller",
    profile="Calm documentary, unhurried and even.",
    fans_only=False,
)

#: The only persona that needs to know who is listening. It is the fans'
#: default, and `app/grounding.py` still admits "we", "our" and "us" from a
#: partisan voice in a sentence citing at least one fact recorded against that
#: side. Nothing asks a model for the first person any more: the prompt
#: refuses it in every voice, and that rule in the check is the guard behind
#: it rather than a permission anything uses.
THE_MATE = Persona(
    id=MATE,
    name="The Mate",
    profile="Warm, from the next seat.",
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
