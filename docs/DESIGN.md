# DESIGN

The design system as the four screens in `app/web/` actually define it. Every
value below is read out of the markup, not from any design brief.

**How to trace a value.** A citation is a screen, written `01` to `04` for
`prelude_01_picker.html` through `prelude_04_moments.html`. The anchor is the
backticked class string in the same table row or bullet: search the cited screen
for that string and you are at the element being described.

Citations used to carry line numbers. They were accurate when written and wrong
after the next markup change, three times over, and once a repair silently
pointed a citation at the wrong element. A class string moves with the element
it belongs to, so it cannot drift. `scripts/check_docs.py` verifies that every
anchor still appears in every screen cited beside it.

The token tables all cite `03`, meaning the `<script id="tailwind-config">`
block. That block is byte-identical across all four screens (sha256
`3b9cf112d3cbc180...`, 3209 chars), so the system is one system.

Anything a screen does not contain is absent here. There is no spec for states,
breakpoints, or components the screens do not have.

`prelude_05_scan.html`, the ticket scanner, is not covered. It arrived after
this document and carries the same `<script id="tailwind-config">` block byte
for byte, so it is built from the system described here, but its own components
(the viewfinder, the reticle and the scan line) are not documented below.

## Foundations

| Property | Value | Source |
| -------- | ----- | ------ |
| Mode | dark only, `darkMode: "class"`, `<html class="dark"` | `03` |
| Page background | `#101319`, set on `html,body` in `@layer base` | `03` |
| Viewport | `width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover` | all four, line 1 |
| Body min height | `max(884px, 100dvh)` | `01`, `03`, `04` |
| Font smoothing | `-webkit-font-smoothing: antialiased` | `03` |
| Overscroll | `overscroll-behavior: none` | `03` |
| Scrollbars | hidden, `::-webkit-scrollbar{display:none;}` | `03` |
| Safe areas | `.pt-safe` and `.pb-safe` map to `env(safe-area-inset-top,0px)` and `env(safe-area-inset-bottom,0px)` | `03` |

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

All hex values come from the `tailwind-config` block in `03`.

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
`tertiary-fixed-dim`. All in the `tailwind-config` block in `03`.

The whole tertiary ramp and the whole error ramp are unused, so the screens
define no error state and no tertiary accent in practice.

## Type

Three families, loaded from `fonts.googleapis.com` in `03`:

| Family | Weights loaded | Used for |
| ------ | -------------- | -------- |
| Syne | 600, 700 | `display-lg`, `display-sm`, `headline-lg`, `headline-lg-mobile` |
| Hanken Grotesk | 400, 500, 600, 700 | `body-lg`, `body-md`, `headline-sm` |
| JetBrains Mono | 400, 500, 600 | `label-lg`, `label-md`, `label-sm` |

Material Symbols Outlined is loaded with axes `wght,FILL@100..700,0..1` (`03`)
and used in 52 places across the four screens. Icons that read as filled set
`font-variation-settings: 'FILL' 1` inline, in `03`.

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

All values come from the `tailwind-config` block in `03`.

Tracking is negative on display and headline sizes and positive on label sizes,
tightening as text gets larger and opening as it gets smaller. Labels are
monospace, uppercase in use, and carry the widest tracking.

Each `fontSize` token has a `fontFamily` token of the same name, so a text
element carries both, for example `font-label-sm text-label-sm` in `03`.

## Spacing

One scale, from the `tailwind-config` block in `03`, used for padding, gap and margin:

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

`DEFAULT` 0.25rem, `lg` 0.5rem, `xl` 0.75rem, `full` 9999px (`03`). Cards use
`rounded-xl`, inner panels `rounded-lg`, pills and buttons `rounded-full`.

## Components

### App shell

Every screen is a fixed header, a scrolling `main`, and a fixed bottom nav.

- **Header**: `fixed top-0 w-full z-50 pt-safe bg-surface/85 backdrop-blur-xl
  shadow-[0_1px_8px_rgba(0,0,0,0.35)]`, inner row `h-16 px-screen-edge-mobile`.
  `01`, `02`, `03`, `04`.
- **Bottom nav**: `fixed bottom-0 w-full z-50 pb-safe bg-surface/90
  backdrop-blur-xl shadow-[0_-1px_12px_rgba(0,0,0,0.4)]`, inner row `h-16`.
  `01`, `02`, `03`, `04`.
- **Main**: `pt-16 pb-24` clears both bars. `03`, `04`.
- **Nav items**: three per screen (`LIVE`, `MOMENTS`, `PROFILE`), each
  `min-w-[44px] min-h-[44px]`, active item `text-primary-container` with
  `aria-current="page"`, inactive `text-on-surface-variant`. Same four lines.

