"""
HOP THROUGH DATA | CDC PLACEMENT INTELLIGENCE
Streamlit dashboard for SSDC 2026

LIGHT DESIGN SYSTEM
-------------------
Search the labels below to edit the visual design quickly:
    [DESIGN 01] Color palette
    [DESIGN 02] Typography
    [DESIGN 03] Global page width and spacing
    [DESIGN 04] Card appearance
    [DESIGN 05] Navigation style
    [LAYOUT 01] Executive KPI grid
    [LAYOUT 02] Executive analysis grid
    [LAYOUT 03] Matching sandbox grid
    [LAYOUT 04] Funnel and EWS grid

Custom icons are configured in ICON_PATHS. PNG/SVG assets are resolved from assets/, assets/icons/, or the project root.

This app reads parquet files produced by etl.py from:
    clean_data/company.parquet
    clean_data/talent_request.parquet
    clean_data/student_all.parquet
    clean_data/status_student.parquet
    clean_data/tracking_company.parquet
    clean_data/tracking_student.parquet

Run:
    py etl.py
    py -m streamlit run app_revised.py
"""

from __future__ import annotations

import base64
import html
import mimetypes
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# =============================================================================
# APPLICATION IDENTITY
# =============================================================================
# Edit these values before submission. Do not add a university identity,
# because the competition rules prohibit institutional identification.
DASHBOARD_TITLE = "CareerBridge"
DASHBOARD_SUBTITLE = "Connecting Talent with Opportunity"
TEAM_NAME = "IRIS SET"
PARTICIPANT_NUMBER = "SSDC2026023"


# =============================================================================
# [DESIGN 00] ASSET / ICON PLACEHOLDERS
# =============================================================================
# Put your own PNG or SVG files at these paths. You only need to replace the
# path strings below when changing an icon. The dashboard stays clean even if
# an asset has not been added yet because a neutral placeholder is shown.
ICON_PATHS = {
    # Brand
    "logo": "assets/logo.png",
    "favicon": "assets/logo.png",

    # Navigation
    "nav_executive": "assets/nav/nav_executive.png",
    "nav_matching": "assets/nav/nav_matching.png",
    "nav_operations": "assets/nav/nav_operations.png",

    # KPI cards
    "student": "assets/cards/student.svg",
    "placement": "assets/cards/placement.svg",
    "company": "assets/cards/company.svg",
    "clock": "assets/cards/clock.svg",
    "sync": "assets/cards/sync.svg",
    "attention": "assets/cards/attention.svg",
    "danger": "assets/cards/danger.svg",
    "matching": "assets/cards/matching.svg",
    "send": "assets/cards/send.svg",

    # Matching form headings
    "panel_eligibility": "assets/panel_eligibility.png",
    "panel_filter": "assets/panel_filter.png",
    "panel_request": "assets/panel_request.png",

    # Insight cards
    "talent_source": "assets/insight/talent_source.png",
    "partner_effective": "assets/insight/partner_effective.png",
    "mobility": "assets/insight/mobility.png",
    "bottleneck": "assets/insight/bottleneck.png",
}

BASE_DIR = Path(__file__).resolve().parent
CLEAN_DIR = BASE_DIR / "clean_data"


# =============================================================================
# [DESIGN 01] LIGHT TEAL COLOR PALETTE
# =============================================================================
# Change these HEX values to recolor the whole dashboard. The first group
# controls backgrounds, the second group controls accents and status colors.
PAGE_BG = "#F1FAF8"          # Main page background
PAGE_BG_ALT = "#E8F7F4"      # Decorative pale-teal background
SURFACE = "#FFFFFF"          # Main card background
SURFACE_ALT = "#F8FCFB"      # Secondary card / input background
SURFACE_STRONG = "#EAF7F4"   # Selected or highlighted surface
BORDER_LIGHT = "#D9ECE8"     # Card and input border
BORDER_STRONG = "#A9D8D1"    # Hover / active border

TEAL = "#149C94"             # Primary accent and main action
TEAL_DARK = "#0C706B"        # Strong teal for text / hover
TEAL_DIM = "#52BEB4"         # Secondary teal
MINT = "#BFEBDD"             # Soft highlight
AMBER = "#D99A32"            # Warning state
CRIMSON = "#D85E70"          # Danger state
VIOLET = "#7682D8"           # Secondary analytical accent

TEXT_HIGH = "#153B39"        # Main text
TEXT_MID = "#526E6C"         # Secondary text
TEXT_LOW = "#2B6661"         # Small text: dark teal for stronger readability
BORDER = "rgba(20, 112, 107, 0.18)"
SHADOW = "0 22px 50px rgba(28, 94, 88, 0.20), 0 7px 18px rgba(28, 94, 88, 0.11)"

# Bright chart palette. Charts intentionally use colors outside the dashboard teal.
CHART_COLORS = [
    "#6F8FEF",  # soft cornflower blue
    "#9887E8",  # soft violet
    "#E98C7C",  # soft coral
    "#E5B65F",  # soft amber
    "#DE85AE",  # soft rose
    "#65B7D8",  # soft sky blue
    "#77BE91",  # soft green
    "#E7A06A",  # soft orange
    "#8795AA",  # blue-grey
    "#B383D6",  # soft orchid
]

# Compatibility aliases used by existing chart code. You normally do not need
# to edit these if the palette above has already been changed.
NAVY_950 = PAGE_BG
NAVY_900 = SURFACE
NAVY_800 = SURFACE
NAVY_750 = SURFACE_ALT
NAVY_700 = SURFACE_STRONG
NAVY_600 = BORDER_STRONG


# =============================================================================
# [DESIGN 02] TYPOGRAPHY
# =============================================================================
# Requested font system:
#   Heading  : Nobile
#   Body     : Roboto Flex
#   KPI/data : Roboto Mono
# Google Fonts require internet. The fallback fonts keep the app readable.
FONT_DISPLAY = "'Encode Sans', 'Segoe UI', sans-serif"
FONT_BODY = "'Roboto Flex', 'Segoe UI', sans-serif"
FONT_MONO = "'Electrolize', 'Consolas', monospace"


def resolve_asset_path(relative_path: str) -> Path | None:
    """Resolve icons from assets/icons, assets root, or the project root.

    The previous version required an exact path such as assets/icons/student.png.
    This resolver also finds assets/student.png and an SVG with the same stem.
    Matching is case-insensitive so Windows filename casing does not matter.
    """
    if not relative_path:
        return None

    requested = Path(relative_path)
    candidate_dirs = [
        BASE_DIR / requested.parent,
        BASE_DIR / "assets" / "icons",
        BASE_DIR / "assets",
        BASE_DIR,
    ]
    extensions = [requested.suffix, ".png", ".svg", ".webp", ".jpg", ".jpeg"]
    extensions = list(dict.fromkeys(ext for ext in extensions if ext))

    exact = BASE_DIR / requested
    if exact.exists() and exact.is_file():
        return exact

    requested_stem = requested.stem.lower()
    for folder in candidate_dirs:
        if not folder.exists():
            continue
        for ext in extensions:
            candidate = folder / f"{requested.stem}{ext}"
            if candidate.exists() and candidate.is_file():
                return candidate
        for candidate in folder.iterdir():
            if (
                candidate.is_file()
                and candidate.stem.lower() == requested_stem
                and candidate.suffix.lower() in {".png", ".svg", ".webp", ".jpg", ".jpeg"}
            ):
                return candidate
    return None


def asset_data_uri(relative_path: str) -> str:
    """Return a base64 URI when an image asset exists."""
    path = resolve_asset_path(relative_path)
    if path is None:
        return ""
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def icon_html(icon_key: str, class_name: str = "ui-icon") -> str:
    """Render a custom PNG/SVG or a visible placeholder when it is missing."""
    relative_path = ICON_PATHS.get(icon_key, "")
    resolved = resolve_asset_path(relative_path) if relative_path else None
    uri = asset_data_uri(relative_path) if resolved else ""
    safe_path = html.escape(str(resolved or relative_path))
    if uri:
        return f'<img class="{class_name}" src="{uri}" alt="" title="{safe_path}">'
    return (
        f'<span class="{class_name} icon-placeholder" '
        f'title="Ikon belum ditemukan: {safe_path}" aria-hidden="true"></span>'
    )


