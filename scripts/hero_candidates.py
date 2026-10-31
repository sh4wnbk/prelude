r"""Several grounded candidate narrations per hero goal, for Shawn to choose from.

`scripts/freeze_narrations.py` writes one narration per goal and commits it.
This writes several and commits none: the words a judge hears are chosen once,
and choosing between five tellings of a move is a better way to arrive at them
than accepting the first one that passed. Shawn picks one per goal and the
freeze script then writes those two.

**Nothing here is frozen and nothing here goes in the repo.** The review file
is written outside the working tree, because a candidate is not a narration the
app may speak: only the two Shawn picks become that, and they get there through
`scripts/freeze_narrations.py`.

**The prompt is the hero prompt**, `build_prompt(..., hero=True)`, which asks
for the whole move in order naming every player who touched the ball, the clock
once at the start, and a last sentence that says the shot scored. The Task 6
narrations were grounded and thin, and all four things wrong with them were
prompt choices rather than grounding limits.

**Sampling is pinned, because watsonx decodes greedily unless told otherwise.**
Five candidates off a greedy model are one candidate five times. This uses
`COMPARISON_DECODING`, which is what the paid comparison in
`docs/narration_eval.md` pinned both candidates to, so it is a setting this
model has already been run at rather than one invented here.

**Only a narration the model wrote and the check passed is kept.** A candidate
slot gets at most `MAX_RETRIES + 1` attempts, and a slot that reaches the
template fallback yields no candidate rather than a candidate the code wrote.
So a run can come back with fewer candidates than it asked for, and says so.

**The call count is printed before anything is sent**, and nothing is sent
without `--confirm`.

What is reported for each candidate: the text, the tagged text the check
passed, which recorded players it names (the coverage the Task 6 narrations
were short on), and what the three recordings of that match would be billed for
speaking it. The billed count is the figure IBM charges, markup counted and
whitespace not, so `--budget` in `scripts/tts_hero.py` can be read against it.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\hero_candidates.py --plan
    .\.venv-prelude\Scripts\python.exe -I scripts\hero_candidates.py --confirm

Standard library only.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# The recorded names carry accents and this script prints them. A Windows
# console is cp1252 by default, which cannot encode "Ángel" as it is spelled.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from app.grounding import check, fold, sentences  # noqa: E402
from app.narration import MAX_RETRIES, MODEL, narrate  # noqa: E402
from app.narration_config import (  # noqa: E402
    ACTIVE_CANDIDATE,
    COMPARISON_DECODING,
)
from app.narration_prompt import (  # noqa: E402
    Facts,
    facts_from_buildup,
    key_beats,
    touched_the_ball,
)
from app.narration_provider import (  # noqa: E402
    COMPARISON_MAX_NEW_TOKENS,
    WatsonxProvider,
)
from app.statsbomb_event_feed import StatsBombEventFeed  # noqa: E402
from app.tts import speech_text  # noqa: E402

#: Where `hero.voice_for` and the headers are read from.
MATCHES = ROOT / "app" / "web" / "matches.json"

#: The two hero goals, by the match they are in and the clock they are at. The
#: same pair `scripts/freeze_narrations.py` freezes and
#: `scripts/tts_samples.py` records; the clock is checked against the feed
#: below, so a wrong one here fails rather than narrating another goal.
HEROES: tuple[tuple[int, int, int, int], ...] = (
    (1986, 3750191, 54, 18),
    (2022, 3869685, 35, 22),
)

_NOTE = (
    "Candidate narrations for the two hero goals, written by the model named "
    "here and each one passed by the grounding check in app/grounding.py. "
    "None of these is frozen: app/web/narrations.json is what the app reads, "
    "and scripts/freeze_narrations.py --pick is what writes a candidate from "
    "this file into it. Regenerate with scripts/hero_candidates.py --confirm, "
    "which is a paid watsonx run. tagged_text is what the check passed and "
    "text is what a card would show and a voice would read."
)

#: Candidates asked for per goal. Five is what Shawn asked to choose from.
DEFAULT_PER_GOAL = 5

#: Where the review file goes, which is outside the repo on purpose. A
#: candidate is not a narration the app may speak, and a file in the working
#: tree is a file that gets committed by habit.
DEFAULT_OUT = Path.home() / "prelude-review"


def moment_at(feed: StatsBombEventFeed, match_id: int, minute: int, second: int):
    """The one defining moment at this clock, or a refusal."""
    found = [
        moment
        for moment in feed.defining_moments(match_id)
        if (moment.minute, moment.second) == (minute, second)
    ]
    if len(found) != 1:
        raise SystemExit(
            "match {} has {} goals at {}:{:02d}; the hero is one".format(
                match_id, len(found), minute, second
            )
        )
    return found[0]


def distinctive_parts(facts: Facts) -> dict[str, frozenset[str]]:
    """Per recorded player, the words of their name no other one shares.

    Coverage is "did the narration name this player", and the obvious way to
    answer it is wrong on this data: three of the four England defenders in the
    1986 buildup are called Peter, so a narration naming Peter Shilton would
    be read as naming Beardsley and Reid too. So a player is matched on the
    parts that belong to them alone in this passage, which is "Shilton" rather
    than "Peter".

    A player sharing every part of their name with another is not in this
    data; if one ever is, they get all their parts and the count is reported
    as the generous reading rather than silently as a miss.
    """
    players = sorted({fact.beat.player for fact in facts.facts})
    parts = {
        player: {fold(word) for word in player.replace("-", " ").split()}
        for player in players
    }
    out: dict[str, frozenset[str]] = {}
    for player, mine in parts.items():
        shared: set[str] = set()
        for other, theirs in parts.items():
            if other != player:
                shared |= theirs
        unique = mine - shared
        out[player] = frozenset(unique or mine)
    return out


def named_players(text: str, facts: Facts) -> tuple[str, ...]:
    """Which recorded players a narration names, in the recorded order.

    Read off the words of the narration rather than off its citations: a
    sentence can cite a fact without naming the player in it, and what a
    listener hears is the name.
    """
    words = {
        fold(word).strip(".,;:!?'’")
        for word in text.replace("\n", " ").split()
    }
    distinctive = distinctive_parts(facts)
    order: list[str] = []
    for fact in facts.facts:
        player = fact.beat.player
        if player in order:
            continue
        if distinctive[player] & words:
            order.append(player)
    return tuple(order)


def billed_for_match(match_id: int, narration: str) -> int:
    """What the three recordings of this match would be billed for the text.

    Every listener of a match hears the same narration under a different
    voice, so the price of a candidate is the three requests and not one. The
    header is included because it is in the same request, and the markup is
    included because IBM charges for it: this is `billed_characters` on
    `SpeechRequest`, computed the same way without needing credentials to
    build a request.
    """
    doc = json.loads(MATCHES.read_text(encoding="utf-8"))
    match = next(
        one for one in doc["matches"] if one["match_id"] == match_id
    )
    header = match["hero"]["opening"]["header"]
    total = 0
    for key in sorted(set(match["hero"]["voice_for"].values())):
        persona_id, situation = key.rsplit("_", 1)
        text = speech_text(header, narration, persona_id, situation)
        total += len("".join(text.split()))
    return total


def coverage(text: str, tagged: str, facts: Facts) -> dict:
    """What a candidate covers, as numbers a choice can be made on."""
    recorded = []
    for fact in facts.facts:
        if fact.beat.player not in recorded:
            recorded.append(fact.beat.player)
    named = named_players(text, facts)
    touched = touched_the_ball(facts)
    cited: set[int] = set()
    for sentence in sentences(tagged):
        cited |= set(sentence.cites)
    beats = key_beats(facts)
    return {
        "recorded_players": tuple(recorded),
        "named_players": named,
        "missing_players": tuple(
            player for player in recorded if player not in named
        ),
        "players_who_touched_the_ball": touched,
        "touched_and_named": tuple(
            player for player in touched if player in named
        ),
        "touched_not_named": tuple(
            player for player in touched if player not in named
        ),
        "key_beats": len(beats),
        "key_beats_covered": sum(
            1 for beat in beats if beat.covered_by(cited)
        ),
        "sentences": len(sentences(tagged)),
        "cited_facts": tuple(sorted(cited)),
        "clocks": sum(1 for s in sentences(tagged) if ":" in s.text),
        "says_scored": "scored" in text.lower(),
    }


def gather(backend: WatsonxProvider, per_goal: int) -> list[dict]:
    """Narrate each goal `per_goal` times over and keep what passed."""
    feed = StatsBombEventFeed()
    goals: list[dict] = []
    for year, match_id, minute, second in HEROES:
        moment = moment_at(feed, match_id, minute, second)
        facts = facts_from_buildup(feed.buildup(match_id, moment))
        print("{} match {} {}:{:02d}: {} ({}), {} facts, {} players".format(
            year, match_id, minute, second, moment.player, moment.team,
            len(facts.facts), len(touched_the_ball(facts)),
        ))
        kept: list[dict] = []
        refused: list[dict] = []
        for slot in range(1, per_goal + 1):
            narrated = narrate(
                feed,
                match_id,
                moment,
                narration_provider=backend,
                max_retries=MAX_RETRIES,
                hero=True,
            )
            attempts = len(narrated.attempts)
            if narrated.source != MODEL:
                # The slot spent its attempts and reached the code's fallback,
                # which is not a candidate: a frozen narration is one a model
                # wrote.
                print("  candidate {}: no model narration after {} "
                      "attempt(s), dropped".format(slot, attempts - 1))
                for attempt in narrated.attempts:
                    if not attempt.grounded:
                        print("    x {}".format(attempt.summary))
                refused.append(
                    {
                        "slot": slot,
                        "attempts": attempts - 1,
                        "failures": [
                            a.summary
                            for a in narrated.attempts
                            if not a.grounded
                        ],
                    }
                )
                continue
            # Re-checked here rather than trusting the pipeline's verdict,
            # because the verdict is what gets reported beside the words.
            result = check(narrated.tagged_text, facts)
            if not result.grounded:
                raise SystemExit(
                    "candidate {} for match {} passed in the pipeline and "
                    "fails a second check: {}".format(
                        slot, match_id, result.summary
                    )
                )
            one = {
                "slot": slot,
                "text": narrated.text,
                "tagged_text": narrated.tagged_text,
                "attempt": attempts,
                "first_attempt_grounded": narrated.first_attempt_grounded,
                "claims_checked": result.checked,
                "billed_characters": billed_for_match(
                    match_id, narrated.text
                ),
                "coverage": coverage(
                    narrated.text, narrated.tagged_text, facts
                ),
            }
            kept.append(one)
            print("  candidate {}: grounded on {} claims, attempt {}, "
                  "{} billed".format(
                      slot, result.checked, attempts,
                      one["billed_characters"],
                  ))
            print("    | {}".format(narrated.text))
        goals.append(
            {
                "year": year,
                "match_id": match_id,
                "minute": minute,
                "second": second,
                "player": moment.player,
                "team": moment.team,
                "facts": len(facts.facts),
                "recorded_players": tuple(
                    dict.fromkeys(fact.beat.player for fact in facts.facts)
                ),
                "players_who_touched_the_ball": touched_the_ball(facts),
                "candidates": kept,
                "dropped": refused,
            }
        )
        print()
    return goals


def review(goals: Sequence[dict], model: str, provider: str) -> str:
    """The review file: every candidate, its coverage and its price.

    Markdown, because a person reads it and chooses from it. It is written
    outside the repo, so the no-em-dash rule in `CLAUDE.md` covers it as a
    matter of habit rather than of gate; `scripts/check_docs.py` does not see
    this file.
    """
    out: list[str] = []
    out.append("# Hero narration candidates")
    out.append("")
    out.append("Generated {} by scripts/hero_candidates.py.".format(
        date.today().isoformat()
    ))
    out.append("")
    out.append("Model {} on {}, chat endpoint, reasoning effort {}, "
               "decoding pinned to temperature {}, top_p {}, top_k {}.".format(
                   model, provider,
                   ACTIVE_CANDIDATE.reasoning_effort or "not set",
                   COMPARISON_DECODING.temperature,
                   COMPARISON_DECODING.top_p,
                   COMPARISON_DECODING.top_k,
               ))
    out.append("")
    out.append("Every candidate here was written by the model and passed the "
               "grounding check in app/grounding.py. Nothing here is frozen: "
               "pick one per goal and scripts/freeze_narrations.py writes "
               "those two into app/web/narrations.json.")
    out.append("")
    out.append("The billed count is what the three recordings of that match "
               "would cost together, markup counted and whitespace not, "
               "which is the figure IBM charges and the one "
               "scripts/tts_hero.py --budget is set on.")
    out.append("")

    for goal in goals:
        out.append("## {} ({}:{:02d}, {})".format(
            goal["year"], goal["minute"], goal["second"], goal["player"]
        ))
        out.append("")
        out.append("Match {}, {} recorded facts. {} players touched the "
                   "ball: {}.".format(
                       goal["match_id"], goal["facts"],
                       len(goal["players_who_touched_the_ball"]),
                       ", ".join(goal["players_who_touched_the_ball"]),
                   ))
        out.append("")
        out.append("All {} recorded players: {}.".format(
            len(goal["recorded_players"]),
            ", ".join(goal["recorded_players"]),
        ))
        out.append("")
        if goal["dropped"]:
            out.append("{} candidate slot(s) reached the template fallback "
                       "and were dropped.".format(len(goal["dropped"])))
            out.append("")
        if not goal["candidates"]:
            out.append("No candidate for this goal passed.")
            out.append("")
            continue
        out.append("| # | Billed | Sentences | Clocks | Says scored | "
                   "Players named | Beats |")
        out.append("| - | -----: | --------: | -----: | ----------- | "
                   "------------- | ----- |")
        for one in goal["candidates"]:
            cover = one["coverage"]
            out.append("| {} | {} | {} | {} | {} | {} of {} | {} of {} |".format(
                one["slot"],
                one["billed_characters"],
                cover["sentences"],
                cover["clocks"],
                "yes" if cover["says_scored"] else "no",
                len(cover["named_players"]),
                len(cover["recorded_players"]),
                cover["key_beats_covered"],
                cover["key_beats"],
            ))
        out.append("")
        for one in goal["candidates"]:
            cover = one["coverage"]
            out.append("### Candidate {}".format(one["slot"]))
            out.append("")
            out.append("> {}".format(one["text"]))
            out.append("")
            out.append("- Billed: {} characters for the three recordings "
                       "of this match".format(one["billed_characters"]))
            out.append("- Grounded on {} claims, on attempt {}".format(
                one["claims_checked"], one["attempt"]
            ))
            out.append("- Sentences: {}; sentences carrying a clock: "
                       "{}".format(cover["sentences"], cover["clocks"]))
            out.append("- Ends on a sentence saying it scored: {}".format(
                "yes" if cover["says_scored"] else "no"
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
            out.append("- Of the players who touched the ball, names {} of "
                       "{}{}".format(
                           len(cover["touched_and_named"]),
                           len(cover["players_who_touched_the_ball"]),
                           "" if not cover["touched_not_named"]
                           else ", missing " + ", ".join(
                               cover["touched_not_named"]
                           ),
                       ))
            out.append("- Key beats covered: {} of {}".format(
                cover["key_beats_covered"], cover["key_beats"]
            ))
            out.append("- Cites facts: {}".format(
                ", ".join(str(n) for n in cover["cited_facts"])
            ))
            out.append("")
            out.append("The tagged text the check passed:")
            out.append("")
            out.append("```")
            out.append(one["tagged_text"])
            out.append("```")
            out.append("")
    return "\n".join(out) + "\n"


def document(goals: Sequence[dict], backend: WatsonxProvider) -> dict:
    """The candidates with the provenance a freeze needs beside them.

    `scripts/freeze_narrations.py --pick` writes one of these candidates into
    `app/web/narrations.json`, and what it records there has to say which
    model wrote the words and how it was asked. A bare list of candidates
    would make the freeze guess that, or reach for `ACTIVE_CANDIDATE` and
    record the model active when the pick is made rather than the one that
    wrote the text.
    """
    return {
        "_note": _NOTE,
        "generated_on": date.today().isoformat(),
        "model": backend.model,
        "provider": backend.name,
        "chat": ACTIVE_CANDIDATE.chat,
        "reasoning_effort": ACTIVE_CANDIDATE.reasoning_effort,
        "max_new_tokens": COMPARISON_MAX_NEW_TOKENS,
        "decoding": {
            "temperature": COMPARISON_DECODING.temperature,
            "top_p": COMPARISON_DECODING.top_p,
            "top_k": COMPARISON_DECODING.top_k,
        },
        "goals": list(goals),
    }


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--plan",
        action="store_true",
        help="print the call count and the goals, and make no call",
    )
    parser.add_argument(
        "--confirm", action="store_true", help="send them; this is the paid path"
    )
    parser.add_argument(
        "--per-goal",
        type=int,
        default=DEFAULT_PER_GOAL,
        help="candidates to ask for per goal (default {})".format(
            DEFAULT_PER_GOAL
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="directory for the review file, outside the repo (default {})"
             .format(DEFAULT_OUT),
    )
    args = parser.parse_args(argv)

    if args.per_goal < 1:
        raise SystemExit("--per-goal is how many candidates to ask for")
    out_dir = args.out.resolve()
    if ROOT == out_dir or ROOT in out_dir.parents:
        raise SystemExit(
            "{} is inside the repo, and a candidate is not a narration the "
            "app may speak: pick a directory outside {}".format(out_dir, ROOT)
        )

    attempts = MAX_RETRIES + 1
    print("model     {} ({})".format(
        ACTIVE_CANDIDATE.model_id, ACTIVE_CANDIDATE.label
    ))
    print("endpoint  {}".format("chat" if ACTIVE_CANDIDATE.chat else "generation"))
    print("effort    {}".format(ACTIVE_CANDIDATE.reasoning_effort or "not set"))
    print("tokens    {} max new".format(COMPARISON_MAX_NEW_TOKENS))
    print("decoding  temperature {}, top_p {}, top_k {} (pinned, because "
          "watsonx decodes greedily unset and five greedy candidates are one "
          "candidate five times)".format(
              COMPARISON_DECODING.temperature,
              COMPARISON_DECODING.top_p,
              COMPARISON_DECODING.top_k,
          ))
    print("prompt    hero: the whole move, the clock once, a goal sentence "
          "that says it scored")
    print("goals     {}".format(len(HEROES)))
    print("wanted    {} candidates per goal, {} in all".format(
        args.per_goal, args.per_goal * len(HEROES)
    ))
    print("calls     at most {} generations ({} goals x {} candidates x {} "
          "attempts), plus 1 IAM exchange".format(
              len(HEROES) * args.per_goal * attempts,
              len(HEROES), args.per_goal, attempts,
          ))
    print("review    {}".format(out_dir))
    print("freezes   nothing: app/web/narrations.json is not written here")
    print()
    if args.plan or not args.confirm:
        print("nothing was sent. --confirm is what sends it.")
        return 0

    backend = WatsonxProvider(
        max_new_tokens=COMPARISON_MAX_NEW_TOKENS,
        decoding=COMPARISON_DECODING,
    )
    goals = gather(backend, args.per_goal)

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "hero_candidates_{}.md".format(date.today().isoformat())
    path.write_text(
        review(goals, backend.model, backend.name),
        encoding="utf-8",
        newline="\n",
    )
    data = out_dir / "hero_candidates_{}.json".format(date.today().isoformat())
    data.write_text(
        json.dumps(document(goals, backend), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    kept = sum(len(goal["candidates"]) for goal in goals)
    print("kept {} of the {} candidates asked for".format(
        kept, args.per_goal * len(HEROES)
    ))
    print("wrote {}".format(path))
    print("wrote {}".format(data))
    print("IAM exchanges: {}".format(backend.iam_exchanges))
    print()
    print("Nothing is frozen. Shawn picks one per goal, and "
          "scripts/freeze_narrations.py writes those two.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
