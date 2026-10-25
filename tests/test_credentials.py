"""Tests for the credentials loader.

**No test here touches the real credentials file.** Every one writes a fake into
pytest's temporary directory and passes that path in, and the autouse fixture in
`tests/conftest.py` points `PRELUDE_ENV_FILE` at a path that does not exist, so
even a test that forgot would read nothing real.

The fake values are obvious fakes. A test fixture that looked like a key is a
test fixture somebody will one day mistake for one.
"""

from pathlib import Path

import pytest

from app.credentials import (
    DEFAULT_ENV_FILE,
    ENV_FILE_VARIABLE,
    REPO_ROOT,
    CredentialsInsideRepo,
    describe,
    env_file,
    load,
    parse,
)

FAKE = """
# Prelude credentials, fake ones.
WATSONX_API_KEY=not-a-real-key
WATSONX_PROJECT_ID=00000000-0000-0000-0000-000000000000
WATSONX_URL=https://us-south.ml.cloud.ibm.com

TTS_URL=https://api.us-south.text-to-speech.watson.cloud.ibm.com/instances/fake
TTS_VOICE=en-GB_GeorgeExpressive
"""


@pytest.fixture
def fake_env_file(tmp_path) -> Path:
    path = tmp_path / "credentials" / ".env"
    path.parent.mkdir(parents=True)
    path.write_text(FAKE, encoding="utf-8")
    return path


class TestWhereTheFileLives:
    def test_the_default_is_outside_the_repo(self):
        """The whole point. A recursive search over the working directory swept
        the old in-repo file up without ever naming it, and no rule about one
        filename can help with that."""
        assert not DEFAULT_ENV_FILE.is_relative_to(REPO_ROOT)

    def test_the_default_is_the_prelude_directory_in_the_home_directory(self):
        assert DEFAULT_ENV_FILE.parent.name == ".prelude"
        assert DEFAULT_ENV_FILE.name == ".env"
        assert DEFAULT_ENV_FILE.parent.parent == Path.home()

    def test_the_environment_variable_overrides_it(self, tmp_path, monkeypatch):
        elsewhere = tmp_path / "somewhere" / "else.env"
        monkeypatch.setenv(ENV_FILE_VARIABLE, str(elsewhere))
        assert env_file() == elsewhere

    def test_the_default_applies_when_the_variable_is_unset(self, monkeypatch):
        monkeypatch.delenv(ENV_FILE_VARIABLE, raising=False)
        assert env_file() == DEFAULT_ENV_FILE

    def test_a_tilde_in_the_override_is_expanded(self, monkeypatch):
        monkeypatch.setenv(ENV_FILE_VARIABLE, "~/elsewhere/.env")
        assert env_file() == Path.home() / "elsewhere" / ".env"


class TestRefusingAPathInsideTheRepo:
    """Pointing the override back into the repo would undo the only thing this
    module exists for, so it is refused rather than read."""

    def test_the_repo_root_is_refused(self):
        with pytest.raises(CredentialsInsideRepo) as raised:
            load(path=REPO_ROOT / ".env")
        assert str(REPO_ROOT) in str(raised.value)

    def test_a_subdirectory_of_the_repo_is_refused(self):
        with pytest.raises(CredentialsInsideRepo):
            load(path=REPO_ROOT / "app" / ".env")

    def test_the_refusal_says_where_to_put_it_instead(self):
        with pytest.raises(CredentialsInsideRepo) as raised:
            load(path=REPO_ROOT / ".env")
        message = str(raised.value)
        assert str(DEFAULT_ENV_FILE) in message
        assert ENV_FILE_VARIABLE in message

    def test_describe_refuses_it_too(self):
        """The diagnostic path must not be a way around the rule."""
        with pytest.raises(CredentialsInsideRepo):
            describe(path=REPO_ROOT / ".env")

    def test_a_path_outside_the_repo_is_allowed(self, fake_env_file):
        assert load(path=fake_env_file, environ={})["WATSONX_URL"]


