r"""Grounded goal-call candidates, three per recorded slot, for Shawn to choose from.

`scripts/hero_candidates.py` writes several candidates per goal, because the
narration used to be one text that all three voices spoke. The framework in
`docs/VOICE.md` ends that: **each narrator has its own text**, so there are six
recordings and six narrations rather than two, and a candidate belongs to a
slot rather than to a goal.

The six slots are the ones `hero.voice_for` in `app/web/matches.json` names,
for each of the two hero goals:

| Slot | Who hears it | The side it is written as |
| ---- | ------------ | ------------------------- |
| `storyteller_neutral` | a listener with no side | nobody |
| `buddy_scored` | a fan of the side that scored | that side |
| `buddy_conceded` | a fan of the side that conceded | nobody, and no "we" |

The Caller has a style in `app/goal_call_prompt.py` and no recording, because
`hero.voice_for` does not send a listener to it; nothing here generates for it.

**The prompt is the goal-call prompt**, `build_goal_call_prompt`, which carries
the records with no clock on them, the move as steps, the style for this
narrator and situation, and one worked example from an invented match. The
eight reference narrations in `tests/test_reference_narrations.py` are the
standard and never the material: a reference in the prompt for the goal it
describes is dictation.

**Only a narration the model wrote and the check passed is kept.** A slot gets
at most `MAX_RETRIES + 1` attempts per candidate, and a candidate that reaches
the code's template fallback yields nothing rather than a narration the code
wrote. So a run can come back with fewer than it asked for, and says so.

**Nothing here is frozen and nothing here goes in the repo.** The review file
is written outside the working tree. Shawn reads the candidates aloud and picks
six; writing those six into `app/web/narrations.json` is a later task, because
the freeze in `scripts/freeze_narrations.py` writes one narration per goal and
not one per slot.

**The call count is printed before anything is sent**, and nothing is sent
without `--confirm`.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\narrator_candidates.py --plan
    .\.venv-prelude\Scripts\python.exe -I scripts\narrator_candidates.py --confirm

Standard library only.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Mapping, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# The recorded names carry accents and this script prints them. A Windows
# console is cp1252 by default, which cannot encode "Ángel" as it is spelled.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from app.goal_call_prompt import (  # noqa: E402
    GOAL_CALL_CHARACTERS_PER_WORD,
    GOAL_CALL_TARGET_CHARACTERS,
    STYLES,
    build_goal_call_prompt,
    shared_name_parts,
    situation_for,
    slot_key,
)
from app.grounding import check  # noqa: E402
from app.narration import MAX_RETRIES, MODEL, narrate  # noqa: E402
from app.narration_config import (  # noqa: E402
    ACTIVE_CANDIDATE,
    COMPARISON_DECODING,
)
from app.narration_prompt import (  # noqa: E402
    Facts,
    beat_record,
    facts_from_buildup,
    key_beats,
    touched_the_ball,
)
from app.narration_provider import (  # noqa: E402
    COMPARISON_MAX_NEW_TOKENS,
    DEFAULT_TIMEOUT,
    NarrationProviderError,
    WatsonxProvider,
)
from app.personas import THE_BUDDY, THE_STORYTELLER  # noqa: E402
from app.recorded_names import recorded_nicknames  # noqa: E402
from app.statsbomb_event_feed import StatsBombEventFeed  # noqa: E402
from app.tts import speech_text  # noqa: E402

# One copy of the measuring code, not two: these answer the same questions for
# a goal call that they answered for a cited narration.
from scripts.hero_candidates import (  # noqa: E402
    HEROES,
    MATCHES,
    moment_at,
    named_players,
    odd_characters,
)
from scripts.tts_hero import DEFAULT_BUDGET  # noqa: E402

#: Candidates asked for per slot. Three is what Shawn asked to choose from,
#: and six slots makes eighteen.
DEFAULT_PER_SLOT = 3

#: Where the review file goes, which is outside the repo on purpose: a
#: candidate is not a narration the app may speak, and a file in the working
#: tree is a file that gets committed by habit.
DEFAULT_OUT = Path.home() / "prelude-review"

#: Characters a token is worth, for the estimate the plan prints.
#:
#: It is an estimate and is labelled one everywhere it is printed. Counting
#: the tokens exactly would mean sending the prompt to watsonx's tokenization
#: endpoint, which is a call to the paid service in order to find out what the
#: paid service will cost. Four characters a token is the usual figure for
#: English prose and is close enough to decide whether a run fits a budget.
CHARACTERS_A_TOKEN = 4.0

_NOTE = (
    "Goal-call candidate narrations, three per recorded slot, written by the "
    "model named here and each one passed by the grounding check in "
    "app/grounding.py reading it as a goal call. None of these is frozen: "
    "app/web/narrations.json is what the app reads and holds one narration "
    "per goal, while these are one per slot, so writing a pick into it is a "
    "later task. Regenerate with scripts/narrator_candidates.py --confirm, "
    "which is a paid watsonx run."
)


def match_record(match_id: int) -> dict:
    """The fixture's own record in `app/web/matches.json`."""
    doc = json.loads(MATCHES.read_text(encoding="utf-8"))
    return next(
        one for one in doc["matches"] if one["match_id"] == match_id
    )


