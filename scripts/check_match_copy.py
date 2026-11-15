r"""Check every factual value in app/web/matches.json against the raw events.

matches.json is fixed display copy, written by hand. This is what keeps it
honest: every name, minute, score, count, body part, play pattern and assist in
it is looked up in data/raw and compared. Exit code is 1 on any mismatch, so it
can gate a commit.

It does not search the data for goals or buildups. It is handed the values the
copy claims and checks each one. Finding moments is the EventFeed module's job.

**A line that describes the play says so in a `grounding` block.** Task 33
asked what in the app describes the play, who passed, dribbled or scored and
how, without anything holding it to the feed, and found the moment card's
caption, its share text and both 1986 moments. Three rules keep that from
coming back, and together they make the block a claim about these words rather
than about the goal:

1. **Every key in a `grounding` block is checked against the feed.** That was
   already true of `body_part`, `play_pattern` and `assist`; `solo_run`,
   `own_half`, `dribbled_past`, `yards_from_goal`, `recovers_error` and
   `match_goal_number` are the keys Task 33 added for the lines it found.
2. **Every key has to be said in the words beside it**, in the form `SAYS`
   gives. A key nothing says is a fact nobody reads, and a block of them
   would be a grounding score rather than a grounded line.
3. **Every claim in the words has to have a key.** `CLAIMS` is the list of
   phrases that are claims about the play: a line using one with no key
   behind it fails, wherever in matches.json it is written.

On top of those, any player this repo's own data knows who is named in a line
has to be recorded in that goal's possession, which is how the removed
broadcast quote was held before it went.

    .\.venv-prelude\Scripts\python.exe -I scripts\check_match_copy.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
COPY = ROOT / "app" / "web" / "matches.json"

INDEXES = {
    3750191: RAW / "matches" / "43" / "54.json",
    3869685: RAW / "matches" / "43" / "106.json",
}

# Period 5 is a shootout and is never a moment of the match.
LAST_MATCH_PERIOD = 4
PERIOD_LABELS = {1: "1H", 2: "2H", 3: "ET", 4: "ET"}

#: StatsBomb's pitch, in yards, with the attacking goal at the right. A team
#: attacks towards x = 120 in its own event co-ordinates, so its own half is
#: everything short of the halfway line.
PITCH_LENGTH = 120.0
PITCH_WIDTH = 80.0
HALFWAY = PITCH_LENGTH / 2

#: How a number may be written in a line of copy. Only as far as the copy
#: goes: a line claiming more than a dozen of anything can add to this.
IN_WORDS = {
    1: ("one", "first", "opener"),
    2: ("two", "second", "doubles"),
    3: ("three", "third"),
    4: ("four", "fourth"),
    5: ("five", "fifth"),
    6: ("six", "sixth"),
    7: ("seven", "seventh"),
    8: ("eight", "eighth"),
    9: ("nine", "ninth"),
    10: ("ten", "tenth"),
    11: ("eleven", "eleventh"),
    12: ("twelve", "twelfth"),
}


def says_name(prose, full):
    """Whether a line names this player, by any part of their name."""
    return any(re.search(r"\b%s\b" % re.escape(part), prose, re.IGNORECASE)
               for part in name_parts(full))


def says_number(prose, n):
    """Whether a line says the number n, as a digit or as a word."""
    forms = [str(n)] + list(IN_WORDS.get(n, ()))
    return any(re.search(r"\b%s\b" % form, prose, re.IGNORECASE) for form in forms)


#: A name token shorter than this matches too much to be a name: "Di" is in
#: "Di María" and in nothing else here, but it is also two letters.
SHORTEST_NAME = 4


def name_parts(full):
    """The parts of a player's name a line of copy might use.

    Not the last word. StatsBomb records both surnames, so Valdano is
    "Jorge Alberto Francisco Valdano Castellano" and Messi is "Lionel Andrés
    Messi Cuccittini": a line saying "Valdano" or "Messi" is naming the last
    word of neither. Every part long enough to be a name is read instead.
    """
    return [part for part in full.split() if len(part) >= SHORTEST_NAME]


def load(path):
    if not path.exists():
        raise SystemExit(f"missing {path}; run scripts/fetch_statsbomb.py first")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def goals_of(events):
    """Goal-outcome shots in periods 1 to 4, earliest first."""
    goals = [
        e
        for e in events
        if e["type"]["name"] == "Shot"
        and e["shot"]["outcome"]["name"] == "Goal"
        and e["period"] <= LAST_MATCH_PERIOD
    ]
    goals.sort(key=lambda e: (e["period"], e["minute"], e["second"]))
    return goals


def clock(event):
    return (event["period"], event["minute"], event["second"])


def find_goal(goals, want):
    for g in goals:
        if clock(g) == (want["period"], want["minute"], want["second"]):
            return g
    return None


def check_event(tag, claimed, g, fail):
    if claimed["player"] != g["player"]["name"]:
        fail(tag, f"player {claimed['player']!r}, the feed says {g['player']['name']!r}")
    if claimed["team"] != g["team"]["name"]:
        fail(tag, f"team {claimed['team']!r}, the feed says {g['team']['name']!r}")
    if claimed["shot_type"] != g["shot"]["type"]["name"]:
        fail(tag, f"shot_type {claimed['shot_type']!r}, the feed says {g['shot']['type']['name']!r}")


def check_labels(tag, block, g, fail):
    if block["display_minute"] != g["minute"] + 1:
        fail(
            tag,
            f"display minute {block['display_minute']} for raw minute {g['minute']}; "
            "the broadcast convention is raw + 1",
        )
    if PERIOD_LABELS[g["period"]] != block["period_label"]:
        fail(
            tag,
            f"period {g['period']} labelled {block['period_label']!r}, "
            f"expected {PERIOD_LABELS[g['period']]!r}",
        )


def other_team(g, home_team, away_team):
    """The team that was not on the ball for this goal, by name."""
    return away_team if g["team"]["name"] == home_team else home_team


def in_possession(events, g):
    """Every event of the goal's possession, in order."""
    return [e for e in events if e["possession"] == g["possession"]]


