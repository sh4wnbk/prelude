"""Reading a goal call: what a narration says when it cites no facts.

`app/grounding.py` was built around a narration that cites its facts by number,
one sentence at a time. The framework in `docs/VOICE.md` is a goal call, and a
goal call carries no numbers:

    Cuciuffo's recovery started the counter, and Enrique played it to Maradona
    just inside his own half, who carried it forward under pressure past
    Beardsley, Butcher and Fenwick and took it into the box, where he went
    around Peter Shilton and scored with his left foot.

There is nothing in that for the cited reading to work with, and refusing it is
not an option: it is the standard, in
`tests/test_reference_narrations.py::TestTheReferences`. So this module reads
the sentence instead. It turns a goal call into an ordered list of `Move`s,
each one a thing the sentence asserts, and says which records in the buildup
hold each one. `app/grounding.py` turns a `Move` with no support into a
refusal.

**What it reads.** Seven constructions, which are the ones the framework asks
for:

| Said | `Move.kind` | Held by |
| ---- | ----------- | ------- |
| a name part that picks out one player | `name` | that player being in the buildup |
| "he", "his", "who", "whose" | resolved, never a move of its own | the player the move is following |
| "Molina to MacAllister", "found MacAllister", "set up Di María" | `chain` | a `Pass` by the first with the second as its recipient |
| "a long ball from Álvarez" | merged into the `chain` | `pass.length` at or over `LONG_PASS_YARDS` |
| "past Beardsley", "around Shilton" | `past` | a `Dribbled Past` on the defender and a `Dribble` by the player at the same clock |
| "picked it up", "won it back", "closed him down", "finished" | `touch`, `action` | a record of that type by that player |
| "in his own half", "into the box" | `position` | a coordinate of that player's against the pitch's own lines |
| "under pressure", "first time", "with his left" | `pressured`, `first_time`, `body_part` | the field of that name on a record |
| "on the counter" | `pattern` | `play_pattern` |
| "in under ten seconds" | `duration` | the span between the first and last timestamp |
| "straight into the box" | `straight` | the carries running straight, which in 1986 they do not |
| "forward", "back", "ahead" | `direction` | the change in x on a pass or a carry of that player's |
| "drove", "ran", "burst" | `run` | a carry of at least `RUN_YARDS` |
| "carried it to Vance" | `carry_delivery` | nothing: a carry does not hand the ball to anybody |

**The player a pronoun means is the one with the ball.** "He" is resolved to
the most recently named player who has a recorded touch in this passage, which
is the player the move is following. The plainer rule, the most recently named
player of any kind, gets the Storyteller's 1986 line wrong: "past Beardsley,
Butcher and Fenwick and took it into the box, where he went around Peter
Shilton" names three defenders between Maradona and the "he" that means him,
and every one of those three has no touch in the passage, only a `Pressure` or
a `Dribbled Past`. Being beaten is not having the ball.

**The actor of a claim is read from the words around it, in order.** A name
before the claim and after the last one owns it ("Beardsley and Reid closed him
down"), several names before it all own it, a name after it owns it when none
came before ("We won it back through Cuciuffo", which is the framework's action
before name), and with no name either side it belongs to the player with the
ball ("and finished with his left"). A name taken as a chain's target or as the
defender in "past X" is spoken for and does not become anybody's actor.

**Which way the ball went is read now, and it used to be prose.** "Forward"
and "back" are a claim about the change in x on a pass or a carry, "drove" and
"ran" are a claim about a carry with yards in it, and a carry never delivers
the ball to another player. The live run of 2026-10-31 wrote all three
mistakes: a pass of 38 yards up the pitch called a carry back to the man who
played it, and "drove forward" over a carry of 0.7 yards. Every one of them
read as prose and passed.

**What it cannot read.** The same blunt edge the cited reading has: nothing in
the text says which name goes with which claim, so a clause with two claims and
two free names pairs both with both. A direction is held by any pass or carry
of that player's that went that way rather than by the one the words were said
about, which is the same bluntness and the same price. And the lexicon is
narrow on purpose, like `ACTION_CLAIMS`: a word that is not in the tables below
is prose rather than a claim, so "turned", "advanced" and "the whole way" are
checked against nothing.

Standard library only, like the rest of `app/`.
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Mapping, Sequence

from app.narration_prompt import (
    LONG_PASS_YARDS,
    TOUCH_ACTIONS,
    Beat,
    Facts,
    Spot,
)

#: A word, with the apostrophe kept so "O'Brien" survives and the accented
#: letters kept so "Álvarez" is one word.
WORD = re.compile(r"[A-Za-zÀ-ɏ][A-Za-zÀ-ɏ'’-]*")

#: A possessive ending, taken off before any name lookup: the word pattern
#: keeps apostrophes, so "Cuciuffo's" arrives with its ending attached.
_POSSESSIVE = re.compile(r"(?:['’]s|['’])$")

#: A clause break, which is as far as the framework's action before name
#: reaches. "We won it back through Cuciuffo" puts the player after the action
#: in one clause; "picked it up in his own half, and though Beardsley and Reid
#: closed him down" puts a comma between the two, and the Beardsley on the
#: other side of it is nobody's actor for the half the ball was in.
CLAUSE_BREAK = re.compile(r"[,;:]")

#: How far a run may stray from the straight line between its two ends and
#: still be called straight, in StatsBomb's yards. Five is loose enough that a
#: carry drifting a yard or two is not called a curve and tight enough to
#: refuse the 1986 run, which strays sixteen.
STRAIGHT_TOLERANCE_YARDS = 5.0

#: How far up or down the pitch the ball has to go before a narration may call
#: it forward or back, in StatsBomb's yards of x.
#:
#: Two is a gap in the data rather than a view about football. Six records in
#: the two hero passages move the ball less than a yard in x: five carries of
#: 0.2 to 0.8 yards, where a player takes a touch and stands still, and
#: Maradona's last carry of 0.6 before the shot. Nothing in either passage
#: moves it between 0.8 and 9.0. So the threshold sits in that gap with room
#: on both sides, and "he carried it forward" over a player standing still is
#: refused while every pass and carry either passage would call forward is
#: held.
DIRECTION_YARDS = 2.0

#: How long a carry has to be before a narration may call it a run, in
#: StatsBomb's yards.
#:
#: Ten is Shawn's number and the data agrees with it: Maradona's three long
#: carries are 34.9, 16.8 and 16.7 yards, and every other carry in either
#: passage is 1.1 yards or less. The live run of 2026-10-31 wrote "drove
#: forward" and "drove ahead" about Álvarez, whose one carry is 0.7 yards.
RUN_YARDS = 10.0


def bare(folded_word: str) -> str:
    """Drop a possessive ending, so "Argentina's" matches "Argentina"."""
    return _POSSESSIVE.sub("", folded_word)


def fold(text: str) -> str:
    """Lowercase and strip accents, so "Hector" matches "Héctor"."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


