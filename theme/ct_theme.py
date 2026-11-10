"""Aftergrant theme for Streamlit — colours and type taken from the logo.

    from theme.ct_theme import inject_theme, brand, label, pill, tile, banner, conf
    st.set_page_config(page_title="Aftergrant", page_icon=ICON_PNG, layout="wide")
    inject_theme()
"""

import base64
from pathlib import Path

import streamlit as st

BRAND_DIR = Path(__file__).with_name("brand")
ICON_PNG = str(BRAND_DIR / "aftergrant-icon-256.png")

C = {
    "bg": "#f4f1eb", "surface": "#fffdf9", "surface_alt": "#faf7f0",
    "surface_hover": "#f6f2e8", "surface_sel": "#f4efe2", "fill": "#f1ede3",
    "border": "#e5dfd0", "border_strong": "#ddd6c6", "border_soft": "#f1ecdf",
    "track": "#ece6d7",
    "rail": "#1f3d30", "rail_raised": "#2c5341", "rail_hover": "#264a3a",
    "rail_ink": "#f1efe6", "rail_muted": "#b9cabe", "rail_faint": "#8fa898",
    "ink": "#1b2a22", "body": "#36413a", "muted": "#66706a",
    "faint": "#939a92", "hair": "#c4bca9",
    "accent": "#234f3d", "accent_hover": "#1a3d2f", "accent_ink": "#1f4434",
    "accent_tint": "#e6efe8", "accent_line": "#c8dccd",
    "arrow": "#29875b", "arrow_soft": "#7cc796",
    "overdue": "#a3352c", "overdue_tint": "#f3dedb",
    "action": "#b07818", "action_tint": "#f6e8d2", "action_ink": "#8a5a14",
    "submitted": "#4a5878", "submitted_tint": "#e7e9f0", "submitted_ink": "#3e4c6d",
    "discharged": "#29875b", "discharged_tint": "#e1efe5", "discharged_ink": "#1f6b47",
}

FONTS = ("https://fonts.googleapis.com/css2?"
         "family=Montserrat:wght@500;600;700"
         "&family=Public+Sans:wght@400;500;600;700&display=swap")

# status key -> (tint bg, text colour, dot)
STATUS = {
    "overdue":    (C["overdue_tint"],    C["overdue"],         C["overdue"]),
    "action":     (C["action_tint"],     C["action_ink"],      C["action"]),
    "submitted":  (C["submitted_tint"],  C["submitted_ink"],   C["submitted"]),
    "discharged": (C["discharged_tint"], C["discharged_ink"],  C["discharged"]),
}