def on_the_ball(events, g):
    """The scoring team's own events in the possession, in order.

    An opponent's Pressure, Duel or Dribbled Past is recorded in the same
    possession and is not that player having the ball, so the team is what
    this reads rather than the possession alone.
    """
    return [e for e in in_possession(events, g)
            if e.get("team", {}).get("name") == g["team"]["name"]
            and "player" in e]


def check_grounding(tag, grounding, g, goals, events, home_team, away_team,
                    fail):
    if "body_part" in grounding and grounding["body_part"] != g["shot"]["body_part"]["name"]:
        fail(tag, f"body_part {grounding['body_part']!r}, the feed says "
                  f"{g['shot']['body_part']['name']!r}")
    if "play_pattern" in grounding and grounding["play_pattern"] != g["play_pattern"]["name"]:
        fail(tag, f"play_pattern {grounding['play_pattern']!r}, the feed says "
                  f"{g['play_pattern']['name']!r}")
    if "assist" in grounding:
        assists = [
            e["player"]["name"]
            for e in events
            if e["type"]["name"] == "Pass"
            and e.get("pass", {}).get("goal_assist")
            and e["possession"] == g["possession"]
        ]
        if grounding["assist"] not in assists:
            fail(tag, f"assist {grounding['assist']!r}, the feed's goal_assist in that "
                      f"possession is {assists or 'none'}")
    if "seconds_after_previous_goal" in grounding:
        idx = goals.index(g)
        if idx == 0:
            fail(tag, "seconds_after_previous_goal on the first goal of the match")
        else:
            prev = goals[idx - 1]
            gap = (g["minute"] * 60 + g["second"]) - (prev["minute"] * 60 + prev["second"])
            if gap != grounding["seconds_after_previous_goal"]:
                fail(tag, f"claims {grounding['seconds_after_previous_goal']}s after the "
                          f"previous goal, the feed says {gap}s")
    if "player_goal_number" in grounding:
        n = sum(1 for x in goals
                if x["player"]["name"] == g["player"]["name"] and clock(x) <= clock(g))
        if n != grounding["player_goal_number"]:
            fail(tag, f"claims goal number {grounding['player_goal_number']} for that player, "
                      f"the feed says {n}")
    if "score_after" in grounding:
        upto = [x for x in goals if clock(x) <= clock(g)]
        home = sum(1 for x in upto if x["team"]["name"] == home_team)
        actual = [home, len(upto) - home]
        if grounding["score_after"] != actual:
            fail(tag, f"claims the score was {grounding['score_after']}, the feed says {actual}")
    if "match_goal_number" in grounding:
        n = goals.index(g) + 1
        if n != grounding["match_goal_number"]:
            fail(tag, f"claims goal number {grounding['match_goal_number']} of the match, "
                      f"the feed says {n}")
    if "solo_run" in grounding:
        own = on_the_ball(events, g)
        mine = [e for e in own if e["player"]["name"] == g["player"]["name"]]
        if not grounding["solo_run"]:
            fail(tag, "solo_run is there and false; a key is a claim, so leave it out")
        elif not mine:
            fail(tag, "solo_run, but the scorer is not on the ball in that possession")
        else:
            after = own[own.index(mine[0]):]
            others = sorted({e["player"]["name"] for e in after
                             if e["player"]["name"] != g["player"]["name"]})
            if others:
                fail(tag, f"solo_run, but from the scorer's first touch to the shot the "
                          f"feed also records {', '.join(others)} on the ball")
            # Nobody else on the ball is not yet a run: a one-touch finish
            # satisfies it on its own, and the 2022 hero is exactly that. So
            # the scorer has to have moved with the ball himself as well.
            moved = [e for e in after if e["type"]["name"] in ("Carry", "Dribble")]
            if not moved:
                fail(tag, "solo_run, but the feed records no carry or dribble by the "
                          "scorer between his first touch and the shot")
    if "own_half" in grounding:
        where = grounding["own_half"]
        if where == "first touch":
            mine = [e for e in on_the_ball(events, g)
                    if e["player"]["name"] == g["player"]["name"] and e.get("location")]
            at = mine[0]["location"][0] if mine else None
        elif where == "possession start":
            started = [e for e in in_possession(events, g)
                       if e.get("location")
                       and e.get("team", {}).get("name") == g["team"]["name"]]
            at = started[0]["location"][0] if started else None
        else:
            at = None
            fail(tag, f"own_half {where!r} is neither 'first touch' nor "
                      "'possession start'")
        if at is not None and at >= HALFWAY:
            fail(tag, f"own_half {where!r}, but the feed puts it at x={at}, which is "
                      f"past the halfway line at {HALFWAY:.0f}")
    if "dribbled_past" in grounding:
        beaten = [e for e in in_possession(events, g)
                  if e["type"]["name"] == "Dribbled Past"]
        if len(beaten) != grounding["dribbled_past"]:
            fail(tag, f"claims {grounding['dribbled_past']} player(s) dribbled past, the "
                      f"feed records {len(beaten)} in that possession")
        theirs = sorted({e["team"]["name"] for e in beaten})
        if theirs and theirs != [other_team(g, home_team, away_team)]:
            fail(tag, f"the players dribbled past are {theirs}, not the other team alone")
    if "yards_from_goal" in grounding:
        x, y = g["location"][:2]
        far = ((PITCH_LENGTH - x) ** 2 + (PITCH_WIDTH / 2 - y) ** 2) ** 0.5
        if round(far) != grounding["yards_from_goal"]:
            fail(tag, f"claims {grounding['yards_from_goal']} yards from goal, the feed "
                      f"puts the shot at {far:.1f}")
    if "recovers_error" in grounding:
        said = grounding["recovers_error"]
        run = in_possession(events, g)
        errors = [e for e in run if e["type"]["name"] == "Error"]
        if not any(said == e["player"]["name"] for e in errors):
            fail(tag, f"claims {said!r} made an error, the feed records "
                      f"{[e['player']['name'] for e in errors] or 'none'} in that possession")
        else:
            at = max(run.index(e) for e in errors if e["player"]["name"] == said)
            got = [e for e in run[at:]
                   if e["type"]["name"] == "Ball Recovery"
                   and e.get("team", {}).get("name") == g["team"]["name"]]
            if not got:
                fail(tag, f"claims the error by {said!r} was recovered, and the feed "
                          "records no recovery by the scoring team after it")