#: Number words a duration claim may be written with. A goal call says "in
#: under ten seconds" and not "in under 10 seconds", because the framework
#: allows no digit anywhere.
NUMBER_WORDS: Mapping[str, int] = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "fifteen": 15,
    "twenty": 20,
    "thirty": 30,
}

_NUMBER_WORD = "|".join(NUMBER_WORDS)

#: The phrases a goal call is built out of, longest first within a start
#: position. Each is `(pattern, kind, detail)`, and `app/grounding.py` is what
#: decides whether the records hold the move a hit becomes.
#:
#: They are matched on the sentence as written, case insensitively, and a hit
#: that overlaps an earlier one is dropped, which is what lets "his left foot"
#: win over "left foot" and "closed him down" swallow the "him" inside it.
#:
#: Narrow on purpose. Every phrase here is one the framework asks for or one of
#: the eight references says; a phrase nobody says is a phrase nothing has
#: measured.
PHRASES: Sequence[tuple[str, str, object]] = (
    # A duration, which is the span of the passage rather than a clock.
    (rf"in under ({_NUMBER_WORD}) seconds?", "duration", "under"),
    (rf"under ({_NUMBER_WORD}) seconds?", "duration", "under"),
    (rf"in over ({_NUMBER_WORD}) seconds?", "duration", "over"),
    (rf"over ({_NUMBER_WORD}) seconds?", "duration", "over"),
    # Pressure, said the way a commentator says it. StatsBomb records the
    # player applying it and nobody being pressed, so the pronoun inside each
    # phrase is swallowed by it rather than resolved and checked.
    (r"closed (?:him|her|them|it) down", "action", ("Pressure",)),
    (r"closed down", "action", ("Pressure",)),
    (r"came back at (?:him|her|them|it)", "action", ("Pressure",)),
    (r"came back at", "action", ("Pressure",)),
    (r"under pressure", "pressured", None),
    # Winning the ball back, which is a Ball Recovery and not a Foul Won.
    (r"won it back", "action", ("Ball Recovery",)),
    (r"wins? it back", "action", ("Ball Recovery",)),
    # Having the ball at all, which is any of the records that put it at a
    # player's feet.
    (r"picked it up", "touch", None),
    (r"picks it up", "touch", None),
    # The ball going in, which is the plainest English for the finish and
    # was a false refusal until the live run of 2026-10-31 found it. Nine of
    # eighteen candidates were dropped and this was in every one of the nine:
    # "shot with his left foot and the ball went in" passed because "shot" is
    # a Shot claim, and "and the ball went in" alone did not, although the
    # moment is a goal and the record says `outcome` Goal. The framework in
    # `docs/VOICE.md` asks a narration to land the finish, so refusing the
    # words it lands on was this module's mistake.
    (r"(?:the ball |it )?went in", "action", ("Shot",)),
    (r"found the net", "action", ("Shot",)),
    # The shot struck without a touch to control it first.
    (r"with one touch", "first_time", None),
    (r"one touch", "first_time", None),
    (r"first time", "first_time", None),
    # A pass the game calls a long ball. It is merged into the chain beside it
    # where there is one, so that one record has to be both.
    (r"long ball", "long_pass", None),
    (r"long pass", "long_pass", None),
    # Where on the pitch, which is a coordinate against one of two lines.
    (r"his own half", "position", "own half"),
    (r"their own half", "position", "own half"),
    (r"own half", "position", "own half"),
    (r"into the box", "position", "the box"),
    (r"in the box", "position", "the box"),
    (r"inside the box", "position", "the box"),
    (r"the box", "position", "the box"),
    (r"the penalty area", "position", "the box"),
    # How the possession started.
    (r"on the counter", "pattern", "From Counter"),
    (r"the counter", "pattern", "From Counter"),
    # The shape of the run, which the start and end of every carry can refuse.
    (r"straight", "straight", None),
    # Which way the ball went, which the two ends of a pass or a carry can
    # refuse. StatsBomb mirrors a defensive record's coordinates, so x rising
    # is the recorded player's own attacking direction whichever team they are
    # on, and the change in x is what "forward" and "back" are about.
    #
    # "Back" is the word the live run of 2026-10-31 got wrong three times
    # over, calling Álvarez's 38 yard ball up the pitch a ball back to
    # MacAllister. The longer phrases that hold "back" sit above this one and
    # swallow it, so "won it back" is still a recovery and "came back at him"
    # is still pressure.
    (r"forwards?", "direction", "forward"),
    (r"upfield", "direction", "forward"),
    (r"ahead", "direction", "forward"),
    (r"backwards?", "direction", "back"),
    (r"back", "direction", "back"),
    # A run: a carry with yards in it rather than a touch on the spot. These
    # words say a player covered ground, which is a claim about how long a
    # recorded carry was.
    (
        r"(?:drove|driving|drives|drive|ran|running|runs|burst|bursting"
        r"|bursts|charged|charging|surged|surging|raced|racing|sprinted"
        r"|sprinting|stormed|storming|powered|powering)",
        "run",
        None,
    ),
    # The body part, which is the goal's and not a pass's.
    (r"(?:with )?his left foot", "body_part", "Left Foot"),
    (r"(?:with )?his right foot", "body_part", "Right Foot"),
    (r"left foot", "body_part", "Left Foot"),
    (r"right foot", "body_part", "Right Foot"),
    (r"his left", "body_part", "Left Foot"),
    (r"his right", "body_part", "Right Foot"),
    (r"header", "body_part", "Head"),
    (r"headed", "body_part", "Head"),
)

