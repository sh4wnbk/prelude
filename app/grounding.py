"""The grounding check: can every claim in a narration be pointed at?

`CLAUDE.md` allows "Verified from play data" only over narration whose claims
trace back to the event data, and says there is no partial credit. This module
is what decides that. It takes a narration and the `Facts` it was written from,
pulls out the claims each sentence makes, and reports the ones that cannot be
pointed at.

**There are two readings, and the narration's own shape picks one.**

The first is the cited reading. `app/narration_prompt.py` gives the model a
numbered list, one plain fact per recorded event, and the prompt requires every
sentence to carry the numbers of the facts it used:

    [14, 15] Maradona dribbled past Terry Butcher.

Those numbers are what the cited reading checks against. A sentence is read
against the facts it cited, not against the buildup as a lump, and
`strip_citations` takes the tags off again before anything is shown or voiced.

The second is the goal-call reading, for a narration that carries no tag at
all. `docs/VOICE.md` settles that a Prelude narration is the recap stage of a
goal call, and a goal call has no numbers in it:

    Cuciuffo's recovery started the counter, and Enrique played it to Maradona
    just inside his own half, who carried it forward under pressure past
    Beardsley, Butcher and Fenwick and took it into the box, where he went
    around Peter Shilton and scored with his left foot.

So the sentence itself is read, by `app/narration_grammar.py`: the names, the
pronoun that means the player with the ball, the chains ("Molina to
MacAllister"), "past X", and the recorded fields a goal call says out loud. The
eight narrations that are the standard are in
`tests/test_reference_narrations.py`.

`check` picks the reading by looking for a citation tag, which is a property of
the text rather than an argument, so one narration is never read both ways.
Both readings refuse the same nicknames, epithets, force words, outcome claims,
dashes and markup, and hold the same present-tense rule. What they differ on is
how a claim is traced to a record, the clock, which the goal call does not
carry at all, the rule about where an exclamation mark may stand, which is the
goal call's, and the reaction layer, which only the goal call has.

**A goal call has two layers and this checks one of them.** The play is
traced to the records, claim by claim, and is the whole of what the eight
references are. The reaction is the narrator feeling the moment ("Oh,
lovely!", "What a finish!", and for the side that conceded "Ah, no."), it
stands once and only at the goal, and nothing in it is traced to a record
because nothing in it points at one: `REACTION_WORDS` has the shape test and
the reasoning. Every other rule here still applies to it, so a verdict, a
force word, "you", a clock or a cheer from a voice that does not cheer is
refused in a reaction exactly as in the play.

**A persona changes the delivery and not the rules.** `check` takes the
persona the narration was asked for and the side the listener is on, and the
one difference they make is the first person: a partisan persona may say "we"
over a fact about that side and no voice may say it anywhere else. Everything
below reads the same narration the same way whoever wrote it.

**That first-person rule is a guard rather than a permission in use.** The
prompt in `app/narration_prompt.py` asks for one style in every voice and
refuses the first person in all of them, so nothing now asks a model for
"we". The rule stays because a model that writes it anyway has to be caught,
and catching it needs to know whose side the word could be about.

**It is all past tense, and it ends on the goal.** A buildup is playback of a
passage that already happened, so the facts are written in the past tense and a
present-tense verb in a narration is refused rather than grounded. The last
sentence has to cite the goal's shot, because nothing follows the goal: there is
no closing line addressed to the fan. `docs/VOICE.md` carries both decisions.

**What it checks.** A claim is something a sentence asserts that the records can
confirm or refuse:

| Kind | A sentence claiming it | Grounded when |
| ---- | ---------------------- | ------------- |
| `name` | a capitalised word | it is a player or team name in a cited fact |
| `number` | a bare digit | it is a cited fact's minute, or the goal's second |
| `clock` | "54:13" | it is the clock of a cited fact |
| `action` | "passed", "dribbled", "cleared" | a cited fact records that event type |
| `pairing` | a name and an action together | one cited fact holds both |
| `shot_type` | "penalty", "free kick", "corner" | the goal shot is recorded as that |
| `body_part` | "header", "left foot" | the goal shot is recorded as that |
| `tense` | "dribbles", "is dribbled past" | never; the buildup already happened |
| `ending` | a last sentence not citing the goal | never; the narration ends on the goal |
| `untagged` | a sentence citing nothing | never; every sentence cites its facts |
| `citation` | a number that is not a fact | never |
| `banned` | a nickname, a verdict, force, a dash, markup | never; these are refused outright |
| `first person` | "we", "our", "us" | never, unless the persona is partisan |
| `side` | a partisan "we" | a cited fact is recorded against the listener's side |
| `cheer` | "!" | only on the finish or the reaction after it, and only from the Caller or the scoring side's Buddy |
| `reaction` | a reaction away from the goal | never; it stands once, at the goal, after the finish has landed |

The goal-call reading adds `chain`, `past`, `position`, `straight`,
`duration`, `direction`, `run` and `carry_delivery` to that list and drops
`untagged` and `citation`, which a narration with no numbers in it cannot
commit. `docs/VERIFICATION.md` has the table for both, one test per kind.

A narration that makes **no** name, number or clock claim is refused too, as
`unverifiable`. Prose that names nobody and quotes no clock has nothing tracing
back to the data, so there is nothing for the label to be true about. A check
that passed it would be reporting "found no problem" in a narration that
asserted nothing, which is not the same as grounded.

**Pairing is the point of the numbering.** Checking that each word appears
somewhere in the passage catches invention and nothing else. The records for the
54:18 goal hold a `Dribble` and they hold Peter Reid, so "dribbles past Peter
Reid" passes a membership check while describing something that did not happen:
Reid pressured and was never dribbled past. So every name in a sentence is also
paired with every action in it, and the pair has to meet inside one cited fact.
Reid's only record in that passage is a `Pressure`, so no cited fact can pair
him with a dribble, and the sentence is refused.

Pairing every name with every action is deliberately blunt. Nothing in the text
says which name goes with which action, so a sentence holding two actions and
three names is one the check cannot read exactly, and refusing it is the
conservative answer. Rule 3 of the prompt therefore asks for one action per
sentence. The cost is real and is the price of catching misdescription: "Di
Maria wins a foul and Messi scores" is true and is refused, because no one fact
pairs Messi with the foul. Written as two sentences, both pass.

**What it still cannot do.** It reads a sentence against the facts that sentence
cited; it does not read the sentence's grammar. Direction survives: "Maradona
passes to Enrique" and "Enrique passes to Maradona" cite the same facts and both
pass, and only one of them is what happened. Prose that asserts nothing about an
event (who was where, what it meant) is outside its reach entirely. Any claim
that the app's narration is *correct* rests on more than this module.

Accents are normalised before matching, so "Hector" matches the recorded
"Héctor". That is a spelling variant of a player who is really there, not an
invented player, and failing it would report a hallucination that did not
happen.

**A player has two recorded names and both are grounded.** The event feed
carries the full name and the lineups file carries a `player_nickname` beside
it, so `Lionel Andrés Messi Cuccittini` and `Lionel Messi` are the same
player read out of the same match's data. A sentence naming either is naming
somebody the records name. A short form the files do not record is not: "Leo"
is refused as an unknown name, exactly like an invented player, and a player
the lineups file records no nickname for has only their full name to be named
by.

Standard library only, like the rest of `app/`.
"""

import re
from dataclasses import dataclass
from typing import Mapping, Sequence

