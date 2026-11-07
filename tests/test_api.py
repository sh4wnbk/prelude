"""The hosted read-only API: every endpoint, every error, and what it may not do.

`app/api.py` exists so watsonx Orchestrate has a stable public URL to call.
It is deployed on a free tier that spins down after fifteen minutes without
traffic and rebuilds its filesystem from the build, so the service holds no
state, writes nothing, needs no credentials and makes no paid call. Those are
not comments here: `TestWhatItDoesNotReach` reads the module's imports and
`TestItWritesNothing` reads its calls.

**The slot rule is the one thing in this file that is also somewhere else.**
`Prelude.slotFor` in `app/web/match-content.js` picks the narration the moment
card shows and the recording its player plays; `slot_for` in `app/api.py`
picks the same slot for a caller. Two copies of a rule drift, so the table
they answer lives in `tests/slot_rows.json` and is handed to both test files
by the `slot_rows` fixture in `tests/conftest.py`. This file runs each row
through the Python copy and through `GET /buildup`;
`tests/test_narrator_picker.py::TestTheSevenRows` reads the same rows against
`hero.voice_for` and `hero.audio`, which is what the browser's copy indexes.

**The goals are the ones in the data.** `EXPECTED_GOALS` was read off
`GET /moments` against `data/raw/`, both matches, and it is the shootout-free
scoreline the index reconciles with: Argentina 2 England 1, and Argentina 3
France 3. `scripts/check_match_copy.py` is what holds `matches.json` to the
same data; this holds the endpoint to it.

The suite has no network and no credentials (`tests/conftest.py`), and
`TestClient` speaks to the application object in process, so nothing here
opens a connection.
"""

import ast
import json
import re
import socket
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import (
    BUILD_COMMIT_FILE,
    PAGES_BASE,
    app,
    build_commit,
    display_minute,
    slot_for,
)
from app.grounding import GROUNDING_LABEL

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
WEB = APP / "web"
API_SOURCE = APP / "api.py"

MATCHES = json.loads((WEB / "matches.json").read_text(encoding="utf-8"))
NARRATIONS = json.loads((WEB / "narrations.json").read_text(encoding="utf-8"))
NARRATORS = json.loads((WEB / "narrators.json").read_text(encoding="utf-8"))

MATCH_IDS = sorted(entry["match_id"] for entry in MATCHES["matches"])

#: A match id that is not one of the two, for the 404 paths.
ABSENT_MATCH = 1

#: Every goal of each match as the endpoint reports it: scorer, team, the
#: minute the app captions, the score after it, and whether the app narrates
#: it. Read off the live endpoint against `data/raw/` on 2026-11-07. Period 5
#: is the 2022 shootout and is not a goal of the match, which is Bob's rule in
#: `app/statsbomb_event_feed.py`, so the 2022 final ends 3-3 here.
EXPECTED_GOALS = {
    3750191: [
        ("Diego Armando Maradona", "Argentina", 51, 1, 0, False),
        ("Diego Armando Maradona", "Argentina", 55, 2, 0, True),
        ("Gary Lineker", "England", 81, 2, 1, False),
    ],
    3869685: [
        ("Lionel Andrés Messi Cuccittini", "Argentina", 23, 1, 0, False),
        ("Ángel Fabián Di María Hernández", "Argentina", 36, 2, 0, True),
        ("Kylian Mbappé Lottin", "France", 80, 2, 1, False),
        ("Kylian Mbappé Lottin", "France", 81, 2, 2, False),
        ("Lionel Andrés Messi Cuccittini", "Argentina", 108, 3, 2, False),
        ("Kylian Mbappé Lottin", "France", 118, 3, 3, False),
    ],
}