#: The phrases that introduce the player a pass reached, and whether the pass
#: has to be the one that set the goal up.
#:
#: A marker is only a chain when a name follows it. "in the box to score" has
#: the bare marker in it and no name after it, so nothing is claimed by the
#: "to"; `read` drops a marker whose next hit is not a name.
CHAIN_MARKERS: Sequence[tuple[str, bool]] = (
    (r"played it on to", False),
    (r"played it to", False),
    (r"played it into", False),
    (r"gave it to", False),
    (r"gives it to", False),
    (r"moved it on to", False),
    (r"moved it to", False),
    (r"slipped it to", False),
    (r"laid it off to", False),
    (r"set it up for", True),
    (r"set up", True),
    (r"found", False),
    (r"on to", False),
    (r"to", False),
)

#: The chain markers that carry no verb of their own, so the verb in front of
#: them is the one that delivered the ball. "Molina to MacAllister" says the
#: pass with the preposition alone; "carried it to MacAllister" says it with a
#: carry, and a carry keeps the ball at the player's own feet.
#:
#: **They are also the markers that may follow the ball rather than the
#: sentence.** A bare marker continues a journey: "Molina to MacAllister on
#: to Messi" is the ball going on from whoever just received it, so its
#: source is the player with the ball. A marker carrying its own verb asserts
#: a new action, and an action belongs to the subject of the clause it was
#: said in. `Reader.read` is where the two part company, and
#: `_subject_of_the_clause` is why.
BARE_CHAIN_MARKERS = frozenset({"to", "on to"})

#: A second verb between an action and a bare chain marker. "Carried and
#: played it back to MacAllister" has one, so the carry is not what delivered
#: the ball and only the "back" is wrong; "carried it back to MacAllister" has
#: none, so the carry is being asked to do a pass's job.
ANOTHER_VERB = re.compile(r"\b(?:and|then|before|who|which|that)\b", re.I)

#: The prepositions that name a defender who was beaten. The player beaten is
#: spoken for by the preposition, so they never become the actor of the next
#: claim and never become what a pronoun means.
PAST_MARKERS = (r"past", r"around", r"round")

#: The pronouns a goal call follows the ball with. Each resolves to the player
#: with the ball and asserts nothing of its own.
PRONOUNS = (r"he", r"his", r"him", r"himself", r"who", r"whose", r"whom")


def _clause_start(text: str, at: int) -> tuple[int, int]:
    """Where the clause holding `at` begins, and where `at` is.

    Used by the actor rule, which may not reach a name on the other side of a
    comma. `app/grounding.py` has its own clause span for the first person;
    they are the same idea applied to two different rules.
    """
    before = [match.end() for match in CLAUSE_BREAK.finditer(text, 0, at)]
    return (before[-1] if before else 0), at


@dataclass(frozen=True)
class Move:
    """One thing a goal call asserts, and where in the sentence it said it.

    `actor` and `target` are full recorded player names, or a team name for
    `actor` where a team did the thing ("Argentina were on the counter"), or
    `None` where the words named nobody. `said` is the words themselves, for a
    refusal somebody has to recognise.
    """

    kind: str
    said: str
    at: int
    actor: str | None = None
    target: str | None = None
    detail: object = None

    def __str__(self) -> str:
        return self.said


def recorded_spellings(facts: Facts) -> Mapping[str, tuple[str, ...]]:
    """Full recorded player name to every spelling the match records for them.

    Two per player at most: the event feed's full name, and the lineups file's
    `player_nickname` where there is one. Both are the data's own, which is why
    a narration may say either; see `app/recorded_names.py`.
    """
    out: dict[str, set[str]] = {}
    for beat in facts.beats:
        out.setdefault(beat.player, set()).add(beat.player)
        if beat.nickname:
            out[beat.player].add(beat.nickname)
    return {player: tuple(sorted(names)) for player, names in out.items()}