from app.narration_grammar import (
    PRONOUNS,
    Move,
    Reader,
    bare,
    fold,
    support,
    why,
)
from app.narration_prompt import Fact, Facts
from app.plain_characters import plain
from app.orchestrator_contract import CALLER
from app.personas import Persona


class NoSideForAPartisanVoice(ValueError):
    """A `fans_only` persona was asked for without a side to be on.

    The Buddy is checked as the listener's team, so a Buddy narration from
    somebody with no team is one this module cannot read: the first person in
    it has nothing to be true about. Checking it as though nobody were
    partisan would admit "we" with no side behind it, and guessing a side
    would decide for a listener who did not, so this raises instead.

    It lived in `app/narration_prompt.py` while the prompt was the other
    place that needed a side. The prompt takes no persona any more, so the
    exception sits with its one raiser, `check`.
    """

#: "X passed to Y" is two records: a `Pass` on X's and a `Ball Receipt*` on Y's.
#: Both ground the word, so naming the player a pass reached is not reported as
#: an invented action.
_PASS = frozenset({"Pass", "Ball Receipt*"})

#: "X dribbled past Y" is likewise two records: a `Dribble` on X's and a
#: `Dribbled Past` on Y's. This pair is what makes the Reid case decidable.
_DRIBBLE = frozenset({"Dribble", "Dribbled Past"})

#: "X fouled Y" is a `Foul Committed` on X's record and a `Foul Won` on Y's.
_FOUL = frozenset({"Foul Committed", "Foul Won"})

#: Event types with one word each and no second side.
_CARRY = frozenset({"Carry"})
_RECEIPT = frozenset({"Ball Receipt*"})
_PRESSURE = frozenset({"Pressure"})
_RECOVERY = frozenset({"Ball Recovery"})
_SHOT = frozenset({"Shot"})

#: Words that assert a specific StatsBomb event type, and the types that satisfy
#: them. A narration using one is claiming that event is in the facts it cited,
#: so one of the types has to be there.
#:
#: Deliberately narrow: these are the actions a model writes when it drifts, and
#: a word that is not here is ordinary prose rather than a claim. A word maps to
#: more than one type only where one phrase asserts both sides of the same
#: event, which is what lets a sentence name the player an action was done to.
#:
#: **Past tense and the tenseless nouns, and nothing in the present.** A buildup
#: is playback, so `EVENT_VERBS` writes the facts in the past tense and the
#: narration follows. The present-tense form of each of these is in
#: `PRESENT_TENSE` below and is refused rather than grounded: "dribbles" is not
#: a weaker way of saying "dribbled", it is a narration describing the match as
#: if it were still happening.
#:
#: The list grows from live runs rather than from a wish to be complete. "carry",
#: "receive" and "press" are here because `EVENT_VERBS` says those events in
#: those words, so a model reads them off the facts and writes them back, and a
#: word the facts use to state an event is a word that asserts it. The noun
#: "pressure" is deliberately absent: "under pressure" is as often scene setting
#: as a claim about a `Pressure` record, and refusing it would cost good copy.
#:
#: "won" asserts a `Foul Won`, which is the only thing a buildup records being
#: won. It is the word that makes "won a foul" groundable while
#: `BANNED_PATTERNS` refuses "won the match": one is a record, the other is a
#: claim about a result no buildup carries.
ACTION_CLAIMS: Mapping[str, frozenset[str]] = {
    "passed": _PASS,
    "pass": _PASS,
    "dribbled": _DRIBBLE,
    "dribble": _DRIBBLE,
    "carried": _CARRY,
    "carry": _CARRY,
    "received": _RECEIPT,
    "receive": _RECEIPT,
    "pressed": _PRESSURE,
    "press": _PRESSURE,
    "recovered": _RECOVERY,
    "recovery": _RECOVERY,
    "cleared": frozenset({"Clearance"}),
    "clearance": frozenset({"Clearance"}),
    "blocked": frozenset({"Block"}),
    "block": frozenset({"Block"}),
    "intercepted": frozenset({"Interception"}),
    "interception": frozenset({"Interception"}),
    "saved": frozenset({"Goal Keeper"}),
    "save": frozenset({"Goal Keeper"}),
    "fouled": _FOUL,
    "foul": _FOUL,
    "committed": frozenset({"Foul Committed"}),
    "won": frozenset({"Foul Won"}),
    "contested": frozenset({"Duel"}),
    "dispossessed": frozenset({"Dispossessed"}),
    "miscontrolled": frozenset({"Miscontrol"}),
    "shot": _SHOT,
    "scored": _SHOT,
    # The three words a goal call lands the finish with. "finished" is the
    # game's own word for a shot and means nothing else on a football pitch;
    # "hit" can be a shot or a pass, so it grounds against either and the
    # player it is paired with does the rest. "score" is here as the bare
    # infinitive, which is what "set him up to score" is: the third person
    # "scores" is a present-tense narration and stays in `PRESENT_TENSE`.
    "finished": _SHOT,
    "finish": _SHOT,
    "hit": frozenset({"Shot", "Pass"}),
    "score": _SHOT,
    # The other neutral finishes. Each one says a shot was struck and says
    # nothing about how hard: that is the line Task 9d draws, with the force
    # words in `BANNED_PATTERNS` on the other side of it. They are claims
    # rather than prose now, so "MacAllister struck it" is refused in a
    # passage where MacAllister has four records and no shot.
    "struck": _SHOT,
    "fired": _SHOT,
    "slotted": _SHOT,
}

#: Present-tense verbs, and the past-tense form the facts use instead. A buildup
#: already happened, and narrating it as though it were live is the one thing
#: this table refuses. Every value is a word `ACTION_CLAIMS` grounds or a verb
#: `EVENT_VERBS` writes, which
#: `tests/test_grounding.py::TestTense::test_every_present_form_has_a_past_form_the_check_knows`
#: holds.
#:
#: It covers the verbs the facts and the narration actually use, not every verb
#: in English: a word outside it is unchecked prose, and "turned", "advanced" or
#: "went again" are nobody's claim about a record.
PRESENT_TENSE: Mapping[str, str] = {
    "passes": "passed",
    "dribbles": "dribbled",
    "carries": "carried",
    "receives": "received",
    "presses": "pressed",
    "recovers": "recovered",
    "clears": "cleared",
    "blocks": "blocked",
    "intercepts": "intercepted",
    "saves": "saved",
    "fouls": "fouled",
    "commits": "committed",
    "contests": "contested",
    "miscontrols": "miscontrolled",
    "shoots": "shot",
    "scores": "scored",
    "wins": "won",
    "plays": "played",
    "makes": "made",
}

#: The two facts written with an auxiliary. A single word cannot catch these,
#: because the verb in them is already the past participle the facts use, so the
#: tense sits in "is" and "are" and the phrase has to be matched whole. Matching
#: "is" alone would refuse half of ordinary English.
PRESENT_TENSE_PHRASES: Mapping[str, str] = {
    "is dribbled past": "was dribbled past",
    "are dribbled past": "were dribbled past",
    "is dispossessed": "was dispossessed",
    "are dispossessed": "were dispossessed",
}

#: Words that assert the goal's recorded shot type. The highest-value entries in
#: this module: a goal becoming a penalty is a change of fact, and the run of
#: play alone does not reveal it.
SHOT_TYPE_CLAIMS: Mapping[str, str] = {
    "penalty": "Penalty",
    "penalties": "Penalty",
    "spot kick": "Penalty",
    "free kick": "Free Kick",
    "freekick": "Free Kick",
    "corner": "Corner",
}