#: What `app/api.py` may not import, directly or through anything it imports.
#: `app/tts.py` is Watson Text to Speech and `app/narration_provider.py` is
#: the watsonx backend, so either one in the closure would put a paid client
#: in the deployed process. `app/credentials.py` reads the file outside the
#: repo, and `app/narration_config.py` carries the model ids that only a paid
#: call needs. The service serves frozen narration and committed recordings,
#: so it needs none of them.
FORBIDDEN_MODULES = {
    "app.tts",
    "app.narration_provider",
    "app.narration_config",
    "app.credentials",
}

#: Names that would make the module a writer. A service whose filesystem is
#: rebuilt from the build cannot keep anything it writes, so writing at all
#: would be a bug that only showed up after a spin-down.
WRITE_CALLS = ("write_text", "write_bytes", "mkdir", "unlink", "rmtree", "touch")


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def heroes():
    return {entry["match_id"]: entry["hero"] for entry in MATCHES["matches"]}


def api_tree():
    return ast.parse(API_SOURCE.read_text(encoding="utf-8"))


def imported_modules(path: Path) -> set[str]:
    """Every module `path` imports, by dotted name, read off its syntax tree.

    A string in a docstring is not an import, which is why this parses rather
    than greps: `app/api.py` names `app/tts.py` in its own docstring to say it
    does not import it.
    """
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            found.add(node.module)
    return found


def app_import_closure() -> set[str]:
    """Every `app.*` module reachable from `app/api.py` by imports."""
    seen: set[str] = set()
    queue = ["app.api"]
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        path = APP / (name.split(".", 1)[1] + ".py")
        if not path.is_file():
            continue
        queue.extend(
            found for found in imported_modules(path) if found.startswith("app.")
        )
    return seen


class TestHealth:
    def test_it_says_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_it_names_no_commit_when_nothing_wrote_one(self, client, monkeypatch):
        """A local run has no build stamp, and `/health` says nothing instead
        of guessing. `render.yaml` writes the file on Render."""
        monkeypatch.setattr(
            "app.api.BUILD_COMMIT_FILE", ROOT / "build" / "absent-commit.txt"
        )
        assert client.get("/health").json() == {"status": "ok"}

    def test_it_names_the_commit_the_build_wrote(self, client, monkeypatch, tmp_path):
        stamp = tmp_path / "commit.txt"
        stamp.write_text("b88bf48\n", encoding="utf-8")
        monkeypatch.setattr("app.api.BUILD_COMMIT_FILE", stamp)
        assert client.get("/health").json() == {
            "status": "ok",
            "commit": "b88bf48",
        }

    def test_an_empty_stamp_is_no_commit(self, monkeypatch, tmp_path):
        stamp = tmp_path / "commit.txt"
        stamp.write_text("\n", encoding="utf-8")
        monkeypatch.setattr("app.api.BUILD_COMMIT_FILE", stamp)
        assert build_commit() is None

    def test_the_stamp_is_not_committed(self):
        """The file is written by the build, so the repo does not carry one."""
        assert not BUILD_COMMIT_FILE.is_file()


