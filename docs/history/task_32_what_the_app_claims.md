# Task 32: what the app claims and what it shows

**This is a record, not a description of the repo today.** Present tense in it
means 2026-11-14, the day the task closed. `HANDOFF.md` is the only file that
describes the repo now, and `docs/history/README.md` says where each decision
below now lives.

**What Shawn asked for on 2026-11-14.** A read-only review of the app by IBM
Bob, run in Ask mode, found four lines claiming more than the code does, a
metric the app could show honestly and a stale `README.md` line. Those
findings were read against the repo first and then acted on, with the app
polish from 2026-11-13 beside them.

**The two missing session rows** (`fcf8566`). `bob_sessions/README.md` listed
fourteen sessions while sixteen exports are committed. Task 15's work and its
export landed in one commit, `39856bd`, so both commit columns hold that id.
The review has no work commit at all: Ask mode changed no file, so `927ad9e`,
which added the export, is the only commit it produced. Eleven rows now take
their Bobcoin figure from the Bobalytics export at submission rather than
nine.

**The four lines that claimed more than the code does** (`2f7f81a`).

| What it said | Why it was not true |
| ------------ | ------------------- |
| "AT VENUE, GPS" on Live and on the ticket | `CLAUDE.md` names GPS presence as an input and no code here reads a position |
| "LIVE AUDIO SYNC" on the moment card | it wrote SYNCED over its own label for 1.8 seconds and changed nothing; the six recordings are files |
| "Play data connected, AI narration ready" on the list, the ticket and in `matches.json` | nothing checks a connection and the narration is frozen rather than becoming ready |
| the confirm button's 1.5 second sequence | nothing was synchronizing and there is no venue feed |

The app still presents a match in progress, which is the decision above under
"The app is always live". What these four claimed was a sensor, a live feed
and a connection, and the clock and the LIVE tag say nothing about those.
`scripts/scan_copy.py` holds five patterns, one per line and two for the
button that said two things; `scripts/check_match_copy.py` asked for the badge
on Live and against it on the list, and now fails on any screen carrying it.

**The claim count, under the label it stands on** (`4117f1a`). "Verified from
play data" is a yes and says nothing about how much was checked. The card now
reads "<n> claims checked against the play data", where n is
`check.claims_checked` out of `app/web/narrations.json`: 17, 18 and 18 for
1986 and 22, 23 and 23 for 2022, written by the freeze and re-checked against
`data/raw/` by `tests/test_frozen_narrations.py`. `showNarration` reveals the
words, the label, the count and the play button in one step, and a slot with
no usable count shows none of them. The block was re-measured in Chromium at
390 px, where the six are 260, 286 and 312 px, so it reserves 19.5rem rather
than Task 29's 16.75rem.

**Tailwind compiled, and the fonts, the QR reader and the icon served from
here** (`cf93e85`, `36ec85a`). The screens loaded 407 KB of JavaScript from
`cdn.tailwindcss.com`, four stylesheets and fourteen font files from Google,
and jsQR from `cdn.jsdelivr.net`. `scripts/build_tailwind.py` compiles
`app/web/tailwind.css` (45 KB) from the config block the screens share, with
the version the Play CDN was bundling; `scripts/fetch_fonts.py` wrote
`fonts.css` and fourteen woff2 files, every subset, because a fan's typed name
goes into the header; `scripts/fetch_vendor.py` wrote
`assets/vendor/jsQR.js`, checked against the integrity hash the scanner
carried.

One screen looks different and it is the one that was wrong: five screens
loaded the CDN with `?plugins=forms,container-queries` and two did not, so the
app ran two stylesheets, and `docs/DESIGN.md` records that the match select
takes the forms plugin's chevron. The event list's select now matches the
scanner's, and its expanded manual entry panel is 1 px taller. Read in
Chromium over 24 views, 18 were byte-identical, 5 were inside the measured
noise floor and that one changed.

**One player, and the Moments hero card follows the voice** (`89364cd`). The
file held two players; it holds one, `wirePlayer`, and both screens hand it
their own markup, including the two class names a bar carries behind and ahead
of the playhead. When the button may be pressed is an argument: the moment
card passes `Prelude.whenNarrationShown` and a Moments card releases at once.
A card with no recording is handed nothing, so its bars keep their heights,
its clock stays empty and its track is not a slider.