#: What a line has to say for each grounding key beside it, as a reading of
#: the key's value against the words. A key with no reading here is a key
#: this cannot hold the words to, and `WITHOUT_WORDS` is where it says so.
SAYS = {
    "body_part": lambda v, prose, g: v.lower() in prose.lower(),
    "play_pattern": lambda v, prose, g: v.split()[-1].lower() in prose.lower(),
    "assist": lambda v, prose, g: says_name(prose, v),
    "solo_run": lambda v, prose, g: "solo" in prose.lower(),
    "own_half": lambda v, prose, g: "own half" in prose.lower(),
    "dribbled_past": lambda v, prose, g: says_number(prose, v),
    "yards_from_goal": lambda v, prose, g: says_number(prose, v),
    "recovers_error": lambda v, prose, g: says_name(prose, v),
    "match_goal_number": lambda v, prose, g: says_number(prose, v),
    "player_goal_number": lambda v, prose, g: says_number(prose, v),
    "seconds_after_previous_goal": lambda v, prose, g: says_number(prose, v),
}

#: Keys with no reading of their own. `score_after` is two numbers and a line
#: carrying a score says it in whatever shape it likes, so this holds the
#: numbers to the feed and says nothing about the words.
WITHOUT_WORDS = {"score_after"}

#: Every phrase in match copy that is a claim about the play, and the key
#: that has to be behind it. A phrase here with no key is a line saying
#: something nothing read out of the feed.
CLAIMS = (
    (r"\bsolo\b", "solo_run"),
    (r"\bown half\b", "own_half"),
    (r"\bcounter\b", "play_pattern"),
    (r"\bdribbl\w*\b|\bpast\b|\brounds\b|\bbeats\b", "dribbled_past"),
    (r"\byards?\b", "yards_from_goal"),
    (r"\berror\b|\bmistake\b", "recovers_error"),
    (r"\b(left|right) foot\b|\bhis head\b|\bheader\b", "body_part"),
    (r"\bset up by\b|\bassist\w*\b", "assist"),
    (r"\bopener\b|\bdoubles\b", "match_goal_number"),
    (r"\bpenalt\w+\b|\bfrom the spot\b", "shot type Penalty"),
)