#: Words that assert the body part the goal was scored with.
BODY_PART_CLAIMS: Mapping[str, str] = {
    "header": "Head",
    "heads": "Head",
    "headed": "Head",
    "left foot": "Left Foot",
    "right foot": "Right Foot",
}

#: Refused wherever they appear. `CLAUDE.md` bans verdict nicknames and
#: editorial epithets from app output, and narration is app output; it bans em
#: dashes from copy. `scripts/scan_copy.py` enforces the same rule on the static
#: screens, which is a different surface from generated text.
#:
#: The last entry is not a rule from `CLAUDE.md` but a fact about this
#: pipeline: narration is plain prose here and markup only ever reaches it by
#: mistake, so a bracket is refused on sight.
BANNED_PATTERNS: Sequence[tuple[str, str]] = (
    ("verdict nickname", r"goal of the century"),
    ("verdict nickname", r"hand of god"),
    ("verdict nickname", r"\bcontrovers\w*"),
    ("verdict nickname", r"\bwonder goal\b"),
    ("verdict nickname", r"\bgreatest\b"),
    # A verdict about history, which needs knowledge from outside the moment.
    # Nothing in one passage of event data says where a goal stands among
    # every other goal, so the ranking is the narrator's and not a finding.
    # It is refused in the reaction too: the reaction is the narrator's
    # feeling, and "the best of all time" is a claim about the record books.
    ("verdict about history", r"\bof all time\b"),
    ("verdict about history", r"\ball[- ]time\b"),
    ("verdict about history", r"\bbest\b"),
    ("verdict about history", r"\bfinest\b"),
    # Editorial epithets. `CLAUDE.md` asks for neutral language describing what
    # the data shows, and these are judgements the data did not make. The first
    # live run that got past the name checks still called the goal "this
    # decisive moment" and "a significant moment", which is the sentence that
    # put this group here.
    ("editorial epithet", r"\bdecisive\b"),
    ("editorial epithet", r"\bsignificant\b"),
    ("editorial epithet", r"\bbrilliant\b"),
    ("editorial epithet", r"\bstunning\b"),
    ("editorial epithet", r"\bmagnificent\b"),
    ("editorial epithet", r"\bincredible\b"),
    ("editorial epithet", r"\bunbelievable\b"),
    ("editorial epithet", r"\bsuperb\b"),
    ("editorial epithet", r"\bsensational\b"),
    ("editorial epithet", r"\bhistoric\b"),
    ("editorial epithet", r"\biconic\b"),
    ("editorial epithet", r"\blegendary\b"),
    ("editorial epithet", r"\bmemorable\b"),
    ("editorial epithet", r"\bdramatic\b"),
    ("editorial epithet", r"\bsublime\b"),
    ("editorial epithet", r"\bmasterful\b"),
    # Outcome claims. A buildup is one passage of play and carries no scoreline,
    # so anything about the result is outside the facts the narration was
    # written from. Both narrations in the first run that passed every other
    # check ended on "securing Argentina's victory" and "secured the victory
    # for his team", neither of which the data says.
    #
    # "win" and "won" are not banned as words: "won a foul" is a recorded Foul
    # Won event, and refusing the word would fail every penalty buildup.
    # "score" and its forms are left alone for the same reason, since the goal
    # is the thing being narrated. What is refused is winning the thing a
    # buildup cannot show, so the pattern reaches past the verb to its object.
    ("outcome claim", r"\b(?:win|wins|won|winning)\s+the\s+"
                      r"(?:match|game|final|tie|cup|title|trophy|world cup)\b"),
    ("outcome claim", r"\bvictor\w*\b"),
    ("outcome claim", r"\btriumph\w*\b"),
    ("outcome claim", r"\bdefeat\w*\b"),
    ("outcome claim", r"\bequali[sz]er\b"),
    ("outcome claim", r"\bwinner\b"),
    ("outcome claim", r"\bchampions?\b"),
    ("outcome claim", r"\btrophy\b"),
    ("outcome claim", r"\bscoreline\b"),
    ("unearned authority", r"\bofficial\w*"),
    # Force the record does not hold. A shot record carries who struck it,
    # with which foot, from where and whether it went in; it carries nothing
    # about how hard, so "smashed it home" is a reading of the pictures rather
    # than of the data. The live run of 2026-10-31 wrote "smashed it home"
    # twice and "blasting it in" once, and all three were grounded, because
    # the force was prose and the body part beside it was true.
    #
    # The neutral finishes stay sayable and are in `ACTION_CLAIMS`:
    # "finished", "scored", "struck", "fired", "hit" and "slotted" each say a
    # shot was taken and nothing about the manner of it.
    ("force the record does not hold", r"\bsmash\w*"),
    ("force the record does not hold", r"\bblast\w*"),
    ("force the record does not hold", r"\bhammer\w*"),
    ("force the record does not hold", r"\brifl\w*"),
    ("force the record does not hold", r"\bthump\w*"),
    ("force the record does not hold", r"\blash\w*"),
    ("force the record does not hold", r"\bwallop\w*"),
    ("force the record does not hold", r"\bdrill\w*"),
    ("force the record does not hold", r"\bthunder\w*"),
    ("force the record does not hold", r"\bcrash\w*"),
    # Addressing the fan. The narration ends on the goal and says nothing after
    # it, so there is no line spoken to the reader for second person to belong
    # to. The `ending` rule holds where the narration stops, which a closing
    # line citing the goal's own fact satisfies; this holds what it may say.
    ("address to the reader", r"\byou\b"),
    ("address to the reader", r"\byour\b"),
    ("address to the reader", r"\byours\b"),
    ("em dash", r"—"),
    ("en dash", r"–"),
    # Markup, which is every angle bracket and not an element this check knows
    # the shape of. `app/pronunciation.py` wraps a word in
    # `<phoneme alphabet="ipa" ph="liːd">`, and it is applied where the speech
    # request is built, after this check has run. A narration reaching here
    # with a bracket in it has been marked up a step early, and that mistake
    # used to pass: `phoneme`, `alphabet` and `ipa` are not names, actions,
    # clocks or numbers, so the marked-up and the plain 1986 narration came
    # back grounded on the same claims, and the marked-up one would have been
    # labelled "Verified from play data" and read out with the tags in it.
    # Nothing the prompt or the template writes holds either character, so
    # there is nothing to lose by refusing both.
    ("markup", r"[<>]"),
)

#: The first person plural, which belongs to one persona and no other.
#:
#: `app/personas.py` has the Buddy as the partisan voice, so "we" is the one
#: it could be. From the Caller or the Storyteller it is a claim
#: nobody made: neither is written as either team, and a narration that says
#: "our goal" without a side to mean by it has put a loyalty in the app's
#: mouth. `check` therefore refuses these from every persona but a partisan
#: one, and from a partisan one only in a sentence whose cited facts record
#: the listener's side.
#:
#: Patterns rather than words, like `BANNED_PATTERNS` and unlike the name
#: loop, because an apostrophe is a word boundary: `\bwe\b` catches "we're"
#: and "we've", which the word loop reads as single words ending in neither a
#: possessive nor anything else it strips.
#:
#: "You", "your" and "yours" are not here. They are refused for every persona
#: by `BANNED_PATTERNS`, because no narration is addressed to the fan whoever
#: is telling it.
FIRST_PERSON: Sequence[str] = (
    r"\bwe\b",
    r"\bour\b",
    r"\bours\b",
    r"\bus\b",
)

