r"""Check every factual value in app/web/matches.json against the raw events.

matches.json is fixed display copy, written by hand. This is what keeps it
honest: every name, minute, score, count, body part, play pattern and assist in
it is looked up in data/raw and compared. Exit code is 1 on any mismatch, so it
can gate a commit.

It does not search the data for goals or buildups. It is handed the values the
copy claims and checks each one. Finding moments is the EventFeed module's job.

    .\.venv-prelude\Scripts\python.exe -I scripts\check_match_copy.py
"""

import json
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


def check_grounding(tag, grounding, g, goals, events, home_team, fail):
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


def check_match(entry, fail, note):
    mid = entry["match_id"]
    events = load(RAW / "events" / f"{mid}.json")
    index = next(m for m in load(INDEXES[mid]) if m["match_id"] == mid)
    goals = goals_of(events)
    home_team = entry["home_team"]
    where = f"match {mid}"

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
            fail(where, f"picker still carries {banned!r}; the list shows no clock and no "
                        "GPS badge")
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
        in_poss = {e["player"]["name"] for e in events
                   if e["possession"] == g["possession"] and "player" in e}
        for name in hero["quote_names"]:
            if not any(name in full for full in in_poss):
                fail(where + " hero",
                     f"quote names {name!r}, who is not recorded in possession {g['possession']}")
            if name not in hero["quote"]:
                fail(where + " hero", f"quote_names lists {name!r} but the quote does not say it")
        # The share sheet must describe this match, so it has to name the scorer.
        share = hero.get("share_text", "")
        named = [w.strip(".,'’s") for w in share.split()
                 if len(w.strip(".,'’s")) >= 4 and w.strip(".,'’s") in g["player"]["name"]]
        if not share:
            fail(where + " hero", "no share_text; the share sheet would describe no match")
        elif not named:
            fail(where + " hero",
                 f"share_text {share!r} names nobody from {g['player']['name']!r}")
        note(f"  hero: {g['player']['name']} at {g['minute']}:{g['second']:02d} p{g['period']} "
             f"shown as {hero['period_label']} {hero['display_minute']}'")
        note(f"  share text names {named}")
        note(f"  quote names {hero['quote_names']} all recorded in possession {g['possession']}")

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
        check_grounding(tag, m.get("grounding", {}), g, goals, events, home_team, fail)
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


WEB = ROOT / "app" / "web"
DEFAULT_MATCH = 3750191


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
    if "AT VENUE" in picker:
        fail("list", "a GPS badge is on the list; it belongs to the Live screen")
    if "AT VENUE" not in live:
        fail("Live screen", "the GPS badge is missing after selection")
    if "Change event" not in live:
        fail("Live screen", "no 'Change event' link back to the list")
    for entry in doc["matches"]:
        for name in ("before", "after"):
            st = entry["live_seated"][name]
            clock_text = f"{st['period_label']} \u00b7 {st['display_minute']}'"
            if clock_text in picker:
                fail("list", f"shows an in-match clock {clock_text!r}; the list is pre-match")
    note("  list markup carries both cards from matches.json, with no clock and no GPS badge")
    note("  Live screen carries the GPS badge and a 'Change event' link")

    default = next(e for e in doc["matches"] if e["match_id"] == DEFAULT_MATCH)
    inline = {
        "prelude_02_live_seated.html": [
            default["live_seated"]["venue"], default["live_seated"]["ticket"],
            default["live_seated"]["caption"],
        ],
        "prelude_03_moment_card.html": [default["hero"]["caption"], default["hero"]["quote"]],
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
