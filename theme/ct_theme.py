"""Condition Tracker theme for Streamlit.

Usage — first two lines of your app, before anything renders:

    from theme.ct_theme import inject_theme, eyebrow, pill, GATE
    st.set_page_config(page_title="Condition Tracker", layout="wide")
    inject_theme()

Then use the helpers instead of st.metric / st.info / emoji badges:

    st.markdown(eyebrow("BEFORE YOU START ON SITE"), unsafe_allow_html=True)
    st.markdown(pill("Blocks start on site", "block"), unsafe_allow_html=True)
"""

from pathlib import Path
import streamlit as st

C = {
    "bg": "#EEF1F5", "surface": "#FCFDFE", "surface_hover": "#F6F8FB",
    "surface_sel": "#EEF2FB", "border": "#DFE4EA", "border_soft": "#EBEEF2",
    "track": "#E1E6EC",
    "ink": "#161A22", "body": "#3A414D", "muted": "#5B6472",
    "faint": "#8A93A1", "fainter": "#A2AAB6",
    "accent": "#2A54D6", "accent_hover": "#1E3EA8",
    "accent_tint": "#E4EAF9", "accent_soft": "#A8C0EC",
    "red": "#C6473C", "red_ink": "#A03A30", "red_tint": "#F7E5E2",
    "amber": "#A9660B", "amber_ink": "#7A4A08", "amber_tint": "#F7EFE0",
    "green": "#2C7A55", "green_ink": "#236344", "green_tint": "#E1EFE7",
    "grey": "#7B8799", "grey_faint": "#B9C1CC",
}

FONTS = ("https://fonts.googleapis.com/css2?"
         "family=Archivo:wght@500;600;700"
         "&family=IBM+Plex+Sans:wght@400;500;600"
         "&family=IBM+Plex+Mono:wght@400;500&display=swap")

# label -> (dot colour, text colour). Colour means severity, nothing else.
GATE = {
    "block":   (C["red"],        C["red_ink"]),    # blocks any start on site
    "piling":  (C["amber"],      C["amber"]),      # required before piling
    "above":   (C["green"],      C["green_ink"]),  # groundworks ok
    "due":     (C["grey"],       C["grey"]),       # pre-occupation
    "ongoing": (C["grey_faint"], C["faint"]),      # compliance during works
}

_STREAMLIT_CSS = """
/* ── Streamlit chrome ─────────────────────────────────────── */
#MainMenu, footer, header [data-testid="stDecoration"] { display:none; }

html, body, [data-testid="stAppViewContainer"] {
  background: var(--ct-bg);
  font-family: var(--ct-font-body);
  color: var(--ct-ink);
}
.block-container { padding-top: 2.2rem; max-width: 1440px; }

h1, h2, h3 { font-family: var(--ct-font-display) !important; letter-spacing:-.5px; }
h1 { font-size: 31px !important; font-weight: 700 !important; }
h2 { font-size: 20px !important; font-weight: 600 !important; }
h3 { font-size: 15px !important; font-weight: 600 !important; }
p, li, [data-testid="stMarkdownContainer"] { font-size: 13.5px; line-height: 1.7; }

/* Sidebar reads as a quiet rail, not a panel */
[data-testid="stSidebar"] { background: var(--ct-bg); border-right:1px solid var(--ct-border); }
[data-testid="stSidebar"] .block-container { padding-top: 1.6rem; }

/* Buttons */
.stButton > button {
  border:1px solid var(--ct-border); background:#fff; color:var(--ct-ink);
  border-radius: var(--ct-r-md); padding:.5rem .95rem;
  font-size:12.5px; font-weight:600; box-shadow:none; transition:all .12s;
}
.stButton > button:hover { border-color:var(--ct-accent); color:var(--ct-accent); background:#fff; }
.stButton > button[kind="primary"] { background:var(--ct-accent); border-color:var(--ct-accent); color:#fff; }
.stButton > button[kind="primary"]:hover { background:var(--ct-accent-hover); border-color:var(--ct-accent-hover); color:#fff; }

/* Inputs */
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stTextArea textarea {
  background:#fff; border-color:var(--ct-border); border-radius:var(--ct-r-md);
  font-size:13px; color:var(--ct-ink);
}
.stTextInput input:focus { border-color:var(--ct-accent); box-shadow:none; }

/* Uploader — the hero control on the first screen */
[data-testid="stFileUploaderDropzone"] {
  background: var(--ct-surface); border:1.5px dashed #C2CAD5;
  border-radius: var(--ct-r-lg); padding: 2.2rem;
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--ct-accent); background:#FAFCFF; }

/* Tabs as quiet segmented nav */
.stTabs [data-baseweb="tab-list"] { gap:4px; border-bottom:1px solid var(--ct-border); }
.stTabs [data-baseweb="tab"] {
  height:auto; padding:8px 13px; font-size:12.5px; font-weight:500;
  color:var(--ct-faint); background:transparent;
}
.stTabs [aria-selected="true"] { color:var(--ct-ink) !important; font-weight:600; }
.stTabs [data-baseweb="tab-highlight"] { background:var(--ct-accent); }

/* Containers, expanders, dataframes all share one card treatment */
[data-testid="stExpander"], [data-testid="stDataFrame"],
div[data-testid="stVerticalBlockBorderWrapper"] > div:has(> [data-testid="stVerticalBlock"]) {
  background: var(--ct-surface); border:1px solid var(--ct-border);
  border-radius: var(--ct-r-lg);
}
[data-testid="stExpander"] summary { font-size:13.5px; font-weight:500; }
[data-testid="stExpander"] summary:hover { color:var(--ct-accent); }

[data-testid="stDataFrame"] { font-size:12.5px; }
[data-testid="stDataFrame"] [role="columnheader"] {
  font-family: var(--ct-font-mono); font-size:9.5px; letter-spacing:1.4px;
  text-transform:uppercase; color:var(--ct-fainter); background:var(--ct-surface);
}

/* Metrics: mono eyebrow label, display-face number */
[data-testid="stMetricLabel"] p {
  font-family: var(--ct-font-mono) !important; font-size:9.5px !important;
  letter-spacing:1.8px; text-transform:uppercase; color:var(--ct-fainter) !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--ct-font-display); font-weight:700; font-size:31px;
  font-variant-numeric: tabular-nums; color:var(--ct-ink);
}

/* Progress + divider */
.stProgress > div > div > div > div { background:var(--ct-accent); }
.stProgress > div > div > div { background:var(--ct-track); height:5px; border-radius:3px; }
hr { border-color: var(--ct-border); }

/* Kill Streamlit's stock alert colours — use ct-banner instead */
[data-testid="stAlert"] {
  border:none; border-radius:var(--ct-r-md); font-size:13px;
  background:var(--ct-accent-tint); color:var(--ct-ink);
}
"""