#: Capitalised words that are ordinary prose rather than a claim about who was
#: on the pitch. Without this, the first word of every sentence is reported as
#: an invented player.
#:
#: "Our" and "ours" are in here for a different reason from the rest. They are
#: ordinary prose in the sense that matters to this loop: `FIRST_PERSON` owns
#: them, and leaving them out would report a partisan "Our" twice, once as the
#: first person and once as a player nobody has heard of. One failure per
#: mistake, so the name loop skips them. "We" and "us" were already here.
#:
#: This is a list, and a list is never finished. The first live run of the
#: pipeline failed three model attempts in a row on the word "Finally", which
#: was this module's bug and not the model's: narration is thrown away whole
#: when the check fails, so a false positive here costs a good narration and
#: makes a model look worse than it is. When the failure log shows an ordinary
#: word being reported as a name, the word belongs here.
#:
#: **The last group is the reaction's own.** A reaction is a fragment, so its
#: first word is capitalised and `_name_hits` reads a capitalised word as a
#: name: "Oh, lovely!" was reported as a player called Oh. The words a
#: reaction opens with are therefore listed, which also keeps the opening a
#: closed set rather than anything a model feels like starting with, and a
#: recorded name inside a reaction still makes it play. `REACTION_WORDS` has
#: the two layers written out.
NOT_A_NAME = frozenset(
    """
    a about above across after afterwards again against all almost along already
    also although always an and another any are around as at away
    back barely be because been before beginning behind below beneath beside
    besides between beyond both but by
    despite down during
    each earlier either enough even eventually every
    few finally first following for found from further
    half halfway having he her here hers herself him himself his how however
    i if immediately in initially inside instead into is it its itself
    just
    last late later least left less
    many meanwhile might minute minutes moment moments more most moving much
    near nearly neither never next no none nor not now
    of off on once one only onto or other others our ours out outside over own
    past per perhaps
    quickly
    rather right round
    second seconds seven several she shortly side simultaneously since six so
    some soon still suddenly
    ten than that the their theirs them themselves then there these they third
    this those three through throughout thus to together too towards toward
    turning turns twice two
    under until up upon us
    very
    was we well what when where which while who whom whose why with within
    without
    yard yards yet you your
    ah beautiful dear goodness hey lovely oh ooh phew poor wow
    """.split()
)

#: Words that name a team by nationality rather than by its recorded name. One
#: is grounded when the team it refers to is in a cited fact, so "the English
#: defender" is fine over a fact recorded against England and refused over one
#: that is not. The table only covers the teams in `data/raw/`; a third match
#: needs its own entries, and until it has them a demonym for its teams is
#: reported as an unknown name rather than silently allowed.
TEAM_DEMONYMS = {
    "english": "England",
    "argentine": "Argentina",
    "argentinian": "Argentina",
    "argentinean": "Argentina",
    "french": "France",
}

_WORD = re.compile(r"[A-Za-zÀ-ɏ][A-Za-zÀ-ɏ'’-]*")
_NUMBER = re.compile(r"\d+")

#: A clock, as a fact writes it: minute, colon, two-digit second.
_CLOCK = re.compile(r"\b(\d{1,3}):(\d{2})\b")

#: A citation tag: the fact numbers a sentence used. Written "[14, 15]" by the
#: prompt's example; a space or a bare run of numbers is accepted too, because
#: refusing a narration over its punctuation would throw away good copy.
_TAG = re.compile(r"\[\s*\d+(?:\s*[,;\s]\s*\d+)*\s*\]")

#: A sentence: everything up to a full stop, question mark or exclamation mark,
#: or to the end of a line.
_SENTENCE = re.compile(r"[^.!?\n]+[.!?]*")

#: A list marker a model wrote in front of its own sentences, which the splitter
#: sees as a sentence holding one number.
_ENUMERATOR = re.compile(r"\d+\s*[.)]?")

#: `bare` and `fold` live in `app/narration_grammar.py`, which is the module
#: about reading the words of a narration, and are re-exported here because
#: this is where callers and tests have always imported them from. One
#: definition, two import paths: two copies of the accent folding would
#: eventually disagree about a name.


@dataclass(frozen=True)
class Claim:
    """One thing a narration asserts, and where it said it."""

    kind: str
    value: str
    sentence_number: int
    sentence: str

    def __str__(self) -> str:
        return f"sentence {self.sentence_number}: {self.kind} {self.value!r}"


@dataclass(frozen=True)
class Sentence:
    """One sentence of a narration, and the facts it cited.

    `text` has the citation tags taken out, so nothing downstream reads a fact
    number as a clock or a count. `raw` keeps the sentence as the model wrote
    it, for a failure report that has to be recognisable.
    """

    number: int
    text: str
    cites: tuple[int, ...]
    raw: str


@dataclass(frozen=True)
class GroundingResult:
    """The verdict on one narration.

    `grounded` is the whole-narration answer, because `CLAUDE.md` gives no
    partial credit. `failures` holds every claim that could not be pointed at,
    not just the first, so a retry and a log have something to work with.
    """

    grounded: bool
    failures: tuple[Claim, ...]
    checked: int

    @property
    def summary(self) -> str:
        if self.grounded:
            return f"grounded: {self.checked} claim(s) all traced to the data"
        return (
            f"not grounded: {len(self.failures)} of {self.checked} claim(s) "
            "could not be pointed at: "
            + "; ".join(str(failure) for failure in self.failures)
        )


def name_parts(facts: Facts) -> frozenset[str]:
    """Every word of every player and team name in the buildup, folded.

    What this answers is "is this name in the passage at all", which is what
    tells an invented player from a miscited one. Whether a name is grounded is
    a question about the facts one sentence cited; see `fact_names`.

    The recorded nicknames are in it for the same reason they are in
    `fact_names`: a player recorded twice over is one player, and a sentence
    naming them by either recorded spelling is naming somebody who is there.
    """
    parts: set[str] = set()
    names = list(facts.players) + list(facts.teams)
    names += [beat.nickname for beat in facts.beats if beat.nickname]
    for name in names:
        for part in _WORD.findall(name):
            parts.add(fold(part))
    return frozenset(parts)


def fact_names(fact: Fact) -> frozenset[str]:
    """Every word of the player and team named by one fact, folded.

    Narration shortens "Diego Armando Maradona" to "Maradona", so the parts are
    what a sentence can be matched against rather than the whole name.

    **Both recorded spellings of a player count.** StatsBomb records a full
    name on the event and a `player_nickname` on the lineup, and
    `app/narration_prompt.py` prints the nickname in the facts where there is
    one, so that is the spelling a narration is being asked for. Usually the
    nickname's words are already words of the full name and this adds nothing;
    sometimes they are not, and "Alexis MacAllister" is the case in this data,
    one word where the full name has two. Accepting it is not a loosening: the
    nickname is read out of `data/raw/`, exactly like the full name, and a
    short form the file does not record is still refused.
    """
    parts: set[str] = set()
    for name in (fact.beat.player, fact.beat.nickname, fact.beat.team):
        if not name:
            continue
        for part in _WORD.findall(name):
            parts.add(fold(part))
    return frozenset(parts)


def _tag_numbers(tag: str) -> tuple[int, ...]:
    return tuple(int(number) for number in _NUMBER.findall(tag))


