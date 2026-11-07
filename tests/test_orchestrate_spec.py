r"""The OpenAPI file watsonx Orchestrate imports, held to the API it describes.

`orchestrate/prelude_tools.yaml` is the tool contract: Orchestrate reads it,
creates one tool per operation, and the agent calls
`https://prelude-api.onrender.com` from then on. It is written by hand because
FastAPI cannot produce it. `app.openapi()` serves OpenAPI 3.1.0 and IBM's
authoring guide requires 3.0, so the file is a second description of the same
service, and a second description of anything drifts.

**So almost nothing here is spelled twice.** The parameters, the required
flags, the types, the listener enum and the response types are read out of
`app.api`'s own `app.openapi()` inside the tests and compared with the file. A
parameter renamed in `app/api.py` fails this file rather than failing in
Orchestrate, where the symptom is an agent calling with an argument the
service drops.

The three things this file does assert on its own, because the code does not
hold them:

- **The version is 3.0**, which IBM requires and FastAPI does not serve. This
  is the one place the file must not match the code.
- **The narrator enum is the persona ids that have recordings**, read from
  `hero.audio` in `app/web/matches.json`. `narrator` is an open string in
  `app/api.py`, because an id with no recording is a documented fallback
  rather than an error. An agent choosing among three names needs the two that
  change what a fan hears, so the file narrows what the code accepts. The
  narrowing is checked against the recordings, not typed in here.
- **Every operation and parameter carries a description, and every parameter
  an example.** The agent reads the operation description to decide whether to
  call the tool at all. FastAPI writes operation descriptions from the
  docstrings and writes no parameter descriptions at all.

The status codes the file may declare are not assumed either: each one is
demonstrated against the application in process before the file is allowed to
name it.

The suite has no network (`tests/conftest.py`), so the live URL in the file is
compared as a string and never called. `docs/bob_brief.md` records the run
against the deployed service.
"""

import json
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app.api import app

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"

SPEC_FILE = ROOT / "orchestrate" / "prelude_tools.yaml"

MATCHES = json.loads((WEB / "matches.json").read_text(encoding="utf-8"))
NARRATORS = json.loads((WEB / "narrators.json").read_text(encoding="utf-8"))

#: The base URL of the deployed service, which is the one thing in the file
#: that is neither in the code nor derivable from it: Render names the service
#: and `app/api.py` never learns its own address.
LIVE_BASE_URL = "https://prelude-api.onrender.com"

#: The two operations an agent gets. `/health` is deliberately not one: it is
#: for the keepalive in `.github/workflows/keepalive.yml` and for a judge
#: waking the service by hand, and a tool an agent can choose wrongly costs a
#: turn. `app/api.py` still serves it.
TOOL_PATHS = ("/moments", "/buildup")

#: What `app.openapi()` says, read once. This is the contract the file is held
#: to, in every respect but the three the module docstring lists.
LIVE = app.openapi()


def recorded_narrators() -> list[str]:
    """The persona ids that have a recording, from `hero.audio`.

    A slot key is the persona id and the situation joined by an underscore,
    which is how `scripts/write_headers.py` builds it, so the id is the part
    before the first underscore. Two of the three narrators are in here; the
    Caller has no recording in either hero.
    """
    return sorted(
        {
            key.split("_")[0]
            for entry in MATCHES["matches"]
            for key in entry["hero"]["audio"]
        }
    )


def spec() -> dict:
    """The parsed file, or a failure that says the file is not written yet."""
    if not SPEC_FILE.is_file():
        pytest.fail(
            f"{SPEC_FILE.relative_to(ROOT).as_posix()} does not exist. It is "
            "the OpenAPI file Orchestrate imports; see docs/bob_brief.md."
        )
    with SPEC_FILE.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def operation(path: str) -> dict:
    """The file's GET operation for `path`."""
    paths = spec().get("paths") or {}
    assert path in paths, f"the file declares no {path}"
    assert "get" in paths[path], f"{path} has no GET"
    return paths[path]["get"]


def live_operation(path: str) -> dict:
    return LIVE["paths"][path]["get"]


def parameters(operation_body: dict) -> dict:
    return {
        parameter["name"]: parameter
        for parameter in operation_body.get("parameters") or []
    }