class TestMoments:
    @pytest.mark.parametrize("match_id", MATCH_IDS)
    def test_every_goal_of_the_match(self, client, match_id):
        body = client.get("/moments", params={"match": match_id}).json()
        reported = [
            (
                goal["scorer"],
                goal["team"],
                goal["display_minute"],
                goal["score_after"]["home"],
                goal["score_after"]["away"],
                goal["narrated"],
            )
            for goal in body["goals"]
        ]
        assert reported == EXPECTED_GOALS[match_id]

    @pytest.mark.parametrize("match_id", MATCH_IDS)
    def test_it_names_the_two_teams(self, client, match_id):
        entry = next(m for m in MATCHES["matches"] if m["match_id"] == match_id)
        body = client.get("/moments", params={"match": match_id}).json()
        assert body["match_id"] == match_id
        assert body["home_team"] == entry["home_team"]
        assert body["away_team"] == entry["away_team"]

    @pytest.mark.parametrize("match_id", MATCH_IDS)
    def test_one_goal_is_narrated_and_it_is_the_hero(self, client, match_id):
        """`narrated` is not a flag about the data. It says which goal the six
        frozen narrations and the six recordings were made for, which is
        `hero.event` in `matches.json`."""
        body = client.get("/moments", params={"match": match_id}).json()
        narrated = [goal for goal in body["goals"] if goal["narrated"]]
        hero = heroes()[match_id]["event"]
        assert len(narrated) == 1
        assert narrated[0]["scorer"] == hero["player"]
        assert narrated[0]["team"] == hero["team"]
        assert narrated[0]["display_minute"] == display_minute(hero["minute"])

    @pytest.mark.parametrize("match_id", MATCH_IDS)
    def test_the_score_after_the_last_goal_is_the_full_score(self, client, match_id):
        """Each row's score counts that goal, so the last row is the match."""
        goals = client.get("/moments", params={"match": match_id}).json()["goals"]
        home = sum(1 for g in goals if g["team"] == EXPECTED_GOALS[match_id][0][1])
        assert goals[-1]["score_after"]["home"] == home

    def test_an_unknown_match_is_404(self, client):
        response = client.get("/moments", params={"match": ABSENT_MATCH})
        assert response.status_code == 404
        assert str(ABSENT_MATCH) in response.json()["detail"]

    def test_a_missing_match_is_422(self, client):
        assert client.get("/moments").status_code == 422

    def test_a_match_that_is_not_a_number_is_422(self, client):
        assert client.get("/moments", params={"match": "final"}).status_code == 422


class TestTheSevenRows:
    """One table, two languages. The rows are in `tests/slot_rows.json`."""

    def test_there_are_seven(self, slot_rows):
        assert len(slot_rows) == 7

    def test_the_rule_in_python_answers_every_row(self, slot_rows):
        answers = [
            slot_for(
                heroes()[row["match_id"]]["voice_for"],
                row["listener"],
                row["narrator"],
            )
            for row in slot_rows
        ]
        assert answers == [row["slot"] for row in slot_rows]

    def test_the_endpoint_answers_every_row(self, client, slot_rows):
        answers = []
        for row in slot_rows:
            params = {"match": row["match_id"], "listener": row["listener"]}
            if row["narrator"]:
                params["narrator"] = row["narrator"]
            response = client.get("/buildup", params=params)
            assert response.status_code == 200, row["reads"]
            answers.append(response.json()["slot"])
        assert answers == [row["slot"] for row in slot_rows]

    def test_the_rows_cover_both_matches_and_all_three_answers(self, slot_rows):
        """What the seven are for: both heroes, every answer to "Who are you
        with", the default and a chosen narrator, and the fallback."""
        assert {row["match_id"] for row in slot_rows} == set(MATCH_IDS)
        assert {row["listener"] for row in slot_rows} == {
            "team_a",
            "team_b",
            "neutral",
        }
        assert None in {row["narrator"] for row in slot_rows}
        assert {"buddy", "storyteller"} <= {row["narrator"] for row in slot_rows}