def sentences(text: str) -> tuple[Sentence, ...]:
    """Split a narration into sentences and read each one's citations.

    Two layouts have to be read, and a tag between two sentences is ambiguous
    between them. The prompt asks for the citation first, which is what the
    fallback writes and what a model given that example produces:

        [15] Maradona dribbled past a defender.

    The first live run against `granite4:micro` put the tag just after the full
    stop instead, every time, and ran the sentences together on one line:

        Maradona dribbled past a defender. [15] He carried the ball. [16]

    Read one way, "[15] He carried the ball." is a sentence citing fact 15. Read
    the other, the tag closes the sentence before it and "He carried the ball."
    cites nothing. Nothing inside the chunk settles it.

    **The first chunk settles it for the whole narration.** A tag opening the
    first chunk has no sentence before it to belong to, so a narration that
    starts with one is citation-first and every leading tag binds to the
    sentence it opens. Otherwise the tags trail, and a leading tag belongs to
    the sentence before it. Deciding once per narration rather than per chunk is
    what keeps an untagged sentence in a citation-first narration reported
    against itself: binding its successor's tag backwards would flag the wrong
    sentence and hide the one that cited nothing.
    """
    found: list[Sentence] = []
    carried: tuple[int, ...] = ()

    first = next((c.strip() for c in _SENTENCE.findall(text) if c.strip()), "")
    leading_binds_forward = _TAG.match(first) is not None

    def add_to_previous(cites: tuple[int, ...], raw: str) -> bool:
        if leading_binds_forward or not found or found[-1].cites:
            return False
        previous = found[-1]
        found[-1] = Sentence(
            number=previous.number,
            text=previous.text,
            cites=cites,
            raw=f"{previous.raw} {raw}",
        )
        return True

    for chunk in _SENTENCE.findall(text):
        rest = chunk.strip()

        while True:
            leading = _TAG.match(rest)
            if leading is None:
                break
            cites = _tag_numbers(leading.group(0))
            if not add_to_previous(cites, leading.group(0)):
                carried += cites
            rest = rest[leading.end():].lstrip()

        if not rest:
            continue

        inner = tuple(
            number for tag in _TAG.findall(rest) for number in _tag_numbers(tag)
        )
        said = _TAG.sub(" ", rest).strip()

        # Nothing but punctuation left: a tag standing on its own between two
        # sentences, which the loop above has already placed unless the
        # sentence before it was tagged.
        if not said.strip(" \t.,;:!?"):
            if inner and not add_to_previous(inner, rest):
                carried += inner
            continue

        # A bare number before a full stop is a list marker, not a sentence.
        # One live attempt numbered its four sentences "1." to "4.", which read
        # as four sentences asserting a count and citing nothing. A sentence
        # that is only a number says nothing either way, so dropping it cannot
        # hide a claim.
        if _ENUMERATOR.fullmatch(said):
            carried += inner
            continue

        found.append(
            Sentence(
                number=len(found) + 1,
                text=re.sub(r"\s{2,}", " ", said),
                cites=carried + inner,
                raw=rest,
            )
        )
        carried = ()
    return tuple(found)


def strip_citations(text: str) -> str:
    """The narration as it is shown and voiced: no tags, one paragraph.

    The citations are machinery for the check, not copy. `CLAUDE.md` governs
    what the app says, and "[14, 15]" is not something a screen displays or a
    voice reads aloud, so it comes off before either. The sentences are joined
    into a single paragraph because that is how narration is displayed and
    spoken; the per-line layout is only what the prompt asked the model for.
    """
    without_tags = _TAG.sub("", text)
    tidied = re.sub(r"[ \t]+([.,;:!?])", r"\1", without_tags)
    lines = [line.strip() for line in tidied.splitlines()]
    return re.sub(r"\s{2,}", " ", " ".join(line for line in lines if line)).strip()


@dataclass(frozen=True)
class _NameClaim:
    """A capitalised word, and what it has to be grounded against."""

    word: str
    value: str
    demonym: bool


@dataclass(frozen=True)
class _ActionClaim:
    """An action word, and the event types that satisfy it."""

    word: str
    types: frozenset[str]


def _supports_name(fact: Fact, claim: _NameClaim) -> bool:
    if claim.demonym:
        return fact.beat.team == claim.value
    return claim.value in fact_names(fact)


def _in_the_buildup(claim: _NameClaim, facts: Facts, known: frozenset[str]) -> bool:
    if claim.demonym:
        return claim.value in facts.teams
    return claim.value in known


def _cited(cites: Sequence[int]) -> str:
    return "[" + ", ".join(str(number) for number in sorted(set(cites))) + "]"


def check(
    text: str,
    facts: Facts,
    persona: Persona | None = None,
    side: str | None = None,
) -> GroundingResult:
    """Decide whether `text` is grounded in `facts`.

    Every sentence is read against the facts it cited. Returns every failing
    claim rather than stopping at the first, and counts the claims it looked at
    so a pass means something more than "found no problem in a narration that
    asserted nothing".

    **A persona changes one thing and only one.** `persona` and `side` are the
    voice the narration was asked for and the team the listener is on, and the
    single difference they make is the first person: a partisan persona may
    call `side` "we", "our" or "us", and nothing else may. Every other rule in
    this module reads a narration the same way whoever wrote it, because a
    voice that could loosen one would make "Verified from play data" mean
    something different depending on who was listening.

    A partisan persona with no side raises `NoSideForAPartisanVoice` rather
    than quietly checking the narration as though nobody were partisan. This
    is the only place that raises it: the prompt takes no persona.

    **The text is made plain first.** `app/plain_characters.py` rewrites a
    disguised space or hyphen as the plain one: two candidates have arrived
    carrying a `NARROW NO-BREAK SPACE` inside a player's name and a
    `NON-BREAKING HYPHEN` inside a number written out in words. Reading the
    text as written is what let them through, since a narrow space is
    whitespace and a hyphen is not a claim. The check runs on the plain text
    so that the words it reads are the words a voice would say, and the
    rewrite reaches no dash: the em dash and the en dash are refused below and
    turning either into a hyphen here would undo that.
    """
    text = plain(text)
    partisan = persona is not None and persona.fans_only
    if partisan and not side:
        raise NoSideForAPartisanVoice(
            f"the {persona.name} writes as the listener's side, so a "
            "narration in that voice cannot be checked without one"
        )
    if _TAG.search(text):
        return _cited_reading(text, facts, persona, side, partisan)
    return _goal_call(text, facts, persona, side, partisan)