def slots_for(
    match_id: int,
    scoring_team: str,
    only: Sequence[str] = (),
) -> tuple[tuple[str, str | None], ...]:
    """The recorded slots of one match, and the side each is written as.

    Read off `hero.voice_for` rather than written down, so a slot added to the
    app is a slot this run generates for. The side is derived from the goal:
    the Buddy that cheers is the scoring team's, the one that does not is the
    other team's, and the Storyteller has no side.
    """
    match = match_record(match_id)
    other = (
        match["away_team"]
        if match["home_team"] == scoring_team
        else match["home_team"]
    )
    sides = {
        "buddy_scored": scoring_team,
        "buddy_conceded": other,
        "storyteller_neutral": None,
    }
    keys = sorted(set(match["hero"]["voice_for"].values()))
    for key in keys:
        if key not in sides:
            raise SystemExit(
                "match {} sends a listener to {!r}, which this run has no "
                "side for; the slots it knows are {}".format(
                    match_id, key, ", ".join(sorted(sides))
                )
            )
    for key in only:
        if key not in keys:
            raise SystemExit(
                "{!r} is not a recorded slot of match {}; its slots are "
                "{}".format(key, match_id, ", ".join(keys))
            )
    return tuple(
        (key, sides[key]) for key in keys if not only or key in only
    )


def narrator_for(key: str):
    """The persona a slot is written in."""
    return THE_BUDDY if key.startswith("buddy") else THE_STORYTELLER


def billed_for_slot(match_id: int, key: str, narration: str) -> int:
    """What this one recording would be billed for this text.

    One recording, not three: each slot has its own narration now, so the
    price of a candidate is its own request. The header is included because it
    is in the same request, and the markup because IBM charges for it.
    """
    match = match_record(match_id)
    header = match["hero"]["opening"]["header"]
    persona_id, situation = key.rsplit("_", 1)
    spoken = speech_text(header, narration, persona_id, situation)
    return len("".join(spoken.split()))


def slot_coverage(text: str, facts: Facts) -> dict:
    """What a goal-call candidate covers, as numbers a choice can be made on.

    Read off the words rather than off citations, because a goal call has
    none. The beats are the same `key_beats` the rest of the repo uses, and a
    beat counts as reached when the narration names the player that beat is
    about: the defender who was dribbled past, or the scorer for the shot.

    **Which record a beat is about matters here.** A dribble beat holds two,
    the `Dribbled Past` on the defender and the `Dribble` on the player who
    beat him, so counting a beat as reached when either name appears would
    score every dribble in the 1986 passage off the word "Maradona". The
    defender is the one the beat is about and `beat_record` is what says so.
    """
    recorded: list[str] = []
    for fact in facts.facts:
        if fact.beat.player not in recorded:
            recorded.append(fact.beat.player)
    named = named_players(text, facts)
    touched = touched_the_ball(facts)
    beats = key_beats(facts)
    by_number = {fact.number: fact for fact in facts.facts}
    reached = 0
    missed: list[str] = []
    for beat in beats:
        about = beat_record(beat, by_number).beat.player
        if about in named:
            reached += 1
        else:
            missed.append(beat.label)
    return {
        "recorded_players": tuple(recorded),
        "named_players": named,
        "missing_players": tuple(
            player for player in recorded if player not in named
        ),
        "players_who_touched_the_ball": touched,
        "touched_not_named": tuple(
            player for player in touched if player not in named
        ),
        "key_beats": len(beats),
        "key_beats_reached": reached,
        "beats_missed": tuple(missed),
        "sentences": text.count(".") + text.count("!") + text.count("?"),
        "cheers": text.count("!"),
        "digits": sum(1 for character in text if character.isdigit()),
        "says_scored": any(
            word in text.lower() for word in ("scored", "finished", "score")
        ),
        "odd_characters": [
            {
                "character": character,
                "name": name,
                "codepoint": "U+{:04X}".format(ord(character)),
            }
            for character, name in odd_characters(text)
        ],
    }