#: Copy that is not about the play and is checked elsewhere. `opening` is the
#: orchestrator's header, written by `scripts/write_headers.py` and held to a
#: rerun of it by `tests/test_moment_card_header.py`; `audio` and `voice_for`
#: are file names and slot keys.
#: `tag` is GOAL or PENALTY and is held to the feed's shot type by
#: `check_match`, so it is a value rather than a line of copy.
NOT_PROSE = {"opening", "audio", "voice_for", "event", "grounding",
             "session_clock", "tag"}


def claims_in(prose):
    """Every claim about the play in one line, with the key each one needs."""
    return [(re.search(pattern, prose, re.IGNORECASE).group(0), key)
            for pattern, key in CLAIMS
            if re.search(pattern, prose, re.IGNORECASE)]


def check_prose(tag, prose, block, g, events, fail, note):
    """One line of copy, both ways: every key said, and every claim keyed.

    `block` is the object the line belongs to, so its `grounding` and its
    `event` are what back it.
    """
    grounding = block.get("grounding", {})
    claimed = block.get("event", {})
    for key, value in sorted(grounding.items()):
        if key in WITHOUT_WORDS:
            continue
        reading = SAYS.get(key)
        if reading is None:
            fail(tag, f"grounding key {key!r} has no reading in SAYS, so nothing "
                      "holds the words to it")
        elif not reading(value, prose, g):
            fail(tag, f"grounding says {key}={value!r} and the words do not: {prose!r}")
    for said, key in claims_in(prose):
        if key == "shot type Penalty":
            backed = claimed.get("shot_type") == "Penalty"
        else:
            backed = key in grounding
        if not backed:
            fail(tag, f"says {said!r}, which is a claim about the play, with no "
                      f"{key} behind it: {prose!r}")
    note(f"  {tag}: {len(grounding)} key(s), "
         f"{len(claims_in(prose))} claim(s) in the words")


def check_names(tag, prose, g, events, players, fail):
    """A player named in a line was on the ball in that goal's possession.

    This is what held the removed broadcast quote: it listed the players it
    named and each one had to be recorded in the possession. The quote is
    gone and the rule is not, and it reads the line itself now rather than a
    list beside it, so a name added to a caption is read the same way.
    """
    there = {e["player"]["name"] for e in in_possession(events, g) if "player" in e}
    among = {part for one in there for part in name_parts(one)}
    for full in sorted(players):
        for part in name_parts(full):
            if not re.search(r"\b%s\b" % re.escape(part), prose, re.IGNORECASE):
                continue
            if part not in among:
                fail(tag, f"names {part!r}, who the feed does not record in "
                          f"possession {g['possession']}")


def check_other_copy(entry, fail, note):
    """No line anywhere else in the entry makes a claim about the play.

    The two blocks above are where a description belongs and where one is
    held. This is the other direction: a description moved into the list
    card's status line, or a Live helper, or a moments subtitle, would be out
    of their reach, so it is a failure wherever it is written.
    """
    found = 0

    def walk(value, path):
        nonlocal found
        if isinstance(value, dict):
            for key, inner in value.items():
                if key not in NOT_PROSE:
                    walk(inner, f"{path}.{key}" if path else key)
        elif isinstance(value, list):
            for i, inner in enumerate(value):
                walk(inner, f"{path}[{i}]")
        elif isinstance(value, str) and path not in HELD_PROSE:
            found += 1
            for said, key in claims_in(value):
                fail(f"match {entry['match_id']} {path}",
                     f"says {said!r}, which is a claim about the play, on a line "
                     f"no grounding block stands behind: {value!r}")

    walk(entry, "")
    note(f"  {found} other line(s) of copy carry no claim about the play")


