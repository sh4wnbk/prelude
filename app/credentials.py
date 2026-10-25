"""Where the credentials live, which is deliberately outside this repo.

The credentials file used to sit at the repo root, and that is what made the
leak possible: a recursive search over the working directory swept it up
without ever naming it. A rule against opening one file cannot help there,
because nothing in the command said which file it would read. Moving the file
out of the repo closes the path itself, for every tool and every command, and
no search over the repo can reach it.

So the live file is **outside the working directory**:

| Where | Which file |
| ----- | ---------- |
| Default | `~/.prelude/.env`, which on Shawn's machine is `C:\\Users\\shawn\\.prelude\\.env` |
| Override | whatever `PRELUDE_ENV_FILE` points at |

`.env.example` stays in the repo. It lists the variable names and holds no
values, which is what makes it safe to read and safe to commit.

**A path inside the repo is refused.** Pointing `PRELUDE_ENV_FILE` back into
the working directory would undo the only thing this module is for, so
`load` raises instead of reading it.

**Nothing here prints a value.** `describe` exists so a missing credential can
be diagnosed by variable name without any value reaching a terminal, a log or a
transcript. `load` returns a mapping, and a caller that prints it has defeated
that; nothing in this repo does.

The process environment wins over the file. A variable exported in a shell is a
deliberate override for one run, and it would be surprising for a file on disk
to quietly beat it.

Standard library only, like the rest of `app/`.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

#: The repo, so a credentials file inside it can be refused.
REPO_ROOT = Path(__file__).resolve().parent.parent

#: Outside the repo, in the user's home directory.
DEFAULT_DIRECTORY = Path.home() / ".prelude"
DEFAULT_ENV_FILE = DEFAULT_DIRECTORY / ".env"

#: Set this to read the credentials from somewhere else.
ENV_FILE_VARIABLE = "PRELUDE_ENV_FILE"


class CredentialsInsideRepo(RuntimeError):
    """The credentials file was pointed at a path inside the repo.

    Refused rather than read. The file lives outside the working directory so
    that no search over the repo can reach it, and a path inside the repo gives
    that up.
    """


@dataclass(frozen=True)
class Source:
    """What was found, named but never valued.

    `names` holds the variable names the file defines and none of their values,
    so this is safe to print when a credential seems to be missing.
    """

    path: Path
    exists: bool
    names: tuple[str, ...]

    @property
    def summary(self) -> str:
        if not self.exists:
            return f"no credentials file at {self.path}"
        if not self.names:
            return f"{self.path} exists but defines no variables"
        return f"{self.path} defines {', '.join(self.names)}"


def env_file(environ: Mapping[str, str] | None = None) -> Path:
    """The credentials file to read: `PRELUDE_ENV_FILE`, or the default."""
    environ = os.environ if environ is None else environ
    override = environ.get(ENV_FILE_VARIABLE)
    return Path(override).expanduser() if override else DEFAULT_ENV_FILE


def _check_outside_repo(path: Path) -> Path:
    resolved = path.expanduser()
    try:
        absolute = resolved.resolve()
    except OSError:  # a path that cannot be resolved cannot be read either
        return resolved
    if absolute == REPO_ROOT or absolute.is_relative_to(REPO_ROOT):
        raise CredentialsInsideRepo(
            f"the credentials file would be {absolute}, which is inside the "
            f"repo at {REPO_ROOT}. It has to live outside the working "
            "directory, so that no search over the repo can reach it. Move it "
            f"to {DEFAULT_ENV_FILE} or point {ENV_FILE_VARIABLE} somewhere "
            "outside the repo."
        )
    return resolved


def parse(text: str) -> dict[str, str]:
    """Read `KEY=VALUE` lines.

    Blank lines and `#` comments are skipped, a leading `export` is tolerated,
    and surrounding single or double quotes come off the value. A line with no
    `=` is skipped rather than guessed at.
    """
    values: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        if name.startswith("export "):
            name = name[len("export ") :].strip()
        if not name:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[name] = value
    return values


def describe(
    path: Path | None = None, environ: Mapping[str, str] | None = None
) -> Source:
    """What the credentials file defines, by name only.

    Safe to print. This is what a missing-credential report should use, since
    `CLAUDE.md` forbids putting a value anywhere it could be read.
    """
    target = _check_outside_repo(env_file(environ) if path is None else path)
    if not target.is_file():
        return Source(path=target, exists=False, names=())
    names = tuple(sorted(parse(target.read_text(encoding="utf-8"))))
    return Source(path=target, exists=True, names=names)


def load(
    path: Path | None = None, environ: Mapping[str, str] | None = None
) -> dict[str, str]:
    """The credentials: the file, with the process environment over the top.

    A missing file is not an error here. The caller is what knows which
    variables it needs, and it reports the ones it did not get by name.
    """
    environ = os.environ if environ is None else environ
    target = _check_outside_repo(env_file(environ) if path is None else path)

    values: dict[str, str] = {}
    if target.is_file():
        values.update(parse(target.read_text(encoding="utf-8")))
    values.update(environ)
    return values