def _cited_reading(
    text: str,
    facts: Facts,
    persona: Persona | None,
    side: str | None,
    partisan: bool,
) -> GroundingResult:
    """The cited reading: every sentence against the fact numbers it named.

    This is the whole of what `check` used to be, and it is still what the
    pipeline in `app/narration.py` produces: `build_prompt` asks a model for a
    citation on every line, the fallback writes them, and
    `scripts/freeze_narrations.py` records which `event_id` in `data/raw/`
    stands behind each sentence. A narration written this way is read this way.
    """
    listener_side = fold(side) if side else None

    by_number = {fact.number: fact for fact in facts.facts}
    goal = facts.goal_fact
    known_names = name_parts(facts)
    failures: list[Claim] = []
    # The name, number and clock claims found anywhere in the narration. These
    # are the ones that tie it to this moment, so a narration with none of them
    # is refused below however clean the rest of it looks.
    claims_made: list[str] = []
    checked = 0

    parsed = sentences(text)
    for sentence in parsed:
        folded = fold(sentence.text)

        def failed(kind: str, value: str) -> None:
            failures.append(
                Claim(kind, value, sentence.number, sentence.raw)
            )

        for label, pattern in BANNED_PATTERNS:
            for hit in re.findall(pattern, folded):
                checked += 1
                failed(label, hit if isinstance(hit, str) else sentence.text)

        # The first person, which is the one thing a persona changes. A voice
        # that is not partisan has no side to mean by "we", so the word is
        # refused here and the side check below never runs; a partisan voice
        # is held to what it cited instead, once the citations are known.
        said_as_us = [
            hit
            for pattern in FIRST_PERSON
            for hit in re.findall(pattern, folded)
        ]
        if said_as_us and not partisan:
            for word in said_as_us:
                checked += 1
                failed(
                    "first person",
                    f"{word!r}: this narration is not written as either side, "
                    "so there is nobody for the first person to be",
                )

        # The tense, before the words are read as claims. A present-tense verb
        # is not a weaker way of saying the past one: it narrates the passage as
        # though it were still happening, which is a different thing from what
        # the records say.
        for phrase, past in PRESENT_TENSE_PHRASES.items():
            if phrase in folded:
                checked += 1
                failed(
                    "tense",
                    f"{phrase!r} is present tense; the facts say {past!r}",
                )

        # Multi-word claims first, so "free kick" is not read as "kick".
        for phrase, required in SHOT_TYPE_CLAIMS.items():
            if phrase in folded:
                checked += 1
                if facts.set_piece != required:
                    recorded = facts.set_piece or "Open Play"
                    failed(
                        "shot_type",
                        f"{phrase!r} but the shot is recorded as {recorded}",
                    )

        for phrase, required in BODY_PART_CLAIMS.items():
            if phrase in folded:
                checked += 1
                if facts.body_part != required:
                    recorded = facts.body_part or "not recorded"
                    failed(
                        "body_part",
                        f"{phrase!r} but the body part is recorded as {recorded}",
                    )

        names: list[_NameClaim] = []
        actions: list[_ActionClaim] = []

        for word in _WORD.findall(sentence.text):
            folded_word = bare(fold(word))

            if folded_word in PRESENT_TENSE:
                checked += 1
                failed(
                    "tense",
                    f"{word!r} is present tense; the facts say "
                    f"{PRESENT_TENSE[folded_word]!r}",
                )
                continue

            if folded_word in ACTION_CLAIMS:
                actions.append(_ActionClaim(word, ACTION_CLAIMS[folded_word]))
                continue

            if not word[0].isupper() or folded_word in NOT_A_NAME:
                continue

            claims_made.append("name")
            if folded_word in TEAM_DEMONYMS:
                names.append(
                    _NameClaim(word, TEAM_DEMONYMS[folded_word], demonym=True)
                )
            else:
                names.append(_NameClaim(word, folded_word, demonym=False))

        clocks = [
            (match.group(0), int(match.group(1)), int(match.group(2)))
            for match in _CLOCK.finditer(sentence.text)
        ]
        claims_made += ["clock"] * len(clocks)

        # A clock's digits are already accounted for, so they are taken out
        # before the bare numbers are read: "54:13" is one clock claim, not the
        # minute 54 and the count 13.
        digits = _NUMBER.findall(_CLOCK.sub(" ", sentence.text))
        claims_made += ["number"] * len(digits)

        cited: list[Fact] = []
        for number in sentence.cites:
            fact = by_number.get(number)
            if fact is None:
                checked += 1
                failed(
                    "citation",
                    f"[{number}] is not one of the {len(facts.facts)} facts "
                    "this narration was written from",
                )
            elif fact not in cited:
                cited.append(fact)

        if not cited:
            if not sentence.cites:
                checked += 1
                failed(
                    "untagged",
                    "the sentence cites no fact, so there is nothing to check "
                    "its names, actions and clocks against",
                )
            continue

        # A partisan "we" has to have the listener's side under it. The
        # sentence needs one cited fact recorded against that side, which is
        # the same shape as a name claim: a name is grounded when some cited
        # fact holds it, not when every cited fact does. Requiring all of them
        # would refuse "[10, 11] We dribbled past Beardsley", which cites the
        # two records of one dribble and is true for an Argentina listener.
        if said_as_us and partisan:
            checked += 1
            if not any(fold(fact.beat.team) == listener_side for fact in cited):
                failed(
                    "side",
                    f"{sorted(set(said_as_us))} said over "
                    f"{_cited(sentence.cites)}, which records nothing for "
                    f"{side}, so the first person has nothing to stand on",
                )

        # Names and actions are checked for membership first. A claim that
        # failed there is not paired afterwards: one failure per mistake, so a
        # retry reads a list of problems rather than a list of consequences.
        held_names: list[_NameClaim] = []
        for claim in names:
            checked += 1
            if any(_supports_name(fact, claim) for fact in cited):
                held_names.append(claim)
            elif _in_the_buildup(claim, facts, known_names):
                failed(
                    "name",
                    f"{claim.word!r} is in the buildup but not in the facts "
                    f"this sentence cites, {_cited(sentence.cites)}",
                )
            elif claim.demonym:
                failed(
                    "name",
                    f"{claim.word!r} refers to {claim.value}, which is not in "
                    "the buildup",
                )
            else:
                failed("name", claim.word)

        held_actions: list[_ActionClaim] = []
        for claim in actions:
            checked += 1
            wanted = " or ".join(sorted(claim.types))
            if any(fact.beat.action in claim.types for fact in cited):
                held_actions.append(claim)
            elif claim.types & facts.actions:
                failed(
                    "action",
                    f"{claim.word!r} claims a {wanted} event, which is in the "
                    f"buildup but not in the facts this sentence cites, "
                    f"{_cited(sentence.cites)}",
                )
            else:
                failed(
                    "action",
                    f"{claim.word!r} claims a {wanted} event, which is not in "
                    "the buildup",
                )

        for action in held_actions:
            for name in held_names:
                checked += 1
                if any(
                    fact.beat.action in action.types and _supports_name(fact, name)
                    for fact in cited
                ):
                    continue
                wanted = " or ".join(sorted(action.types))
                failed(
                    "pairing",
                    f"{name.word!r} with {action.word!r}: no cited fact records "
                    f"a {wanted} involving {name.word}, so the sentence pairs "
                    "two facts that the data does not pair",
                )

        for written, minute, second in clocks:
            checked += 1
            if not any(
                (fact.beat.minute, fact.beat.second) == (minute, second)
                for fact in cited
            ):
                failed(
                    "clock",
                    f"{written} is not the clock of any fact this sentence "
                    f"cites, {_cited(sentence.cites)}",
                )

        for written in digits:
            checked += 1
            value = int(written)
            if any(value == fact.beat.minute for fact in cited):
                continue
            if goal in cited and value == goal.beat.second:
                continue
            failed(
                "number",
                f"{written} is not the minute of a fact this sentence cites, "
                "or the second the goal was scored at",
            )

    # The narration ends on the goal. Nothing follows it: no summary, no
    # comment, no line addressed to the fan. So the last sentence has to cite
    # the shot the moment was built from, and a sentence after that one is a
    # sentence the app did not need to say.
    if parsed and goal.number not in parsed[-1].cites:
        checked += 1
        failures.append(
            Claim(
                "ending",
                f"the narration ends on a sentence citing {_cited(parsed[-1].cites)}, "
                f"not fact {goal.number}, the shot the moment was built from; "
                "the narration ends on the goal and nothing follows it",
                parsed[-1].number,
                parsed[-1].raw,
            )
        )

    if not claims_made:
        checked += 1
        failures.append(
            Claim(
                "unverifiable",
                "the narration names no player, team or clock value from the "
                "facts, so nothing in it traces back to the data",
                0,
                text.strip(),
            )
        )

    return GroundingResult(
        grounded=not failures, failures=tuple(failures), checked=checked
    )