def name_keys(facts: Facts) -> Mapping[str, tuple[str, ...]]:
    """Every run of words in a recorded name, folded, to the players it fits.

    A goal call says the shortest name that picks out one player, so the key is
    any contiguous run of the words of a recorded spelling: "Shilton", "Peter
    Shilton" and "Peter" are all keys of the 1986 buildup, and the last of them
    fits three players.

    A key fitting more than one player is what makes "Terry" and "Peter"
    refusable: the value is a tuple, and `app/grounding.py` refuses any key
    whose tuple is not exactly one player long. That is the price of short
    names and it is paid by the narration rather than by the listener.
    """
    keys: dict[str, set[str]] = {}
    for player, spellings in recorded_spellings(facts).items():
        for spelling in spellings:
            parts = [fold(part) for part in WORD.findall(spelling)]
            for start in range(len(parts)):
                for end in range(start + 1, len(parts) + 1):
                    keys.setdefault(" ".join(parts[start:end]), set()).add(
                        player
                    )
    return {key: tuple(sorted(players)) for key, players in keys.items()}


def touched(facts: Facts) -> frozenset[str]:
    """Every player with a recorded touch, by full recorded name.

    This is what a pronoun resolves against: the move is followed by whoever
    has the ball, and `TOUCH_ACTIONS` in `app/narration_prompt.py` is the list
    of records that say somebody did.
    """
    return frozenset(
        beat.player for beat in facts.beats if beat.action in TOUCH_ACTIONS
    )


@dataclass(frozen=True)
class _Hit:
    """One thing the scanner found in a sentence, before it is a `Move`."""

    kind: str
    said: str
    at: int
    end: int
    detail: object = None
    #: For a name hit: the players the key fits, which is one when it resolves.
    players: tuple[str, ...] = ()


def _phrase_hits(text: str) -> list[_Hit]:
    found: list[_Hit] = []
    for pattern, kind, detail in PHRASES:
        for match in re.finditer(rf"\b{pattern}\b", text, re.IGNORECASE):
            value = detail
            if kind == "duration":
                value = (detail, NUMBER_WORDS[match.group(1).lower()])
            found.append(
                _Hit(kind, match.group(0), match.start(), match.end(), value)
            )
    for pattern, assist in CHAIN_MARKERS:
        for match in re.finditer(rf"\b{pattern}\b", text, re.IGNORECASE):
            found.append(
                _Hit(
                    "chain_marker",
                    match.group(0),
                    match.start(),
                    match.end(),
                    assist,
                )
            )
    for pattern in PAST_MARKERS:
        for match in re.finditer(rf"\b{pattern}\b", text, re.IGNORECASE):
            found.append(
                _Hit("past_marker", match.group(0), match.start(), match.end())
            )
    for pattern in PRONOUNS:
        for match in re.finditer(rf"\b{pattern}\b", text, re.IGNORECASE):
            found.append(
                _Hit("pronoun", match.group(0), match.start(), match.end())
            )
    return found


def _capitalised_runs(text: str) -> list[list[re.Match]]:
    """The runs of adjacent capitalised words, which is where a name can be."""
    runs: list[list[re.Match]] = []
    previous: re.Match | None = None
    for match in WORD.finditer(text):
        if not match.group(0)[0].isupper():
            previous = None
            continue
        joined = previous is not None and text[previous.end():match.start()].strip() == ""
        if joined and runs:
            runs[-1].append(match)
        else:
            runs.append([match])
        previous = match
    return runs


def _name_hits(
    text: str,
    keys: Mapping[str, tuple[str, ...]],
    teams: Sequence[str],
    demonyms: Mapping[str, str],
    not_a_name: frozenset[str],
) -> list[_Hit]:
    """Every name a sentence says, longest run first, resolved or reported.

    A run of capitalised words is read from the left, longest match first, so
    "Peter Shilton" is one name and not a shared forename followed by a
    surname. A word that matches nothing is a hit all the same, with no player
    on it, because an invented name has to be refused rather than skipped.
    """
    folded_teams = {fold(team): team for team in teams}
    found: list[_Hit] = []
    for run in _capitalised_runs(text):
        index = 0
        while index < len(run):
            best: tuple[int, tuple[str, ...]] | None = None
            for length in range(len(run) - index, 0, -1):
                words = run[index:index + length]
                key = " ".join(bare(fold(word.group(0))) for word in words)
                if key in keys:
                    best = (length, keys[key])
                    break
            if best is not None:
                length, players = best
                words = run[index:index + length]
                found.append(
                    _Hit(
                        "name",
                        text[words[0].start():words[-1].end()],
                        words[0].start(),
                        words[-1].end(),
                        players=players,
                    )
                )
                index += length
                continue

            word = run[index]
            said = word.group(0)
            folded = bare(fold(said))
            index += 1
            if folded in folded_teams:
                found.append(
                    _Hit("team", said, word.start(), word.end(),
                         detail=folded_teams[folded])
                )
            elif folded in demonyms:
                found.append(
                    _Hit("team", said, word.start(), word.end(),
                         detail=demonyms[folded])
                )
            elif folded in not_a_name:
                continue
            else:
                found.append(_Hit("name", said, word.start(), word.end()))
    return found