_STREAMLIT_CSS = """
/* ── Streamlit chrome ─────────────────────────────────────── */
#MainMenu, footer, header [data-testid="stDecoration"] { display:none; }

html, body, [data-testid="stAppViewContainer"] {
  background: var(--ct-bg); font-family: var(--ct-font-body); color: var(--ct-ink);
}
[data-testid="stHeader"] { background: var(--ct-bg); }
[data-testid="stMarkdownContainer"] a, [data-testid="stCaptionContainer"] a {
  color: var(--ct-accent); text-decoration: none; font-weight: 600;
}
[data-testid="stMarkdownContainer"] a:hover { color: var(--ct-arrow); text-decoration: underline; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] a { color: var(--ct-rail-ink); font-weight: 500; }
.block-container { padding-top: 2rem; max-width: 1560px; }

h1, h2, h3 { font-family: var(--ct-font-display) !important; font-weight:600 !important; color:var(--ct-ink); }
h1 { font-size:32px !important; font-weight:700 !important; letter-spacing:-.6px; }
h2 { font-size:20px !important; letter-spacing:-.2px; }
h3 { font-size:17px !important; }
p, li, [data-testid="stMarkdownContainer"] { font-size:13.5px; line-height:1.65; color:var(--ct-body); }

/* Sidebar as the dark rail */
[data-testid="stSidebar"] { background: var(--ct-rail); border-right:none; }
[data-testid="stSidebar"] * { color: var(--ct-rail-ink); }
[data-testid="stSidebar"] .block-container { padding-top:1.5rem; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  font-family: var(--ct-font-display) !important; color:var(--ct-rail-ink) !important;
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color:var(--ct-rail-muted) !important; font-size:13px; }
[data-testid="stSidebar"] .stButton > button {
  width:100%; text-align:left; justify-content:flex-start;
  background:transparent; border:none; border-radius:8px;
  color:var(--ct-rail-muted); font-weight:500; font-size:13.5px; padding:.5rem .6rem;
}
[data-testid="stSidebar"] .stButton > button:hover { background:var(--ct-rail-hover); color:var(--ct-rail-ink); }
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background:var(--ct-rail-raised); color:var(--ct-rail-ink); font-weight:600;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label { color:var(--ct-rail-muted) !important; }
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover { background:var(--ct-arrow); }
[data-testid="stSidebar"] hr { border-color:var(--ct-rail-raised); }

/* Buttons */
.stButton > button {
  border:1px solid var(--ct-border-strong); background:var(--ct-surface); color:var(--ct-ink);
  border-radius:var(--ct-r-sm); padding:.5rem .9rem;
  font-size:13px; font-weight:600; box-shadow:none; transition:all .12s;
}
.stButton > button:hover { background:var(--ct-fill); border-color:var(--ct-border-strong); color:var(--ct-ink); }
.stButton > button[kind="primary"] { background:var(--ct-accent); border-color:var(--ct-accent); color:var(--ct-bg); }
.stButton > button[kind="primary"]:hover { background:var(--ct-accent-hover); border-color:var(--ct-accent-hover); }

/* Inputs */
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stTextArea textarea {
  background:var(--ct-surface); border-color:var(--ct-border-strong);
  border-radius:var(--ct-r-sm); font-size:13px; color:var(--ct-ink);
}
.stTextInput input::placeholder { color:var(--ct-faint); }
.stTextInput input:focus { border-color:var(--ct-arrow); box-shadow:none; }

/* Uploader */
[data-testid="stFileUploaderDropzone"] {
  background:var(--ct-surface); border:1.5px dashed var(--ct-border-strong);
  border-radius:var(--ct-r-lg); padding:2rem;
}
[data-testid="stFileUploaderDropzone"]:hover { border-color:var(--ct-arrow); background:var(--ct-accent-tint); }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap:6px; border-bottom:1px solid var(--ct-border); }
.stTabs [data-baseweb="tab"] { height:auto; padding:8px 13px; font-size:13px; font-weight:500; color:var(--ct-muted); }
.stTabs [aria-selected="true"] { color:var(--ct-ink) !important; font-weight:600; }
.stTabs [data-baseweb="tab-highlight"] { background:var(--ct-arrow); }

/* Cards, expanders, tables */
[data-testid="stExpander"], [data-testid="stDataFrame"],
div[data-testid="stVerticalBlockBorderWrapper"] > div:has(> [data-testid="stVerticalBlock"]) {
  background:var(--ct-surface); border:1px solid var(--ct-border); border-radius:var(--ct-r-lg);
}
[data-testid="stExpander"] summary { font-size:13.5px; font-weight:600; }
[data-testid="stExpander"] summary:hover { color:var(--ct-arrow); }

[data-testid="stDataFrame"] { font-size:13px; }
[data-testid="stDataFrame"] [role="columnheader"] {
  font-size:10.5px; font-weight:700; letter-spacing:.9px; text-transform:uppercase;
  color:var(--ct-faint); background:var(--ct-surface);
}

/* Metrics — serif numerals, uppercase label */
[data-testid="stMetric"] {
  background:var(--ct-surface-alt); border:1.5px solid var(--ct-border);
  border-radius:12px; padding:14px 16px;
}
[data-testid="stMetricLabel"] p {
  font-size:12px !important; font-weight:600 !important; color:var(--ct-muted) !important;
}
[data-testid="stMetricValue"] {
  font-family:var(--ct-font-display); font-weight:600; font-size:28px;
  font-variant-numeric:tabular-nums; color:var(--ct-ink);
}

/* Progress + divider */
.stProgress > div > div > div > div { background:var(--ct-arrow); }
.stProgress > div > div > div { background:var(--ct-track); height:4px; border-radius:2px; }
hr { border-color:var(--ct-border); }

/* Replace stock alerts with the paper banner */
[data-testid="stAlert"] {
  border:1px solid var(--ct-accent-line); border-radius:var(--ct-r-md);
  background:var(--ct-accent-tint); color:var(--ct-accent-ink); font-size:13px;
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

def _svg_uri(name: str) -> str:
    data = (BRAND_DIR / name).read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(data).decode("ascii")


def brand(tagline: str = "", on_green: bool = False, height: int = 34) -> str:
    """The Aftergrant wordmark (inline SVG, so it works on Streamlit Cloud with no static folder)."""
    name = "aftergrant-wordmark-on-green.svg" if on_green else "aftergrant-wordmark.svg"
    tag = f'<span class="ag-tagline">{tagline}</span>' if tagline else ""
    return (f'<div class="ag-brand"><img src="{_svg_uri(name)}" alt="Aftergrant" '
            f'style="height:{height}px">{tag}</div>')


def label(text: str) -> str:
    """Uppercase micro-label above a heading or block."""
    return f'<div class="ct-label">{text}</div>'


def pill(text: str, status: str = "submitted") -> str:
    """status: overdue | action | submitted | discharged"""
    bg, fg, dot = STATUS.get(status, STATUS["submitted"])
    return (f'<span style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;'
            f'border-radius:99px;background:{bg};color:{fg};'
            f'font:600 12.5px/1 var(--ct-font-body)">'
            f'<span style="width:6px;height:6px;border-radius:50%;background:{dot}"></span>'
            f"{text}</span>")


def tile(label_text: str, value, dot: str = None, active: bool = False, danger: bool = False) -> str:
    """Stat tile that doubles as a status filter. Pair with a st.button for the click."""
    return (f'<div class="ct-tile" aria-pressed="{str(active).lower()}">'
            f'<div style="display:flex;align-items:center;gap:7px;font:600 12px/1 var(--ct-font-body);'
            f'color:{C["muted"]}">'
            + (f'<span style="width:8px;height:8px;border-radius:50%;background:{dot}"></span>' if dot else "")
            + f'{label_text}</div>'
            f'<div class="ct-stat" style="margin-top:6px;'
            f'color:{C["overdue"] if danger else C["ink"]}">{value}</div></div>')


def banner(text: str, action: str = "") -> str:
    """One soft green strip — AI extraction summary, counts, review prompt."""
    right = (f'<span style="margin-left:auto;font-weight:600;font-size:12.5px">{action}</span>'
             if action else "")
    return (f'<div class="ct-banner">'
            f'<span style="width:8px;height:8px;border-radius:50%;background:{C["arrow"]};flex-shrink:0"></span>'
            f"<span>{text}</span>{right}</div>")


def conf(value: float) -> str:
    """AI confidence: percentage + bar. Below 0.90 turns amber."""
    pct = round(value * 100)
    col = C["action"] if value < 0.90 else C["arrow"]
    return (f'<div style="font:600 12px/1 var(--ct-font-body);color:{col}">{pct}%</div>'
            f'<div class="ct-conf" style="margin-top:4px">'
            f'<i style="width:{pct}%;background:{col}"></i></div>')


def event(title: str, date: str, dot: str = None) -> str:
    """One row of the activity timeline."""
    d = dot or C["hair"]
    return (f'<div class="ct-event"><div class="ct-event-mark">'
            f'<span style="background:{d}"></span><span></span></div>'
            f'<div style="padding-bottom:16px">'
            f'<div style="font:600 13px/1.3 var(--ct-font-body)">{title}</div>'
            f'<div style="font-size:11.5px;color:{C["faint"]};margin-top:1px">{date}</div>'
            f"</div></div>")


def note(text: str) -> str:
    return f'<div class="ct-note">{text}</div>'