#: A clause, for the one rule that is about a clause rather than a sentence.
#: The first person stands over the play in the clause it was said in: "We won
#: it back through Cuciuffo and Enrique gave it to Maradona" is Argentina's all
#: the way through, and an England listener saying it would be claiming
#: somebody else's recovery. A comma, a semicolon or a colon ends a clause,
#: which is rough and is the shape a goal call is written in.
_CLAUSE_BREAK = re.compile(r"[,;:]")

#: Where the listener would cheer, which is the finish and the reaction after
#: it, and nowhere else.
_CHEER = "!"

#: The longest a reaction may be, in words.
#:
#: **A narration has two layers and only one of them is checked.** Shawn
#: settled this on 2026-10-31: the play (who, what, where, how it finished) is
#: grounded strictly, and the reaction (the narrator feeling the moment: "Oh,
#: lovely!", "What a finish!", and for the side that conceded "Ah, no.") is
#: the narrator's own voice. It follows the listener's side, it claims nothing
#: about the data, and so there is nothing in it for the records to hold or
#: refuse. "Verified from play data" still means every event happened as told,
#: because the reaction tells no event.
#:
#: Eight words is what keeps that true by shape rather than by trust. A clause
#: this short with no name, no pronoun, no digit and no claim about a recorded
#: field has nowhere to put a misdescription: it can be wrong about how a
#: narrator feels, which is not a thing the data has a view on.
REACTION_WORDS = 8

#: The move kinds a reaction may still make, which is the one that asserts
#: nothing once nobody is named.
#:
#: "What a finish!" is one of Shawn's three examples of a reaction and
#: "finish" is in `ACTION_CLAIMS`, so an action word cannot be what rules a
#: reaction out. With no name and no pronoun in the sentence there is nobody
#: for the word to be about: it points at no record, so no record can refuse
#: it. Everything else a goal call can say is about a specific record, and a
#: sentence making one of those claims is play and is read as play, however
#: short it is.
REACTION_MOVES = frozenset({"action"})

#: The pronouns that make a sentence play rather than reaction. A pronoun
#: means the player with the ball, so "He scored." is the finish said shortly
#: and not a reaction, which is the case this rule exists for.
_PRONOUN_WORDS = frozenset(PRONOUNS)


def _is_a_reaction(text: str, moves: Sequence[Move]) -> bool:
    """Whether this sentence is the narrator's reaction rather than the play.

    Four things, and all of them are about the shape of the sentence rather
    than about what it happens to say: it is at most `REACTION_WORDS` words,
    it holds no digit, it names nobody (no player, no team, no pronoun), and
    every move in it is in `REACTION_MOVES`.
    """
    words = _WORD.findall(text)
    if not words or len(words) > REACTION_WORDS:
        return False
    if _NUMBER.search(text):
        return False
    if any(bare(fold(word)) in _PRONOUN_WORDS for word in words):
        return False
    return all(move.kind in REACTION_MOVES for move in moves)


def _clause(text: str, at: int) -> tuple[int, int]:
    """The clause the character at `at` sits in, as a span of `text`."""
    before = [match.end() for match in _CLAUSE_BREAK.finditer(text, 0, at)]
    start = before[-1] if before else 0
    after = _CLAUSE_BREAK.search(text, at)
    return start, after.start() if after else len(text)


def _may_cheer(persona: Persona | None, facts: Facts, side: str | None) -> bool:
    """Whether this listener's narration may end on an exclamation mark.

    The ball going in is the only moment of a recap a listener cheers at, and
    two voices do not cheer at all: the Storyteller is a documentary register
    whoever scored, and a Buddy sitting with the side that conceded is not
    celebrating the goal it just conceded. A narration with no narrator has
    nobody to cheer either, so it gets no mark.
    """
    if persona is None:
        return False
    if persona.fans_only:
        return bool(side) and fold(side) == fold(facts.moment.team)
    return persona.id == CALLER


def _cheer_failures(
    parsed: Sequence[Sentence],
    persona: Persona | None,
    facts: Facts,
    side: str | None,
    may_stand_on: frozenset[int],
) -> list[Claim]:
    """Every exclamation mark that is not where the listener would cheer.

    Two rules, and they are the framework's rather than the data's: the mark
    belongs where the ball goes in, which is the sentence that lands the
    finish and the reaction that may follow it, and it belongs only to the
    Caller and to the Buddy of the side that scored. `may_stand_on` is those
    one or two sentence numbers, worked out by the reading. This is a rule
    about what the app says out loud, so it is the goal-call reading's rather
    than the data's; the cited reading has no reaction layer and asks for no
    exclamation mark anywhere.
    """
    allowed = _may_cheer(persona, facts, side)
    whose = persona.name if persona else "a narration with no narrator"
    failures: list[Claim] = []
    for sentence in parsed:
        if _CHEER not in sentence.text and _CHEER not in sentence.raw:
            continue
        if sentence.number not in may_stand_on:
            failures.append(
                Claim(
                    "cheer",
                    "an exclamation mark on a sentence that is neither the "
                    "finish nor the reaction after it; the listener cheers "
                    "when the ball goes in and not before",
                    sentence.number,
                    sentence.raw,
                )
            )
        elif not allowed:
            failures.append(
                Claim(
                    "cheer",
                    f"an exclamation mark from {whose}, which does not cheer "
                    f"this goal: {facts.moment.team} scored it",
                    sentence.number,
                    sentence.raw,
                )
            )
    return failures