def prompt_characters(
    facts: Facts, key: str, per_slot: int
) -> tuple[int, ...]:
    """The prompt for each candidate of one slot, in characters.

    One figure per candidate, because the prompt grows: `avoid` carries the
    candidates already kept for this slot, so the second prompt holds one
    narration and the third holds two. They are measured with filler of the
    length the prompt asks a narration to be, since the real ones do not
    exist until the run has made them.
    """
    filler = "x" * GOAL_CALL_TARGET_CHARACTERS
    return tuple(
        len(build_goal_call_prompt(facts, key, avoid=[filler] * number))
        for number in range(per_slot)
    )


def token_estimate(
    slots: Sequence[tuple[int, str]],
    characters: Mapping[tuple[int, str], tuple[int, ...]],
    attempts: int,
    max_new_tokens: int,
) -> dict[str, int]:
    """What this run is expected to spend, and what it could spend at most.

    Two figures, because they are far apart and only one of them is a
    prediction. The ceiling has every candidate failing the check until its
    last attempt and every answer running to the length cap. The first-attempt
    figure has every candidate grounded the first time, which is what 15 of
    the 18 did on 2026-10-31.

    Input is counted once per call and output at the cap, because a reasoning
    model writes its reasoning into the same budget and `reasoning_effort`
    high is a request for more of it.
    """
    one_pass = sum(sum(characters[slot]) for slot in slots)
    first_attempt_in = round(one_pass / CHARACTERS_A_TOKEN)
    calls_first = sum(len(characters[slot]) for slot in slots)
    return {
        "calls_at_most": calls_first * attempts,
        "calls_if_first_attempt": calls_first,
        "input_if_first_attempt": first_attempt_in,
        "output_if_first_attempt": calls_first * max_new_tokens,
        "at_most": (first_attempt_in + calls_first * max_new_tokens) * attempts,
        "if_first_attempt": first_attempt_in + calls_first * max_new_tokens,
    }