The header is translucent at 85% and the nav at 90%, both over `backdrop-blur-xl`.

### Live status pill

`rounded-full bg-surface-container-high/80 backdrop-blur-md` with a
`w-1.5 h-1.5 rounded-full bg-primary-container pulse-live` dot and a `label-sm`
uppercase caption. Present in all four headers: `01`, `02`, `03`, `04`.

### Pulse animation

```
@keyframes pulse-amber { 0%,100% { opacity:1; transform:scale(1) }
                         50%     { opacity:0.35; transform:scale(0.85) } }
.pulse-live { animation: pulse-amber 2s cubic-bezier(0.4,0,0.6,1) infinite; }
```

`@keyframes pulse-amber` is defined in `03` and applied at 11 sites across
`01`, `02` and `03`. It is the only animation in the system; everything else is
a CSS transition.

### Card

`rounded-xl` on a surface one or two steps up from the page, with a hairline
border at low opacity and a shadow:

- `rounded-xl bg-surface-container overflow-hidden shadow-xl` with a
  `border border-surface-container-highest/30` hairline, in `03`.
- `bg-surface-container-low rounded-xl border border-surface-container-high/60`,
  three times in `04`.
- Inner panel: `rounded-xl bg-surface-container-high p-card-padding-md` with a
  `border border-surface-container-highest/40` hairline, in `03`.

Borders are always a surface token at 20 to 60 percent opacity, never a solid line.

### Buttons

| Role | Spec | Source |
| ---- | ---- | ------ |
| Primary CTA | `w-full h-touch-target-min rounded-full bg-primary-container text-on-primary-container font-label-lg text-label-lg font-bold`, `active:scale-[0.99]` | `01` |
| Primary play | `w-14 h-14 rounded-full bg-primary-container text-on-primary` with `shadow-lg shadow-primary-container/20`, `hover:scale-105 active:scale-95` | `03` |
| Secondary play, active | `w-11 h-11 shrink-0 rounded-full bg-primary-container text-on-primary`, `active:scale-95` | `04` |
| Secondary play, idle | `w-11 h-11 shrink-0 rounded-full bg-surface-container-highest text-primary`, `hover:bg-primary-container hover:text-on-primary` | `04` |
| Tertiary action | `h-16 rounded-xl bg-surface-container hover:bg-surface-container-high`, `active:scale-98`, icon over `label-sm` caption | `03` |

Press feedback is a scale transform in every case: 0.99, 0.95 or 0.98. The
minimum touch target is 2.75rem (44px), which `touch-target-min` and the
`min-w-[44px] min-h-[44px]` nav items both honor.

### Filter chips

Single row, horizontally scrollable: `overflow-x-auto pb-1 select-none no-scrollbar`.
Selected chip `rounded-full bg-surface-container-high text-primary`, unselected
`rounded-full bg-surface-container-low text-secondary`, each closing with
`border border-outline-variant/40` or `border border-transparent`. Five chips in `04`.

### Waveform

Static bars, no canvas. Two variants:

- Moment card: `w-[3px]` bars, heights `h-2` to `h-9`, played bars
  `bg-primary-container`, unplayed `bg-secondary-container/70`, on a
  `bg-surface-container-lowest/60 rounded-lg` track. 24 bars, in `03`.
  A playhead in `03` is `w-1.5 h-7 bg-primary rounded-full` with
  `shadow-[0_0_8px_rgba(255,219,160,0.8)]`, positioned `left-[78%]`.
- Moments cards: `w-1` bars on a `rounded bg-surface-container-highest` track,
  same played and unplayed colors. `04`.

Card headers also carry a decorative bar field at `opacity-25` with
`pointer-events-none`, in `04`.

### Verified marker

`rounded-lg bg-surface-container-lowest` holding a filled `verified` Material
Symbol at `text-[16px] text-primary-container` and a `label-sm text-secondary`
caption reading "Verified from play data". `03`.

### Text input

`w-full bg-surface-container px-3 py-1.5 rounded text-body-md text-on-surface
border border-outline-variant/30`, with the only real focus treatment in the
system: `focus:outline-none focus:border-primary-container`, so the border
changes color rather than gaining a ring. Three instances in `01`: the section,
row and seat of a ticket entered by hand. Each carries a `placeholder` and a
`<label>` bound to it by `for`.

### Select

The same field classes as the text input, `bg-surface-container px-3 py-1.5
rounded`, on the match select in `01`. It is the only select in the system and
takes the forms plugin's own chevron rather than a drawn one.

### Toggle switch

`h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-primary-container` with
`role="switch"`, `aria-checked="true"`, `aria-label`, and an `sr-only` caption.
The knob is `translate-x-5 inline-block h-5 w-5 transform rounded-full bg-on-primary`, moved by
`transition duration-200 ease-in-out`. `04`. Only the checked
appearance exists; the unchecked colors are not defined anywhere.