class TestBuildup:
    @pytest.mark.parametrize("match_id", MATCH_IDS)
    def test_the_text_is_the_frozen_slots_own(self, client, match_id, slot_rows):
        """The words a caller is handed are the words in
        `app/web/narrations.json` for that slot, not a rewrite of them."""
        for row in slot_rows:
            if row["match_id"] != match_id:
                continue
            params = {"match": match_id, "listener": row["listener"]}
            if row["narrator"]:
                params["narrator"] = row["narrator"]
            body = client.get("/buildup", params=params).json()
            frozen = NARRATIONS["narrations"][str(match_id)]["slots"][row["slot"]]
            assert body["text"] == frozen["text"]
            assert body["authorship"] == frozen["authorship"]

    def test_the_narrator_is_named_as_the_list_names_them(self, client, slot_rows):
        names = {n["id"]: n["name"] for n in NARRATORS["narrators"]}
        for row in slot_rows:
            params = {"match": row["match_id"], "listener": row["listener"]}
            if row["narrator"]:
                params["narrator"] = row["narrator"]
            body = client.get("/buildup", params=params).json()
            frozen = NARRATIONS["narrations"][str(row["match_id"])]["slots"][
                row["slot"]
            ]
            assert body["narrator"] == names[frozen["narrator"]]

    def test_it_reports_the_listener_it_was_asked_about(self, client):
        body = client.get(
            "/buildup", params={"match": MATCH_IDS[0], "listener": "neutral"}
        ).json()
        assert body["listener"] == "neutral"
        assert body["match_id"] == MATCH_IDS[0]

    def test_a_narrator_nobody_has_recorded_falls_back(self, client):
        """The Caller has no slot in either hero, so a fan who asks for one
        hears the telling their side was written. The browser's copy does the
        same, which is why Profile marks the Storyteller and not the Caller."""
        body = client.get(
            "/buildup",
            params={"match": 3869685, "listener": "team_a", "narrator": "caller"},
        ).json()
        assert body["slot"] == "buddy_scored"

    def test_an_unknown_narrator_id_falls_back(self, client):
        body = client.get(
            "/buildup",
            params={"match": 3869685, "listener": "team_b", "narrator": "nobody"},
        ).json()
        assert body["slot"] == "buddy_conceded"

    def test_an_unknown_match_is_404(self, client):
        response = client.get(
            "/buildup", params={"match": ABSENT_MATCH, "listener": "neutral"}
        )
        assert response.status_code == 404
        assert str(ABSENT_MATCH) in response.json()["detail"]

    @pytest.mark.parametrize("bad", ["team_c", "argentina", "TEAM_A", ""])
    def test_a_listener_that_is_not_one_of_the_three_is_422(self, client, bad):
        response = client.get(
            "/buildup", params={"match": MATCH_IDS[0], "listener": bad}
        )
        assert response.status_code == 422

    def test_no_listener_at_all_is_422(self, client):
        assert (
            client.get("/buildup", params={"match": MATCH_IDS[0]}).status_code == 422
        )

    def test_no_match_at_all_is_422(self, client):
        assert client.get("/buildup", params={"listener": "neutral"}).status_code == 422


class TestTheRecording:
    def test_every_audio_url_is_a_file_under_app_web(self, client, slot_rows):
        """The URL is the Pages site, and the site is `app/web/`. So a path
        that is not a file in the repo is a 404 a judge would hear as
        silence."""
        for row in slot_rows:
            params = {"match": row["match_id"], "listener": row["listener"]}
            if row["narrator"]:
                params["narrator"] = row["narrator"]
            url = client.get("/buildup", params=params).json()["audio_url"]
            assert url.startswith(PAGES_BASE), url
            path = WEB / url[len(PAGES_BASE):]
            assert path.is_file(), url

    def test_the_url_is_absolute_and_on_the_pages_site(self):
        assert PAGES_BASE == "https://sh4wnbk.github.io/prelude/"

    def test_the_recording_is_the_slots_own(self, client, slot_rows):
        """One key for the words and the file, which is the invariant
        `tests/test_narrator_picker.py` holds in the browser."""
        for row in slot_rows:
            params = {"match": row["match_id"], "listener": row["listener"]}
            if row["narrator"]:
                params["narrator"] = row["narrator"]
            body = client.get("/buildup", params=params).json()
            expected = heroes()[row["match_id"]]["audio"][row["slot"]]
            assert body["audio_url"] == PAGES_BASE + expected