def gather(
    backend: WatsonxProvider,
    per_slot: int,
    heroes: Sequence[tuple[int, int, int, int]] = HEROES,
    allowance: int | None = None,
    only: Sequence[str] = (),
) -> list[dict]:
    """Narrate every slot of every goal `per_slot` times and keep what passed."""
    feed = StatsBombEventFeed()
    goals: list[dict] = []
    for year, match_id, minute, second in heroes:
        moment = moment_at(feed, match_id, minute, second)
        facts = facts_from_buildup(
            feed.buildup(match_id, moment), recorded_nicknames(match_id)
        )
        print("{} match {} {}:{:02d}: {} ({}), {} records, {} players".format(
            year, match_id, minute, second, moment.player, moment.team,
            len(facts.facts), len(touched_the_ball(facts)),
        ))
        print("  names two players share, printed in the prompt: {}".format(
            ", ".join(shared_name_parts(facts)) or "none"
        ))
        slots: list[dict] = []
        for key, side in slots_for(match_id, moment.team, only):
            persona = narrator_for(key)
            style = STYLES[slot_key(
                persona.id, situation_for(side, moment.team)
            )]
            print("  {} ({})".format(key, style.label))
            kept: list[dict] = []
            dropped: list[dict] = []
            for number in range(1, per_slot + 1):
                # Every candidate already kept for this slot goes into the
                # prompt, so the model is asked for a telling that differs
                # from them in structure rather than in wording. Three
                # independent calls at temperature 0.8 produced three near
                # copies on 2026-10-31, which is what rule 13 and this are
                # for.
                try:
                    narrated = narrate(
                        feed,
                        match_id,
                        moment,
                        narration_provider=backend,
                        max_retries=MAX_RETRIES,
                        persona=persona,
                        side=side,
                        goal_call=True,
                        avoid=[one["text"] for one in kept],
                    )
                except (OSError, NarrationProviderError) as lost:
                    # A call that never came back costs this candidate and
                    # not the run. The run of 2026-10-31 read the first slot
                    # at effort high, lost the next call to a read timeout
                    # and ended, which threw away three candidates that had
                    # already been written and paid for. Nothing is written
                    # to the review file until the last slot is done, so a
                    # raise here is the whole run.
                    print("    candidate {}: the call did not come back, "
                          "dropped: {}".format(number, lost))
                    dropped.append(
                        {
                            "candidate": number,
                            "attempts": 0,
                            "lost": str(lost),
                            "refused": [],
                            "failures": [],
                        }
                    )
                    continue
                attempts = len(narrated.attempts)
                if narrated.source != MODEL:
                    print("    candidate {}: no model narration after {} "
                          "attempt(s), dropped".format(number, attempts - 1))
                    for attempt in narrated.attempts:
                        if not attempt.grounded:
                            print("      x {}".format(attempt.summary))
                    dropped.append(
                        {
                            "candidate": number,
                            "attempts": attempts - 1,
                            # The words as well as the verdict. The run of
                            # 2026-10-31 dropped nine candidates and the
                            # document held only the refusals, so working out
                            # whether the model or the check was wrong meant
                            # reading the console log. Two of those nine were
                            # the check.
                            "refused": [
                                {
                                    "attempt": one.number,
                                    "text": one.text,
                                    "summary": one.summary,
                                }
                                for one in narrated.attempts
                                if not one.grounded
                            ],
                            "failures": [
                                one.summary
                                for one in narrated.attempts
                                if not one.grounded
                            ],
                        }
                    )
                    continue
                # Re-checked here rather than trusting the pipeline's verdict,
                # because the verdict is what gets reported beside the words.
                result = check(
                    narrated.text, facts, persona=persona, side=side
                )
                if not result.grounded:
                    raise SystemExit(
                        "candidate {} for {} of match {} passed in the "
                        "pipeline and fails a second check: {}".format(
                            number, key, match_id, result.summary
                        )
                    )
                billed = billed_for_slot(match_id, key, narrated.text)
                one = {
                    "candidate": number,
                    "text": narrated.text,
                    "attempt": attempts,
                    "first_attempt_grounded": narrated.first_attempt_grounded,
                    "claims_checked": result.checked,
                    "billed_characters": billed,
                    "characters": len(narrated.text),
                    "words": len(narrated.text.split()),
                    "coverage": slot_coverage(narrated.text, facts),
                }
                if allowance is not None and billed > allowance:
                    print("    candidate {}: grounded on {} claims, but {} "
                          "billed is over the {} a slot may spend; "
                          "dropped".format(
                              number, result.checked, billed, allowance
                          ))
                    print("      | {}".format(narrated.text))
                    one["over_allowance"] = allowance
                    dropped.append(one)
                    continue
                kept.append(one)
                print("    candidate {}: grounded on {} claims, attempt {}, "
                      "{} billed, {} characters".format(
                          number, result.checked, attempts, billed,
                          len(narrated.text),
                      ))
                print("      | {}".format(narrated.text))
            slots.append(
                {
                    "slot": key,
                    "label": style.label,
                    "narrator": persona.id,
                    "side": side,
                    "candidates": kept,
                    "dropped": dropped,
                }
            )
        goals.append(
            {
                "year": year,
                "match_id": match_id,
                "minute": minute,
                "second": second,
                "player": moment.player,
                "team": moment.team,
                "records": len(facts.facts),
                "recorded_players": tuple(
                    dict.fromkeys(fact.beat.player for fact in facts.facts)
                ),
                "players_who_touched_the_ball": touched_the_ball(facts),
                "shared_name_parts": shared_name_parts(facts),
                "slots": slots,
                "generated_on": date.today().isoformat(),
                "model": backend.model,
                "provider": backend.name,
                "target_characters": GOAL_CALL_TARGET_CHARACTERS,
                "allowance": allowance,
            }
        )
        print()
    return goals