def _action_hits(
    text: str, actions: Mapping[str, frozenset[str]], taken: Sequence[_Hit]
) -> list[_Hit]:
    """The one-word action claims left over once the phrases are out.

    `actions` is `ACTION_CLAIMS` from `app/grounding.py`, so a verb grounds the
    same event types whichever reading is in force. It is passed in rather than
    imported because `app/grounding.py` imports this module.
    """
    covered = [(hit.at, hit.end) for hit in taken]
    found: list[_Hit] = []
    for match in WORD.finditer(text):
        if any(start <= match.start() < end for start, end in covered):
            continue
        folded = bare(fold(match.group(0)))
        if folded in actions:
            found.append(
                _Hit(
                    "action",
                    match.group(0),
                    match.start(),
                    match.end(),
                    tuple(sorted(actions[folded])),
                )
            )
    return found


def _without_overlaps(hits: Sequence[_Hit]) -> list[_Hit]:
    """The hits in reading order, dropping any that overlaps a longer one.

    Sorted by where it starts and then by length, longest first, so the longer
    phrase wins at a shared start: "his left foot" over "left foot", "moved it
    on to" over "on to" and then over "to".
    """
    ordered = sorted(hits, key=lambda hit: (hit.at, -(hit.end - hit.at)))
    kept: list[_Hit] = []
    reach = -1
    for hit in ordered:
        if hit.at < reach:
            continue
        kept.append(hit)
        reach = hit.end
    return kept