def _goal_call(
    text: str,
    facts: Facts,
    persona: Persona | None,
    side: str | None,
    partisan: bool,
) -> GroundingResult:
    """The goal-call reading: a narration that cites nothing, read as prose.

    `docs/VOICE.md` settles that a Prelude narration is the recap stage of a
    goal call, and a goal call carries no fact numbers. So the sentence itself
    has to be read, which `app/narration_grammar.py` does: it turns each
    sentence into the moves it makes, in order, following the ball from one to
    the next, and says which records hold each one. A move no record holds is a
    refusal here.

    **What this reading adds to the cited one.** Chains, the pronoun that means
    the player with the ball, a name part that has to pick out one player,
    action before name, "past X" as a dribble past X, and the recorded fields a
    goal call says out loud: the counter, the pressure, the long ball, the
    assist, the first-time finish, the body part, the two field positions and
    the duration.

    **What it takes away.** The clock. The framework asks for no clock in a
    narration at all, in digits or in words, so a goal call carries no digit
    anywhere: the header already says when the goal came, and a colon between
    two numbers is read aloud as a colon between two numbers.

    **The first person stands over the clause it was said in.** A partisan
    Buddy may say "we" where that clause's own records are the listener side's.
    The France fan's Buddy cannot say it about the 2022 counter at all, because
    all thirteen records in that passage are Argentina's.

    **The last sentence may be a reaction, and a reaction is not checked.**
    `_is_a_reaction` is the shape test, `REACTION_WORDS` says why it is safe,
    and what it exempts is the support of the moves. Everything a reaction
    could be refused for it is still refused for: the banned verdicts, the
    force words, "you", a clock, a digit, the present tense, the first person
    with nothing to stand on, and an exclamation mark from a voice that does
    not cheer. It is allowed once, it is allowed only as the last sentence,
    and it is allowed only once the play has landed the finish, so a reaction
    anywhere else is a refusal of its own.
    """
    listener_side = fold(side) if side else None
    reader = Reader(
        facts=facts,
        not_a_name=NOT_A_NAME,
        demonyms=TEAM_DEMONYMS,
        actions=ACTION_CLAIMS,
    )
    failures: list[Claim] = []
    claims_made = 0
    checked = 0
    parsed = sentences(text)
    said_the_goal = False

    # Read in one pass and in order, because the reader follows the ball
    # across a full stop, and then decide which sentences are reactions. The
    # decision has to be made before the sentences are checked: it is what
    # says whether a sentence is read as play at all.
    read = [reader.read(sentence.text) for sentence in parsed]
    reactions = frozenset(
        index
        for index, sentence in enumerate(parsed)
        if _is_a_reaction(sentence.text, read[index])
    )
    last = len(parsed) - 1
    the_reaction = last if last in reactions else None
    # Where the play ends: the last sentence, or the one before the reaction.
    last_play = last if the_reaction is None else the_reaction - 1
    may_cheer_on = frozenset(
        index + 1
        for index in (last_play, the_reaction)
        if index is not None and index >= 0
    )

    for index, sentence in enumerate(parsed):
        folded = fold(sentence.text)
        reaction = index in reactions

        def failed(kind: str, value: str) -> None:
            failures.append(Claim(kind, value, sentence.number, sentence.raw))

        for label, pattern in BANNED_PATTERNS:
            for hit in re.findall(pattern, folded):
                checked += 1
                failed(label, hit if isinstance(hit, str) else sentence.text)

        for phrase, past in PRESENT_TENSE_PHRASES.items():
            if phrase in folded:
                checked += 1
                failed(
                    "tense",
                    f"{phrase!r} is present tense; the facts say {past!r}",
                )

        for word in _WORD.findall(sentence.text):
            folded_word = bare(fold(word))
            if folded_word in PRESENT_TENSE:
                checked += 1
                failed(
                    "tense",
                    f"{word!r} is present tense; the facts say "
                    f"{PRESENT_TENSE[folded_word]!r}",
                )

        # No clock, and so no digit. This is the one rule the goal-call
        # reading is stricter about than the cited one, and it is the
        # framework's: a recap does not say when it happened.
        for written in _CLOCK.finditer(sentence.text):
            checked += 1
            failed(
                "clock",
                f"{written.group(0)!r}: a goal call carries no clock, and the "
                "header already says when the goal came",
            )
        for written in _NUMBER.findall(_CLOCK.sub(" ", sentence.text)):
            checked += 1
            failed(
                "number",
                f"{written!r}: a goal call writes no digit, so a minute, a "
                "second and a count are all out",
            )

        held: list[tuple[Move, tuple]] = []
        if reaction:
            # The one thing a reaction is exempt from: the moves in it are not
            # traced to a record, because a sentence naming nobody points at
            # none. What it is not exempt from is where it may stand.
            checked += 1
            if index != the_reaction:
                failed(
                    "reaction",
                    f"{sentence.text.strip()!r} is a reaction, and a reaction "
                    "stands at the goal with nothing after it: this one comes "
                    + (
                        "before the finish"
                        if index < last_play
                        else "after another reaction"
                    ),
                )
        else:
            for move in read[index]:
                checked += 1
                if move.kind in ("name", "team"):
                    claims_made += 1
                backing = support(move, facts)
                if backing:
                    held.append((move, backing))
                else:
                    failed(
                        _FAILED_AS.get(move.kind, move.kind),
                        why(move, facts),
                    )

        # The first person, which is the one thing a narrator changes. A voice
        # that is not partisan has nobody to mean by "we"; a partisan one has
        # to be saying it over its own side's play, in the clause it said it
        # in.
        for pattern in FIRST_PERSON:
            for hit in re.finditer(pattern, folded):
                checked += 1
                if not partisan:
                    failed(
                        "first person",
                        f"{hit.group(0)!r}: this narration is not written as "
                        "either side, so there is nobody for the first person "
                        "to be",
                    )
                    continue
                start, end = _clause(sentence.text, hit.start())
                teams = {
                    beat.team
                    for move, backing in held
                    if start <= move.at < end
                    for beat in backing
                }
                if not any(fold(team) == listener_side for team in teams):
                    said = sentence.text[start:end].strip()
                    held_by = ", ".join(sorted(teams)) or "nothing"
                    failed(
                        "side",
                        f"{hit.group(0)!r} in {said!r}, whose play the records "
                        f"put on {held_by} and not on {side}, so the first "
                        "person has nothing to stand on",
                    )

        if any(_is_the_finish(move, backing, facts) for move, backing in held):
            said_the_goal = True
            if index != last_play:
                checked += 1
                failed(
                    "ending",
                    "the narration says the goal and then keeps talking; it "
                    "ends on the finish, and the only thing that may follow "
                    "it is the narrator's reaction",
                )

    if parsed and not said_the_goal:
        checked += 1
        failures.append(
            Claim(
                "ending",
                "the narration does not land the finish: nothing in it is a "
                "claim the goal's own record holds, so it never says the ball "
                "went in",
                parsed[-1].number,
                parsed[-1].raw,
            )
        )

    failures += _cheer_failures(
        parsed, persona, facts, side, may_cheer_on
    )

    if not claims_made:
        checked += 1
        failures.append(
            Claim(
                "unverifiable",
                "the narration names no player or team from the records, so "
                "nothing in it traces back to the data",
                0,
                text.strip(),
            )
        )

    return GroundingResult(
        grounded=not failures, failures=tuple(failures), checked=checked
    )


#: The kinds of move that can be the finish: a claim the goal's own record
#: holds. Three of them, and the list is a rule rather than a vocabulary.
#:
#: **It used to be the Shot action alone, and that was a vocabulary.** The
#: live run of 2026-10-31 refused nine of eighteen candidates on this rule and
#: every one of the nine ended "with his left foot", after "firing", "struck",
#: "smashed it home" or "blasting it home". None of those four words is in
#: `ACTION_CLAIMS`, so none of them claimed a `Shot`, so the check decided a
#: narration that said the goal was scored with the left foot had not reached
#: the goal. Extending the verb list would have worked for those four and
#: found four more on the next run, which is the chase `ACTION_CLAIMS`
#: documents itself as not being in.
#:
#: So the rule is what the words assert rather than which words they are: the
#: body part and the first-time flag are read off the goal shot itself, so a
#: sentence claiming either is a sentence about the shot that scored, whatever
#: verb it used to get there.
#:
#: **What it cannot catch.** A last sentence naming the body part without
#: saying the ball went in: "he went around Shilton with his left foot" lands
#: the finish by this rule and does not say it in words. The prompt asks for
#: the finish plainly, and this is the shape of the gap rather than a reason
#: to go back to a verb list.
FINISH_KINDS = frozenset({"action", "body_part", "first_time"})


def _is_the_finish(move: Move, backing: Sequence, facts: Facts) -> bool:
    """Whether this move is a claim about the shot that scored."""
    if move.kind not in FINISH_KINDS:
        return False
    if move.kind == "action" and "Shot" not in (move.detail or ()):
        return False
    return facts.goal_beat in backing


#: How a failed move is reported, where the move's own kind is not the word a
#: reader of the report wants. The rest are reported under their own kind, so
#: a refusal says "chain", "past" or "position" and a retry has something to
#: work with.
_FAILED_AS: Mapping[str, str] = {
    "unknown_name": "name",
    "ambiguous_name": "name",
    "long_pass": "action",
    "touch": "action",
    "pressured": "action",
    "first_time": "shot_type",
}