def review(
    goals: Sequence[dict],
    model: str,
    provider: str,
    reasoning_effort: str | None,
    max_new_tokens: int,
) -> str:
    """The review file: every candidate, grouped by slot, with its price.

    Markdown, because a person reads it aloud and chooses from it. It is
    written outside the repo, so the no-em-dash rule in `CLAUDE.md` covers it
    as a matter of habit rather than of gate.
    """
    out: list[str] = []
    out.append("# Goal-call candidates, by narrator")
    out.append("")
    out.append("Generated {} by scripts/narrator_candidates.py.".format(
        date.today().isoformat()
    ))
    out.append("")
    out.append("Model {} on {}, chat endpoint, reasoning effort {} for this "
               "run, {} max new tokens, decoding pinned to temperature {}, "
               "top_p {}, top_k {}.".format(
                   model, provider,
                   reasoning_effort or "not set",
                   max_new_tokens,
                   COMPARISON_DECODING.temperature,
                   COMPARISON_DECODING.top_p,
                   COMPARISON_DECODING.top_k,
               ))
    out.append("")
    out.append("Every candidate was written by the model and passed the "
               "grounding check in app/grounding.py, read as a goal call. "
               "Nothing here is frozen.")
    out.append("")
    out.append("The billed count is what that one recording would cost, "
               "markup counted and whitespace not, which is the figure IBM "
               "charges and the one scripts/tts_hero.py --budget is set on.")
    out.append("")

    for goal in goals:
        out.append("## {} ({}:{:02d}, {})".format(
            goal["year"], goal["minute"], goal["second"], goal["player"]
        ))
        out.append("")
        out.append("Match {}, {} records, {} players had the ball: {}.".format(
            goal["match_id"], goal["records"],
            len(goal["players_who_touched_the_ball"]),
            ", ".join(goal["players_who_touched_the_ball"]),
        ))
        out.append("")
        out.append("Name parts two players share, which the prompt tells the "
                   "model to avoid: {}.".format(
                       ", ".join(goal["shared_name_parts"]) or "none"
                   ))
        out.append("")
        for slot in goal["slots"]:
            out.append("### {} ({})".format(slot["slot"], slot["label"]))
            out.append("")
            if slot["side"]:
                out.append("Written for a fan of {}.".format(slot["side"]))
            else:
                out.append("Written for a listener with no side.")
            out.append("")
            if not slot["candidates"]:
                out.append("No candidate for this slot passed.")
                out.append("")
                continue
            out.append("| # | Billed | Characters | Words | \"!\" | Digits | "
                       "Players named | Beats |")
            out.append("| - | -----: | ---------: | ----: | ---: | -----: | "
                       "------------: | ----- |")
            for one in slot["candidates"]:
                cover = one["coverage"]
                out.append("| {} | {} | {} | {} | {} | {} | {} of {} | "
                           "{} of {} |".format(
                               one["candidate"], one["billed_characters"],
                               one["characters"], one["words"],
                               cover["cheers"], cover["digits"],
                               len(cover["named_players"]),
                               len(cover["recorded_players"]),
                               cover["key_beats_reached"], cover["key_beats"],
                           ))
            out.append("")
            for one in slot["candidates"]:
                cover = one["coverage"]
                out.append("**Candidate {}**".format(one["candidate"]))
                out.append("")
                out.append("> {}".format(one["text"]))
                out.append("")
                out.append("- Billed: {} characters for this recording"
                           .format(one["billed_characters"]))
                out.append("- Length: {} characters, {} words".format(
                    one["characters"], one["words"]
                ))
                out.append("- Grounded on {} claims, on attempt {}".format(
                    one["claims_checked"], one["attempt"]
                ))
                out.append("- Names {} of the {} recorded players: {}".format(
                    len(cover["named_players"]),
                    len(cover["recorded_players"]),
                    ", ".join(cover["named_players"]) or "none",
                ))
                if cover["missing_players"]:
                    out.append("- Does not name: {}".format(
                        ", ".join(cover["missing_players"])
                    ))
                out.append("- Reaches {} of {} key beats{}".format(
                    cover["key_beats_reached"], cover["key_beats"],
                    "" if not cover["beats_missed"]
                    else ", missing " + "; ".join(cover["beats_missed"]),
                ))
                if cover.get("odd_characters"):
                    out.append("- **Unusual characters, which would be sent "
                               "to the speech service as written:** "
                               "{}".format("; ".join(
                                   "{} ({})".format(
                                       entry["name"], entry["codepoint"]
                                   )
                                   for entry in cover["odd_characters"]
                               )))
                out.append("")
            if slot["dropped"]:
                out.append("{} candidate(s) were dropped for this "
                           "slot.".format(len(slot["dropped"])))
                out.append("")
    return "\n".join(out) + "\n"


