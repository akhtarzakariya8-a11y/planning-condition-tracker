# Condition Tracker — editorial theme

```
your-app/
├─ .streamlit/config.toml        # copy from theme-editorial/config.toml
└─ theme_editorial/
   ├─ tokens.css                 # the theme (CSS variables + primitives)
   └─ ct_theme.py                # inject_theme() + markup helpers
```

```python
import streamlit as st
from theme_editorial.ct_theme import inject_theme, label, pill, tile, banner, conf, event, note, C

st.set_page_config(page_title="Conditions", layout="wide")
inject_theme()
```

## What makes it look like this

**Warm paper, not white.** Page `#f4f1ea`, cards `#fffdf9`, borders `#e5dfd0`.
Never pure white and never pure grey — the warmth is the whole identity.

**Serif for authority.** Source Serif 4 on headings, big stat numbers and panel
titles. Public Sans for everything else. Two faces, no exceptions.

**A near-black rail.** `#21201b` sidebar with `#e9e4d8` text; the active item
is a raised `#35332b` block, not a coloured bar. Every nav item carries a small
dot — muted `#5a564b` when inactive, mint `#7db894` when active.

**Green is the only accent.** `#2e6e4e` for primary buttons and links. Status
uses its own four-colour set and nothing else: red overdue, amber action
needed, slate submitted, green discharged — always a tinted pill with a dot.

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
| Page heading | Source Serif 4 | 30px / 600, `-0.3px` |
| Panel heading | Source Serif 4 | 21px / 600 |
| Stat number | Source Serif 4 | 28px / 600, tabular |
| Table cell | Public Sans | 14px / 600 |
| Body, clause text | Public Sans | 13.5px / 400, `1.65` |
| Secondary | Public Sans | 12.5px / 400 |
| Column header | Public Sans | 10.5px / 700, `0.9px` upper |
| Disclaimer | Public Sans | 11.5px / 400 |

## Note

Streamlit's sidebar theming (`[theme.sidebar]`) needs Streamlit ≥ 1.44. On
older versions the CSS in `ct_theme.py` still darkens the rail — the config
block just makes native widgets match.
