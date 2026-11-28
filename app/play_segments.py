"""Which words of a narration stand on which records.

A narration that passed the grounding check is a run of claims, and each claim
the check traced was traced to one or more events in `data/raw/`. This module
says where in the stored text each of those claims was said, and which events
hold it, so a span of the words can be pointed at its records.

    segments(text, facts, persona, side)

returns the segments in text order, each a dict:

    {"start_char": 104, "end_char": 113, "said": "Beardsley",
     "kind": "past", "event_ids": ["372c9acf-...", "1aca4e20-..."]}

`text[start_char:end_char] == said` for every one.

**Only a narration the check passes is read.** `check` runs first, and a
narration it refuses raises rather than coming back with whatever segments
could be found: a span pointed at records is a claim that the words stand on
them, and a refused narration has words that do not. The text is also required
to be already plain, with straight apostrophes, because the check reads the
plain text and every offset here is an offset into the text as stored.

**Only claims that say an event happened are kept.** Those are the kinds in
`EVENT_KINDS`. Three kinds of move are left out, and each for a reason:

- A name or a team. A player's name is held by every record that player has,
  so a span over "Maradona" would point at eleven events and say nothing about
  which one the sentence meant.
- The pattern ("on the counter"), for the same reason: it is held by every
  record of the possession.
- A zone, a position or a direction. Each one describes a move that is already
  a segment of its own, so it adds a place and not an event.

**A reaction is not a claim.** A final sentence the check reads as the
narrator's reaction ("What a finish.") is skipped, because the check did not
trace its moves to any record.

**Claims said over the same words are one segment.** "Beardsley and Reid
pressed him" is two claims on the one word "pressed", one per presser, and the
segment carries both events.

**"Under pressure from X" is one segment as well.** It is two claims, the
carrier's `pressured` flag over "under pressure from" and X's `pressed_by`
record over "under pressure from X", and the first span sits inside the
second. They are one segment over the longer span, carrying both claims'
records. That is the only overlap folded; any other one raises.

**Where a move's words are is computed, never searched for.** Three kinds of
move are built so that `at` is not where `said` starts, and each is placed
from the numbers the reader built it from, which it keeps in the move's
`detail` under `SPAN_KEYS` in `app/narration_grammar.py`:

- A chain, `f"{marker} {name}"` at the name: `at` is where the receiver's
  name starts, so the span ends at `at + len(receiver_said)` and starts
  `len(said)` before that. "found Maradona" ends on "Maradona".
- "Under pressure from X", built the same way: the same rule.
- A long ball folded into its chain by `Reader._merge_long`. Its `said` is
  the two parts joined by a space ("long ball to MacAllister") while the text
  has "forward" between them, so this one move is not one run of the text.
  The span runs from the long ball at `at` to the end of the chain's name at
  `chain_at`, and its segment's `said` is the text in that span ("long ball
  forward to MacAllister"). Both parts are asserted at their two ends, and
  what lies between them may only be what `_merge_long` steps over. The whole
  span stands on the one long pass that holds the merged move.

Every other move starts at `at` and has to read exactly as it said it. A move
whose words are not where these numbers put them raises: a search could land
on another occurrence of the same words and pass on the wrong place.

Standard library only, like every module in `app/` but `app/api.py`.
"""

from typing import Mapping, Sequence

from app.grounding import check, goal_call_reader, is_a_reaction, sentences
from app.narration_grammar import Move, support
from app.narration_prompt import Facts
from app.personas import Persona
from app.plain_characters import plain, straight_apostrophes

#: The kinds of move that say an event happened. Everything else the reader
#: emits is a name, a team, a pattern, a place or a direction, and the module
#: docstring says why each is left out.
EVENT_KINDS = frozenset(
    {
        "action",
        "chain",
        "past",
        "touch",
        "long_pass",
        "pressured",
        "pressed_by",
        "first_time",
        "body_part",
    }
)

#: What `Reader._merge_long` steps over between "a long ball" and its chain,
#: and so the only moves that may sit inside the gap of a merged move's span.
_MERGE_STEPS_OVER = frozenset({"name", "team", "direction", "run", "zone"})


class NotGrounded(ValueError):
    """The narration is not one the check passes, so no span may be pointed
    at records."""


def _is_merged_long(move: Move) -> bool:
    """Whether this is the move `Reader._merge_long` built: a chain whose
    detail says `long`, which no other chain does."""
    return (
        move.kind == "chain"
        and isinstance(move.detail, Mapping)
        and move.detail.get("long") is True
    )