def merged(goals: Sequence[dict], path: Path) -> list[dict]:
    """This run's slots, plus any slot in `path` this run did not generate.

    A rerun of one slot used to throw the other five away, which is the same
    mistake `scripts/hero_candidates.py` made with one goal and the other, on
    2026-10-30. `--slot buddy_scored` exists so that a slot can be rerun after
    a check or a prompt fix without spending calls on five that are already
    good, and that is only true if the document survives it.

    A slot this run produced replaces its older self. A slot it did not touch
    is carried across with the provenance it was written with, so a reader can
    tell which run each candidate came from.
    """
    if not path.is_file():
        return list(goals)
    existing = json.loads(path.read_text(encoding="utf-8"))
    older = existing["goals"] if isinstance(existing, dict) else existing
    by_match = {goal["match_id"]: goal for goal in goals}
    out: list[dict] = []
    for one in older:
        match_id = one["match_id"]
        fresh = by_match.pop(match_id, None)
        if fresh is None:
            print("  carried over match {} whole from the earlier document: "
                  "{} slot(s)".format(match_id, len(one["slots"])))
            out.append(one)
            continue
        produced = {slot["slot"] for slot in fresh["slots"]}
        carried = [
            slot for slot in one["slots"] if slot["slot"] not in produced
        ]
        for slot in carried:
            print("  carried over match {} {} from the earlier document: "
                  "{} candidate(s), written {}".format(
                      match_id, slot["slot"], len(slot["candidates"]),
                      one.get("generated_on", "date not recorded"),
                  ))
        fresh = dict(fresh)
        fresh["slots"] = sorted(
            list(fresh["slots"]) + carried, key=lambda slot: slot["slot"]
        )
        out.append(fresh)
    out += list(by_match.values())
    order = [match_id for _, match_id, _, _ in HEROES]
    return sorted(
        out,
        key=lambda goal: order.index(goal["match_id"])
        if goal["match_id"] in order
        else len(order),
    )


def document(goals: Sequence[dict], backend: WatsonxProvider) -> dict:
    """The candidates with the provenance a later freeze will need."""
    return {
        "_note": _NOTE,
        "generated_on": date.today().isoformat(),
        "model": backend.model,
        "provider": backend.name,
        "chat": backend.chat,
        "reasoning_effort": backend.reasoning_effort,
        "max_new_tokens": backend.max_new_tokens,
        "decoding": {
            "temperature": COMPARISON_DECODING.temperature,
            "top_p": COMPARISON_DECODING.top_p,
            "top_k": COMPARISON_DECODING.top_k,
        },
        "goals": list(goals),
    }