def schema_types(schema: dict) -> set:
    """The types a schema allows, flattening the `anyOf` FastAPI writes.

    An optional parameter arrives from `app.openapi()` as a string or a null,
    because `narrator` is `str | None`. A query parameter that is simply left
    out is the same thing to a caller, so the file writes `type: string` and
    this is what makes the two comparable.
    """
    if "anyOf" in schema:
        return {member.get("type") for member in schema["anyOf"]}
    return {schema.get("type")}


def every_key(value, into: list) -> list:
    """Every key in a nested structure, for the checks that read the whole
    file rather than one place in it."""
    if isinstance(value, dict):
        for key, member in value.items():
            into.append(key)
            every_key(member, into)
    elif isinstance(value, list):
        for member in value:
            every_key(member, into)
    return into


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


class TestTheFile:
    def test_the_file_is_in_the_repo(self):
        assert SPEC_FILE.is_file(), (
            f"{SPEC_FILE.relative_to(ROOT).as_posix()} is the file Orchestrate "
            "imports and it is not written yet"
        )

    def test_it_parses_as_yaml(self):
        assert isinstance(spec(), dict), "the file does not parse to a mapping"

    def test_the_openapi_version_is_3_0(self):
        """IBM's authoring guide: the OpenAPI version must be 3.0."""
        declared = spec().get("openapi")
        assert isinstance(declared, str), "no openapi version in the file"
        assert declared.startswith("3.0."), declared

    def test_it_is_not_the_version_fastapi_serves(self):
        """The one place the file may not match the code.

        `app.openapi()` is 3.1.0. Importing that into Orchestrate is the
        failure this test exists to stop, and it is the reason the file is
        written by hand rather than exported.
        """
        assert spec()["openapi"] != LIVE["openapi"]
        assert LIVE["openapi"].startswith("3.1."), (
            "FastAPI no longer serves 3.1, so re-read IBM's requirement "
            "before changing this file"
        )

    def test_it_names_the_service_and_a_version(self):
        info = spec().get("info") or {}
        assert info.get("title"), "no info.title"
        assert info.get("version"), "no info.version"


class TestTheServer:
    def test_there_is_exactly_one_server(self):
        """IBM: the specification must include a servers block with exactly
        one URL.
        """
        servers = spec().get("servers")
        assert isinstance(servers, list), "no servers block"
        assert len(servers) == 1, servers

    def test_the_server_is_the_deployed_api(self):
        assert spec()["servers"][0]["url"] == LIVE_BASE_URL

    def test_the_url_carries_no_parameterization(self):
        """IBM: that URL cannot contain parameterization."""
        server = spec()["servers"][0]
        assert "{" not in server["url"], server["url"]
        assert "variables" not in server, server

    def test_no_operation_overrides_the_server(self):
        """One URL for the whole file, so an operation that moved would be
        visible here rather than in Orchestrate.
        """
        for path in TOOL_PATHS:
            assert "servers" not in operation(path)
            assert "servers" not in spec()["paths"][path]