#: The lines a grounding block stands behind. They are read together, because
#: one block is the facts behind one goal's copy and a claim may be made in
#: either line: the hero's share text says "solo goal" and its caption is
#: where "solo" is traced.
HERO_PROSE = ("caption", "share_text")
MOMENT_PROSE = ("title", "body")

#: The same lines by their path in the entry. Everything else in matches.json
#: is held by `check_other_copy` to making no claim about the play at all.
HELD_PROSE = {f"hero.{field}" for field in HERO_PROSE} | {
    f"moments[{i}].{field}" for i in range(8) for field in MOMENT_PROSE
}


def check_match(entry, fail, note):
    mid = entry["match_id"]
    events = load(RAW / "events" / f"{mid}.json")
    index = next(m for m in load(INDEXES[mid]) if m["match_id"] == mid)
    goals = goals_of(events)
    home_team = entry["home_team"]
    away_team = entry["away_team"]
    where = f"match {mid}"
    # Every player this match's own feed records, which is the universe a
    # name in a line of copy is read against.
    players = {e["player"]["name"] for e in events if "player" in e}

    for key, actual in (("home_team", index["home_team"]["home_team_name"]),
                        ("away_team", index["away_team"]["away_team_name"])):
        if entry[key] != actual:
            fail(where, f"{key} is {entry[key]!r}, the index says {actual!r}")

    venue = index.get("stadium", {}).get("name")
    if venue:
        for screen in ("picker", "live_seated"):
            claimed = entry[screen]["venue"]
            if venue.split()[0] not in claimed:
                fail(where, f"{screen} venue {claimed!r} does not name the index stadium {venue!r}")

    note(f"{where}: {entry['home_team']} vs {entry['away_team']} at {venue}, "
         f"{len(goals)} goals in periods 1 to {LAST_MATCH_PERIOD}")

    # The list of today's events is pre-match: the kickoff time off the index,
    # and nothing that has happened since, which is 0-0.
    pick = entry["picker"]
    kick = (index.get("kick_off") or "")[:5]
    if pick["kickoff"] != kick:
        fail(where, f"picker kickoff {pick['kickoff']!r}, the index says {kick!r}")
    if [pick["home_goals"], pick["away_goals"]] != [0, 0]:
        fail(where, f"picker shows {pick['home_goals']}-{pick['away_goals']}; a pre-match "
                    "card is 0-0")
    want = f"{entry['home_abbr']} 0 - 0 {entry['away_abbr']}"
    if pick["score"] != want:
        fail(where, f"picker score {pick['score']!r}, expected {want!r}")
    if venue and pick.get("stadium") != venue:
        fail(where, f"picker stadium {pick.get('stadium')!r}, the index says {venue!r}")
    for banned in ("state", "badge"):
        if banned in pick:
            fail(where, f"picker still carries {banned!r}; the list shows no clock "
                        "and nothing from after kickoff")
    note(f"  list card: kickoff {pick['kickoff']}, {pick['score']}, {pick['stadium']}")

    tally = {entry["home_team"]: 0, entry["away_team"]: 0}
    for g in goals:
        tally[g["team"]["name"]] += 1
    if [tally[entry["home_team"]], tally[entry["away_team"]]] != [index["home_score"], index["away_score"]]:
        fail(where, f"goals in the feed are {tally}, the index says "
                    f"{index['home_score']}-{index['away_score']}")
    note(f"  index score {index['home_score']}-{index['away_score']} reconciles with the feed")

    hero = entry["hero"]
    g = hero_goal = find_goal(goals, hero["event"])
    if g is None:
        fail(where, f"hero event {hero['event']} is not a goal in the feed")
    else:
        check_event(where + " hero", hero["event"], g, fail)
        check_labels(where + " hero", hero, g, fail)
        if not hero["caption"].startswith(hero["period_label"]):
            fail(where + " hero", "caption does not open with the period label")
        if f"{hero['display_minute']}'" not in hero["caption"]:
            fail(where + " hero", f"caption does not carry display minute {hero['display_minute']}")
        # The share sheet must describe this match, so it has to name the scorer.
        share = hero.get("share_text", "")
        named = [w.strip(".,'’s") for w in share.split()
                 if len(w.strip(".,'’s")) >= 4 and w.strip(".,'’s") in g["player"]["name"]]
        if not share:
            fail(where + " hero", "no share_text; the share sheet would describe no match")
        elif not named:
            fail(where + " hero",
                 f"share_text {share!r} names nobody from {g['player']['name']!r}")
        check_grounding(where + " hero", hero.get("grounding", {}), g, goals, events,
                        home_team, away_team, fail)
        said = " ".join(hero[field] for field in HERO_PROSE)
        check_prose(where + " hero", said, hero, g, events, fail, note)
        check_names(where + " hero", said, g, events, players, fail)
        note(f"  hero: {g['player']['name']} at {g['minute']}:{g['second']:02d} p{g['period']} "
             f"shown as {hero['period_label']} {hero['display_minute']}'")
        note(f"  share text names {named}")

    # One session clock, sitting at the hero moment.
    sc = entry["session_clock"]
    session = (sc["period"], sc["minute"], sc["second"])
    if hero_goal is not None and session != clock(hero_goal):
        fail(where, f"session clock {session} is not the hero moment {clock(hero_goal)}")
    if PERIOD_LABELS[sc["period"]] != sc["period_label"]:
        fail(where, f"session clock period {sc['period']} labelled {sc['period_label']!r}")
    if sc["display_minute"] != sc["minute"] + 1:
        fail(where, f"session clock display minute {sc['display_minute']} for raw {sc['minute']}")
    note(f"  session clock: {sc['period_label']} {sc['display_minute']}' "
         f"(raw {sc['minute']}:{sc['second']:02d} p{sc['period']})")

    # Live has two states. Before the moment the clock is short of it; after, it
    # has moved to the moment and the score is what the data records there.
    for name, inclusive in (("before", False), ("after", True)):
        st = entry["live_seated"][name]
        if inclusive:
            counted = [x for x in goals if clock(x) <= session]
        else:
            cut = (st["period"], st["display_minute"] - 1, 0)
            counted = [x for x in goals if clock(x) < cut]
        home = sum(1 for x in counted if x["team"]["name"] == home_team)
        away = len(counted) - home
        if [st["home_goals"], st["away_goals"]] != [home, away]:
            fail(where, f"Live {name} shows {st['home_goals']}-{st['away_goals']} at "
                        f"{st['period_label']} {st['display_minute']}', the feed says {home}-{away}")
        if PERIOD_LABELS[st["period"]] != st["period_label"]:
            fail(where, f"Live {name} period {st['period']} labelled {st['period_label']!r}")
        for key in ("prompt", "action", "help"):
            if not st.get(key):
                fail(where, f"Live {name} has no {key}")
        note(f"  Live {name}: {st['period_label']} {st['display_minute']}' "
             f"{entry['home_abbr']} {home} - {away} {entry['away_abbr']}  [{st['prompt']}]")

    if entry["live_seated"]["after"]["display_minute"] != sc["display_minute"]:
        fail(where, "Live after does not sit on the session clock")
    if entry["live_seated"]["before"]["display_minute"] >= sc["display_minute"]:
        fail(where, "Live before is not earlier than the session clock")

    # One step-away, one goal missed. The moment card tells one buildup, so a
    # fan who leaves before one goal and returns after another would come back
    # to a score the card does not explain. Every goal between the two Live
    # states has to be the hero moment and nothing else.
    st = entry["live_seated"]["before"]
    cut = (st["period"], st["display_minute"] - 1, 0)
    missed = [x for x in goals if cut <= clock(x) <= session]
    if len(missed) != 1:
        fail(where, f"{len(missed)} goals fall between Live before "
                    f"({st['period_label']} {st['display_minute']}') and the session "
                    "clock; the moment card tells exactly one")

    if entry["synced_count"] != len(entry["moments"]):
        fail(where, f"synced_count {entry['synced_count']} but {len(entry['moments'])} moments")
    upto = [x for x in goals if clock(x) <= session]
    if len(entry["moments"]) != len(upto):
        fail(where, f"{len(entry['moments'])} moments for {len(upto)} goals at or before the "
                    "session clock")

    seen = set()
    for m in entry["moments"]:
        g = find_goal(goals, m["event"])
        tag = f"{where} {m['title']!r}"
        if g is None:
            fail(tag, f"event {m['event']} is not a goal in periods 1 to {LAST_MATCH_PERIOD}")
            continue
        seen.add(clock(g))
        check_event(tag, m["event"], g, fail)
        check_labels(tag, m, g, fail)
        want_tag = "PENALTY" if g["shot"]["type"]["name"] == "Penalty" else "GOAL"
        if m["tag"] != want_tag:
            fail(tag, f"tagged {m['tag']}, the feed says shot type {g['shot']['type']['name']}")
        named = m["title"].split()[0].rstrip("'s")
        if named not in g["player"]["name"]:
            fail(tag, f"title names {named!r}, the scorer is {g['player']['name']!r}")
        check_grounding(tag, m.get("grounding", {}), g, goals, events, home_team,
                        away_team, fail)
        said = " ".join(m[field] for field in MOMENT_PROSE)
        check_prose(tag, said, m, g, events, fail, note)
        check_names(tag, said, g, events, players, fail)
        note(f"  {m['tag']:<8} {m['period_label']} {m['display_minute']:>3}'  "
             f"{g['player']['name']} ({g['shot']['type']['name']}, "
             f"{g['shot']['body_part']['name']})")

    expected = {clock(g) for g in goals if clock(g) <= session}
    missing = expected - seen
    if missing:
        fail(where, f"goals at or before the session clock with no moment: {sorted(missing)}")
    late = sorted(c for c in seen if c > session)
    if late:
        fail(where, f"Moments shows {late}, which is after the session clock {session}")
    note(f"  Moments stops at the session clock: {len(seen)} of {len(goals)} goals")
    check_other_copy(entry, fail, note)


