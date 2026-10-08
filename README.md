# Prelude

Prelude narrates a football moment in audio, saying only what the play data can prove.

> **Status: skeleton.** This README is structure first — the sections below are
> headings awaiting the code that fills them, and the evidence column is
> deliberately empty. What actually runs today is listed under
> [Capability honesty](#capability-honesty), and nothing else here should be read
> as working.

## The problem

<!-- To be written. -->

## What makes it different

<!-- To be written. -->

## How it works

### The loop

<!-- One loop, written once the code exists. -->

### Pillars

<!-- The pillars the loop rests on, written once the code exists. -->

## Judging criteria → evidence

Each row pairs a judging criterion with something a reader can actually run and
watch succeed. Rows stay empty until the code that proves them exists; an
entry is earned by a command, not by a description.

| Judging criterion            | Runnable evidence |
| ---------------------------- | ----------------- |
| Completeness and feasibility |                   |
| Creativity and innovation    |                   |
| Design and usability         |                   |
| Effectiveness and efficiency |                   |

## Capability honesty

This section is the authoritative list of what Prelude can do at this commit.
Everything above it is structure.

**Runs today:**

- `scripts/fetch_statsbomb.py` — downloads the StatsBomb open-data files the
  project uses into `data/raw/` (gitignored, reproducible).
- `scripts/data_check.py` — reads the 1986 Argentina vs England event feed,
  lists every goal and the shot counts per team, and writes
  [`docs/data_check.md`](docs/data_check.md) from that output.

**Not built yet:** everything else, including narration, audio output, GPS
presence handling, and any user-facing interface. The EventFeed and
moment-detection module is owned by another contributor and is not implemented
here.

No claim in this README is intended to run ahead of the code. If you find one
that does, it is a bug in the README.

## Data and attribution

Play data comes from the [StatsBomb open data](https://github.com/hudl/open-data)
repository, used under its terms. Any research, analysis, or insight published
from this project states StatsBomb as the data source.

Data provided by StatsBomb.