# =============================================================================
# [DESIGN 03] GLOBAL PAGE CONFIGURATION
# =============================================================================
# Change layout="wide" to layout="centered" for a narrower dashboard.
favicon_file = resolve_asset_path(ICON_PATHS["favicon"])
st.set_page_config(
    page_title=f"{DASHBOARD_TITLE} | SSDC 2026",
    page_icon=str(favicon_file) if favicon_file else None,
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =============================================================================
# GLOBAL CSS
# =============================================================================
# [DESIGN 03] Change max-width and padding to control the overall page width.
# [DESIGN 04] Change border-radius, border, and shadow for the card appearance.
# [DESIGN 05] Change the stRadio rules to redesign horizontal navigation.
CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Encode+Sans:wght@400;500;600;700&family=Roboto+Flex:opsz,wght@8..144,300..700&family=Electrolize&display=swap');

:root {{
  --page-bg:{PAGE_BG}; --page-bg-alt:{PAGE_BG_ALT};
  --surface:{SURFACE}; --surface-alt:{SURFACE_ALT}; --surface-strong:{SURFACE_STRONG};
  --border-light:{BORDER_LIGHT}; --border-strong:{BORDER_STRONG};
  --teal:{TEAL}; --teal-dark:{TEAL_DARK}; --teal-dim:{TEAL_DIM}; --mint:{MINT};
  --amber:{AMBER}; --crimson:{CRIMSON}; --violet:{VIOLET};
  --text-hi:{TEXT_HIGH}; --text-mid:{TEXT_MID}; --text-low:{TEXT_LOW};
  --border:{BORDER}; --shadow:{SHADOW};
  --font-display:{FONT_DISPLAY}; --font-body:{FONT_BODY}; --font-mono:{FONT_MONO};
}}

html, body, [data-testid="stAppViewContainer"] {{
  background:
    radial-gradient(circle at 8% 3%, rgba(191,235,221,.75) 0, rgba(191,235,221,0) 26%),
    radial-gradient(circle at 92% 12%, rgba(82,190,180,.15) 0, rgba(82,190,180,0) 28%),
    linear-gradient(180deg, var(--page-bg) 0%, #F8FCFB 48%, #F2FAF8 100%);
  color: var(--text-hi);
  font-family: {FONT_BODY};
}}

[data-testid="stAppViewBlockContainer"] {{
  max-width: 1500px;
  padding-top: 1.15rem;
  padding-bottom: 5rem;
}}

[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stToolbar"] {{ right: 1rem; }}

h1, h2, h3, h4 {{
  font-family: {FONT_DISPLAY};
  color: var(--text-hi);
  letter-spacing: -0.1px;
}}

p, label, div, button, input {{ font-family: {FONT_BODY}; }}

/* Header shell */
.hop-topbar {{
  display:flex; align-items:center; justify-content:space-between;
  gap:18px; flex-wrap:wrap; padding:20px 22px;
  margin:2px 0 18px;
  background:linear-gradient(135deg,#FFFFFF 0%,#F4FCFA 100%);
  border:1px solid var(--border-light); border-radius:22px;
  box-shadow:var(--shadow);
}}
.hop-brand {{ display:flex; align-items:center; gap:14px; }}
.hop-mark {{
  width:48px; height:48px; border-radius:15px;
  background:linear-gradient(145deg,#E4F8F3,#FFFFFF);
  border:1px solid var(--border-light);
  display:flex; align-items:center; justify-content:center;
  box-shadow:0 8px 20px rgba(20,156,148,.10);
}}
.brand-logo {{ width:29px; height:29px; object-fit:contain; }}
.hop-title {{ font-family:{FONT_DISPLAY}; font-size:21px; font-weight:700; line-height:1.15; color:var(--text-hi); }}
.hop-sub {{ color:var(--teal-dark); font-size:12.5px; margin-top:4px; font-weight:520; }}
.hop-asof {{
  display:flex; gap:9px; align-items:center; padding:9px 14px;
  background:#FFFFFF; border:1px solid var(--border-light);
  border-radius:999px; color:var(--text-mid); font-family:{FONT_MONO}; font-size:11px;
}}
.live-dot {{ width:8px; height:8px; background:var(--teal); border-radius:50%; box-shadow:0 0 0 4px rgba(20,156,148,.11); }}

/* Generic custom icons. Replace paths in ICON_PATHS near the top of the file. */
.ui-icon {{ width:30px; height:30px; object-fit:contain; display:block; }}
.icon-placeholder {{
  position:relative; display:inline-block;
  border:1.5px solid rgba(20,156,148,.50); border-radius:7px;
  background:linear-gradient(145deg,#FFFFFF,#E9F8F4);
}}
.icon-placeholder::before {{
  content:''; position:absolute; width:7px; height:7px;
  border:1.5px solid var(--teal); border-radius:50%; left:5px; top:4px;
}}
.icon-placeholder::after {{
  content:''; position:absolute; width:10px; height:5px;
  border-left:1.5px solid var(--teal); border-bottom:1.5px solid var(--teal);
  transform:rotate(-25deg); right:3px; bottom:4px;
}}

/* Custom navigation with replaceable PNG/SVG icons */
.hop-nav-shell {{
  display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px;
  padding:8px; background:rgba(255,255,255,.88);
  border:1px solid var(--border-light); border-radius:18px;
  box-shadow:0 12px 30px rgba(28,94,88,.10); margin-bottom:8px;
}}
.hop-nav-item {{
  min-height:62px; display:flex; align-items:center; gap:12px;
  padding:10px 16px; border-radius:13px; text-decoration:none !important;
  border:1px solid transparent; color:var(--text-hi) !important;
  font-family:{FONT_BODY}; font-size:13px; font-weight:700;
  transition:transform .18s ease, box-shadow .18s ease, background .18s ease;
}}
.hop-nav-item:hover {{
  background:#F4FBF9; border-color:var(--border-light);
  transform:translateY(-2px); box-shadow:0 9px 22px rgba(28,94,88,.10);
}}
.hop-nav-item.active {{
  background:linear-gradient(135deg,var(--teal),var(--teal-dark));
  color:#FFFFFF !important; box-shadow:0 12px 26px rgba(20,156,148,.26);
}}
.nav-icon-box {{
  width:50px; height:50px; flex:0 0 50px; border-radius:12px;
  display:flex; align-items:center; justify-content:center;
  background:#FFFFFF; border:1px solid rgba(255,255,255,.75);
  box-shadow:0 5px 14px rgba(20,112,107,.13);
}}
.hop-nav-item:not(.active) .nav-icon-box {{ background:#ECF8F5; border-color:#D2ECE7; }}
.nav-icon-img {{ width:34px; height:34px; object-fit:contain; display:block; }}
@media(max-width:850px) {{
  .hop-nav-shell {{ grid-template-columns:1fr; }}
}}

/* Section headings */
.section-row {{ display:flex; align-items:flex-end; justify-content:space-between; gap:10px; flex-wrap:wrap; margin:30px 0 13px; }}
.section-title {{ font-family:{FONT_DISPLAY}; font-size:17px; font-weight:700; color:var(--text-hi); }}
.section-desc {{ color:var(--teal-dark); font-size:12.5px; font-weight:520; line-height:1.55; max-width:760px; margin-top:4px; }}
.section-tag {{
  font-family:{FONT_MONO}; font-size:10px; letter-spacing:.4px;
  color:var(--teal-dark); background:#E7F7F3;
  border:1px solid #C9EAE4; border-radius:7px; padding:5px 9px;
}}

/* [DESIGN 04] KPI and information cards */
.hop-card, .kpi-card, .insight-card {{
  position:relative; overflow:hidden;
  background:linear-gradient(180deg,#FFFFFF 0%,#FBFEFD 100%);
  border:1px solid var(--border-light); border-radius:18px;
  padding:20px 21px; box-shadow:var(--shadow);
}}
.hop-card::before, .kpi-card::before, .insight-card::before {{
  content:''; position:absolute; left:0; right:0; top:0; height:3px;
  background:linear-gradient(90deg,var(--teal),var(--mint)); opacity:.75;
}}
.kpi-label {{ color:var(--teal-dark); font-size:11px; font-weight:700; letter-spacing:.55px; text-transform:uppercase; }}
.kpi-value {{ color:var(--text-hi); font-family:{FONT_MONO}; font-size:30px; font-weight:650; margin-top:10px; }}
.kpi-foot {{ color:var(--teal-dark); font-size:11.5px; margin-top:8px; line-height:1.45; }}
.kpi-icon {{
  position:absolute; top:16px; right:17px; width:60px; height:60px;
  border-radius:16px; background:#E7F7F3; border:1px solid #D0ECE7;
  display:flex; align-items:center; justify-content:center;
}}
.kpi-icon .ui-icon {{ width:36px; height:36px; }}
.card-title {{ font-family:{FONT_DISPLAY}; font-size:14px; font-weight:700; color:var(--text-hi); }}
.card-sub {{ color:var(--teal-dark); font-size:11.7px; margin-top:5px; line-height:1.5; }}

/* Plotly containers act as clean white chart cards */
div[data-testid="stPlotlyChart"] {{
  background:#FFFFFF; border:1.35px solid #A9D5CF;
  border-radius:20px; padding:10px 11px; box-shadow:var(--shadow);
  transition:transform .18s ease, box-shadow .18s ease;
}}
div[data-testid="stPlotlyChart"]:hover {{
  transform:translateY(-2px);
  box-shadow:0 26px 58px rgba(28,94,88,.24), 0 7px 16px rgba(28,94,88,.12);
}}
/* Sankey stays flat by request; only its border remains. */
.st-key-sankey_chart div[data-testid="stPlotlyChart"] {{
  box-shadow:none !important; transform:none !important;
}}
/* Prevent an empty Plotly title object from rendering as the word undefined. */
.g-gtitle {{ display:none !important; }}


/* Dataframe, form, and input styling */
[data-testid="stDataFrame"] {{
  background:#FFFFFF; border:1px solid var(--border-light);
  border-radius:16px; overflow:hidden; box-shadow:var(--shadow);
}}
[data-testid="stForm"] {{
  background:linear-gradient(180deg,#FFFFFF,#FBFEFD);
  border:1px solid var(--border-light); border-radius:18px;
  padding:18px 19px; box-shadow:var(--shadow);
}}
[data-baseweb="select"] > div, [data-baseweb="input"] > div,
[data-testid="stNumberInput"] input, [data-testid="stDateInput"] input {{
  background:var(--surface-alt) !important;
  border-color:var(--border-light) !important;
  color:var(--text-hi) !important;
  border-radius:10px !important;
}}
[data-baseweb="select"] > div:focus-within, [data-baseweb="input"] > div:focus-within {{
  border-color:var(--teal) !important;
  box-shadow:0 0 0 3px rgba(20,156,148,.10) !important;
}}
[data-testid="stSlider"] [role="slider"] {{ background:var(--teal) !important; }}
[data-testid="stCheckbox"] svg {{ color:var(--teal) !important; }}
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] button {{
  background:linear-gradient(135deg,var(--teal),var(--teal-dark));
  color:#FFFFFF; border:0; border-radius:10px;
  font-weight:700; min-height:39px; box-shadow:0 8px 18px rgba(20,156,148,.16);
}}
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] button:hover {{
  filter:brightness(1.04); color:#FFFFFF; transform:translateY(-1px);
}}

/* Sidebar */
[data-testid="stSidebar"] {{
  background:linear-gradient(180deg,#F5FCFA,#EAF7F4);
  border-right:1px solid var(--border-light);
}}
[data-testid="stSidebar"] * {{ color:var(--text-mid); }}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{ color:var(--text-hi); }}

/* Streamlit alerts */
[data-testid="stAlert"] {{ border-radius:14px; border:1px solid var(--border-light); }}

/* Status badges */
.badge {{ display:inline-block; border-radius:999px; padding:4px 9px; font-size:10.5px; font-weight:700; }}
.badge-green {{ color:var(--teal-dark); background:#E1F6F1; }}
.badge-amber {{ color:#9B681D; background:#FFF2D8; }}
.badge-red {{ color:#A83F51; background:#FCE7EB; }}
.badge-violet {{ color:#5966B8; background:#EEF0FF; }}

/* Stronger readability for Streamlit captions and helper text */
[data-testid="stCaptionContainer"] p,
[data-testid="stWidgetLabel"] p,
small {{
  color:var(--teal-dark) !important;
  font-weight:520 !important;
}}

/* Insight cards with large, replaceable icons */
.insight-head {{ display:flex; align-items:center; justify-content:space-between; gap:12px; }}
.insight-icon-box {{
  width:64px; height:64px; flex:0 0 64px; border-radius:17px;
  display:flex; align-items:center; justify-content:center;
  background:linear-gradient(145deg,#F5F1FF,#FFFFFF);
  border:1px solid #DED8FF; box-shadow:0 10px 24px rgba(118,130,216,.16);
}}
.insight-icon-img {{ width:39px; height:39px; object-fit:contain; display:block; }}
.insight-card {{ min-height:158px; padding-right:20px; }}
.insight-card .card-title {{ margin-top:12px; font-size:15px; }}
.insight-card .card-sub {{ font-size:12.5px; line-height:1.55; max-width:88%; }}


/* Matching form headings with large custom icons */
.panel-heading {{
  display:flex; align-items:center; gap:14px; margin:1px 0 17px;
}}
.panel-icon-box {{
  width:62px; height:62px; flex:0 0 62px; border-radius:17px;
  display:flex; align-items:center; justify-content:center;
  background:linear-gradient(145deg,#EFF8FF,#FFFFFF);
  border:1px solid #D7E6F4;
  box-shadow:0 11px 25px rgba(82,112,148,.15);
}}
.panel-icon-img {{ width:39px; height:39px; object-fit:contain; display:block; }}
.panel-heading-title {{
  font-family:var(--font-display, 'Encode Sans');
  color:var(--text-hi); font-size:19px; line-height:1.2; font-weight:700;
}}
.panel-heading-sub {{
  color:var(--teal-dark); font-size:11.5px; line-height:1.4;
  font-weight:520; margin-top:4px;
}}

/* Footer */
.hop-footer {{
  margin-top:52px; padding:19px 20px;
  background:rgba(255,255,255,.75); border:1px solid var(--border-light);
  border-radius:14px; color:var(--teal-dark); font-size:11px; text-align:center;
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =============================================================================
# DATA LOADING AND VALIDATION
# =============================================================================
REQUIRED_FILES = {
    "company": "company.parquet",
    "talent_request": "talent_request.parquet",
    "student_all": "student_all.parquet",
    "status_student": "status_student.parquet",
    "tracking_company": "tracking_company.parquet",
    "tracking_student": "tracking_student.parquet",
}


@st.cache_data(show_spinner=False)
def load_data(clean_dir: str) -> dict[str, pd.DataFrame]:
    """Load all parquet tables produced by etl.py."""
    folder = Path(clean_dir)
    missing = [filename for filename in REQUIRED_FILES.values() if not (folder / filename).exists()]
    if missing:
        raise FileNotFoundError(
            "File hasil ETL belum lengkap: " + ", ".join(missing)
        )

    tables = {
        name: pd.read_parquet(folder / filename)
        for name, filename in REQUIRED_FILES.items()
    }

    # Standardize date columns again for safety if parquet was generated elsewhere.
    date_columns = {
        "company": ["created_at"],
        "talent_request": ["request_date"],
        "status_student": ["sync_date"],
        "tracking_company": ["request_date", "send_date"],
        "tracking_student": ["last_update"],
    }
    for table_name, columns in date_columns.items():
        for column in columns:
            if column in tables[table_name].columns:
                tables[table_name][column] = pd.to_datetime(
                    tables[table_name][column], errors="coerce"
                )

    return tables


def max_valid_date(*series_list: pd.Series) -> pd.Timestamp:
    values: list[pd.Timestamp] = []
    for series in series_list:
        converted = pd.to_datetime(series, errors="coerce").dropna()
        if not converted.empty:
            values.append(converted.max())
    return max(values) if values else pd.Timestamp.today().normalize()


def safe_divide(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def normalize_tools(value: object) -> list[str]:
    """Convert strings, lists, or arrays into a normalized list of tool names."""
    if isinstance(value, (list, tuple, set, np.ndarray)):
        raw_items = list(value)
    else:
        raw_items = re.split(r"[,;/|]", str(value or ""))
    return sorted({normalize_text(item) for item in raw_items if normalize_text(item)})


def mask_name(name: object) -> str:
    parts = str(name or "-").split()
    return " ".join(part[0] + "•" * max(len(part) - 1, 1) for part in parts)


def mask_nim(nim: object) -> str:
    text = str(nim or "-")
    return text[:4] + "•" * max(len(text) - 6, 2) + text[-2:] if len(text) > 6 else "•" * len(text)


def format_int(value: float | int) -> str:
    return f"{int(value):,}".replace(",", ".")


def format_pct(value: float) -> str:
    return f"{value:.1f}%"


try:
    DATA = load_data(str(CLEAN_DIR))
except FileNotFoundError as exc:
    st.error("Dashboard belum dapat membaca hasil ETL.")
    st.code(
        "py etl.py\npy -m streamlit run app_hop.py",
        language="bash",
    )
    st.caption(str(exc))
    st.stop()
except Exception as exc:
    st.error("Terjadi kesalahan ketika memuat data parquet.")
    st.exception(exc)
    st.stop()

company = DATA["company"].copy()
talent_request = DATA["talent_request"].copy()
student_all = DATA["student_all"].copy()
status_student = DATA["status_student"].copy()
tracking_company = DATA["tracking_company"].copy()
tracking_student = DATA["tracking_student"].copy()

DEFAULT_AS_OF = max_valid_date(
    tracking_student.get("last_update", pd.Series(dtype="datetime64[ns]")),
    tracking_company.get("send_date", pd.Series(dtype="datetime64[ns]")),
    status_student.get("sync_date", pd.Series(dtype="datetime64[ns]")),
)


# =============================================================================
# SIDEBAR SETTINGS
# =============================================================================
# These settings are operational controls, not core visual elements.
with st.sidebar:
    st.markdown("### Dashboard Settings")
    as_of_date = st.date_input(
        "Tanggal acuan analisis",
        value=DEFAULT_AS_OF.date(),
        help="Gunakan tanggal maksimum dataset agar metrik ghosting historis tetap relevan.",
    )
    privacy_mode = st.selectbox(
        "Mode tampilan data",
        ["Publik / Lomba", "Internal CDC"],
        help="Mode publik menyamarkan nama dan NIM mahasiswa.",
    )
    st.markdown("---")
    st.caption("Warna, font, radius kartu, dan tata letak dapat diubah dari blok [DESIGN] dan [LAYOUT] di file Python.")
    with st.expander("Status ikon dan aset"):
        st.caption("Kode mencari PNG/SVG di assets/, assets/icons/, dan folder project.")
        for asset_key, configured_path in ICON_PATHS.items():
            resolved_path = resolve_asset_path(configured_path)
            status_text = "Terdeteksi" if resolved_path else "Belum ditemukan"
            shown_path = str(resolved_path.relative_to(BASE_DIR)) if resolved_path else configured_path
            st.write(f"**{asset_key}** — {status_text}: `{shown_path}`")

AS_OF = pd.Timestamp(as_of_date)
IS_PUBLIC = privacy_mode == "Publik / Lomba"


# =============================================================================
# DATA MARTS AND DERIVED METRICS
# =============================================================================
@st.cache_data(show_spinner=False)
def build_placement_mart(
    tracking_student_df: pd.DataFrame,
    tracking_company_df: pd.DataFrame,
    company_df: pd.DataFrame,
) -> pd.DataFrame:
    """One row per candidate process with company master attributes."""
    mart = tracking_student_df.copy()
    tc_cols = [
        column for column in ["id_tracking_company", "id_company", "id_talent_req", "request_date", "send_date"]
        if column in tracking_company_df.columns
    ]
    mart = mart.merge(
        tracking_company_df[tc_cols].drop_duplicates("id_tracking_company"),
        on="id_tracking_company",
        how="left",
    )
    company_cols = [
        column for column in ["id_company", "company_name", "industry_sector", "kota", "company_type", "skala_perusahaan"]
        if column in company_df.columns
    ]
    mart = mart.merge(
        company_df[company_cols].drop_duplicates("id_company"),
        on="id_company",
        how="left",
        suffixes=("", "_master"),
    )
    return mart


placement_mart = build_placement_mart(tracking_student, tracking_company, company)

# Canonical outcome follows the dataset documentation.
rejection_text = placement_mart.get("rejection", pd.Series("", index=placement_mart.index)).astype(str)
progress_text = placement_mart.get("progress_student", pd.Series("", index=placement_mart.index)).astype(str)
placement_mart["canonical_outcome"] = np.select(
    [
        rejection_text.eq("Placement") | progress_text.eq("Placement"),
        rejection_text.eq("Ghosting") | progress_text.eq("Ghosting"),
        rejection_text.str.startswith("Rejection") | progress_text.eq("Rejected"),
    ],
    ["Placement", "Ghosting", "Rejected"],
    default="On Progress",
)

# One definitive placement record per student, taking the most recent update.
placed_processes = placement_mart[placement_mart["canonical_outcome"] == "Placement"].copy()
placed_processes = placed_processes.sort_values("last_update", na_position="first")
placed_unique = placed_processes.drop_duplicates("NIM", keep="last")
placed_nims = set(placed_unique["NIM"].astype(str))

# Student readiness mart, one row per student.
student_cols = [column for column in student_all.columns if column not in {"semester", "program_studi", "nama"}]
readiness = status_student.merge(
    student_all[student_cols].drop_duplicates("NIM"),
    on="NIM",
    how="left",
    suffixes=("", "_master"),
)
readiness["NIM"] = readiness["NIM"].astype(str)
readiness["is_placed"] = readiness["NIM"].isin(placed_nims) | readiness.get("ketersediaan", "").eq("Placed")
readiness["basic_eligible"] = (
    readiness.get("status", "").eq("Active")
    & readiness.get("ketersediaan", "").eq("Available")
    & readiness.get("CV", "").eq("Ada")
)
readiness["tools_normalized"] = readiness.get("tools_list", readiness.get("tools", "")).apply(normalize_tools)


# =============================================================================
# CHART HELPERS
# =============================================================================
PLOTLY_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
    "scrollZoom": False,
}


def style_figure(fig: go.Figure, height: int | None = None) -> go.Figure:
    """Apply the light visual language and explicitly clear empty Plotly titles.

    An empty title object can occasionally be rendered by Plotly as the word
    `undefined`; title_text="" and the .g-gtitle CSS guard prevent that.
    """
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Roboto Flex", "color": TEAL_DARK, "size": 12},
        title_text="",
        margin={"l": 18, "r": 18, "t": 18, "b": 18},
        hoverlabel={
            "bgcolor": SURFACE,
            "font_color": TEXT_HIGH,
            "bordercolor": BORDER_STRONG,
            "font_family": "Roboto Flex",
        },
        height=height,
    )
    fig.update_xaxes(
        gridcolor="rgba(20,112,107,.08)",
        zerolinecolor="rgba(20,112,107,.10)",
        linecolor="rgba(20,112,107,.10)",
        tickfont={"color": TEAL_DARK, "family": "Roboto Flex", "size": 12},
        title_font={"color": TEAL_DARK, "family": "Encode Sans", "size": 13},
    )
    fig.update_yaxes(
        gridcolor="rgba(20,112,107,.08)",
        zerolinecolor="rgba(20,112,107,.10)",
        linecolor="rgba(20,112,107,.10)",
        tickfont={"color": TEAL_DARK, "family": "Roboto Flex", "size": 12},
        title_font={"color": TEAL_DARK, "family": "Encode Sans", "size": 13},
    )
    return fig


def section_header(title: str, description: str, tag: str) -> None:
    st.markdown(
        f"""
        <div class="section-row">
          <div>
            <div class="section-title">{html.escape(title)}</div>
            <div class="section-desc">{html.escape(description)}</div>
          </div>
          <span class="section-tag">{html.escape(tag)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, foot: str, icon_key: str) -> None:
    """Render a KPI card with a replaceable icon from ICON_PATHS."""
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-icon">{icon_html(icon_key)}</div>
          <div class="kpi-label">{html.escape(label)}</div>
          <div class="kpi-value">{html.escape(value)}</div>
          <div class="kpi-foot">{html.escape(foot)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def panel_heading(title: str, subtitle: str, icon_key: str) -> None:
    """Heading used inside matching panels with a large replaceable icon."""
    st.markdown(
        f"""
        <div class="panel-heading">
          <span class="panel-icon-box">{icon_html(icon_key, "panel-icon-img")}</span>
          <span>
            <div class="panel-heading-title">{html.escape(title)}</div>
            <div class="panel-heading-sub">{html.escape(subtitle)}</div>
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(
    title: str,
    text: str,
    badge: str = "INSIGHT",
    icon_key: str = "talent_source",
) -> None:
    """Render an insight card with a large replaceable PNG/SVG icon."""
    st.markdown(
        f"""
        <div class="insight-card">
          <div class="insight-head">
            <span class="badge badge-violet">{html.escape(badge)}</span>
            <span class="insight-icon-box">{icon_html(icon_key, "insight-icon-img")}</span>
          </div>
          <div class="card-title">{html.escape(title)}</div>
          <div class="card-sub">{html.escape(text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# HEADER AND NAVIGATION
# =============================================================================
st.markdown(
    f"""
    <div class="hop-topbar">
      <div class="hop-brand">
        <div class="hop-mark">{icon_html("logo", "brand-logo")}</div>
        <div>
          <div class="hop-title">{html.escape(DASHBOARD_TITLE)}</div>
          <div class="hop-sub">{html.escape(DASHBOARD_SUBTITLE)}</div>
        </div>
      </div>
      <div class="hop-asof"><span class="live-dot"></span> DATA PER {AS_OF.strftime('%d %b %Y').upper()}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# [DESIGN 05] Custom navigation with user-replaceable icons.
PAGE_OPTIONS = {
    "executive": "1 Ringkasan Penempatan",
    "matching": "2 Temukan Kandidat",
    "operations": "3 Pantau Proses Seleksi",
}
current_page_key = st.query_params.get("page", "executive")
if current_page_key not in PAGE_OPTIONS:
    current_page_key = "executive"
page = PAGE_OPTIONS[current_page_key]

navigation_items = [
    ("executive", "nav_executive", PAGE_OPTIONS["executive"]),
    ("matching", "nav_matching", PAGE_OPTIONS["matching"]),
    ("operations", "nav_operations", PAGE_OPTIONS["operations"]),
]
nav_html = ['<div class="hop-nav-shell">']
for key, icon_key, label in navigation_items:
    active_class = " active" if key == current_page_key else ""
    nav_html.append(
        f'<a class="hop-nav-item{active_class}" href="?page={key}" target="_self">'
        f'<span class="nav-icon-box">{icon_html(icon_key, "nav-icon-img")}</span>'
        f'<span>{html.escape(label)}</span></a>'
    )
nav_html.append('</div>')
st.markdown("".join(nav_html), unsafe_allow_html=True)

st.caption(f"Tim: **{TEAM_NAME}**  ·  Nomor peserta: **{PARTICIPANT_NUMBER}**")


# =============================================================================
# PAGE 1: EXECUTIVE VIEW
# Covers BT-04 and BT-07.
# =============================================================================
if current_page_key == "executive":
    total_students = student_all["NIM"].astype(str).nunique()
    active_students = readiness.loc[readiness.get("status", "").eq("Active"), "NIM"].nunique()
    total_placed = len(placed_nims)
    placement_rate = safe_divide(total_placed, active_students) * 100
    total_companies = company["id_company"].nunique()
    total_requests = talent_request["id_talent_req"].nunique()

    valid_send = tracking_company.dropna(subset=["request_date", "send_date"]).copy()
    valid_send["days_to_send"] = (valid_send["send_date"] - valid_send["request_date"]).dt.days
    avg_send_days = valid_send.loc[valid_send["days_to_send"] >= 0, "days_to_send"].mean()

    # [LAYOUT 01] Change 4 columns to 2 or 3 columns to alter the KPI grid.
    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1:
        kpi_card("Mahasiswa Aktif", format_int(active_students), f"{format_int(total_students)} mahasiswa pada master data", "student")
    with k2:
        kpi_card("Mahasiswa Placed", format_int(total_placed), f"Placement rate {format_pct(placement_rate)}", "placement")
    with k3:
        kpi_card("Perusahaan Mitra", format_int(total_companies), f"{format_int(total_requests)} talent request tercatat", "company")
    with k4:
        send_text = f"{avg_send_days:.1f} hari" if pd.notna(avg_send_days) else "N/A"
        kpi_card("Rata-rata Time to Send", send_text, "Dari request diterima sampai kandidat dikirim", "clock")

    # -------------------------------------------------------------------------
    # Sankey conversion flow
    # -------------------------------------------------------------------------
    section_header(
        "Alur Konversi Talenta",
        "Perjalanan mahasiswa dari master data, status aktif, ketersediaan, hingga sektor penempatan.",
        "BT-04 · SANKEY",
    )

    status_dedup = status_student.sort_values("sync_date", na_position="first").drop_duplicates("NIM", keep="last")
    status_counts = status_dedup.get("status", pd.Series(dtype=str)).fillna("Belum diketahui").value_counts()

    active_set = set(status_dedup.loc[status_dedup.get("status", "").eq("Active"), "NIM"].astype(str))
    placed_active_set = placed_nims.intersection(active_set)
    available_active_set = set(
        status_dedup.loc[
            status_dedup.get("status", "").eq("Active")
            & status_dedup.get("ketersediaan", "").eq("Available"),
            "NIM",
        ].astype(str)
    ) - placed_active_set
    other_active_set = active_set - placed_active_set - available_active_set

    placement_sector = placed_unique[placed_unique["NIM"].astype(str).isin(placed_active_set)].copy()
    placement_sector["industry_sector"] = placement_sector.get("industry_sector", "Tidak diketahui").fillna("Tidak diketahui")
    sector_counts = placement_sector.groupby("industry_sector")["NIM"].nunique().sort_values(ascending=False)
    top_sectors = sector_counts.head(7)
    remainder = max(len(placed_active_set) - int(top_sectors.sum()), 0)
    if remainder:
        top_sectors.loc["Sektor lainnya / belum terpetakan"] = remainder

    labels = ["Semua Mahasiswa"]
    sources: list[int] = []
    targets: list[int] = []
    values: list[int] = []
    node_colors = [CHART_COLORS[0]]
    link_colors: list[str] = []

    def rgba(hex_color: str, alpha: float = 0.24) -> str:
        clean = hex_color.lstrip("#")
        red, green, blue = int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)
        return f"rgba({red},{green},{blue},{alpha})"

    def add_link(source_label: str, target_label: str, value: int, color: str) -> None:
        if value <= 0:
            return
        if source_label not in labels:
            labels.append(source_label)
            node_colors.append(CHART_COLORS[len(labels) % len(CHART_COLORS)])
        if target_label not in labels:
            labels.append(target_label)
            node_colors.append(color)
        sources.append(labels.index(source_label))
        targets.append(labels.index(target_label))
        values.append(int(value))
        link_colors.append(rgba(color, 0.22))

    known_status_total = 0
    status_color = {"Active": CHART_COLORS[6], "Inactive": CHART_COLORS[8], "Cuti": CHART_COLORS[3], "Lulus": CHART_COLORS[1]}
    for status_name, count in status_counts.items():
        known_status_total += int(count)
        add_link("Semua Mahasiswa", str(status_name), int(count), status_color.get(str(status_name), TEXT_LOW))
    missing_status = max(total_students - known_status_total, 0)
    add_link("Semua Mahasiswa", "Belum terhubung ke status", missing_status, TEXT_LOW)

    add_link("Active", "Placed", len(placed_active_set), CHART_COLORS[0])
    add_link("Active", "Available", len(available_active_set), CHART_COLORS[5])
    add_link("Active", "Status aktif lainnya", len(other_active_set), CHART_COLORS[2])
    for sector, count in top_sectors.items():
        add_link("Placed", str(sector), int(count), CHART_COLORS[(len(labels) + int(count)) % len(CHART_COLORS)])

    sankey = go.Figure(
        go.Sankey(
            arrangement="snap",
            node={
                "pad": 18,
                "thickness": 18,
                "line": {"color": "rgba(20,112,107,.18)", "width": 0.8},
                "label": [f"<b>{label}</b>" for label in labels],
                "color": node_colors,
            },
            link={
                "source": sources,
                "target": targets,
                "value": values,
                "color": link_colors,
            },
        )
    )
    style_figure(sankey, 480)
    sankey.update_layout(
        font={"family": "Encode Sans", "size": 12, "color": TEXT_HIGH},
        title_text="",
    )
    st.plotly_chart(
        sankey,
        use_container_width=True,
        config=PLOTLY_CONFIG,
        key="sankey_chart",
    )

    # -------------------------------------------------------------------------
    # [LAYOUT 02] Change [1.25, 0.85] to adjust the width of the two panels.
    # -------------------------------------------------------------------------
    left, right = st.columns([1.25, 0.85], gap="large")

    with left:
        section_header(
            "Penyerapan per Program Studi",
            "Jumlah mahasiswa placed dan placement rate berdasarkan program studi.",
            "BT-07 · TOP 15",
        )
        prodi_summary = (
            readiness.groupby("program_studi", dropna=False)
            .agg(
                total_students=("NIM", "nunique"),
                placed_students=("is_placed", "sum"),
            )
            .reset_index()
        )
        prodi_summary["placement_rate"] = (
            prodi_summary["placed_students"] / prodi_summary["total_students"] * 100
        ).fillna(0)
        prodi_summary = prodi_summary.sort_values("placed_students", ascending=False).head(15).sort_values("placed_students")
        fig_prodi = px.bar(
            prodi_summary,
            x="placed_students",
            y="program_studi",
            orientation="h",
            text="placed_students",
            custom_data=["placement_rate", "total_students"],
        )
        fig_prodi.update_traces(
            marker_color=[CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(prodi_summary))],
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b><br>Placed: %{x:,.0f}<br>Total: %{customdata[1]:,.0f}"
                "<br>Placement rate: %{customdata[0]:.1f}%<extra></extra>"
            ),
        )
        style_figure(fig_prodi, 520)
        fig_prodi.update_layout(xaxis_title="Mahasiswa Placed", yaxis_title=None)
        st.plotly_chart(fig_prodi, use_container_width=True, config=PLOTLY_CONFIG)

    with right:
        section_header(
            "Sinkronisasi Domisili dan Lokasi Kerja",
            "Perbandingan penempatan pada kota yang sama dengan penempatan lintas kota.",
            "BT-04 · MOBILITY",
        )
        relocation = placed_unique.merge(
            readiness[["NIM", "domisili"]].drop_duplicates("NIM"),
            on="NIM",
            how="left",
        )
        relocation = relocation.dropna(subset=["domisili", "kota"])
        relocation["same_city"] = (
            relocation["domisili"].astype(str).str.strip().str.lower()
            == relocation["kota"].astype(str).str.strip().str.lower()
        )
        same_city = int(relocation["same_city"].sum())
        relocate = int((~relocation["same_city"]).sum())
        donut_data = pd.DataFrame(
            {"Kategori": ["Kota sama", "Relokasi"], "Jumlah": [same_city, relocate]}
        )
        fig_donut = px.pie(
            donut_data,
            names="Kategori",
            values="Jumlah",
            hole=0.64,
            color="Kategori",
            color_discrete_map={"Kota sama": CHART_COLORS[5], "Relokasi": CHART_COLORS[1]},
        )
        fig_donut.update_traces(textinfo="percent+label", hovertemplate="%{label}: %{value:,.0f}<extra></extra>")
        style_figure(fig_donut, 300)
        fig_donut.update_layout(showlegend=False)
        st.plotly_chart(fig_donut, use_container_width=True, config=PLOTLY_CONFIG)

        st.markdown('<div class="card-title">Top Sektor Penempatan</div>', unsafe_allow_html=True)
        sector_show = sector_counts.head(6).rename_axis("Sektor").reset_index(name="Placement")
        fig_sector = px.bar(sector_show.sort_values("Placement"), x="Placement", y="Sektor", orientation="h")
        fig_sector.update_traces(marker_color=[CHART_COLORS[(i + 2) % len(CHART_COLORS)] for i in range(len(sector_show))], hovertemplate="%{y}: %{x:,.0f}<extra></extra>")
        style_figure(fig_sector, 300)
        fig_sector.update_layout(xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig_sector, use_container_width=True, config=PLOTLY_CONFIG)

    # -------------------------------------------------------------------------
    # Geographic company distribution
    # -------------------------------------------------------------------------
    section_header(
        "Peta Sebaran Perusahaan Mitra",
        "Ukuran titik menunjukkan jumlah perusahaan terdaftar pada setiap kota yang dapat dipetakan.",
        "GEO",
    )

    # Add or edit coordinates here when the dataset contains new cities.
    CITY_COORDINATES = {
        "Jakarta": (-6.2088, 106.8456),
        "Surakarta": (-7.5755, 110.8243),
        "Yogyakarta": (-7.7956, 110.3695),
        "Semarang": (-6.9667, 110.4167),
        "Bandung": (-6.9175, 107.6191),
        "Surabaya": (-7.2575, 112.7521),
        "Malang": (-7.9666, 112.6326),
        "Bekasi": (-6.2383, 106.9756),
        "Tangerang": (-6.1783, 106.6319),
        "Depok": (-6.4025, 106.7942),
        "Bogor": (-6.5950, 106.8166),
        "Karanganyar": (-7.5961, 110.9508),
        "Klaten": (-7.7058, 110.6067),
        "Boyolali": (-7.5331, 110.5958),
        "Magelang": (-7.4797, 110.2177),
    }
    city_counts = company.get("kota", pd.Series(dtype=str)).value_counts().rename_axis("kota").reset_index(name="jumlah_perusahaan")
    city_counts["lat"] = city_counts["kota"].map(lambda x: CITY_COORDINATES.get(str(x), (np.nan, np.nan))[0])
    city_counts["lon"] = city_counts["kota"].map(lambda x: CITY_COORDINATES.get(str(x), (np.nan, np.nan))[1])
    geo_data = city_counts.dropna(subset=["lat", "lon"])

    if not geo_data.empty:
        map_fig = px.scatter_mapbox(
            geo_data,
            lat="lat",
            lon="lon",
            size="jumlah_perusahaan",
            color="jumlah_perusahaan",
            hover_name="kota",
            hover_data={"lat": False, "lon": False, "jumlah_perusahaan": ":,.0f"},
            color_continuous_scale=[[0, CHART_COLORS[5]], [0.5, CHART_COLORS[1]], [1, CHART_COLORS[2]]],
            size_max=42,
            zoom=4.3,
            center={"lat": -7.2, "lon": 110.5},
        )
        map_fig.update_layout(mapbox_style="carto-positron", coloraxis_showscale=False)
        style_figure(map_fig, 430)
        st.plotly_chart(map_fig, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        st.info("Tidak ada kota yang cocok dengan kamus koordinat pada bagian CITY_COORDINATES.")

    # -------------------------------------------------------------------------
    # Partner success table
    # -------------------------------------------------------------------------
    section_header(
        "Mitra dengan Tingkat Keberhasilan Tertinggi",
        "Success rate dihitung dari proses kandidat yang berakhir Placement. Minimum lima kandidat dikirim.",
        "BT-04 · PARTNER",
    )
    partner_summary = (
        placement_mart.groupby(["id_company", "company_name", "industry_sector", "kota"], dropna=False)
        .agg(
            candidates_sent=("id_tracking_student", "nunique"),
            placed=("canonical_outcome", lambda s: int((s == "Placement").sum())),
            ghosting=("canonical_outcome", lambda s: int((s == "Ghosting").sum())),
        )
        .reset_index()
    )
    partner_summary = partner_summary[partner_summary["candidates_sent"] >= 5].copy()
    partner_summary["success_rate"] = partner_summary["placed"] / partner_summary["candidates_sent"] * 100
    partner_summary["ghosting_rate"] = partner_summary["ghosting"] / partner_summary["candidates_sent"] * 100
    partner_summary = partner_summary.sort_values(["success_rate", "placed"], ascending=False).head(20)
    partner_display = partner_summary.rename(
        columns={
            "company_name": "Perusahaan",
            "industry_sector": "Sektor",
            "kota": "Kota",
            "candidates_sent": "Dikirim",
            "placed": "Placed",
            "success_rate": "Success Rate (%)",
            "ghosting_rate": "Ghosting Rate (%)",
        }
    )[["Perusahaan", "Sektor", "Kota", "Dikirim", "Placed", "Success Rate (%)", "Ghosting Rate (%)"]]
    st.dataframe(
        partner_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Success Rate (%)": st.column_config.ProgressColumn(
                "Success Rate (%)", min_value=0, max_value=100, format="%.1f%%"
            ),
            "Ghosting Rate (%)": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )

    # Dynamic decision-oriented insights
    if not prodi_summary.empty and not partner_summary.empty:
        top_prodi = prodi_summary.sort_values("placed_students", ascending=False).iloc[0]
        best_partner = partner_summary.iloc[0]
        i1, i2, i3 = st.columns(3, gap="medium")
        with i1:
            insight_card(
                "Sumber talenta utama",
                f"{top_prodi['program_studi']} menyumbang {format_int(top_prodi['placed_students'])} mahasiswa placed dengan rate {top_prodi['placement_rate']:.1f}%.",
                icon_key="talent_source",
            )
        with i2:
            insight_card(
                "Mitra paling efektif",
                f"{best_partner['company_name']} memiliki success rate {best_partner['success_rate']:.1f}% dari {format_int(best_partner['candidates_sent'])} kandidat.",
                icon_key="partner_effective",
            )
        with i3:
            mobility_rate = safe_divide(relocate, same_city + relocate) * 100
            insight_card(
                "Mobilitas penempatan",
                f"{mobility_rate:.1f}% placement terpetakan berlangsung di luar kota domisili mahasiswa.",
                icon_key="mobility",
            )


# =============================================================================
# PAGE 2: TALENT MATCHING SANDBOX
# Covers BT-01, BT-03, BT-06, and BT-08.
# =============================================================================
elif current_page_key == "matching":
    section_header(
        "Talent Matching & Eligibility Sandbox",
        "Pilih talent request, terapkan filter kelayakan, lalu hitung indeks kecocokan berbobot terhadap mahasiswa available.",
        "BT-01 · BT-03 · BT-06 · BT-08",
    )

    # Request mart with priority score.
    request_mart = talent_request.merge(
        company[["id_company", "kota", "company_name", "industry_sector"]].drop_duplicates("id_company"),
        on="id_company",
        how="left",
        suffixes=("", "_master"),
    )
    request_mart["request_age"] = (AS_OF - request_mart["request_date"]).dt.days.clip(lower=0)
    request_mart["priority_score"] = request_mart["request_age"] * 0.60 + request_mart["headcount"].fillna(0) * 0.40

    latest_tc = tracking_company.sort_values("request_date", na_position="first").drop_duplicates("id_talent_req", keep="last")
    request_mart = request_mart.merge(
        latest_tc[["id_talent_req", "progress", "send_date"]],
        on="id_talent_req",
        how="left",
    )
    request_mart["is_open"] = request_mart["progress"].fillna("Draft").ne("Closed")
    open_requests = request_mart[request_mart["is_open"]].copy()

    # Sync status for BT-08.
    sync_lag = (AS_OF - readiness["sync_date"]).dt.days
    sync_summary = {
        "Sinkron ≤30 hari": int((sync_lag <= 30).sum()),
        "Perlu perhatian 31-90 hari": int(((sync_lag > 30) & (sync_lag <= 90)).sum()),
        "Usang >90 hari": int((sync_lag > 90).sum()),
    }

    s1, s2, s3 = st.columns(3, gap="large")

    with s1:
        kpi_card("Data Sinkron", format_int(sync_summary["Sinkron ≤30 hari"]), "Sync lag maksimal 30 hari", "sync")

    with s2:
        kpi_card("Perlu Perhatian", format_int(sync_summary["Perlu perhatian 31-90 hari"]), "Sync lag 31 sampai 90 hari", "attention")

    with s3:
        kpi_card("Data Usang", format_int(sync_summary["Usang >90 hari"]), "Sync lag lebih dari 90 hari", "danger")

    st.markdown(
        '<div style="height:28px;"></div>',
        unsafe_allow_html=True,
    )

    # [LAYOUT 03] The HTML uses three visual panels. In Streamlit, filters and
    # request selection are grouped in one form, then results use the full width.
    with st.form("matching_form"):
        f1, f2, f3 = st.columns([1.05, 1.05, 1.2], gap="large")

        with f1:
            panel_heading("Panel Kelayakan", "Atur syarat minimum kandidat", "panel_eligibility")
            ipk_min = st.slider("IPK minimum", 2.00, 4.00, 2.50, 0.05)
            semester_min = st.slider("Semester aktif minimum", 1, 14, 1)
            cv_required = st.checkbox("Wajib memiliki CV", value=True)
            portfolio_required = st.checkbox("Wajib memiliki portofolio", value=False)

        with f2:
            panel_heading("Filter Mahasiswa", "Persempit kandidat sesuai kebutuhan", "panel_filter")
            domicile_options = ["Semua kota"] + sorted(readiness["domisili"].dropna().astype(str).unique().tolist())
            prodi_options = ["Semua program studi"] + sorted(readiness["program_studi"].dropna().astype(str).unique().tolist())
            domicile_filter = st.selectbox("Domisili", domicile_options)
            prodi_filter = st.selectbox("Program studi", prodi_options)
            placement_filter = st.selectbox(
                "Jenis penempatan request",
                ["Semua", "Magang", "Part-time", "Full-time"],
            )

        with f3:
            panel_heading("Permintaan Talenta Aktif", "Pilih posisi yang akan dicocokkan", "panel_request")
            request_view = open_requests.copy()
            if placement_filter != "Semua":
                request_view = request_view[request_view["jenis_penempatan"] == placement_filter]
            request_view = request_view.sort_values("priority_score", ascending=False).head(1000)
            # Fallback keeps the form usable if a category has no open request.
            if request_view.empty:
                st.warning("Tidak ada request aktif pada jenis penempatan ini. Menampilkan seluruh request aktif.")
                request_view = open_requests.sort_values("priority_score", ascending=False).head(1000).copy()
            request_view["label"] = (
                request_view["id_talent_req"].astype(str)
                + " · "
                + request_view["nama_posisi"].astype(str)
                + " | "
                + request_view["nama_perusahaan"].astype(str)
            )
            selected_label = st.selectbox("Pilih request", request_view["label"].tolist())
            selected_request = request_view.loc[request_view["label"] == selected_label].iloc[0]
            st.caption(
                f"Prioritas {selected_request['priority_score']:.1f} · "
                f"usia request {int(selected_request['request_age'])} hari · "
                f"headcount {int(selected_request['headcount'])}"
            )

        run_matching = st.form_submit_button("Hitung Kandidat Terbaik", use_container_width=True)

    # Matching dictionaries. Add new aliases here to improve text extraction.
    TOOL_ALIASES = {
        "python": ["python"], "r": [" r ", "python/r"], "sql": ["sql"],
        "power bi": ["power bi", "powerbi"], "tableau": ["tableau"],
        "excel": ["excel", "microsoft excel"], "figma": ["figma"],
        "adobe xd": ["adobe xd"], "autocad": ["autocad"],
        "solidworks": ["solidworks"], "sap": ["sap"], "spss": ["spss"],
        "javascript": ["javascript"], "react": ["react"], "html/css": ["html/css", "html", "css"],
        "git": ["git"], "seo": ["seo"], "matlab": ["matlab"],
        "arcgis": ["arcgis"], "qgis": ["qgis"], "myob": ["myob"],
        "accurate": ["accurate"], "canva": ["canva"],
    }

    def extract_request_tools(text: object) -> list[str]:
        padded = f" {normalize_text(text)} "
        result = []
        for canonical, aliases in TOOL_ALIASES.items():
            if any(alias in padded for alias in aliases):
                result.append(canonical)
        return result

    def jaccard(left: Iterable[str], right: Iterable[str]) -> float:
        a, b = set(left), set(right)
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def prodi_similarity(student_prodi: object, requirement: object) -> float:
        student_value = normalize_text(student_prodi)
        needed = [normalize_text(item) for item in str(requirement or "").split(",")]
        if student_value in needed:
            return 1.0
        student_words = {word for word in student_value.split() if len(word) > 3}
        if any(student_words.intersection(set(item.split())) for item in needed):
            return 0.5
        return 0.0

    def compute_matching_results(request_row: pd.Series) -> pd.DataFrame:
        pool = readiness[
            readiness.get("status", "").eq("Active")
            & readiness.get("ketersediaan", "").eq("Available")
            & readiness["IPK"].ge(ipk_min)
            & readiness["semester"].ge(semester_min)
        ].copy()
        if cv_required:
            pool = pool[pool.get("CV", "").eq("Ada")]
        if portfolio_required:
            pool = pool[pool.get("portofolio", "").eq("Ada")]
        if domicile_filter != "Semua kota":
            pool = pool[pool["domisili"].astype(str).eq(domicile_filter)]
        if prodi_filter != "Semua program studi":
            pool = pool[pool["program_studi"].astype(str).eq(prodi_filter)]

        request_tools = extract_request_tools(request_row.get("deskripsi_requirement", ""))
        working_arrangement = normalize_text(request_row.get("working_arrangement", ""))
        request_city = normalize_text(request_row.get("kota", ""))
        minimum_semester = float(request_row.get("minimum_semester", 0) or 0)

        rows = []
        for candidate in pool.itertuples(index=False):
            candidate_data = candidate._asdict()
            candidate_tools = set(candidate_data.get("tools_normalized", []))
            tool_score = jaccard(candidate_tools, request_tools)
            academic_score = 1.0 if float(candidate_data.get("semester", 0) or 0) >= minimum_semester else 0.0
            study_score = prodi_similarity(candidate_data.get("program_studi"), request_row.get("bidang_studi_dibutuhkan"))
            location_score = 1.0 if "wfh" in working_arrangement else (
                1.0 if normalize_text(candidate_data.get("domisili")) == request_city else 0.0
            )

            # Matching formula follows the HTML prototype:
            # 40% tools + 20% semester + 25% program study + 15% location.
            total_score = (
                0.40 * tool_score
                + 0.20 * academic_score
                + 0.25 * study_score
                + 0.15 * location_score
            ) * 100
            common_tools = sorted(candidate_tools.intersection(request_tools))

            rows.append(
                {
                    "NIM": str(candidate_data.get("NIM", "")),
                    "Nama": candidate_data.get("nama", "-"),
                    "Program Studi": candidate_data.get("program_studi", "-"),
                    "Semester": candidate_data.get("semester", np.nan),
                    "IPK": candidate_data.get("IPK", np.nan),
                    "Domisili": candidate_data.get("domisili", "-"),
                    "Tools Cocok": ", ".join(common_tools) if common_tools else "-",
                    "Skor Tools": tool_score * 100,
                    "Skor Prodi": study_score * 100,
                    "Skor Lokasi": location_score * 100,
                    "Match Score (%)": total_score,
                }
            )

        result = pd.DataFrame(rows)
        if not result.empty:
            result = result.sort_values(["Match Score (%)", "IPK"], ascending=False).head(40)
        return result

    if run_matching:
        with st.spinner("Menghitung kecocokan kandidat..."):
            st.session_state["matching_results"] = compute_matching_results(selected_request)
            st.session_state["matching_request"] = selected_request.to_dict()

    if "matching_results" in st.session_state:
        result = st.session_state["matching_results"].copy()
        request_info = st.session_state["matching_request"]

        st.markdown(
            f"""
            <div class="hop-card" style="margin-top:18px;">
              <div class="card-title">{html.escape(str(request_info.get('nama_posisi', '-')))}</div>
              <div class="card-sub">
                {html.escape(str(request_info.get('nama_perusahaan', '-')))} ·
                {html.escape(str(request_info.get('jenis_penempatan', '-')))} ·
                {html.escape(str(request_info.get('working_arrangement', '-')))} ·
                headcount {int(request_info.get('headcount', 0) or 0)}
              </div>
              <div class="card-sub" style="margin-top:10px;">{html.escape(str(request_info.get('deskripsi_requirement', '-')))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if result.empty:
            st.warning("Tidak ada kandidat yang memenuhi kombinasi filter saat ini. Longgarkan filter kelayakan lalu jalankan kembali.")
        else:
            display_result = result.copy()
            if IS_PUBLIC:
                display_result["Nama"] = display_result["Nama"].map(mask_name)
                display_result["NIM"] = display_result["NIM"].map(mask_nim)

            st.dataframe(
                display_result,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "IPK": st.column_config.NumberColumn(format="%.2f"),
                    "Skor Tools": st.column_config.NumberColumn(format="%.0f%%"),
                    "Skor Prodi": st.column_config.NumberColumn(format="%.0f%%"),
                    "Skor Lokasi": st.column_config.NumberColumn(format="%.0f%%"),
                    "Match Score (%)": st.column_config.ProgressColumn(
                        "Match Score (%)", min_value=0, max_value=100, format="%.1f%%"
                    ),
                },
            )

            # Internal simulation only. It does not write to parquet.
            selection_nim = result["NIM"].map(mask_nim) if IS_PUBLIC else result["NIM"].astype(str)
            selection_name = result["Nama"].map(mask_name) if IS_PUBLIC else result["Nama"].astype(str)
            selection_labels = (
                selection_nim
                + " · "
                + selection_name
                + " · "
                + result["Match Score (%)"].round(1).astype(str)
                + "%"
            ).tolist()
            selected_candidates = st.multiselect(
                "Pilih kandidat untuk draft pengiriman",
                selection_labels,
                max_selections=int(request_info.get("headcount", 1) or 1) * 3,
            )
            if st.button("Kirim ke Draft TRACKING COMPANY", use_container_width=True):
                if selected_candidates:
                    st.success(
                        f"{len(selected_candidates)} kandidat masuk ke draft simulasi. Data parquet tidak diubah."
                    )
                else:
                    st.warning("Pilih minimal satu kandidat terlebih dahulu.")


# =============================================================================
# PAGE 3: OPERATIONAL FUNNEL AND GHOSTING
# Covers BT-02 and BT-05.
# =============================================================================
else:
    section_header(
        "Corong Rekrutmen",
        "Distribusi tahapan seleksi mahasiswa dan titik proses dengan volume kandidat terbesar.",
        "BT-02 · PIPELINE",
    )

    funnel_order = [
        "Selecting Student by Company",
        "CDC Briefing Student",
        "Study Case",
        "Interview User",
        "Final Interview",
        "Placement",
    ]
    funnel_counts = (
        tracking_student.get("progress_student", pd.Series(dtype=str))
        .value_counts()
        .reindex(funnel_order)
        .fillna(0)
        .astype(int)
    )
    funnel_df = funnel_counts.rename_axis("Tahap").reset_index(name="Kandidat")

    # [LAYOUT 04] Adjust [1.05, 0.95] to resize funnel and status panels.
    funnel_col, status_col = st.columns([1.05, 0.95], gap="large")
    with funnel_col:
        funnel_fig = go.Figure(
            go.Funnel(
                y=funnel_df["Tahap"],
                x=funnel_df["Kandidat"],
                textinfo="value+percent initial",
                marker={"color": [CHART_COLORS[5], CHART_COLORS[0], CHART_COLORS[1], CHART_COLORS[3], CHART_COLORS[2], CHART_COLORS[6]]},
                connector={"line": {"color": "#7A8A99", "width": 1.2}},
            )
        )
        style_figure(funnel_fig, 470)
        st.plotly_chart(funnel_fig, use_container_width=True, config=PLOTLY_CONFIG)

    with status_col:
        progress_dist = tracking_student.get("progress_student", pd.Series(dtype=str)).value_counts().head(12)
        progress_df = progress_dist.rename_axis("Status").reset_index(name="Jumlah").sort_values("Jumlah")
        status_fig = px.bar(progress_df, x="Jumlah", y="Status", orientation="h")
        status_fig.update_traces(
            marker_color=[
                CHART_COLORS[6] if status == "Placement"
                else CHART_COLORS[2] if status == "Rejected"
                else CHART_COLORS[4] if status == "Ghosting"
                else CHART_COLORS[i % len(CHART_COLORS)]
                for i, status in enumerate(progress_df["Status"])
            ],
            hovertemplate="%{y}: %{x:,.0f}<extra></extra>",
        )
        style_figure(status_fig, 470)
        status_fig.update_layout(xaxis_title=None, yaxis_title=None)
        st.plotly_chart(status_fig, use_container_width=True, config=PLOTLY_CONFIG)

    # Bottleneck insight based on the largest loss between adjacent displayed stages.
    losses = []
    for first, second in zip(funnel_order[:-1], funnel_order[1:]):
        losses.append((first, second, int(funnel_counts[first] - funnel_counts[second])))
    losses = sorted(losses, key=lambda item: item[2], reverse=True)
    if losses:
        first, second, loss = losses[0]
        insight_card(
            "Potensi bottleneck terbesar",
            f"Selisih volume terbesar pada corong berada antara {first} dan {second}, sebanyak {format_int(max(loss, 0))} rekam proses.",
            "BOTTLENECK",
            icon_key="bottleneck",
        )

    # -------------------------------------------------------------------------
    # Early warning system
    # -------------------------------------------------------------------------
    section_header(
        "Pusat Peringatan Dini Ghosting",
        "Risiko dihitung dari hari tanpa pembaruan. Final Interview mendapat toleransi tujuh hari lebih panjang.",
        "BT-05 · EWS",
    )

    active_stages = [
        "Selecting Student by Company",
        "CDC Briefing Student",
        "Study Case",
        "Interview User",
        "Final Interview",
        "FU 1",
        "FU 2",
        "FU 3",
    ]
    ews = tracking_student[tracking_student.get("progress_student", "").isin(active_stages)].copy()
    ews["days_idle"] = (AS_OF - ews["last_update"]).dt.days.clip(lower=0)
    ews["base_sla"] = np.where(ews["progress_student"].eq("Final Interview"), 14, 7)
    ews["risk"] = np.select(
        [
            ews["days_idle"] > ews["base_sla"] + 7,
            ews["days_idle"] > ews["base_sla"],
        ],
        ["Bahaya", "Peringatan"],
        default="Aman",
    )

    risk_counts = ews["risk"].value_counts()
    r1, r2, r3 = st.columns(3, gap="medium")
    with r1:
        kpi_card("Aman", format_int(risk_counts.get("Aman", 0)), "Masih berada dalam batas SLA", "sync")
    with r2:
        kpi_card("Peringatan", format_int(risk_counts.get("Peringatan", 0)), "Lewat SLA hingga tujuh hari", "attention")
    with r3:
        kpi_card("Bahaya", format_int(risk_counts.get("Bahaya", 0)), "Lewat SLA lebih dari tujuh hari", "danger")

    filter1, filter2, filter3 = st.columns([0.8, 1.1, 1.2], gap="medium")
    with filter1:
        risk_filter = st.selectbox("Filter risiko", ["Semua", "Bahaya", "Peringatan", "Aman"])
    with filter2:
        stage_filter = st.selectbox("Filter tahap", ["Semua"] + active_stages)
    with filter3:
        company_filter = st.selectbox(
            "Filter perusahaan",
            ["Semua"] + sorted(ews.get("company", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()),
        )

    ews_view = ews.copy()
    if risk_filter != "Semua":
        ews_view = ews_view[ews_view["risk"] == risk_filter]
    if stage_filter != "Semua":
        ews_view = ews_view[ews_view["progress_student"] == stage_filter]
    if company_filter != "Semua":
        ews_view = ews_view[ews_view["company"] == company_filter]

    risk_order = pd.CategoricalDtype(["Bahaya", "Peringatan", "Aman"], ordered=True)
    ews_view["risk"] = ews_view["risk"].astype(risk_order)
    ews_view = ews_view.sort_values(["risk", "days_idle"], ascending=[True, False]).head(200)
    ews_view["risk"] = ews_view["risk"].astype(str)
    ews_display = ews_view[
        ["NIM", "student_name", "position", "company", "progress_student", "last_update", "days_idle", "risk"]
    ].copy()
    if IS_PUBLIC:
        ews_display["student_name"] = ews_display["student_name"].map(mask_name)
        ews_display["NIM"] = ews_display["NIM"].map(mask_nim)

    ews_display = ews_display.rename(
        columns={
            "student_name": "Mahasiswa",
            "position": "Posisi",
            "company": "Perusahaan",
            "progress_student": "Tahap",
            "last_update": "Pembaruan Terakhir",
            "days_idle": "Hari Diam",
            "risk": "Risiko",
        }
    )
    st.dataframe(
        ews_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Pembaruan Terakhir": st.column_config.DateColumn(format="DD MMM YYYY"),
            "Hari Diam": st.column_config.NumberColumn(format="%d hari"),
        },
    )

    # Rejection reason chart enriches the operational diagnosis.
    section_header(
        "Diagnosis Outcome Seleksi",
        "Alasan penolakan dan ghosting membantu CDC menentukan intervensi yang paling relevan.",
        "OPERATIONAL INSIGHT",
    )
    rejection_counts = (
        tracking_student.get("rejection", pd.Series(dtype=str))
        .replace("On Progress", np.nan)
        .dropna()
        .value_counts()
        .rename_axis("Outcome")
        .reset_index(name="Jumlah")
    )
    if not rejection_counts.empty:
        rejection_fig = px.bar(rejection_counts.sort_values("Jumlah"), x="Jumlah", y="Outcome", orientation="h")
        rejection_fig.update_traces(
            marker_color=[
                CHART_COLORS[6] if outcome == "Placement"
                else CHART_COLORS[4] if outcome == "Ghosting"
                else CHART_COLORS[(i + 1) % len(CHART_COLORS)]
                for i, outcome in enumerate(rejection_counts.sort_values("Jumlah")["Outcome"])
            ],
            hovertemplate="%{y}: %{x:,.0f}<extra></extra>",
        )
        style_figure(rejection_fig, 400)
        rejection_fig.update_layout(xaxis_title=None, yaxis_title=None)
        st.plotly_chart(rejection_fig, use_container_width=True, config=PLOTLY_CONFIG)


# =============================================================================
# FOOTER
# =============================================================================
st.markdown(
    f"""
    <div class="hop-footer">
      {html.escape(DASHBOARD_TITLE)} · Dashboard Analitis CDC · SSDC 2026 ·
      {html.escape(TEAM_NAME)} · {html.escape(PARTICIPANT_NUMBER)} · Data per {AS_OF.strftime('%d %B %Y')}
    </div>
    """,
    unsafe_allow_html=True,
)
