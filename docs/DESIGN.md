# DESIGN

The design system as the four screens in `app/web/` actually define it. Every
value below is read out of the markup, not from any design brief.

**How to trace a value.** Token tables cite `prelude_03_moment_card.html:1`,
which is the `<script id="tailwind-config">` block. That block is byte-identical
across all four screens (sha256 `3b9cf112d3cbc180...`, 3209 chars), so the
system is one system; it sits on line 1 of `prelude_03_moment_card.html` and
line 2 of the other three. Component sections cite the lines where the pattern
is actually used.

Anything a screen does not contain is absent here. There is no spec for states,
breakpoints, or components the screens do not have.

## Foundations

| Property | Value | Source |
| -------- | ----- | ------ |
| Mode | dark only, `darkMode: "class"`, `<html class="dark">` | `03:1` |
| Page background | `#101319`, set on `html,body` in `@layer base` | `03:1` |
| Viewport | `width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover` | all four, line 1 |
| Body min height | `max(884px, 100dvh)` | `01:4`, `03:3`, `04:4` |
| Font smoothing | `-webkit-font-smoothing: antialiased` | `03:1` |
| Overscroll | `overscroll-behavior: none` | `03:1` |
| Scrollbars | hidden, `::-webkit-scrollbar{display:none}` | `03:1` |
| Safe areas | `.pt-safe` / `.pb-safe` map to `env(safe-area-inset-top/bottom, 0px)` | `03:1` |

`prelude_02_live_seated.html` sets no body min height; the other three do.

## Color

47 color tokens are defined. 18 are referenced in markup; the remaining 29 are
declared and unused. Both lists are below, because a token that nothing uses is
not part of the working palette.

### In use

Counts are references across all four screens, in `bg-`, `text-`, `border-`,
`shadow-`, `ring-` and `fill-` utilities.

| Token | Hex | Refs |
| ----- | --- | ---: |
| `primary-container` | `#ffb703` | 134 |
| `primary` | `#ffdba0` | 52 |
| `on-surface` | `#e1e2ea` | 48 |
| `secondary` | `#bec7d2` | 42 |
| `on-surface-variant` | `#d5c4ac` | 28 |
| `surface-container-high` | `#272a30` | 28 |
| `secondary-container` | `#414a53` | 19 |
| `surface` | `#101319` | 16 |
| `surface-container` | `#1d2025` | 16 |
| `surface-container-low` | `#191c21` | 15 |
| `surface-container-highest` | `#32353b` | 14 |
| `outline-variant` | `#514532` | 13 |
| `on-primary` | `#422c00` | 12 |
| `surface-container-lowest` | `#0b0e13` | 12 |
| `outline` | `#9e8f78` | 6 |
| `on-primary-container` | `#6b4b00` | 4 |
| `surface-bright` | `#36393f` | 2 |
| `surface-variant` | `#32353b` | 2 |

All hex values: `03:1`.

**Surface ramp**, darkest to lightest, which is how elevation is expressed:
`surface-container-lowest #0b0e13`, `surface #101319`, `surface-container-low
#191c21`, `surface-container #1d2025`, `surface-container-high #272a30`,
`surface-container-highest #32353b`, `surface-bright #36393f`.

**Accent.** `primary-container #ffb703` is the amber action color and the single
most used token. `on-primary #422c00` is the text and icon color on top of it.
`primary #ffdba0` is the lighter amber used for text and emphasis.

`surface-variant` and `surface-container-highest` are both `#32353b`.

### Defined, not used

`background`, `error`, `error-container`, `inverse-on-surface`,
`inverse-primary`, `inverse-surface`, `on-background`, `on-error`,
`on-error-container`, `on-primary-fixed`, `on-primary-fixed-variant`,
`on-secondary`, `on-secondary-container`, `on-secondary-fixed`,
`on-secondary-fixed-variant`, `on-tertiary`, `on-tertiary-container`,
`on-tertiary-fixed`, `on-tertiary-fixed-variant`, `primary-fixed`,
`primary-fixed-dim`, `secondary-fixed`, `secondary-fixed-dim`, `surface-dim`,
`surface-tint`, `tertiary`, `tertiary-container`, `tertiary-fixed`,
`tertiary-fixed-dim`. All at `03:1`.

The whole tertiary ramp and the whole error ramp are unused, so the screens
define no error state and no tertiary accent in practice.

## Type

Three families, loaded from Google Fonts at `03:1`:

| Family | Weights loaded | Used for |
| ------ | -------------- | -------- |
| Syne | 600, 700 | `display-lg`, `display-sm`, `headline-lg`, `headline-lg-mobile` |
| Hanken Grotesk | 400, 500, 600, 700 | `body-lg`, `body-md`, `headline-sm` |
| JetBrains Mono | 400, 500, 600 | `label-lg`, `label-md`, `label-sm` |

Material Symbols Outlined is loaded with axes `wght,FILL@100..700,0..1` (`03:1`)
and used in 52 places across the four screens. Icons that read as filled set
`font-variation-settings: 'FILL' 1` inline, for example `03:35` and `03:88`.