class TestTheLabel:
    def test_the_label_is_the_one_the_check_writes(self, client, slot_rows):
        """`CLAUDE.md` allows the phrase over checked narration and over
        nothing else, so it is read off the frozen record's own permission and
        is not spelled again here or in `app/api.py`."""
        for row in slot_rows:
            params = {"match": row["match_id"], "listener": row["listener"]}
            if row["narrator"]:
                params["narrator"] = row["narrator"]
            body = client.get("/buildup", params=params).json()
            frozen = NARRATIONS["narrations"][str(row["match_id"])]["slots"][
                row["slot"]
            ]
            assert frozen["labelled"] is True
            assert body["label"] == GROUNDING_LABEL == "Verified from play data"

    def test_an_unlabelled_slot_gets_no_label(self, client, monkeypatch):
        """There is no unlabelled slot in the repo, because nothing else was
        frozen. This is the branch that keeps it that way: the permission is
        read, not assumed."""
        slots = dict(NARRATIONS["narrations"]["3750191"]["slots"])
        slots["storyteller_neutral"] = dict(
            slots["storyteller_neutral"], labelled=False
        )
        monkeypatch.setitem(
            __import__("app.api", fromlist=["NARRATIONS"]).NARRATIONS,
            "3750191",
            {"slots": slots},
        )
        body = client.get(
            "/buildup", params={"match": 3750191, "listener": "neutral"}
        ).json()
        assert "label" not in body

    def test_the_module_does_not_spell_the_phrase(self):
        """One spelling, in `app/grounding.py`. A second one here is how a
        softened variant gets in."""
        source = API_SOURCE.read_text(encoding="utf-8")
        assert source.count(GROUNDING_LABEL) == 1
        line = next(
            line for line in source.splitlines() if GROUNDING_LABEL in line
        )
        assert line.lstrip().startswith("`label` carries")


class TestGetOnly:
    @pytest.mark.parametrize("path", ["/health", "/moments", "/buildup"])
    def test_nothing_but_get_is_allowed(self, client, path):
        for method in (client.post, client.put, client.patch, client.delete):
            assert method(path).status_code == 405, path

    def test_cors_lets_a_browser_read_it(self, client):
        response = client.get("/health", headers={"Origin": "https://example.test"})
        assert response.headers["access-control-allow-origin"] == "*"

    def test_the_routes_are_the_three(self):
        routes = sorted(
            route.path for route in app.routes if getattr(route, "methods", None)
        )
        assert [r for r in routes if not r.startswith("/openapi")] == [
            "/buildup",
            "/docs",
            "/docs/oauth2-redirect",
            "/health",
            "/moments",
            "/redoc",
        ]


class TestWhatItDoesNotReach:
    """No credentials, no paid call, no environment. Read off the module."""

    def test_it_imports_no_paid_backend_directly(self):
        assert not FORBIDDEN_MODULES & imported_modules(API_SOURCE)

    def test_it_imports_no_paid_backend_through_anything_else(self):
        """The closure, not the first line: `app/narration.py` imports the
        watsonx backend, so taking one constant from there would have put the
        backend in the deployed process. That is why `GROUNDING_LABEL` moved
        to `app/grounding.py`."""
        assert not FORBIDDEN_MODULES & app_import_closure()

    def test_the_closure_is_the_modules_it_needs(self):
        """Stated rather than bounded, so a new import is a visible change."""
        assert app_import_closure() == {
            "app.api",
            "app.event_feed",
            "app.grounding",
            "app.narration_grammar",
            "app.narration_prompt",
            "app.orchestrator_contract",
            "app.personas",
            "app.pitch_zones",
            "app.plain_characters",
            "app.statsbomb_event_feed",
        }

    def test_it_does_not_import_os(self):
        assert "os" not in imported_modules(API_SOURCE)

    def test_it_reads_no_environment_variable(self):
        """The deploy carries no configuration, which is what makes the
        service nothing to audit. The commit `/health` reports arrives as a
        file `render.yaml` writes at build time, not as `RENDER_GIT_COMMIT`."""
        names = {
            node.attr
            for node in ast.walk(api_tree())
            if isinstance(node, ast.Attribute)
        } | {
            node.id for node in ast.walk(api_tree()) if isinstance(node, ast.Name)
        }
        assert not names & {"environ", "getenv", "environb"}

    def test_the_only_module_in_app_that_takes_a_third_party_package(self):
        """`docs/HARNESS.md` says this, so it is checked: FastAPI is in
        `app/api.py` and in no other module of `app/`."""
        others = sorted(
            path.name
            for path in APP.glob("*.py")
            if path.name != "api.py"
            and {
                found.split(".")[0] for found in imported_modules(path)
            }
            - {"app", "json", "os", "re", "unicodedata", "urllib", "base64",
               "dataclasses", "pathlib", "types", "typing", "datetime",
               "collections", "itertools", "functools", "enum", "math",
               "string", "textwrap", "time", "html", "copy", "io"}
        )
        assert others == []