class TestTheTwoOperations:
    def test_the_file_holds_exactly_the_two(self):
        assert sorted(spec()["paths"]) == sorted(TOOL_PATHS)

    def test_health_is_not_a_tool(self):
        """It is the keepalive's endpoint and a judge's wake-up call, and an
        agent has nothing to do with it. `app/api.py` still serves it, which
        `tests/test_api.py::TestHealth` holds.
        """
        assert "/health" not in spec()["paths"]
        assert "/health" in LIVE["paths"]

    @pytest.mark.parametrize("path", TOOL_PATHS)
    def test_the_only_method_is_get(self, path):
        """The service answers GET and nothing else, which
        `tests/test_api.py` holds against a POST.
        """
        assert list(spec()["paths"][path]) == ["get"]

    @pytest.mark.parametrize("path", TOOL_PATHS)
    def test_the_operation_has_an_operation_id(self, path):
        """IBM: each path that exposes an endpoint must include an
        operationId, and that value becomes the tool name.
        """
        assert operation(path).get("operationId")

    @pytest.mark.parametrize("path", TOOL_PATHS)
    def test_the_operation_id_is_snake_case(self, path):
        """IBM recommends snake_case for operationId values. It is the tool
        name an agent sees, so it is also the name Shawn reads in
        Orchestrate's tool list.
        """
        operation_id = operation(path)["operationId"]
        assert operation_id == operation_id.lower()
        assert operation_id.replace("_", "").isalnum(), operation_id
        assert "-" not in operation_id

    def test_the_two_operation_ids_differ(self):
        ids = [operation(path)["operationId"] for path in TOOL_PATHS]
        assert len(set(ids)) == 2, ids

    @pytest.mark.parametrize("path", TOOL_PATHS)
    def test_the_operation_has_a_description(self, path):
        """IBM: each path that exposes an endpoint must include a
        description, and the agent uses it to decide when to use the tool and
        what the tool does.
        """
        description = operation(path).get("description")
        assert isinstance(description, str)
        assert len(description.strip()) >= 40, description

    def test_the_descriptions_tell_the_two_tools_apart(self):
        """An agent picks by the description, so the two have to answer
        different questions in it. One lists the goals of a match; the other
        hands back one narration for one listener.
        """
        moments = operation("/moments")["description"].lower()
        buildup = operation("/buildup")["description"].lower()
        assert moments != buildup
        assert "goal" in moments
        assert "narration" in buildup


class TestTheParameters:
    @pytest.mark.parametrize("path", TOOL_PATHS)
    def test_the_names_are_the_ones_the_api_takes(self, path):
        assert sorted(parameters(operation(path))) == sorted(
            parameters(live_operation(path))
        )

    @pytest.mark.parametrize("path", TOOL_PATHS)
    def test_every_parameter_is_a_query_parameter(self, path):
        for name, parameter in parameters(operation(path)).items():
            assert parameter.get("in") == "query", name

    @pytest.mark.parametrize("path", TOOL_PATHS)
    def test_the_required_flags_are_the_ones_the_api_enforces(self, path):
        """A parameter the service validates as required and the file calls
        optional is a 422 an agent cannot explain.
        """
        mine = {
            name: bool(parameter.get("required"))
            for name, parameter in parameters(operation(path)).items()
        }
        theirs = {
            name: bool(parameter.get("required"))
            for name, parameter in parameters(live_operation(path)).items()
        }
        assert mine == theirs

    @pytest.mark.parametrize("path", TOOL_PATHS)
    def test_the_types_are_the_ones_the_api_takes(self, path):
        """Null is dropped on the code's side of the comparison, for the
        reason `schema_types` records.
        """
        for name, parameter in parameters(operation(path)).items():
            live = schema_types(parameters(live_operation(path))[name]["schema"])
            assert schema_types(parameter["schema"]) == live - {"null"}, name

    @pytest.mark.parametrize("path", TOOL_PATHS)
    def test_every_parameter_has_a_description(self, path):
        """`app.openapi()` writes none, and an agent filling an argument has
        nothing else to read. `match` in particular is a StatsBomb match id
        and not a number a fan would know.
        """
        for name, parameter in parameters(operation(path)).items():
            assert (parameter.get("description") or "").strip(), name