### Scale

| Token | Size | Line height | Tracking | Weight | Family |
| ----- | ---: | ----------: | -------: | -----: | ------ |
| `display-lg` | 48px | 52px | -0.03em | 700 | Syne |
| `display-sm` | 36px | 40px | -0.02em | 700 | Syne |
| `headline-lg` | 28px | 34px | -0.015em | 600 | Syne |
| `headline-lg-mobile` | 24px | 30px | -0.01em | 600 | Syne |
| `headline-sm` | 20px | 26px | -0.01em | 600 | Hanken Grotesk |
| `body-lg` | 16px | 24px | 0 | 400 | Hanken Grotesk |
| `body-md` | 14px | 20px | 0 | 400 | Hanken Grotesk |
| `label-lg` | 13px | 18px | 0.04em | 500 | JetBrains Mono |
| `label-md` | 11px | 14px | 0.06em | 500 | JetBrains Mono |
| `label-sm` | 9px | 12px | 0.08em | 600 | JetBrains Mono |

All values: `03:1`.

Tracking is negative on display and headline sizes and positive on label sizes,
tightening as text gets larger and opening as it gets smaller. Labels are
monospace, uppercase in use, and carry the widest tracking.

Each `fontSize` token has a `fontFamily` token of the same name, so a text
element carries both, for example `font-label-sm text-label-sm` at `03:88`.

## Spacing

One scale, used for padding, gap and margin (`03:1`):

| Token | Value | | Token | Value |
| ----- | ----: | - | ----- | ----: |
| `space-2xs` | 0.25rem | | `card-padding-md` | 1.25rem |
| `space-xs` | 0.5rem | | `screen-edge-mobile` | 1.25rem |
| `space-sm` | 0.75rem | | `space-lg` | 1.5rem |
| `space-md` | 1rem | | `card-padding-lg` | 1.75rem |
| `card-padding-sm` | 1rem | | `space-xl` | 2rem |
| `touch-target-min` | 2.75rem | | `screen-edge-tablet` | 2rem |
| `space-2xl` | 3rem | | `space-3xl` | 4rem |

`space-md` and `card-padding-sm` are both 1rem; `screen-edge-mobile` and
`card-padding-md` are both 1.25rem; `space-xl` and `screen-edge-tablet` are both
2rem. `screen-edge-tablet`, `card-padding-lg` and `space-3xl` are defined but
not used in the four screens.

### Radius

`DEFAULT` 0.25rem, `lg` 0.5rem, `xl` 0.75rem, `full` 9999px (`03:1`). Cards use
`rounded-xl`, inner panels `rounded-lg`, pills and buttons `rounded-full`.

## Components

### App shell

Every screen is a fixed header, a scrolling `main`, and a fixed bottom nav.

- **Header**: `fixed top-0 w-full z-50 pt-safe bg-surface/85 backdrop-blur-xl
  shadow-[0_1px_8px_rgba(0,0,0,0.35)]`, inner row `h-16 px-screen-edge-mobile`.
  `01:7`, `02:2`, `03:6`, `04:7`.
- **Bottom nav**: `fixed bottom-0 w-full z-50 pb-safe bg-surface/90
  backdrop-blur-xl shadow-[0_-1px_12px_rgba(0,0,0,0.4)]`, inner row `h-16`.
  `01:100`, `02:131`, `03:178`, `04:270`.
- **Main**: `pt-16 pb-24` clears both bars. `03:6`, `04:7`.
- **Nav items**: three per screen (`LIVE`, `MOMENTS`, `PROFILE`), each
  `min-w-[44px] min-h-[44px]`, active item `text-primary-container` with
  `aria-current="page"`, inactive `text-on-surface-variant`. Same four lines.

The header is translucent at 85% and the nav at 90%, both over `backdrop-blur-xl`.

### Live status pill

`rounded-full bg-surface-container-high/80 backdrop-blur-md` with a
`w-1.5 h-1.5 rounded-full bg-primary-container pulse-live` dot and a `label-sm`
uppercase caption. Present in all four headers: `01:7`, `02:2`, `03:6`, `04:7`.

### Pulse animation

```
@keyframes pulse-amber { 0%,100% { opacity:1; transform:scale(1) }
                         50%     { opacity:0.35; transform:scale(0.85) } }
.pulse-live { animation: pulse-amber 2s cubic-bezier(0.4,0,0.6,1) infinite; }
```

Defined at `03:1`, applied at 11 sites including `01:9`, `01:21`, `02:63`,
`03:14`. It is the only animation in the system; everything else is a CSS
transition.

### Card

`rounded-xl` on a surface one or two steps up from the page, with a hairline
border at low opacity and a shadow:

- `rounded-xl bg-surface-container ... border border-surface-container-highest/30
  shadow-xl` at `03:19`.
- `rounded-xl bg-surface-container-low ... border border-surface-container-high/60
  shadow-md` at `04:34`, `04:113`, `04:184`.