WEB = ROOT / "app" / "web"
DEFAULT_MATCH = 3750191
NARRATIONS = WEB / "narrations.json"

#: The slot a listener with no side hears, which is the key `renderNarration`
#: falls back to. The markup carries no copy of it:
#: `check_card_carries_no_narration` is why the card has no inline narration.
NEUTRAL_SLOT = "storyteller_neutral"

CARD = "prelude_03_moment_card.html"


def check_frozen_narrations(doc, match_id, fail):
    """Every listener a match can send to a slot has a narration there.

    **The card shows what the fan hears.** There is one frozen narration per
    `hero.voice_for` key, the renderer picks it by the listener's own
    allegiance and `app/web/narration-player.js` picks the recording by the
    same lookup, so the words under "Verified from play data" are the words
    the voice reads. Every key a match sends a listener to therefore needs a
    narration: a key with none would leave that fan reading another
    listener's telling.

    `NEUTRAL_SLOT` is checked on top of those keys because it is what
    `renderNarration` falls back to when the fan's own key has none.

    Whether the words are still grounded is a different question and is
    `tests/test_frozen_narrations.py`'s. This only asks whether every
    listener has one and whether it says who wrote it.
    """
    if not NARRATIONS.is_file():
        fail("narrations.json", "is missing; run scripts/freeze_narrations.py")
        return
    frozen = json.loads(NARRATIONS.read_text(encoding="utf-8"))
    entry = frozen.get("narrations", {}).get(str(match_id))
    if not entry:
        fail("narrations.json", f"has no frozen narration for match {match_id}")
        return
    slots = entry.get("slots") or {}
    for match in doc["matches"]:
        keys = sorted(set(match["hero"]["voice_for"].values()))
        theirs = (
            frozen.get("narrations", {})
            .get(str(match["match_id"]), {})
            .get("slots")
            or {}
        )
        for key in keys:
            said = theirs.get(key) or {}
            if not said.get("text"):
                fail("narrations.json",
                     f"has no narration for match {match['match_id']} slot "
                     f"{key}, which hero.voice_for sends a listener to")
            elif not said.get("authorship"):
                fail("narrations.json",
                     f"match {match['match_id']} slot {key} carries no "
                     "authorship, so a reader cannot tell who wrote it")
    if not (slots.get(NEUTRAL_SLOT) or {}).get("text"):
        fail("narrations.json",
             f"has no {NEUTRAL_SLOT} narration for match {match_id}, which is "
             "the key the renderer falls back to")