def move_span(
    sentence: str, move: Move, moves: Sequence[Move]
) -> tuple[int, int]:
    """Where `move`'s words are in `sentence`, computed, or raise.

    The module docstring has the three rules. Each one asserts that the text
    at the computed place is the words the reader said were there.
    """
    said = move.said
    if _is_merged_long(move):
        detail = move.detail
        long_said = detail["long_said"]
        chain_said = said[len(long_said) + 1:]
        start = move.at
        end = detail["chain_at"] + len(detail["receiver_said"])
        if said != f"{long_said} {chain_said}":
            raise AssertionError(f"{said!r} does not open on {long_said!r}")
        if sentence[start:start + len(long_said)] != long_said:
            raise AssertionError(
                f"{long_said!r} is not at {start} in {sentence!r}"
            )
        if sentence[end - len(chain_said):end] != chain_said:
            raise AssertionError(
                f"{chain_said!r} does not end at {end} in {sentence!r}"
            )
        between = [
            other
            for other in moves
            if start + len(long_said) <= other.at < end - len(chain_said)
        ]
        if any(other.kind not in _MERGE_STEPS_OVER for other in between):
            raise AssertionError(
                f"something other than a place, a direction or a name sits "
                f"inside {sentence[start:end]!r}"
            )
        return start, end

    if move.kind in ("chain", "pressed_by"):
        end = move.at + len(move.detail["receiver_said"])
        start = end - len(said)
    else:
        start = move.at
        end = start + len(said)
    if start < 0 or sentence[start:end] != said:
        raise AssertionError(
            f"{move.kind} {said!r} is not at {start}: the text there is "
            f"{sentence[max(start, 0):end]!r}"
        )
    return start, end


def _kinds(segment: dict) -> list[str]:
    return segment["kind"].split("+")


def _fold_pressure_into_presser(spans: dict[tuple[int, int], dict]) -> None:
    """Make "under pressure from X" one segment, in place.

    The reader reads it as two claims: `pressured`, the carrier's own flag,
    over "under pressure from", and `pressed_by`, X's own `Pressure` record,
    over "under pressure from X". The first span sits inside the second, so
    they are one segment over the `pressed_by` span carrying both claims'
    records. This is the one overlap that is folded: a `pressured` span
    inside exactly one `pressed_by` span. Any other overlap is left for the
    caller to refuse.
    """
    for key in sorted(spans):
        inner = spans[key]
        if _kinds(inner) != ["pressured"]:
            continue
        outer_keys = [
            other
            for other in spans
            if other != key
            and "pressed_by" in _kinds(spans[other])
            and other[0] <= key[0]
            and key[1] <= other[1]
        ]
        if len(outer_keys) != 1:
            continue
        outer = spans[outer_keys[0]]
        outer["kind"] = "+".join(
            ["pressured"]
            + [kind for kind in _kinds(outer) if kind != "pressured"]
        )
        outer["event_ids"] = inner["event_ids"] + [
            event_id
            for event_id in outer["event_ids"]
            if event_id not in inner["event_ids"]
        ]
        del spans[key]


def segments(
    text: str,
    facts: Facts,
    persona: Persona | None,
    side: str | None,
) -> list[dict]:
    """The event claims in `text`, in text order, with the records behind each.

    Raises `NotGrounded` when the check refuses the narration or the text is
    not already in the form the check reads, and `AssertionError` when a
    claim's words are not where the reader said they were.
    """
    result = check(text, facts, persona=persona, side=side)
    if not result.grounded:
        raise NotGrounded(result.summary)
    if straight_apostrophes(plain(text)) != text:
        raise NotGrounded(
            "the text is not plain with straight apostrophes, so offsets into "
            "it are not offsets into what the check read"
        )

    reader = goal_call_reader(facts, side)
    parsed = sentences(text)
    read = [reader.read(sentence.text) for sentence in parsed]
    last = len(parsed) - 1

    spans: dict[tuple[int, int], dict] = {}
    cursor = 0
    for index, sentence in enumerate(parsed):
        offset = text.find(sentence.text, cursor)
        if offset < 0:
            raise AssertionError(
                f"sentence {sentence.number} {sentence.text!r} is not in the "
                "stored text after the sentence before it"
            )
        cursor = offset + len(sentence.text)
        moves = read[index]
        if index == last and is_a_reaction(sentence.text, moves):
            continue

        for move in moves:
            if move.kind not in EVENT_KINDS:
                continue
            at, until = move_span(sentence.text, move, moves)
            start, end = offset + at, offset + until
            event_ids = [beat.event_id for beat in support(move, facts)]
            if not event_ids:
                raise AssertionError(
                    f"{move.kind} {move.said!r} has no record behind it in a "
                    "narration the check passed"
                )
            segment = spans.setdefault(
                (start, end),
                {
                    "start_char": start,
                    "end_char": end,
                    "said": text[start:end],
                    "kind": move.kind,
                    "event_ids": [],
                },
            )
            if move.kind not in segment["kind"].split("+"):
                segment["kind"] += "+" + move.kind
            for event_id in event_ids:
                if event_id not in segment["event_ids"]:
                    segment["event_ids"].append(event_id)

    _fold_pressure_into_presser(spans)
    ordered = [spans[key] for key in sorted(spans)]
    for before, after in zip(ordered, ordered[1:]):
        if after["start_char"] < before["end_char"]:
            raise AssertionError(
                f"{before['said']!r} and {after['said']!r} overlap in the text"
            )
    return ordered