@dataclass
class Reader:
    """Reads goal-call sentences in order, following the ball between them.

    One reader per narration, because the player a pronoun means carries across
    a full stop: the 2022 Storyteller's second sentence opens "He set it up for
    Di María", and the "He" is the MacAllister its first sentence ended on.
    """

    facts: Facts
    not_a_name: frozenset[str]
    demonyms: Mapping[str, str]
    actions: Mapping[str, frozenset[str]]
    tracked: str | None = None

    def __post_init__(self) -> None:
        self.keys = name_keys(self.facts)
        self.touched = touched(self.facts)
        self.text = ""

    def read(self, text: str) -> tuple[Move, ...]:
        """One sentence as the moves it makes, in the order it makes them."""
        self.text = text
        phrases = _phrase_hits(text)
        names = _name_hits(
            text, self.keys, self.facts.teams, self.demonyms, self.not_a_name
        )
        taken = _without_overlaps(list(phrases) + list(names))
        hits = _without_overlaps(
            taken + _action_hits(text, self.actions, taken)
        )

        moves: list[Move] = []
        free: list[tuple[str, int]] = []
        # (whether it has to be the assist, who played it, the words said,
        #  the carry being asked to deliver the ball or None)
        pending_chain: tuple[bool, str | None, str, _Hit | None] | None = None
        #: The actor of the last chain read, and where its clause began. A
        #: second chain in that same clause, with no name or pronoun between
        #: them, is a second verb on the same subject and keeps that actor.
        #: See `_subject_of_the_clause`.
        last_chain: tuple[str | None, int] | None = None
        past_open = False
        #: The last action claim, for the rule about a carry that delivers.
        recent_action: _Hit | None = None

        def claim(hit: _Hit, kind: str, detail: object = None) -> None:
            """A claim about somebody, with the actor read from the words.

            Only names in the claim's own clause can own it. Without that, "We
            won it back through Cuciuffo, and Maradona scored" pairs the shot
            with Cuciuffo as well as with Maradona, because both names are
            free and nothing but the comma says the first one is done with.
            """
            nonlocal free, past_open
            past_open = False
            start, _ = _clause_start(text, hit.at)
            actors = [
                player for player, at in free if at >= start
            ] or [self._ahead(hits, hit)]
            actors = [actor for actor in actors if actor] or [self.tracked]
            for actor in actors:
                moves.append(
                    Move(kind, hit.said, hit.at, actor=actor, detail=detail)
                )
            free = []

        for hit in hits:
            if pending_chain is not None and hit.kind not in ("name", "team"):
                pending_chain = None

            if hit.kind == "name":
                if len(hit.players) != 1:
                    moves.append(
                        Move(
                            "ambiguous_name" if hit.players else "unknown_name",
                            hit.said,
                            hit.at,
                            detail=hit.players,
                        )
                    )
                    continue
                player = hit.players[0]
                if pending_chain is not None:
                    assist, source, marker, carried = pending_chain
                    moves.append(
                        Move(
                            "chain",
                            f"{marker} {hit.said}",
                            hit.at,
                            actor=source,
                            target=player,
                            detail={"assist": assist, "long": False},
                        )
                    )
                    self._merge_long(moves)
                    if carried is not None:
                        moves.append(
                            Move(
                                "carry_delivery",
                                text[carried.at:hit.end],
                                carried.at,
                                actor=source,
                                target=player,
                            )
                        )
                    last_chain = (source, _clause_start(text, hit.at)[0])
                    pending_chain = None
                    recent_action = None
                    free = []
                elif past_open:
                    moves.append(
                        Move("past", hit.said, hit.at,
                             actor=self.tracked, target=player)
                    )
                else:
                    moves.append(Move("name", hit.said, hit.at, actor=player))
                    free.append((player, hit.at))
                    last_chain = None
                if player in self.touched:
                    self.tracked = player

            elif hit.kind == "team":
                team = str(hit.detail)
                moves.append(Move("team", hit.said, hit.at, actor=team))
                free.append((team, hit.at))

            elif hit.kind == "pronoun":
                past_open = False
                last_chain = None
                if self.tracked:
                    free = [(self.tracked, hit.at)]

            elif hit.kind == "chain_marker":
                source = self._chain_source(text, hit, free, last_chain)
                pending_chain = (
                    bool(hit.detail),
                    source,
                    hit.said,
                    self._carry_delivering(text, hit, recent_action),
                )
                free = []
                past_open = False

            elif hit.kind == "past_marker":
                past_open = True
                free = []

            elif hit.kind == "action":
                claim(hit, "action", tuple(hit.detail or ()))
                recent_action = hit

            elif hit.kind == "long_pass":
                claim(hit, "long_pass")
                # The long ball names the pass itself, so whatever verb came
                # before it is not what delivered the ball.
                recent_action = None

            elif hit.kind in (
                "touch",
                "pressured",
                "first_time",
                "position",
                "pattern",
                "straight",
                "body_part",
                "direction",
                "run",
            ):
                claim(hit, hit.kind, hit.detail)

            elif hit.kind == "duration":
                moves.append(
                    Move("duration", hit.said, hit.at, detail=hit.detail)
                )

        return tuple(moves)

    def _chain_source(
        self,
        text: str,
        marker: _Hit,
        free: Sequence[tuple[str, int]],
        last_chain: tuple[str | None, int] | None,
    ) -> str | None:
        """Who this chain says played the ball.

        Three answers, in order, and the middle one is the fix for what the
        run of 2026-11-05 got away with.

        **A name or a pronoun in the marker's own clause.** That is the
        sentence saying who, and nothing overrides it. "MacAllister set up Di
        María" and "he set up Di María" are both this.

        **Otherwise the subject of the clause, where a chain already
        established one.** "We won it back through Cuciuffo, who passed to
        Enrique and set up Maradona" says Cuciuffo set up Maradona: "and"
        joins a second verb to the same subject. The ball moved on to
        Enrique, and Enrique is the player the records show with the assist,
        so reading the actor off the ball made a false sentence pass on
        twenty-one claims. The subject of the clause did not move, and this
        is what keeps the two apart. A bare marker is exempt, because it
        asserts no verb of its own: "Molina to MacAllister on to Messi" is
        the ball continuing and its source really is whoever has it.

        **Otherwise the player with the ball.** A clause that establishes no
        subject at all is the framework's action before name, and following
        the ball is the only reading left.
        """
        if free:
            return free[-1][0]
        if last_chain is not None and fold(
            marker.said
        ) not in BARE_CHAIN_MARKERS:
            actor, clause = last_chain
            if _clause_start(text, marker.at)[0] == clause:
                return actor
        return self.tracked

    def _ahead(self, hits: Sequence[_Hit], hit: _Hit) -> str | None:
        """The name just after a claim, for the framework's action before name.

        "We won it back through Cuciuffo" puts the action first and the player
        second, which is the order a listener hears the move in. So a claim with
        no free name before it looks at the next hit, and takes it only if it is
        a name that resolves: anything else between the two means the name
        belongs to something other than this claim.
        """
        following = [other for other in hits if other.at > hit.at]
        if not following:
            return None
        nxt = following[0]
        if CLAUSE_BREAK.search(self.text, hit.end, nxt.at):
            return None
        if nxt.kind == "name" and len(nxt.players) == 1:
            return nxt.players[0]
        if nxt.kind == "team":
            return str(nxt.detail)
        return None

    @staticmethod
    def _carry_delivering(
        text: str, marker: _Hit, recent_action: _Hit | None
    ) -> _Hit | None:
        """The carry a bare chain marker is asking to deliver the ball, if any.

        Three things have to hold. The marker carries no verb of its own, so
        the verb in front of it is the one doing the work: "found MacAllister"
        and "played it to MacAllister" say the pass themselves and are not
        this. The action in front of it is a carry and nothing else, so "hit a
        long ball to Vance" and "passed to Enrique" are not this either. And
        it is in the same clause with no second verb between the two, so
        "carried and played it back to MacAllister" is two verbs and only the
        direction in it is wrong, while "carried it back to MacAllister" is a
        carry being asked to do a pass's job.
        """
        if recent_action is None:
            return None
        if fold(marker.said) not in BARE_CHAIN_MARKERS:
            return None
        if set(recent_action.detail or ()) != {"Carry"}:
            return None
        start, _ = _clause_start(text, marker.at)
        if recent_action.at < start:
            return None
        if ANOTHER_VERB.search(text, recent_action.end, marker.at):
            return None
        return recent_action

    def _merge_long(self, moves: list[Move]) -> None:
        """Fold "a long ball" into the chain it was said about.

        "A long ball forward to MacAllister again" is one pass, so one record
        has to be both long and a pass to MacAllister. Left as two moves they
        could be satisfied by two different passes, which is the bluntness this
        one case can cheaply avoid.

        The walk steps over a direction or a run on the way back, because
        "forward" sits between the long ball and the chain in three of the
        eight references and the two moves are still about the one pass.
        """
        if len(moves) < 2 or moves[-1].kind != "chain":
            return
        chain = moves[-1]
        for index in range(len(moves) - 2, -1, -1):
            earlier = moves[index]
            if earlier.kind == "long_pass" and earlier.actor == chain.actor:
                detail = dict(chain.detail or {})
                detail["long"] = True
                moves[-1] = Move(
                    chain.kind,
                    f"{earlier.said} {chain.said}",
                    earlier.at,
                    actor=chain.actor,
                    target=chain.target,
                    detail=detail,
                )
                moves.pop(index)
                return
            if earlier.kind not in ("name", "team", "direction", "run"):
                return