def check_card_carries_no_narration(fail, note):
    """The moment card carries no narration inline, for any match or slot.

    Every other field on this card has the default match's copy inline, so a
    screen whose fetch failed is a correct screen rather than a broken one.
    The narration cannot take that bargain, because it arrives under
    "Verified from play data": the 1986 words standing under a 2022 header
    are a claim the data never made for that match, and a fan on a slow
    connection could read them before `narrations.json` landed.

    So the card ships the paragraph empty, with it and the label hidden, and
    `app/web/match-content.js` fills and shows the two together only once the
    frozen text for the match and the slot on screen is in it. The text this
    holds the markup to is therefore the text the card can show: none of it
    until the fetch answers, and the served slot's afterwards.

    The markup mechanics behind that (the two hidden elements, the empty
    paragraph, the space the block keeps and the one function that reveals
    them) are held by
    `tests/test_frozen_narrations.py::TestTheNarrationAndTheLabelAppearTogether`.
    """
    if not NARRATIONS.is_file():
        return
    markup = (WEB / CARD).read_text(encoding="utf-8")
    frozen = json.loads(NARRATIONS.read_text(encoding="utf-8"))
    counted = 0
    for match_id, entry in sorted(frozen.get("narrations", {}).items()):
        for key, slot in sorted((entry.get("slots") or {}).items()):
            said = (slot or {}).get("text")
            if not said:
                continue
            counted += 1
            if said in markup:
                fail(CARD,
                     f"carries the match {match_id} {key} narration inline; "
                     "the card would show it under the grounding label before "
                     "narrations.json had answered")
    note(f"  {CARD} carries none of the {counted} frozen narrations inline, "
         "so the label has nothing to stand over until one is fetched")