class TestParse:
    def test_it_reads_key_and_value(self):
        assert parse("A=1\nB=two") == {"A": "1", "B": "two"}

    def test_it_skips_blank_lines_and_comments(self):
        assert parse("\n# a comment\nA=1\n\n  # another\n") == {"A": "1"}

    def test_it_skips_a_line_with_no_equals(self):
        """Guessing at a malformed line is worse than ignoring it."""
        assert parse("A=1\nnonsense\nB=2") == {"A": "1", "B": "2"}

    def test_it_tolerates_a_leading_export(self):
        assert parse("export A=1") == {"A": "1"}

    def test_it_strips_surrounding_quotes(self):
        assert parse("A='1'\nB=\"two\"") == {"A": "1", "B": "two"}

    def test_it_keeps_an_equals_sign_inside_a_value(self):
        """A key or a URL with a query string can contain one."""
        assert parse("A=a=b=c") == {"A": "a=b=c"}

    def test_it_keeps_an_empty_value(self):
        """.env.example is all empty values, and an empty one is not the same
        as an absent one."""
        assert parse("A=") == {"A": ""}

    def test_a_later_line_wins(self):
        assert parse("A=1\nA=2") == {"A": "2"}


class TestLoad:
    def test_it_reads_the_file(self, fake_env_file):
        values = load(path=fake_env_file, environ={})
        assert values["WATSONX_API_KEY"] == "not-a-real-key"
        assert values["TTS_VOICE"] == "en-GB_GeorgeExpressive"

    def test_the_process_environment_wins(self, fake_env_file):
        """A variable exported in a shell is a deliberate override for one run,
        and a file on disk quietly beating it would be surprising."""
        values = load(
            path=fake_env_file, environ={"WATSONX_API_KEY": "from-the-shell"}
        )
        assert values["WATSONX_API_KEY"] == "from-the-shell"
        assert values["WATSONX_URL"].startswith("https://")

    def test_a_missing_file_is_not_an_error(self, tmp_path):
        """The caller knows which variables it needs and reports the ones it
        did not get by name, so an absent file is its business, not this
        module's."""
        values = load(path=tmp_path / "absent.env", environ={"A": "1"})
        assert values == {"A": "1"}

    def test_it_returns_the_environment_when_there_is_no_file(self, tmp_path):
        assert load(path=tmp_path / "absent.env", environ={}) == {}


class TestDescribe:
    def test_it_reports_names_and_no_values(self, fake_env_file):
        """This is what a missing-credential report prints, so a value
        appearing here would put a key in a terminal or a transcript."""
        source = describe(path=fake_env_file)
        assert source.exists
        assert "WATSONX_API_KEY" in source.names
        assert "not-a-real-key" not in source.summary
        for value in ("not-a-real-key", "en-GB_GeorgeExpressive"):
            assert value not in source.summary

    def test_it_lists_the_names_in_order(self, fake_env_file):
        assert list(describe(path=fake_env_file).names) == sorted(
            describe(path=fake_env_file).names
        )

    def test_it_says_when_the_file_is_absent(self, tmp_path):
        source = describe(path=tmp_path / "absent.env")
        assert not source.exists
        assert source.names == ()
        assert "no credentials file at" in source.summary

    def test_it_says_when_the_file_defines_nothing(self, tmp_path):
        empty = tmp_path / "empty.env"
        empty.write_text("# only a comment\n", encoding="utf-8")
        source = describe(path=empty)
        assert source.exists
        assert source.names == ()
        assert "defines no variables" in source.summary


class TestTheProviderUsesIt:
    def test_watsonx_reports_the_file_it_looked_in(self, tmp_path, monkeypatch):
        """A missing credential raises the question "which file did it read?",
        so the report answers it, by path and variable name only."""
        from app.narration_provider import MissingCredentials, WatsonxProvider

        absent = tmp_path / "absent.env"
        monkeypatch.setenv(ENV_FILE_VARIABLE, str(absent))
        with pytest.raises(MissingCredentials) as raised:
            WatsonxProvider()
        message = str(raised.value)
        assert "WATSONX_API_KEY" in message
        assert str(absent) in message

    def test_watsonx_builds_from_a_file_outside_the_repo(
        self, fake_env_file, monkeypatch
    ):
        from app.narration_provider import WatsonxProvider

        monkeypatch.setenv(ENV_FILE_VARIABLE, str(fake_env_file))
        provider = WatsonxProvider()
        assert provider.host == "https://us-south.ml.cloud.ibm.com"

    def test_watsonx_never_puts_a_credential_in_its_repr(
        self, fake_env_file, monkeypatch
    ):
        """A provider that printed itself into a log would undo all of this."""
        from app.narration_provider import WatsonxProvider

        monkeypatch.setenv(ENV_FILE_VARIABLE, str(fake_env_file))
        provider = WatsonxProvider()
        assert "not-a-real-key" not in repr(provider)
        assert "not-a-real-key" not in str(provider)