**The mark** (`16d683b`). "P." in Syne Bold, off-white with the full stop in
amber, drawn by `scripts/make_mark.py` into `favicon.svg`, a 32 px favicon, a
180 px apple touch icon and the 192 and 512 px icons the manifest names. The
glyphs are outlines rather than text, because a favicon is rendered with no
font loading. `fonttools` joins the dev group for it and `uv.lock` is updated.

**The launch screen** (`2ed6da2`). The shell paints the wordmark "Prelude."
over "Be there. Even when you're not." while the list loads behind it.
Whether it paints at all is decided in the head before the body is parsed, so
a first load shows it in the first frame and a later load never paints it. It
goes when `data-matches-loaded` says matches.json was answered, which is a
signal the list now makes: `data-match-rendered` is the stronger claim and the
list never makes it, because Prelude renders no match until the fan has
picked. It never outlives two seconds, it does not fade under
`prefers-reduced-motion`, and it is one `role="img"` named Prelude.

**The API rebuilds only when something it serves changes** (`7db7c14`).
`render.yaml` carries a build filter on `app/**`, `pyproject.toml`, `uv.lock`
and itself; every push used to rebuild it, and a doc, a test, a workflow or a
script is a push it has no stake in. `app/**` is broad on purpose: it is the
service, the modules it imports, and `matches.json`, `narrations.json` and
`narrators.json` under `app/web/`, which `app/api.py` reads and answers from.
The cost is that a change to a screen, which is under `app/web/` too, rebuilds
a service it does not affect, and the first push after this did exactly that.

**The README lines this made false** (`1a88987`). The Profile line, which had
been wrong since Bob's Task 10 built the screen, the moments waveform line and
the paragraph about the hosted API.

**The browser suite stopped forgiving and started asserting.** It allowed
failures from three CDNs, which Task 30 recorded under "Found, not fixed"
because a run without them failed anyway. `Fan.offsite` collects every request
that leaves the suite's origin and there must be none, which is what found
jsQR. The `/favicon.ico` allowance went the same way: a page that declares an
icon stops asking. `tests/browser/` is six files and `docs/HARNESS.md` now has
a row for every file in `tests/`, which closes the last of Task 29's seven.

**The evidence.** `pytest -q` reports `2012 passed`, up from `1906`; `pytest
tests/browser` reports `86 passed`, up from `71`; all five gates exit 0;
`git status` is clean after both. Three things a reader should see rather than
read about are committed: `docs/evidence/task32_launch_screen.png` is the
shell with matches.json held for 1.5 seconds,
`docs/evidence/task32_moment_card_claims.png` is the 2022 card for a listener
with no side, with "23 claims checked against the play data" under the label,
and the mark at both sizes is
`app/web/assets/icon/favicon-32.png` and
`app/web/assets/icon/apple-touch-icon-180.png`, which the screens link. All
were taken in headless Chromium at 390 by 844 at two device pixels per CSS
pixel.

**Found, not fixed.**

- **The icon font is 1.14 MB of the 1.34 MB of committed fonts.** Material
  Symbols Outlined is shipped whole and the app uses 52 of its glyphs.
  Google's `icon_names=` parameter would subset it to a few KB, at the cost of
  a missing glyph the first time an icon is added without rerunning the
  script. The deployed site downloaded the same file from Google before, so
  this is not a regression.
- **The Live screen's "PLAY DATA CONNECTED" pill and the Moments cards'
  "AI AUDIO NARRATION, PLAY DATA SYNC" line** are near neighbours of the four
  lines that went. Shawn named four and these are not among them, so they
  stand.
- **`scripts/fetch_statsbomb.py` is not in the Blueprint's build filter.** The
  Render build runs it, so a change to it does not redeploy the service and
  the deployed data stays as it was built. The four paths are the ones Shawn
  named.
- **A screen-only push still rebuilds the API.** `app/web/` is inside
  `app/**`, and it has to be: three files in it are what `/moments` and
  `/buildup` answer from. Separating the screens from the data would mean
  `ignoredPaths` listing files, and a file added later and not listed would be
  a service that never picks it up.
- **The smoke subset does not open the launch screen.** It checks the moment
  card, the label, the claim count and the three endpoints against the live
  site; the first frame of a visit is checked against the working tree only.
- **The compiled stylesheet is not rebuilt by CI.** `app/web/tailwind.css` is
  committed and the step that fails on a dirty tree cannot catch a config
  block edited without rerunning the script, because the script is not run.
  Running it in CI would mean an npm install on every push.
- **CI does not run on a schedule, and the smoke workflow cannot be made to
  fail by a failing deploy.** Both are Task 30's and both still stand; they
  are in Current state under "Still open: what the build does not say".