def check_screens(doc, fail, note):
    """The markup and matches.json must agree.

    The picker lists both matches statically, and the other screens carry the
    default match inline as the copy shown before the renderer runs. Either can
    drift from matches.json without anything else noticing, so both are checked
    against it here.
    """
    picker = (WEB / "prelude_01_picker.html").read_text(encoding="utf-8")
    for entry in doc["matches"]:
        p = entry["picker"]
        for label, value in (("title", p["title"]), ("venue", p["venue"]),
                             ("score", p["score"]), ("status", p["status"])):
            if value not in picker:
                fail(f"list card {entry['match_id']}",
                     f"{label} {value!r} is in matches.json but not in the markup")
        if f"KICKOFF {p['kickoff']}" not in picker:
            fail(f"list card {entry['match_id']}",
                 f"kickoff {p['kickoff']!r} is not in the markup")

    # The list is pre-match, so none of the in-match furniture belongs on it.
    live = (WEB / "prelude_02_live_seated.html").read_text(encoding="utf-8")
    # The badge that read "AT VENUE, GPS" is gone from every screen. It said a
    # satellite fix had placed the fan at the ground, and no code in this repo
    # reads a position: CLAUDE.md names GPS presence as one of the three inputs
    # and nothing uses it. It was on Live and on the ticket; this is both
    # directions of the same check, so putting it back anywhere fails here.
    for name in sorted(WEB.glob("*.html")):
        if "AT VENUE" in name.read_text(encoding="utf-8"):
            fail(name.name, "carries a badge claiming a GPS fix at the venue; "
                            "no code in this repo reads a position")
    if "Change event" not in live:
        fail("Live screen", "no 'Change event' link back to the list")
    for entry in doc["matches"]:
        for name in ("before", "after"):
            st = entry["live_seated"][name]
            clock_text = f"{st['period_label']} \u00b7 {st['display_minute']}'"
            if clock_text in picker:
                fail("list", f"shows an in-match clock {clock_text!r}; the list is pre-match")
    note("  list markup carries both cards from matches.json, with no clock")
    note("  no screen claims a GPS fix at the venue")
    note("  Live screen carries a 'Change event' link back to the list")

    default = next(e for e in doc["matches"] if e["match_id"] == DEFAULT_MATCH)
    inline = {
        "prelude_02_live_seated.html": [
            default["live_seated"]["venue"], default["live_seated"]["ticket"],
            default["live_seated"]["caption"],
        ],
        CARD: [default["hero"]["caption"]],
        "prelude_04_moments.html": [default["moments_subtitle"]]
            + [m["title"] for m in default["moments"]]
            + [m["body"] for m in default["moments"]],
        "prelude_06_ticket.html": [
            default["picker"]["venue"], default["picker"]["kickoff"],
            default["picker"]["status"], default["live_seated"]["venue"],
        ],
    }
    for name, values in inline.items():
        markup = (WEB / name).read_text(encoding="utf-8")
        for value in values:
            if value and value not in markup:
                fail(name, f"inline copy does not carry {value!r} from matches.json")
    note(f"  inline copy on the other screens matches the default match {DEFAULT_MATCH}")

    check_frozen_narrations(doc, DEFAULT_MATCH, fail)
    check_card_carries_no_narration(fail, note)


def main():
    failures = []
    notes = []

    def fail(where, message):
        failures.append(f"  {where}: {message}")

    def note(line):
        notes.append(line)

    doc = json.loads(COPY.read_text(encoding="utf-8"))
    print(f"checking {COPY.relative_to(ROOT).as_posix()} against data/raw\n")
    for entry in doc["matches"]:
        check_match(entry, fail, note)
        notes.append("")
    check_screens(doc, fail, note)
    print("\n".join(notes).rstrip())

    if failures:
        print(f"\n{len(failures)} mismatch(es):")
        print("\n".join(failures))
        return 1
    print("\nevery name, minute, score and count in the copy matches the feed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
