# Aftergrant — app theme

```
.streamlit/config.toml     # native widget colours (match tokens.css)
theme/
├─ tokens.css              # the theme (CSS variables + primitives)
├─ ct_theme.py             # inject_theme(), brand() + markup helpers
└─ brand/                  # wordmark SVGs and the app icon
```

```python
import streamlit as st
from theme.ct_theme import ICON_PNG, inject_theme, brand, label, pill, tile, banner, conf, event, note, C

st.set_page_config(page_title="Aftergrant", page_icon=ICON_PNG, layout="wide")
inject_theme()
```

## What makes it look like this

**Colours come from the logo.** Page cream `#f4f1eb`, cards `#fffdf9`, borders `#e5dfd0`.
Forest `#234f3d` (the logo's letters) for primary buttons, links and the page heading.
Arrow green `#29875b` (the logo's arrow) for anything that moves you forward: progress
bars, the active tab, focus, the dot on the summary banner. Brand files are in `brand/`
(`brand()` puts the wordmark on the page; `ICON_PNG` is the browser-tab icon).

**Montserrat headings, Public Sans body.** Montserrat echoes the wordmark; Public Sans
does the reading. Two faces, no exceptions.

**A forest-green rail.** `#1f3d30` sidebar with cream `#f1efe6` text and the light-arrow
green `#7cc796` for the active item.

**Status keeps its own colours.** Red overdue, amber action needed, slate submitted,
green discharged — always a tinted pill with a dot.

**Generous radii.** 8–14px everywhere, pills at 99px. Nothing sharp.

**Confidence is honest.** The AI bar turns amber below 90% instead of staying
green — `conf(0.88)` does this for you.

## Helpers

| Call | Use for |
|---|---|
| `label("ACTIVITY")` | uppercase micro-label above a block |
| `pill("Overdue", "overdue")` | status — `overdue`, `action`, `submitted`, `discharged` |
| `tile("Overdue", 1, dot=C["overdue"], danger=True)` | stat tile / status filter |
| `banner(text, action="Review extraction")` | the one green summary strip |
| `conf(0.94)` | AI confidence percentage + bar |
| `event("Deadline passed", "1 Aug 2026", C["overdue"])` | activity timeline row |
| `note(text)` | quiet disclaimer |
| `C["accent"]` | any token in Python |

CSS classes are available directly too: `.ct-card`, `.ct-row`, `.ct-chip`,
`.ct-tile`, `.ct-pill--overdue`, `.ct-th`, `.ct-banner`, `.ct-conf`.

## Type scale

| Role | Font | Size / weight |
|---|---|---|
| Page heading | Montserrat | 32px / 700, `-0.6px`, forest |
| Panel heading | Montserrat | 20px / 600 |
| Stat number | Montserrat | 28px / 700, tabular |
| Table cell | Public Sans | 14px / 600 |
| Body, clause text | Public Sans | 13.5px / 400, `1.65` |
| Secondary | Public Sans | 12.5px / 400 |
| Column header | Public Sans | 10.5px / 700, `0.9px` upper |
| Disclaimer | Public Sans | 11.5px / 400 |

## Note

Streamlit's sidebar theming (`[theme.sidebar]`) needs Streamlit ≥ 1.44. On
older versions the CSS in `ct_theme.py` still darkens the rail — the config
block just makes native widgets match.