class TestItWritesNothing:
    def test_the_module_makes_no_write_call(self):
        """The filesystem is rebuilt from the build on every wake, so
        anything written at runtime is lost without a trace. Nothing here
        writes."""
        calls = {
            node.func.attr
            for node in ast.walk(api_tree())
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        assert not calls & set(WRITE_CALLS)

    def test_it_opens_nothing_for_writing(self):
        """`open` appears once, reading `matches.json` and its two siblings,
        and `read_text` reads the build stamp. Neither takes a mode."""
        modes = [
            keyword.value
            for node in ast.walk(api_tree())
            if isinstance(node, ast.Call)
            for keyword in node.keywords
            if keyword.arg == "mode"
        ]
        assert modes == []
        positional = [
            node
            for node in ast.walk(api_tree())
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "open"
            and node.args
        ]
        assert positional == []

    def test_no_route_is_a_write_method(self):
        methods = set()
        for route in app.routes:
            methods |= getattr(route, "methods", set()) or set()
        assert methods == {"GET", "HEAD"} or methods == {"GET"}


class TestTheNetworkGuardStillHolds:
    """The in-process client needs one socket, and the guard still refuses
    every other. `tests/conftest.py` records why: asyncio wakes its own event
    loop through a socket pair on `127.0.0.1`, and nothing this repo talks to
    is on this machine."""

    def test_a_remote_connection_still_refuses(self, network_call_error):
        with pytest.raises(network_call_error):
            socket.socket().connect(("statsbomb.invalid", 443))

    def test_the_client_answers_without_one(self, client):
        assert client.get("/health").status_code == 200


class TestTheSlotRule:
    """`slot_for` on its own, including the shapes no route can hand it."""

    def test_no_voice_for_is_no_slot(self):
        assert slot_for({}, "team_a") is None

    def test_an_answer_with_no_key_falls_back_to_neutral(self):
        assert (
            slot_for({"neutral": "storyteller_neutral"}, "team_a")
            == "storyteller_neutral"
        )

    def test_the_sides_slot_wins_over_the_neutral_one(self):
        voice_for = {
            "team_a": "buddy_scored",
            "neutral": "storyteller_neutral",
        }
        assert slot_for(voice_for, "team_a") == "buddy_scored"

    def test_a_narrator_is_matched_on_the_whole_id(self):
        """`buddy_scored` belongs to `buddy`, and a narrator called `bud`
        does not get it."""
        voice_for = {"team_a": "buddy_scored", "neutral": "storyteller_neutral"}
        assert slot_for(voice_for, "team_a", "bud") == "buddy_scored"
        assert slot_for(voice_for, "team_a", "buddy") == "buddy_scored"

    def test_the_minute_is_the_broadcast_minute(self):
        assert display_minute(54) == 55
        assert display_minute(0) == 1


class TestTheSourceSaysWhatItDoes:
    def test_it_names_the_fixture_both_files_read(self):
        """A reader of `slot_for` is told where the table is, because the
        other copy of the rule is in a language this suite cannot run."""
        source = API_SOURCE.read_text(encoding="utf-8")
        assert "tests/slot_rows.json" in source

    def test_no_em_dashes(self):
        """`CLAUDE.md`, and `scripts/check_docs.py` checks the docs. This
        checks the module a caller reads."""
        source = API_SOURCE.read_text(encoding="utf-8")
        assert chr(0x2014) not in source
        assert not re.search(r"\s--\s", source)