class TestTheEnums:
    def test_the_listener_enum_is_the_api_s_own(self):
        """The three answers to "Who are you with", from the `Literal` in
        `app/api.py`. Read out of `app.openapi()` rather than typed here, so a
        fourth answer or a renamed one fails this test.
        """
        mine = parameters(operation("/buildup"))["listener"]["schema"]["enum"]
        theirs = parameters(live_operation("/buildup"))["listener"]["schema"]["enum"]
        assert mine == theirs

    def test_the_listener_enum_is_the_three_answers(self):
        assert parameters(operation("/buildup"))["listener"]["schema"]["enum"] == [
            "team_a",
            "team_b",
            "neutral",
        ]

    def test_the_narrator_enum_is_the_narrators_with_recordings(self):
        """Two of the three. The file narrows what the service accepts, for
        the reason the module docstring gives, and the narrowing is read off
        `hero.audio` rather than listed here.
        """
        enum = parameters(operation("/buildup"))["narrator"]["schema"]["enum"]
        assert sorted(enum) == recorded_narrators()

    def test_every_value_in_the_narrator_enum_is_a_narrator(self):
        enum = parameters(operation("/buildup"))["narrator"]["schema"]["enum"]
        ids = {narrator["id"] for narrator in NARRATORS["narrators"]}
        assert set(enum) <= ids, enum

    def test_the_caller_is_not_offered(self):
        """There is no Caller recording in either hero, so an agent that
        offered the Caller would be offering a fan the Storyteller under
        another name. Profile says the same thing by disabling the card.
        """
        enum = parameters(operation("/buildup"))["narrator"]["schema"]["enum"]
        assert "caller" not in enum

    def test_the_narrowing_does_not_contradict_the_api(self):
        """The service takes any string and falls back, which
        `tests/test_api.py::TestBuildup::test_an_unknown_narrator_id_falls_back`
        holds. So every value the file offers has to be a string the service
        would accept, and the parameter has to stay optional.
        """
        parameter = parameters(operation("/buildup"))["narrator"]
        live = parameters(live_operation("/buildup"))["narrator"]
        assert not parameter.get("required")
        assert not live.get("required")
        assert all(isinstance(value, str) for value in parameter["schema"]["enum"])

    def test_no_other_parameter_carries_an_enum(self):
        """`match` is a match id and the service answers 404 for one it does
        not serve, which is a better answer than an agent being unable to ask
        the question.
        """
        for path in TOOL_PATHS:
            for name, parameter in parameters(operation(path)).items():
                if name in ("listener", "narrator"):
                    continue
                assert "enum" not in parameter["schema"], name