- Inner panel: `rounded-xl bg-surface-container-high p-card-padding-md ...
  border border-surface-container-highest/40 shadow-md` at `03:31`.

Borders are always a surface token at 20 to 60 percent opacity, never a solid line.

### Buttons

| Role | Spec | Source |
| ---- | ---- | ------ |
| Primary CTA | `w-full h-touch-target-min rounded-full bg-primary-container text-on-primary-container font-label-lg uppercase tracking-wider font-bold`, `active:scale-[0.99]` | `01:56` |
| Primary play | `w-14 h-14 rounded-full bg-primary-container text-on-primary shadow-lg shadow-primary-container/20`, `hover:scale-105 active:scale-95` | `03:34` |
| Secondary play, active | `w-11 h-11 rounded-full bg-primary-container text-on-primary shadow-lg`, `active:scale-95` | `04:76` |
| Secondary play, idle | `w-11 h-11 rounded-full bg-surface-container-highest text-primary`, `hover:bg-primary-container hover:text-on-primary` | `04:151`, `04:221` |
| Tertiary action | `h-16 rounded-xl bg-surface-container hover:bg-surface-container-high`, `active:scale-98`, icon over `label-sm` caption | `03:93`, `03:98`, `03:103` |

Press feedback is a scale transform in every case: 0.99, 0.95 or 0.98. The
minimum touch target is 2.75rem (44px), which `touch-target-min` and the
`min-w-[44px] min-h-[44px]` nav items both honor.

### Filter chips

Single row, horizontally scrollable, `overflow-x-auto no-scrollbar`. Selected
chip `bg-surface-container-high text-primary border border-outline-variant/40`;
unselected `bg-surface-container-low text-secondary border border-transparent
hover:border-outline-variant/30`. Five chips at `04:30`.

### Waveform

Static bars, no canvas. Two variants:

- Moment card: `w-[3px]` bars, heights `h-2` to `h-9`, played bars
  `bg-primary-container`, unplayed `bg-secondary-container/70`, on a
  `bg-surface-container-lowest/60 rounded-lg` track. 24 bars, `03:50` to `03:74`.
  A playhead at `03:77` is `w-1.5 h-7 bg-primary rounded-full` with
  `shadow-[0_0_8px_rgba(255,219,160,0.8)]`, positioned `left-[78%]`.
- Moments cards: `w-1` bars on a `h-6 rounded bg-surface-container-highest`
  track, same played and unplayed colors. `04:85`, `04:159`, `04:229`.

Card headers also carry a decorative bar field at `opacity-25` with
`pointer-events-none`, for example `04:38`.

### Verified marker

`rounded-lg bg-surface-container-lowest` holding a filled `verified` Material
Symbol at `text-[16px] text-primary-container` and a `label-sm text-secondary`
caption reading "Verified from play data". `02:83`, `03:88`.

### Text input

`w-full bg-surface-container px-3 py-1.5 rounded text-body-md text-on-surface
border border-outline-variant/30`, with the only real focus treatment in the
system: `focus:outline-none focus:border-primary-container`, so the border
changes color rather than gaining a ring. Three instances at `01:11`. Each uses
a `placeholder` and has no associated `<label>` element.

### Toggle switch

`h-6 w-11 rounded-full border-2 border-transparent bg-primary-container` with
`role="switch"`, `aria-checked="true"`, `aria-label`, and an `sr-only` caption.
The knob is `h-5 w-5 rounded-full bg-on-primary translate-x-5`, moved by
`transition duration-200 ease-in-out`. `04:263` to `04:265`. Only the checked
appearance exists; the unchecked colors are not defined anywhere.

### Credit footer

Text credit plus the reversed Hudl StatsBomb logo:

- Picker: `Powered by StatsBomb play-by-play data` in `body-md text-secondary`,
  logo at `h-4 w-auto ml-auto` (105px by 16px). `01:54`.
- Moments: `Data: StatsBomb` in `label-sm text-secondary uppercase`, logo at
  `h-3 w-auto` (79px by 12px). `04:260`.

Logo file `app/web/assets/hudl-statsbomb-logo-reversed.png`, 2258 by 344, so
6.56:1.

## What the screens do not define

Not present anywhere in the four files, so not specified: light mode, disabled
states, error or empty states, toasts, modals, form validation, and the
unchecked state of the toggle switch.

Focus is defined only on the text input (`01:11`). Every button in the system
relies on `active:` scale and `hover:` color, with no focus style at all, and
the toggle at `04:263` sets `focus:outline-none` without a replacement, so it
has no visible keyboard focus.

No breakpoint utilities are used: zero occurrences of `sm:`, `md:`, `lg:`,
`xl:` or `2xl:` across the four screens, and `screen-edge-tablet` is defined but
never applied. The layouts are mobile width only.

`pulse-amber` is the only `@keyframes` block, declared once per screen.
Everything else that moves is a CSS transition or a transform on `:hover` and
`:active`.
