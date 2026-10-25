"""The grounding check: can every claim in a narration be pointed at?

`CLAUDE.md` allows "Verified from play data" only over narration whose claims
trace back to the event data, and says there is no partial credit. This module
is what decides that. It takes a narration and the `Facts` it was written from,
pulls out the claims the narration makes, and reports the ones that cannot be
pointed at.

**What it checks.** A claim is something a line asserts that the records can
confirm or refuse:

| Kind | A line claiming it | Grounded when |
| ---- | ------------------ | ------------- |
| `name` | a capitalised word | it is part of a player or team name in the buildup |
| `number` | a digit | it is a buildup minute, or the goal's second |
| `action` | "passes", "dribbles", "clears" | that event type is in the buildup |
| `shot_type` | "penalty", "free kick", "corner" | the goal shot is recorded as that |
| `body_part` | "header", "left foot" | the goal shot is recorded as that |
| `banned` | a nickname, a verdict, an em dash | never; these are refused outright |

A narration that makes **no** name or number claim is refused too, as
`unverifiable`. Prose that names nobody and quotes no clock has nothing tracing
back to the data, so there is nothing for the label to be true about. A check
that passed it would be reporting "found no problem" in a narration that
asserted nothing, which is not the same as grounded.

**What it cannot check, and this matters.** It verifies that everything a line
*names* is in the data. It does not verify that the line's reading of those
facts is right. "Maradona passes to Enrique" and "Enrique passes to Maradona"
are both grounded if both players and a pass are in the buildup, and only one
of them may be what happened. The check catches invention, which is the failure
a language model actually has; it does not catch misdescription. Any claim that
the app's narration is *correct* rests on more than this module.

Accents are normalised before matching, so "Hector" matches the recorded
"Héctor". That is a spelling variant of a player who is really there, not an
invented player, and failing it would report a hallucination that did not
happen.

Standard library only, like the rest of `app/`.
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Mapping, Sequence

from app.narration_prompt import Facts

#: Words that assert a specific StatsBomb event type. A narration using one is
#: claiming that event is in the passage, so the type has to be there.
#: Deliberately narrow: these are the actions a model adds when it drifts, and
#: a word that is not here is ordinary prose rather than a claim.
ACTION_CLAIMS: Mapping[str, str] = {
    "passes": "Pass",
    "passed": "Pass",
    "pass": "Pass",
    "dribbles": "Dribble",
    "dribbled": "Dribble",
    "dribble": "Dribble",
    "clears": "Clearance",
    "cleared": "Clearance",
    "clearance": "Clearance",
    "blocks": "Block",
    "blocked": "Block",
    "intercepts": "Interception",
    "interception": "Interception",
    "saves": "Goal Keeper",
    "save": "Goal Keeper",
    "fouls": "Foul Committed",
    "fouled": "Foul Committed",
    "foul": "Foul Committed",
    "shoots": "Shot",
    "shot": "Shot",
}

#: Words that assert the goal's recorded shot type. The highest-value entries
#: in this module: a goal becoming a penalty is a change of fact, and the run
#: of play alone does not reveal it.
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
#: dashes from copy. `scripts/scan_copy.py` enforces the same rule on the
#: static screens, which is a different surface from generated text.
BANNED_PATTERNS: Sequence[tuple[str, str]] = (
    ("verdict nickname", r"goal of the century"),
    ("verdict nickname", r"hand of god"),
    ("verdict nickname", r"\bcontrovers\w*"),
    ("verdict nickname", r"\bwonder goal\b"),
    ("verdict nickname", r"\bgreatest\b"),
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
    # Outcome claims. A buildup is one passage of play and carries no
    # scoreline, so anything about the result is outside the facts the
    # narration was written from. Both narrations in the first run that passed
    # every other check ended on "securing Argentina's victory" and "secured
    # the victory for his team", neither of which the data says.
    #
    # "win" and "won" are deliberately absent: "wins a foul" is a recorded
    # Foul Won event, and banning the word would fail every penalty buildup.
    # "score" and its forms are absent for the same reason, since the goal is
    # the thing being narrated.
    ("outcome claim", r"\bvictor\w*\b"),
    ("outcome claim", r"\btriumph\w*\b"),
    ("outcome claim", r"\bdefeat\w*\b"),
    ("outcome claim", r"\bequali[sz]er\b"),
    ("outcome claim", r"\bwinner\b"),
    ("outcome claim", r"\bchampions?\b"),
    ("outcome claim", r"\btrophy\b"),
    ("outcome claim", r"\bscoreline\b"),
    ("unearned authority", r"\bofficial\w*"),
    ("em dash", r"—"),
    ("en dash", r"–"),
)

#: Capitalised words that are ordinary prose rather than a claim about who was
#: on the pitch. Without this, the first word of every sentence is reported as
#: an invented player.
#:
#: This is a list, and a list is never finished. The first live run of the
#: pipeline failed three model attempts in a row on the word "Finally", which
#: was this module's bug and not the model's: narration is thrown away whole
#: when the check fails, so a false positive here costs a good narration and
#: makes a model look worse than it is. When the failure log shows an ordinary
#: word being reported as a name, the word belongs here.
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
    of off on once one only onto or other others out outside over own
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
    """.split()
)

