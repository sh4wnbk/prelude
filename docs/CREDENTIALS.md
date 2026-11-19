# Credentials

No credential is in this repo. `.env.example` lists the variable names and
holds no values. The live file lives outside the working directory, at
`~/.prelude/.env` by default or wherever `PRELUDE_ENV_FILE` points, so that no
search over the repo can reach it whatever the tool or the command. That is not
a precaution in the abstract: a recursive search over the working directory
once swept the old repo-root file into a transcript without ever naming it, and
a rule about one filename cannot stop a command that searches everything.

`app/credentials.py` is what reads it. A path inside the repo is refused rather
than read. The `.env` entry in `.gitignore` and the `Read(./.env)` deny rule in
`.claude/settings.json` stay as a second layer, in case a file is ever created
at the repo root by habit; neither is the live location.
