# Prelude

Prelude narrates a football moment in audio, saying only what the play data can prove.

**Live demo: https://sh4wnbk.github.io/prelude/**

What the demo is, precisely:

- **The screens and the navigation work.** You can move through the picker, the
  live seated screen, the moment card and the moments list, and the bottom tabs
  switch between them. Profile has no screen, so that tab is deliberately
  disabled rather than faked.
- **There is no audio.** Playback and the generated narration arrive in later
  phases. The play buttons change their own icon and nothing else; the waveforms
  are static markup, and the timers are empty on purpose, waiting for real
  values.
- **Nothing is live.** The demo replays StatsBomb historical data, the 1986
  Argentina vs England quarter-final, presented as if it were unfolding now.
  There is no live feed, no venue, and no GPS.

> **Status: skeleton.** This README is structure first. The sections below are
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

- `scripts/fetch_statsbomb.py`: downloads the StatsBomb open-data files the
  project uses into `data/raw/` (gitignored, reproducible).
- `scripts/data_check.py`: reads the 1986 Argentina vs England event feed,
  lists every goal and the shot counts per team, and writes
  [`docs/data_check.md`](docs/data_check.md) from that output.
- `scripts/scan_copy.py`: checks the four screens for banned copy and exits
  non-zero on any hit.
- `scripts/check_docs.py`: checks that these docs still match the code they
  describe, and exits non-zero when one has gone stale.
- `tests/test_event_feed.py`: 14 acceptance tests for the EventFeed contract.
  They run, and they all fail on purpose, because nothing implements the
  contract yet.

**Exists but does nothing yet:**

- `app/web/`: four screens that open in a browser as static mockups. Buttons
  toggle their own icons; nothing is wired to data, audio, or each other.
- `app/event_feed.py`: the data shapes and the `EventFeed` interface. A
  contract only, with no implementation behind it.

**Not built yet:** narration, audio output, GPS presence handling, and any
wiring behind the screens. The EventFeed and moment-detection module is
reserved for another contributor and is not implemented here; see
[`docs/bob_brief.md`](docs/bob_brief.md).

No claim in this README is intended to run ahead of the code. If you find one
that does, it is a bug in the README.

## Data and attribution

Play data comes from the [StatsBomb open data](https://github.com/hudl/open-data)
repository, used under its terms. Any research, analysis, or insight published
from this project states StatsBomb as the data source.

Data provided by StatsBomb.