def _collapse(css: str) -> str:
    """Strip blank lines from CSS.

    Streamlit renders markdown, and a markdown HTML block TERMINATES at the first blank line —
    everything after it leaks onto the page as visible prose instead of being parsed as CSS.
    """
    return "\n".join(line for line in css.splitlines() if line.strip())


def inject_theme(css_path: str | None = None) -> None:
    """Load fonts + tokens + Streamlit overrides. Call once, right after set_page_config."""
    tokens = Path(css_path or Path(__file__).with_name("tokens.css")).read_text(encoding="utf-8")
    st.markdown(
        f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        f'<link href="{FONTS}" rel="stylesheet">'
        f"<style>{_collapse(tokens)}{_collapse(_STREAMLIT_CSS)}</style>",
        unsafe_allow_html=True,
    )


# ── Markup helpers ────────────────────────────────────────────────────

def eyebrow(text: str) -> str:
    return f'<div class="ct-eyebrow">{text}</div>'


def pill(label: str, gate: str = "due") -> str:
    dot, fg = GATE.get(gate, GATE["due"])
    return (f'<span style="display:inline-flex;align-items:center;gap:7px;'
            f'font:500 11.5px/1 var(--ct-font-body);color:{fg}">'
            f'<span style="width:7px;height:7px;border-radius:50%;background:{dot}"></span>'
            f"{label}</span>")


def tag(text: str) -> str:
    """AI-detected wording problem: DUPLICATE / TYPO / AMBIGUOUS."""
    return f'<span class="ct-tag">{text}</span>'


def banner(text: str, kind: str = "check") -> str:
    """kind: check | block | ok"""
    dot = {"check": C["amber"], "block": C["red"], "ok": C["green"]}[kind]
    return (f'<div class="ct-banner ct-banner--{kind}">'
            f'<span style="width:6px;height:6px;border-radius:50%;background:{dot};flex-shrink:0"></span>'
            f"<span>{text}</span></div>")


def meter(done: int, submitted: int, total: int) -> str:
    d = round(done / total * 100, 1) if total else 0
    s = round(submitted / total * 100, 1) if total else 0
    return (f'<div class="ct-meter"><i class="done" style="width:{d}%"></i>'
            f'<i class="submitted" style="width:{s}%"></i></div>')


def note(text: str) -> str:
    """Disclaimers, CIL warning, 'not legal advice' — deliberately quiet."""
    return f'<div class="ct-note">{text}</div>'
