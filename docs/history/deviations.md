# Deviations in Phases 1 and 2

Moved out of `HANDOFF.md` unchanged, when that file was restructured as a
running snapshot plus the latest record. **This is the record as it was written
when each task closed, not a description of the repo today**: present tense in
it means the day of the task. `HANDOFF.md` carries the current state, and
`docs/history/README.md` says where each decision from here now lives.

Where the work departed from the task list, and why.

---

## Deviations

### Phase 1

- **`.gitkeep` files.** Git cannot track empty directories, so `app/`,
  `scripts/`, `tests/`, and `docs/` each got a `.gitkeep`. `data/raw/`
  deliberately did not, since it is ignored and a placeholder there would be
  ignored too. A fresh clone has no `data/raw/`; `fetch_statsbomb.py` creates it.
- **`competitions.json` was also downloaded.** Not in the task list, but
  resolving the 2022 season id without it would have meant hardcoding the id.
- **`.gitignore` carried a pre-existing uncommitted line.** `voice_test/` was
  already modified in the working tree before Phase 1 and rode along in
  `d11f686`, with its missing trailing newline fixed.
- **The CRLF normalization warning on `docs/data_check.md`** is resolved in
  `c52358c` and no longer occurs.

### Phase 2

- **The em dash removal covered already-committed docs.** The constraint arrived
  in Phase 2 and says "any doc", so the 20 existing em dashes in `CLAUDE.md`,
  `README.md` and `HANDOFF.md` were treated as violations and fixed, along with
  the prose `--` in the scripts and the generated report. This went beyond the
  four listed housekeeping items.
- **`scripts/scan_copy.py` was not requested.** The exit condition was a scan
  result, and a one-off grep is not evidence anyone else can reproduce, so the
  scan is a committed script that exits non-zero on a hit.
- **The screens were rendered during review, in Edge rather than Chrome.**
  Chrome is not installed on this machine; Edge is the same Blink engine, driven
  headless with `--screenshot`. Both credit rows were confirmed by eye: the
  reversed logo reads correctly as orange and white on the dark surface, beside
  "Powered by StatsBomb play-by-play data" on the picker and "Data: StatsBomb"
  on Moments. That render is what surfaced the credit truncation.
- **The moment-card timer was cleared in review** (`c7934d6`). The display and
  the 60-second cap in the script are both gone, and `#timerReadout` stays in
  place and empty for Phase 5. The moment card's play button was renamed from
  the generic `Play Narration` to `Play buildup narration` in `df6ca25`, so all
  four play buttons now say what they play.
- **A reported 390 px overflow was a measurement artifact, not a defect**
  (no code change). The first review screenshots used Edge headless with
  `--window-size=390`, which does not drive the layout viewport in this build:
  the page laid out at 492 CSS px and the screenshot captured a 390 px crop of
  it, so unclipped elements appeared clipped. Re-measured inside a 390 px
  iframe, every screen reports
  `clientWidth=390 scrollWidth=390 overflow=0px count=0`, and screenshots at a
  true 390 px viewport show the header pill, both primary buttons and the
  `PROFILE` nav label all intact on all four screens. The screens were never
  broken; the earlier handoff entry claiming they were has been removed.
- **`truncate` was dropped from the picker credit** (`c7934d6`). Rendering
  showed the logo squeezing the attribution to "play-by-play da...", which is
  not an intact credit. The text now wraps to two lines and reads in full. This
  changed an existing class rather than only copy.
- **Three claims in `DESIGN.md` were wrong on the first pass** and were
  corrected before commit by verification rather than shipped: the Material
  Symbol count, an omission in the unused spacing list, and a claim that
  `focus:outline-none` was the only focus utility. That last error also
  surfaced two components that had been missed entirely, the text input and the
  toggle switch, both now documented.
- **The four screens arrived mid-session as untracked files** that this session
  did not author. They were left untracked until the task that called for them.