def player_spots(facts: Facts, player: str) -> tuple[Spot, ...]:
    """Everywhere a player is recorded as having been, in order.

    The start of each of their records, and the end of each of their carries,
    because a carry is the one record that moves the player rather than the
    ball alone. A pass ends where the ball arrived and the passer did not go
    with it: MacAllister's assist ends inside the box and he played it from
    four yards outside, so counting a pass's end would have him in the box.
    """
    spots: list[Spot] = []
    for beat in facts.beats:
        if beat.player != player:
            continue
        if beat.start:
            spots.append(beat.start)
        if beat.action == "Carry" and beat.end:
            spots.append(beat.end)
    return tuple(spots)


def carry_path(facts: Facts, player: str) -> tuple[Spot, ...]:
    """The path a player's carries took the ball along, in order."""
    path: list[Spot] = []
    for beat in facts.beats:
        if beat.player != player or beat.action != "Carry":
            continue
        if beat.start:
            path.append(beat.start)
        if beat.end:
            path.append(beat.end)
    return tuple(path)


def change_in_x(beat: Beat) -> float | None:
    """How far up the pitch one record took the ball, or `None` without both
    ends.

    Positive is towards the goal the recorded player's team is attacking,
    because StatsBomb mirrors a defensive record's coordinates. So this reads
    the same way for either team and is what "forward" and "back" are a claim
    about.
    """
    if beat.start is None or beat.end is None:
        return None
    return beat.end.x - beat.start.x


def carry_yards(beat: Beat) -> float | None:
    """How far one carry took the ball, or `None` for a record with no end.

    The straight-line distance between the two ends, which is what "a ten
    yard run" means. The path inside a single carry is not recorded, so there
    is nothing longer to measure.
    """
    if beat.start is None or beat.end is None:
        return None
    return (
        (beat.end.x - beat.start.x) ** 2 + (beat.end.y - beat.start.y) ** 2
    ) ** 0.5


def strays_from_straight(path: Sequence[Spot]) -> float | None:
    """How far a path strays from the straight line between its two ends.

    The largest perpendicular distance from that line, in yards, or `None` for
    a path with nothing to measure. This is what refuses "straight into the
    box" over the 1986 run: it goes out to the touchline and back, sixteen
    yards off the line from where it started to where it finished.
    """
    if len(path) < 3:
        return None
    first, last = path[0], path[-1]
    run_x, run_y = last.x - first.x, last.y - first.y
    length = (run_x * run_x + run_y * run_y) ** 0.5
    if not length:
        return None
    worst = 0.0
    for point in path[1:-1]:
        cross = abs(
            run_x * (point.y - first.y) - run_y * (point.x - first.x)
        )
        worst = max(worst, cross / length)
    return worst


def _went(change: float | None, sense: str) -> bool:
    """Whether a change in x is forward or back by enough to be called it."""
    if change is None:
        return False
    if sense == "forward":
        return change >= DIRECTION_YARDS
    return change <= -DIRECTION_YARDS


def support(move: Move, facts: Facts) -> tuple[Beat, ...]:
    """The records that hold this move, or nothing when none does.

    Every reading in this module ends here: a move with support is grounded,
    and a move without it is what `app/grounding.py` turns into a refusal. The
    records are returned rather than a verdict because the first person needs
    them: "we" has to stand over the listener side's own play, and whose play
    it was is the team on the record.
    """
    beats = facts.beats
    kind = move.kind

    def mine(beat: Beat) -> bool:
        return move.actor is None or beat.player == move.actor or (
            beat.team == move.actor
        )

    if kind in ("name", "team"):
        return tuple(beat for beat in beats if mine(beat))

    if kind == "touch":
        return tuple(
            beat
            for beat in beats
            if mine(beat) and beat.action in TOUCH_ACTIONS
        )

    if kind == "action":
        wanted = set(move.detail or ())
        return tuple(
            beat for beat in beats if mine(beat) and beat.action in wanted
        )

    if kind == "chain":
        detail = move.detail or {}
        return tuple(
            beat
            for beat in beats
            if beat.action == "Pass"
            and beat.player == move.actor
            and beat.recipient == move.target
            and (beat.goal_assist or not detail.get("assist"))
            and (beat.long_pass or not detail.get("long"))
        )

    if kind == "long_pass":
        return tuple(
            beat for beat in beats if mine(beat) and beat.long_pass
        )

    if kind == "direction":
        return tuple(
            beat
            for beat in beats
            if mine(beat)
            and beat.action in ("Pass", "Carry")
            and _went(change_in_x(beat), str(move.detail))
        )

    if kind == "run":
        return tuple(
            beat
            for beat in beats
            if mine(beat)
            and beat.action == "Carry"
            and (carry_yards(beat) or 0.0) >= RUN_YARDS
        )

    if kind == "carry_delivery":
        # Never held, and not because the records were searched: a carry is
        # the record of a player moving with the ball at his own feet, so
        # there is no carry anywhere that gives it to somebody else.
        return ()

    if kind == "past":
        beaten = [
            beat
            for beat in beats
            if beat.action == "Dribbled Past" and beat.player == move.target
        ]
        dribbles = [
            beat
            for beat in beats
            if beat.action == "Dribble"
            and (move.actor is None or beat.player == move.actor)
        ]
        held = [
            (beat, dribble)
            for beat in beaten
            for dribble in dribbles
            if (beat.minute, beat.second) == (dribble.minute, dribble.second)
        ]
        return held[0] if held else ()

    if kind == "pressured":
        return tuple(beat for beat in beats if mine(beat) and beat.under_pressure)

    if kind == "first_time":
        goal = facts.goal_beat
        if goal.first_time and (move.actor is None or goal.player == move.actor):
            return (goal,)
        return ()

    if kind == "body_part":
        goal = facts.goal_beat
        return (goal,) if facts.body_part == move.detail else ()

    if kind == "position":
        for beat in beats:
            if not mine(beat):
                continue
            for place in player_spots(facts, beat.player):
                if move.detail == "own half" and place.in_own_half:
                    return (beat,)
                if move.detail == "the box" and place.in_the_box:
                    return (beat,)
        return ()

    if kind == "pattern":
        return tuple(
            beat
            for beat in beats
            if mine(beat) and beat.play_pattern == move.detail
        )

    if kind == "straight":
        player = move.actor
        if not player:
            return ()
        strays = strays_from_straight(carry_path(facts, player))
        if strays is None or strays > STRAIGHT_TOLERANCE_YARDS:
            return ()
        return tuple(
            beat
            for beat in beats
            if beat.player == player and beat.action == "Carry"
        )

    if kind == "duration":
        sense, wanted = move.detail
        span = facts.seconds
        if span is None:
            return ()
        if sense == "under" and span < wanted:
            return tuple(beats)
        if sense == "over" and span > wanted:
            return tuple(beats)
        return ()

    return ()