def goals_to_run(matches: Sequence[int]) -> tuple[tuple[int, int, int, int], ...]:
    """The heroes to narrate, filtered by `--match`, in `HEROES` order."""
    if not matches:
        return HEROES
    known = {hero[1] for hero in HEROES}
    for match_id in matches:
        if match_id not in known:
            raise SystemExit(
                "match {} is not one of the hero goals ({})".format(
                    match_id, ", ".join(str(one) for one in sorted(known))
                )
            )
    return tuple(hero for hero in HEROES if hero[1] in set(matches))


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--plan",
        action="store_true",
        help="print the call count and the slots, and make no call",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="send them; this is the paid path",
    )
    parser.add_argument(
        "--per-slot",
        type=int,
        default=DEFAULT_PER_SLOT,
        help="candidates to ask for per slot (default {})".format(
            DEFAULT_PER_SLOT
        ),
    )
    parser.add_argument(
        "--match",
        type=int,
        action="append",
        default=[],
        metavar="MATCH_ID",
        help="narrate only this hero goal; repeatable, and the default is both",
    )
    parser.add_argument(
        "--slot",
        action="append",
        default=[],
        metavar="SLOT",
        help="generate only this slot; repeatable, and the default is all "
             "three of each goal",
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=DEFAULT_BUDGET,
        help="the billed characters the six recordings may cost together "
             "(default {}, which is scripts/tts_hero.py --budget)".format(
                 DEFAULT_BUDGET
             ),
    )
    parser.add_argument(
        "--reasoning-effort",
        default=ACTIVE_CANDIDATE.reasoning_effort,
        choices=("low", "medium", "high"),
        help="how much the model thinks before it writes, for this run only "
             "(default {}, which is what app/narration_config.py ships on the "
             "active candidate)".format(
                 ACTIVE_CANDIDATE.reasoning_effort or "not set"
             ),
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=COMPARISON_MAX_NEW_TOKENS,
        help="the length cap sent to watsonx, which a reasoning model writes "
             "its reasoning into as well (default {})".format(
                 COMPARISON_MAX_NEW_TOKENS
             ),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="seconds to wait for one call, which a reasoning model at a high "
             "effort needs more of (default {:.0f})".format(DEFAULT_TIMEOUT),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="directory for the review file, outside the repo (default {})"
             .format(DEFAULT_OUT),
    )
    args = parser.parse_args(argv)

    if args.per_slot < 1:
        raise SystemExit("--per-slot is how many candidates to ask for")
    out_dir = args.out.resolve()
    if ROOT == out_dir or ROOT in out_dir.parents:
        raise SystemExit(
            "{} is inside the repo, and a candidate is not a narration the "
            "app may speak: pick a directory outside {}".format(out_dir, ROOT)
        )

    heroes = goals_to_run(args.match)
    feed = StatsBombEventFeed()
    slots: list[tuple[int, str]] = []
    characters: dict[tuple[int, str], tuple[int, ...]] = {}
    for _, match_id, minute, second in heroes:
        moment = moment_at(feed, match_id, minute, second)
        facts = facts_from_buildup(
            feed.buildup(match_id, moment), recorded_nicknames(match_id)
        )
        for key, _side in slots_for(match_id, moment.team, args.slot):
            slots.append((match_id, key))
            characters[(match_id, key)] = prompt_characters(
                facts, key, args.per_slot
            )

    # Every recording comes out of one monthly allowance and there are six of
    # them, so what one may cost is the budget divided by the slots it is
    # shared with. A grounded candidate over that is reported and dropped: a
    # narration nobody can pay to record is not a candidate.
    recordings = sum(
        len(slots_for(hero[1], moment_at(feed, hero[1], hero[2], hero[3]).team))
        for hero in HEROES
    )
    allowance = args.budget // recordings
    attempts = MAX_RETRIES + 1

    print("model     {} ({})".format(
        ACTIVE_CANDIDATE.model_id, ACTIVE_CANDIDATE.label
    ))
    print("endpoint  {}".format(
        "chat" if ACTIVE_CANDIDATE.chat else "generation"
    ))
    print("effort    {} (this run; app/narration_config.py ships {})".format(
        args.reasoning_effort or "not set",
        ACTIVE_CANDIDATE.reasoning_effort or "not set",
    ))
    print("tokens    {} max new".format(args.max_new_tokens))
    print("timeout   {:.0f} seconds a call; a call that does not come back "
          "costs that candidate and not the run".format(args.timeout))
    print("decoding  temperature {}, top_p {}, top_k {} (pinned, because "
          "watsonx decodes greedily unset and three greedy candidates are "
          "one candidate three times)".format(
              COMPARISON_DECODING.temperature,
              COMPARISON_DECODING.top_p,
              COMPARISON_DECODING.top_k,
          ))
    print("prompt    goal call: the records with no clock, the move as steps, "
          "a style per narrator shown through an invented match")
    print("target    about {} characters a narration, roughly {} words".format(
        GOAL_CALL_TARGET_CHARACTERS,
        round(GOAL_CALL_TARGET_CHARACTERS / GOAL_CALL_CHARACTERS_PER_WORD),
    ))
    print("slots     {}".format(len(slots)))
    for match_id, key in slots:
        print("            match {} {}".format(match_id, key))
    print("budget    {} billed for the {} recordings together, so {} a "
          "recording; a grounded candidate over that is dropped".format(
              args.budget, recordings, allowance
          ))
    print("wanted    {} candidates per slot, {} in all".format(
        args.per_slot, args.per_slot * len(slots)
    ))
    print("calls     at most {} generations ({} slots x {} candidates x {} "
          "attempts), plus 1 IAM exchange".format(
              len(slots) * args.per_slot * attempts,
              len(slots), args.per_slot, attempts,
          ))
    spend = token_estimate(
        slots, characters, attempts, args.max_new_tokens
    )
    print("prompts   {} to {} characters a prompt; the second and third "
          "candidate of a slot carry the ones already kept".format(
              min(min(one) for one in characters.values()),
              max(max(one) for one in characters.values()),
          ))
    print("tokens    about {:,} expected ({} calls, every candidate grounded "
          "on its first attempt: {:,} in, {:,} out at the cap)".format(
              spend["if_first_attempt"],
              spend["calls_if_first_attempt"],
              spend["input_if_first_attempt"],
              spend["output_if_first_attempt"],
          ))
    print("          about {:,} at most ({} calls, every candidate failing "
          "until its last attempt), estimated at {:.0f} characters a "
          "token".format(
              spend["at_most"], spend["calls_at_most"], CHARACTERS_A_TOKEN,
          ))
    print("review    {}".format(out_dir))
    print("freezes   nothing: app/web/narrations.json is not written here")
    print()
    if args.plan or not args.confirm:
        print("nothing was sent. --confirm is what sends it.")
        return 0

    # The effort is this run's and not the module's. It is the one request
    # setting that changes what the answers are worth rather than how they are
    # addressed, so it belongs to the run that chose it: Task 9d asked for
    # high, and `ACTIVE_CANDIDATE` still ships low because that is what the
    # pipeline a fan waits on uses.
    backend = WatsonxProvider(
        max_new_tokens=args.max_new_tokens,
        decoding=COMPARISON_DECODING,
        reasoning_effort=args.reasoning_effort,
        timeout=args.timeout,
    )
    goals = gather(
        backend,
        args.per_slot,
        heroes=heroes,
        allowance=allowance,
        only=args.slot,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = date.today().isoformat()
    path = out_dir / "narrator_candidates_{}.md".format(stamp)
    data = out_dir / "narrator_candidates_{}.json".format(stamp)
    # Merged before either file is written, so the review file and the data
    # file describe the same set of slots.
    produced = goals
    goals = merged(goals, data)
    path.write_text(
        review(
            goals,
            backend.model,
            backend.name,
            backend.reasoning_effort,
            backend.max_new_tokens,
        ),
        encoding="utf-8",
        newline="\n",
    )
    data.write_text(
        json.dumps(document(goals, backend), indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    # This run's own tally, not the merged document's: a slot carried over
    # from an earlier run was not asked for here.
    kept = sum(
        len(slot["candidates"]) for goal in produced for slot in goal["slots"]
    )
    print("kept {} of the {} candidates asked for".format(
        kept, args.per_slot * len(slots)
    ))
    held = sum(
        len(slot["candidates"]) for goal in goals for slot in goal["slots"]
    )
    print("the document now holds {} candidate(s) over {} slot(s)".format(
        held, sum(len(goal["slots"]) for goal in goals)
    ))
    print("wrote {}".format(path))
    print("wrote {}".format(data))
    print("IAM exchanges: {}".format(backend.iam_exchanges))
    print("billed by watsonx: {:,} tokens in all, {:,} prompt and {:,} "
          "completion, read off the usage object on every answer".format(
              backend.total_tokens,
              backend.prompt_tokens,
              backend.completion_tokens,
          ))
    print("the plan estimated {:,} expected and {:,} at most".format(
        spend["if_first_attempt"], spend["at_most"]
    ))
    print()
    print("Nothing is frozen. Shawn reads these aloud and picks six.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