class TestTheResponses:
    @pytest.mark.parametrize("path", TOOL_PATHS)
    def test_it_declares_a_200(self, path):
        assert "200" in {str(code) for code in operation(path)["responses"]}

    @pytest.mark.parametrize("path", TOOL_PATHS)
    def test_the_200_is_json_and_nothing_else(self, path):
        """IBM: endpoints must accept and return JSON."""
        content = operation(path)["responses"]["200"]["content"]
        assert list(content) == ["application/json"]

    @pytest.mark.parametrize("path", TOOL_PATHS)
    def test_the_200_type_is_the_api_s_own(self, path):
        """`app/api.py` returns a `dict` from both, so `app.openapi()` says an
        object with free-form properties. The file may describe the object's
        fields, which is what the next test is for, and it may not call it
        something other than an object.
        """
        mine = operation(path)["responses"]["200"]["content"]["application/json"][
            "schema"
        ]
        theirs = live_operation(path)["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
        assert mine.get("type") == theirs.get("type") == "object"

    @pytest.mark.parametrize("path", TOOL_PATHS)
    def test_the_fields_it_describes_are_fields_the_api_returns(self, path, client):
        """The free-form object in `app.openapi()` tells an agent nothing, so
        the file is allowed to name the fields. What it may not do is name a
        field the service does not return: that is a value an agent would read
        as missing. Checked against the live body, in process.
        """
        schema = operation(path)["responses"]["200"]["content"]["application/json"][
            "schema"
        ]
        described = set(schema.get("properties") or {})
        if not described:
            pytest.skip("the file describes no fields, which is allowed")
        params = {"match": MATCHES["matches"][0]["match_id"]}
        if path == "/buildup":
            params["listener"] = "team_a"
        body = client.get(path, params=params).json()
        assert described <= set(body), sorted(described - set(body))

    @pytest.mark.parametrize("path", TOOL_PATHS)
    def test_every_status_code_is_one_the_service_answers(self, path, client):
        """Demonstrated rather than assumed: 200 for a call that works, 404
        for a match the service does not serve, 422 for a query FastAPI
        refuses. A code outside that set is a promise nothing keeps.
        """
        good = {"match": MATCHES["matches"][0]["match_id"]}
        if path == "/buildup":
            good["listener"] = "team_a"
        answered = {
            client.get(path, params=good).status_code,
            client.get(path, params={**good, "match": 1}).status_code,
            client.get(path, params={}).status_code,
        }
        declared = {int(code) for code in operation(path)["responses"]}
        assert declared <= answered, sorted(declared - answered)

    @pytest.mark.parametrize("path", TOOL_PATHS)
    def test_every_response_it_declares_has_a_description(self, path):
        """OpenAPI requires one on every response object, and Orchestrate
        reads the file as OpenAPI.
        """
        for code, response in operation(path)["responses"].items():
            assert (response.get("description") or "").strip(), code


class TestTheExamples:
    """The file carries one call per operation that a judge can repeat."""

    @pytest.mark.parametrize("path", TOOL_PATHS)
    def test_every_parameter_carries_an_example(self, path):
        for name, parameter in parameters(operation(path)).items():
            assert "example" in parameter, name

    @pytest.mark.parametrize("path", TOOL_PATHS)
    def test_the_examples_are_a_call_the_service_answers(self, path, client):
        """In process here. `docs/bob_brief.md` records the same two calls
        against the deployed service, which is the part a test cannot do.
        """
        params = {
            name: parameter["example"]
            for name, parameter in parameters(operation(path)).items()
        }
        response = client.get(path, params=params)
        assert response.status_code == 200, response.text

    def test_the_example_listener_and_narrator_are_in_their_enums(self):
        for name in ("listener", "narrator"):
            parameter = parameters(operation("/buildup"))[name]
            assert parameter["example"] in parameter["schema"]["enum"], name

    def test_the_example_match_is_a_match_the_service_serves(self):
        """In the spelling the parameter takes, which is a string of digits.

        `match` stopped being an integer on 2026-11-07: Orchestrate serialises
        an integer tool argument as a float, so the example an agent copies
        has to be quoted here or the agent sends `3.869685e+06`. Comparing
        against the ids as strings holds both halves at once, the spelling and
        the id.
        """
        served = {str(entry["match_id"]) for entry in MATCHES["matches"]}
        for path in TOOL_PATHS:
            assert parameters(operation(path))["match"]["example"] in served


class TestItAsksForNoCredentials:
    def test_there_is_no_security_requirement(self):
        """The service reads no environment variable and holds no key, which
        `tests/test_api.py::TestWhatItDoesNotReach` holds. A security block
        would make Orchestrate ask for a connection that does not exist, and a
        tool with an unsatisfied connection does not run.
        """
        assert "security" not in spec()

    def test_no_operation_asks_for_security(self):
        for path in TOOL_PATHS:
            assert "security" not in operation(path)

    def test_there_are_no_security_schemes(self):
        assert "securitySchemes" not in (spec().get("components") or {})

    def test_no_parameter_is_a_credential(self):
        """A key passed as a query parameter would be a credential in a URL,
        and the service has nothing to do with one.
        """
        banned = ("key", "token", "secret", "password", "apikey", "authorization")
        for path in TOOL_PATHS:
            for name in parameters(operation(path)):
                assert not any(word in name.lower() for word in banned), name


class TestWhatTheFileMayNotCarry:
    def test_no_x_ibm_extensions(self):
        """IBM: OpenAPI tools do not support the `x-ibm-` extensions the older
        Skills used.
        """
        assert not [
            key for key in every_key(spec(), []) if str(key).startswith("x-ibm-")
        ]

    def test_no_callbacks(self):
        """A callback is how Orchestrate runs a tool past its forty second
        execution timeout. Both operations answer in well under a second on a
        warm service, so there is nothing to call back about, and the header a
        callback needs would be a parameter the service drops.
        """
        for path in TOOL_PATHS:
            assert "callbacks" not in operation(path)

    def test_no_request_body(self):
        """Both operations are GETs with query parameters."""
        for path in TOOL_PATHS:
            assert "requestBody" not in operation(path)

    def test_it_names_no_other_host(self):
        """The whole file points at one service. A second host in it would be
        a fourth input arriving by the back door, and the recordings on the
        Pages site are the one other address a body can carry.
        """
        spec()  # so an absent file fails here too, rather than passing empty
        text = SPEC_FILE.read_text(encoding="utf-8")
        hosts = {
            line.split("//", 1)[1].split("/", 1)[0].strip().strip("\"'")
            for line in text.splitlines()
            if "//" in line and "http" in line
        }
        assert hosts <= {
            LIVE_BASE_URL.split("//", 1)[1],
            "sh4wnbk.github.io",
        }, hosts