def why(move: Move, facts: Facts) -> str:
    """Why the records do not hold this move, said for a refusal report."""
    actor = move.actor or "the player with the ball"
    if move.kind == "unknown_name":
        return f"{move.said!r} is nobody this passage records"
    if move.kind == "ambiguous_name":
        fits = ", ".join(move.detail or ())
        return (
            f"{move.said!r} fits {len(move.detail or ())} players in this "
            f"passage ({fits}), so it names none of them"
        )
    if move.kind == "chain":
        detail = move.detail or {}
        kind = "pass"
        if detail.get("assist"):
            kind = "pass recorded as the assist"
        if detail.get("long"):
            kind = f"long {kind}"
        return (
            f"{move.said!r}: no {kind} from {actor} to {move.target} is "
            "recorded in this passage"
        )
    if move.kind == "past":
        return (
            f"{move.said!r}: the records hold no dribble past {move.target} "
            f"by {actor}"
        )
    if move.kind == "touch":
        return f"{move.said!r}: no record puts the ball at {actor}'s feet here"
    if move.kind == "action":
        wanted = " or ".join(sorted(move.detail or ()))
        return (
            f"{move.said!r} claims a {wanted} event, and no record of "
            f"{actor} in this passage is one"
        )
    if move.kind == "long_pass":
        return (
            f"{move.said!r}: no pass by {actor} reaches "
            f"{LONG_PASS_YARDS:.0f} yards"
        )
    if move.kind == "direction":
        moved = [
            change_in_x(beat)
            for beat in facts.beats
            if (move.actor is None or beat.player == move.actor)
            and beat.action in ("Pass", "Carry")
        ]
        measured = [change for change in moved if change is not None]
        if not measured:
            return (
                f"{move.said!r}: no pass or carry of {actor} in this passage "
                "has both ends recorded, so there is nothing to measure"
            )
        furthest = max(measured, key=abs)
        went = "forward" if furthest > 0 else "back"
        return (
            f"{move.said!r}: no pass or carry of {actor} takes the ball "
            f"{move.detail} by {DIRECTION_YARDS:.0f} yards; the furthest any "
            f"of them moves it is {abs(furthest):.0f} {went}"
        )
    if move.kind == "run":
        carries = [
            carry_yards(beat)
            for beat in facts.beats
            if (move.actor is None or beat.player == move.actor)
            and beat.action == "Carry"
        ]
        measured = [yards for yards in carries if yards is not None]
        if not measured:
            return (
                f"{move.said!r}: no carry by {actor} is recorded in this "
                "passage, so he covered no ground with the ball"
            )
        return (
            f"{move.said!r}: no carry by {actor} reaches "
            f"{RUN_YARDS:.0f} yards; the longest is {max(measured):.0f}"
        )
    if move.kind == "carry_delivery":
        return (
            f"{move.said!r}: a carry keeps the ball at {actor}'s own feet, so "
            f"it cannot deliver it to {move.target}; only a pass does that"
        )
    if move.kind == "pressured":
        return f"{move.said!r}: no record of {actor} is marked under pressure"
    if move.kind == "first_time":
        return (
            f"{move.said!r}: the goal shot is not recorded as struck first "
            "time"
        )
    if move.kind == "body_part":
        recorded = facts.body_part or "not recorded"
        return f"{move.said!r} but the body part is recorded as {recorded}"
    if move.kind == "position":
        return (
            f"{move.said!r}: no recorded position of {actor} in this passage "
            f"is {move.detail}"
        )
    if move.kind == "pattern":
        held = ", ".join(sorted(facts.play_patterns)) or "nothing"
        return (
            f"{move.said!r} claims a {move.detail} possession, and the "
            f"records say {held}"
        )
    if move.kind == "straight":
        strays = strays_from_straight(carry_path(facts, move.actor or ""))
        if strays is None:
            return f"{move.said!r}: no carry by {actor} is recorded to measure"
        return (
            f"{move.said!r}: the carries stray {strays:.0f} yards from the "
            "line between where the run started and where it ended"
        )
    if move.kind == "duration":
        sense, wanted = move.detail
        span = facts.seconds
        if span is None:
            return f"{move.said!r}: the records carry no timestamp to measure"
        return (
            f"{move.said!r}: the passage runs {span:.1f} seconds, which is "
            f"not {sense} {wanted}"
        )
    return f"{move.said!r} is not held by any record in this passage"
