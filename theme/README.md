# Condition Tracker theme

Three files. Drop them in, two lines of setup.

```
your-app/
├─ .streamlit/config.toml     # native Streamlit widget tokens
├─ theme/tokens.css           # the theme itself (CSS variables + primitives)
└─ theme/ct_theme.py          # inject_theme() + markup helpers
```

```python
import streamlit as st
from theme.ct_theme import inject_theme, eyebrow, pill, tag, banner, meter, note, C

st.set_page_config(page_title="Condition Tracker", layout="wide")
inject_theme()
```

## Rules that make it look intentional

**Colour is semantic, never decorative.** Blue `#2A54D6` = interaction only
(links, primary button, selection). Red / amber / green *only* mean safety-gate
severity. Nothing is coloured because it looked nice.

**Two typefaces, three jobs.** Archivo for headings and big numbers. IBM Plex
Sans for everything read as prose. IBM Plex Mono only for eyebrow labels,
column headers, IDs and dates — the mono is what makes it read as a working
instrument rather than a generic dashboard.

**One accent, one surface.** Cool paper `#EEF1F5` behind, near-white cards
`#FCFDFE` on top, hairline `#DFE4EA` borders. No shadows, no gradients, no
second card colour.

**Status is a dot plus a word.** `pill("Blocks start on site", "block")` — no
filled badges, no emoji. Filled tints are reserved for the one banner strip.

**Let it breathe.** Table rows at 16px vertical padding, 22–30px between
sections. If a screen feels crowded, cut a column before shrinking type.

## Helpers

| Call | Use for |
|---|---|
| `eyebrow("BEFORE YOU START ON SITE")` | mono section label above a heading |
| `pill(label, gate)` | status — gate: `block`, `piling`, `above`, `due`, `ongoing` |
| `tag("DUPLICATE")` | AI-flagged wording problem (also `TYPO`, `AMBIGUOUS`) |
| `banner(text, kind)` | one tinted strip — `check`, `block`, `ok` |
| `meter(6, 2, 32)` | discharge progress (discharged / submitted / total) |
| `note(text)` | CIL warning, "not legal advice" — deliberately quiet |
| `C["accent"]` | any token in Python |

Anything not covered: use the CSS vars directly — `var(--ct-accent)`,
`var(--ct-font-mono)`, `var(--ct-r-lg)`. Full list at the top of `tokens.css`.

## Type scale

| Role | Font | Size / weight |
|---|---|---|
| Page heading | Archivo | 31px / 700, `-0.7px` |
| Panel heading | Archivo | 20px / 600 |
| Section heading | Archivo | 15px / 600 |
| Body, clause text | IBM Plex Sans | 13.5px / 400, `1.7` |
| Table cell | IBM Plex Sans | 14px / 500 |
| Secondary | IBM Plex Sans | 12.5px / 400 |
| Eyebrow, col header | IBM Plex Mono | 9.5px, `1.8px` tracking, upper |
| Disclaimer | IBM Plex Sans | 11.5px / 400 |

Nothing below 9.5px, and only the mono labels go that small.