#: Words that name a team by nationality rather than by its recorded name. One
#: is grounded when the team it refers to is in the buildup, so "the English
#: defender" is fine in a match England played in and refused in one it did
#: not. The table only covers the teams in `data/raw/`; a third match needs its
#: own entries, and until it has them a demonym for its teams is reported as an
#: unknown name rather than silently allowed.
TEAM_DEMONYMS = {
    "english": "England",
    "argentine": "Argentina",
    "argentinian": "Argentina",
    "argentinean": "Argentina",
    "french": "France",
}

_WORD = re.compile(r"[A-Za-zÀ-ɏ][A-Za-zÀ-ɏ'’-]*")
_NUMBER = re.compile(r"\d+")

#: A possessive ending. The word pattern keeps apostrophes so a name like
#: O'Brien survives, which also means "Argentina's" arrives with its ending
#: attached and matches no recorded name. The first live run failed twice on
#: exactly that, so the ending comes off before any lookup.
_POSSESSIVE = re.compile(r"(?:['’]s|['’])$")


def bare(folded_word: str) -> str:
    """Drop a possessive ending, so "Argentina's" matches "Argentina"."""
    return _POSSESSIVE.sub("", folded_word)


@dataclass(frozen=True)
class Claim:
    """One thing a narration asserts, and where it said it."""

    kind: str
    value: str
    line_number: int
    line: str

    def __str__(self) -> str:
        return f"line {self.line_number}: {self.kind} {self.value!r}"


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


def fold(text: str) -> str:
    """Lowercase and strip accents, so "Hector" matches "Héctor"."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def name_parts(facts: Facts) -> frozenset[str]:
    """Every word of every player and team name in the buildup, folded.

    Narration shortens "Diego Armando Maradona" to "Maradona", so the parts are
    what a line can be matched against rather than the whole name.
    """
    parts: set[str] = set()
    for name in list(facts.players) + list(facts.teams):
        for part in _WORD.findall(name):
            parts.add(fold(part))
    return frozenset(parts)


def _lines(text: str) -> list[tuple[int, str]]:
    """Numbered non-empty lines. A narration is usually one block, so a
    sentence is also treated as a line for reporting."""
    numbered = []
    for number, raw in enumerate(text.splitlines(), start=1):
        if raw.strip():
            numbered.append((number, raw.strip()))
    return numbered


def check(text: str, facts: Facts) -> GroundingResult:
    """Decide whether `text` is grounded in `facts`.

    Returns every failing claim rather than stopping at the first, and counts
    the claims it looked at so a pass means something more than "found no
    problem in a narration that asserted nothing".
    """
    known_names = name_parts(facts)
    failures: list[Claim] = []
    # The name and number claims found anywhere in the narration. These are the
    # ones that tie it to this moment, so a narration with none of them is
    # refused below however clean the rest of it looks.
    claims_made: list[str] = []
    checked = 0

    for number, line in _lines(text):
        folded = fold(line)

        for label, pattern in BANNED_PATTERNS:
            for hit in re.findall(pattern, folded):
                checked += 1
                failures.append(Claim(label, hit if isinstance(hit, str) else line, number, line))

        # Multi-word claims first, so "free kick" is not read as "kick".
        for phrase, required in SHOT_TYPE_CLAIMS.items():
            if phrase in folded:
                checked += 1
                if facts.set_piece != required:
                    recorded = facts.set_piece or "Open Play"
                    failures.append(
                        Claim(
                            "shot_type",
                            f"{phrase!r} but the shot is recorded as {recorded}",
                            number,
                            line,
                        )
                    )

        for phrase, required in BODY_PART_CLAIMS.items():
            if phrase in folded:
                checked += 1
                if facts.body_part != required:
                    recorded = facts.body_part or "not recorded"
                    failures.append(
                        Claim(
                            "body_part",
                            f"{phrase!r} but the body part is recorded as {recorded}",
                            number,
                            line,
                        )
                    )

        for word in _WORD.findall(line):
            folded_word = bare(fold(word))

            if folded_word in ACTION_CLAIMS:
                checked += 1
                required = ACTION_CLAIMS[folded_word]
                if required not in facts.actions:
                    failures.append(
                        Claim(
                            "action",
                            f"{word!r} claims a {required} event, which is not in the buildup",
                            number,
                            line,
                        )
                    )
                continue

            if not word[0].isupper() or folded_word in NOT_A_NAME:
                continue

            if folded_word in TEAM_DEMONYMS:
                checked += 1
                claims_made.append("name")
                team = TEAM_DEMONYMS[folded_word]
                if team not in facts.teams:
                    failures.append(
                        Claim(
                            "name",
                            f"{word!r} refers to {team}, which is not in the buildup",
                            number,
                            line,
                        )
                    )
                continue

            checked += 1
            claims_made.append("name")
            if folded_word not in known_names:
                failures.append(Claim("name", word, number, line))

        for digits in _NUMBER.findall(line):
            checked += 1
            claims_made.append("number")
            if int(digits) not in facts.numbers:
                failures.append(
                    Claim(
                        "number",
                        f"{digits} is not a minute in the buildup or the "
                        "second the goal was scored at",
                        number,
                        line,
                    )
                )

    if not claims_made:
        failures.append(
            Claim(
                "unverifiable",
                "the narration names no player, team or clock value from the "
                "buildup, so nothing in it traces back to the data",
                0,
                text.strip(),
            )
        )

    return GroundingResult(
        grounded=not failures, failures=tuple(failures), checked=checked
    )