### Credit footer

Text credit plus the reversed Hudl StatsBomb logo:

- Picker: `Powered by StatsBomb play-by-play data` in `body-md text-secondary`,
  logo at `h-4 w-auto ml-auto` (105px by 16px). `01`.
- Moments: `Data: StatsBomb` in `text-label-sm text-secondary tracking-wider uppercase`, logo at
  `h-3 w-auto` (79px by 12px). `04`.

Both sit on a `bg-surface-container-lowest` panel with a
`border-outline-variant/20` hairline, which is the quietest surface in the ramp
and the reason the two credits read as the same component. The Moments footer
reached that shape late: it was on `surface-container-high` with the credit
nested in a column that also held the callout and competed with the auto-save
control, so at 390px the callout broke to three lines and the credit wrapped
mid-word. It is now two rows, the callout across the full width and the credit
beside the control on a line of their own.

Logo file `app/web/assets/hudl-statsbomb-logo-reversed.png`, 2258 by 344, so
6.56:1.

## Phone frame, wide viewports

The four screens are laid out for a 390 by 844 phone and use no breakpoint
utilities, so on a desktop window they stretch and misread. `app/web/phone-frame.css`
puts a screen inside a generic bezel at its real size above a breakpoint. It is
presentation only: no app layout, copy or component is involved, and it is
built entirely from `body` and `body > main`, which every screen already has.

| Property | Value | Token? |
| -------- | ----- | ------ |
| Breakpoint | `min-width: 501px` | no, chrome only |
| Screen area | 390 by 844 | the viewport the screens are built for |
| Bezel thickness | 16px | no |
| Bezel radius | 48px | no |
| Bezel colour | `#32353b` | yes, `surface-container-highest` |
| Page behind the frame | `#0b0e13` | yes, `surface-container-lowest` |
| Drop shadow | `0 24px 64px rgba(0,0,0,0.55)` | no |

The bezel thickness and radius are not in the token scale and could not be: the
largest non-pill radius token is `xl` at 0.75rem, which is a card corner, not a
device corner. They are frame chrome and are deliberately outside the system.
The two colours are tokens.

**Why `body` carries a transform.** The header and the bottom nav are
`position: fixed`, so by default they pin to the window and would sit outside
the bezel. A transformed ancestor becomes the containing block for fixed
descendants, so `transform: translateZ(0)` on `body` lands both bars inside the
frame. That has a consequence: `body` must stop scrolling (`overflow: hidden`)
and `main` must start (`overflow-y: auto`), otherwise the bars scroll away with
the content. `body` also switches to `box-sizing: content-box` so its width and
height describe the screen area rather than the screen plus bezel.

**At 500px and narrower nothing applies.** The rules live entirely inside the
media query, so the app fills the window exactly as it did before.

**`app/web/index.html` draws the same bezel itself.** It is the entry point and
holds every screen in one iframe, so the frame is built once and navigating
does not rebuild it. Inside that shell the iframe is 390px wide, below the
501px breakpoint, so `phone-frame.css` stays inert and the two never both
apply. The stylesheet still matters when a screen is opened directly.

Measured in both states, on all four screens:

| | 390px viewport | 1440px viewport |
| --- | --- | --- |
| Bezel | none, `border: 0px` | `16px`, radius `48px` |
| Screen area | fills the window, 390 wide | 390 by 844 |
| Frame position | n/a | `left: 509`, centered |
| Header | 390 wide at x=0 | 390 wide at x=525, inside the bezel |
| Bottom nav | at the window bottom | inside the frame, bottom 892 of a 900 window |
| Scrolling | the window scrolls | `main` scrolls, `overflow-y: auto` |
| Horizontal overflow | none | none |

## What the screens do not define

Not present anywhere in the four files, so not specified: light mode, disabled
states, error or empty states, toasts, modals, form validation, and the
unchecked state of the toggle switch.

Focus is defined only on the text input (`01`). Every button in the system
relies on `active:` scale and `hover:` color, with no focus style at all, and
the toggle at `04` sets `focus:outline-none` without a replacement, so it
has no visible keyboard focus.

No breakpoint utilities are used: zero occurrences of `sm:`, `md:`, `lg:`,
`xl:` or `2xl:` across the four screens, and `screen-edge-tablet` is defined but
never applied. The layouts are mobile width only. The only media queries in
the repo are the phone frame above and the matching one in `index.html`, which
wrap the app rather than reflow it.

`pulse-amber` is the only `@keyframes` block, declared once per screen.
Everything else that moves is a CSS transition or a transform on `:hover` and
`:active`.
