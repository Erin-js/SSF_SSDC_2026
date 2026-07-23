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
    py -m streamlit run app.py --server.port 8502
"""

from __future__ import annotations

import base64
import html
import mimetypes
import re
from pathlib import Path
from typing import Iterable
from urllib.parse import quote

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
DASHBOARD_SUBTITLE = "Connecting Talent with Opportunity · Career Opportunity Matching and Monitoring Dashboard"
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
    "chat": "assets/chat2.png",

    # Page navigation shown in Dashboard Settings
    "nav_executive": "assets/nav/nav_executive.png",
    "nav_matching": "assets/nav/nav_matching.png",
    "nav_operations": "assets/nav/nav_operations.png",

    # Section navigation and section headings
    # Replace these files with your own PNG/SVG icons.
    "section_executive_overview": "assets/sections/executive_overview.png",
    "section_executive_flow": "assets/sections/executive_flow.png",
    "section_executive_placement": "assets/sections/executive_placement.png",
    "section_executive_partners": "assets/sections/executive_partners.png",
    "section_executive_insights": "assets/sections/executive_insights.png",
    "section_matching_setup": "assets/sections/matching_setup.png",
    "section_matching_results": "assets/sections/matching_results.png",
    "section_operations_pipeline": "assets/sections/operations_pipeline.png",
    "section_operations_delays": "assets/sections/operations_delays.png",
    "section_operations_followup": "assets/sections/operations_followup.png",
    "section_operations_outcomes": "assets/sections/operations_outcomes.png",

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

    # Page 2 summary cards
    "candidate_ready": "assets/cards/candidate_ready.svg",
    "profile_complete": "assets/cards/profile_complete.svg",
    "request_active": "assets/cards/request_active.svg",

    # Page 3 monitoring cards
    "overdue": "assets/cards/overdue.svg",
    "median_wait": "assets/cards/median_wait.svg",
    "stage_stalled": "assets/cards/stage_stalled.svg",
    "affected_companies": "assets/cards/affected_companies.svg",
    "response_progress": "assets/cards/response_progress.svg",

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
DEEP_TEAL = "#0A4F4A"        # Dark surface for headers, active navigation, and table heads
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
    initial_sidebar_state="expanded",
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
  --teal:{TEAL}; --teal-dark:{TEAL_DARK}; --deep-teal:{DEEP_TEAL};
  --teal-dim:{TEAL_DIM}; --mint:{MINT};
  --amber:{AMBER}; --crimson:{CRIMSON}; --violet:{VIOLET};
  color-scheme: light only;
  --text-hi:{TEXT_HIGH}; --text-mid:{TEXT_MID}; --text-low:{TEXT_LOW};
  --border:{BORDER}; --shadow:{SHADOW};
  --font-display:{FONT_DISPLAY}; --font-body:{FONT_BODY}; --font-mono:{FONT_MONO};
}}

html, body, [data-testid="stAppViewContainer"], .stApp {{
  color-scheme: light only !important;
  background:
    radial-gradient(circle at 8% 3%, rgba(191,235,221,.75) 0, rgba(191,235,221,0) 26%),
    radial-gradient(circle at 92% 12%, rgba(82,190,180,.15) 0, rgba(82,190,180,0) 28%),
    linear-gradient(180deg, var(--page-bg) 0%, #F8FCFB 48%, #F2FAF8 100%) !important;
  color: var(--text-hi) !important;
  font-family: {FONT_BODY};
}}

[data-testid="stAppViewBlockContainer"] {{
  max-width: 1600px;
  padding: .65rem 1.1rem 1rem;
}}

[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stToolbar"] {{ right: 1rem; }}

h1, h2, h3, h4 {{
  font-family: {FONT_DISPLAY};
  color: var(--text-hi);
  letter-spacing: -0.1px;
}}

p, label, div, button, input {{ font-family: {FONT_BODY}; }}

/* Header shell
   Logo is deliberately transparent and is not placed inside a small box. */
.hop-topbar {{
  display:flex; align-items:center; justify-content:space-between;
  gap:22px; flex-wrap:wrap; padding:14px 24px;
  min-height:102px; margin:2px 0 10px;
  background:linear-gradient(135deg,#FFFFFF 0%,#F7FCFB 100%);
  border:1px solid var(--border-light); border-left:6px solid var(--deep-teal); border-radius:24px;
  box-shadow:0 18px 42px rgba(28,94,88,.13);
}}
.hop-brand {{ display:flex; align-items:center; gap:25px; min-width:0; }}
.hop-mark {{
  width:130px; height:76px; flex:0 0 130px;
  background:transparent; border:0; border-radius:0;
  display:flex; align-items:center; justify-content:center;
  box-shadow:none; overflow:visible;
}}
.brand-logo {{
  width:126px; height:72px; max-width:100%;
  object-fit:contain; display:block; background:transparent;
}}
.hop-title {{
  font-family:{FONT_DISPLAY}; font-size:34px; font-weight:700;
  line-height:1.05; letter-spacing:-.65px; color:var(--text-hi);
}}
.hop-sub {{
  color:var(--teal-dark); font-size:12.5px; line-height:1.4;
  margin-top:5px; font-weight:520; max-width:780px;
}}
.hop-asof {{
  display:flex; gap:9px; align-items:center; padding:10px 16px;
  background:#FFFFFF; border:1px solid var(--border-light);
  border-radius:999px; color:var(--text-mid); font-family:{FONT_MONO}; font-size:11px;
  box-shadow:0 7px 18px rgba(28,94,88,.07);
}}
.live-dot {{ width:8px; height:8px; background:var(--teal); border-radius:50%; box-shadow:0 0 0 4px rgba(20,156,148,.11); }}
@media(max-width:900px) {{
  .hop-topbar {{ padding:20px; min-height:auto; }}
  .hop-brand {{ gap:16px; }}
  .hop-mark {{ width:105px; height:70px; flex-basis:105px; }}
  .brand-logo {{ width:102px; height:66px; }}
  .hop-title {{ font-size:30px; }}
  .hop-sub {{ font-size:12px; }}
}}

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
  padding:8px; background:#FFFFFF;
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
  background:linear-gradient(135deg,var(--deep-teal),var(--teal-dark));
  color:#FFFFFF !important; box-shadow:0 12px 26px rgba(10,79,74,.28);
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
.section-row {{ display:flex; align-items:flex-end; justify-content:space-between; gap:10px; flex-wrap:wrap; margin:15px 0 8px; }}
.section-title {{ font-family:{FONT_DISPLAY}; font-size:17px; font-weight:700; color:var(--text-hi); }}
.section-desc {{ color:var(--teal-dark); font-size:12.5px; font-weight:520; line-height:1.55; max-width:760px; margin-top:4px; }}
.section-tag {{
  font-family:{FONT_MONO}; font-size:10px; letter-spacing:.4px;
  color:#FFFFFF; background:var(--deep-teal);
  border:1px solid var(--deep-teal); border-radius:7px; padding:5px 9px;
  box-shadow:0 6px 14px rgba(10,79,74,.14);
}}

/* [DESIGN 04] KPI and information cards */
.hop-card, .kpi-card, .insight-card {{
  position:relative; overflow:hidden;
  background:linear-gradient(180deg,#FFFFFF 0%,#FBFEFD 100%);
  border:1px solid var(--border-light); border-radius:18px;
  padding:15px 17px; box-shadow:var(--shadow);
}}
.hop-card::before, .kpi-card::before, .insight-card::before {{
  content:''; position:absolute; left:0; right:0; top:0; height:4px;
  background:linear-gradient(90deg,var(--deep-teal) 0 25%,var(--teal) 25% 58%,var(--mint) 58% 100%);
  opacity:.95;
}}
.kpi-label {{ color:var(--teal-dark); font-size:11px; font-weight:700; letter-spacing:.55px; text-transform:uppercase; }}
.kpi-value {{ color:var(--text-hi); font-family:{FONT_MONO}; font-size:27px; font-weight:650; margin-top:7px; }}
.kpi-foot {{ color:var(--teal-dark); font-size:11px; margin-top:6px; line-height:1.35; }}
.kpi-icon {{
  position:absolute; top:13px; right:14px; width:52px; height:52px;
  border-radius:16px; background:#E7F7F3; border:1px solid #D0ECE7;
  display:flex; align-items:center; justify-content:center;
}}
.kpi-icon .ui-icon {{ width:32px; height:32px; }}
.card-title {{ font-family:{FONT_DISPLAY}; font-size:14px; font-weight:700; color:var(--text-hi); }}
.card-sub {{ color:var(--teal-dark); font-size:11.7px; margin-top:5px; line-height:1.5; }}
.kpi-value-text {{
  font-family:{FONT_DISPLAY}; font-size:19px; font-weight:700;
  line-height:1.24; max-width:78%; margin-top:11px;
}}

/* Page 3 response summary */
.response-progress-card {{
  position:relative; min-height:245px; padding:25px 26px; overflow:hidden;
  background:linear-gradient(145deg,#FFFFFF 0%,#F8FCFB 100%);
  border:1.35px solid #A9D5CF; border-radius:20px; box-shadow:var(--shadow);
}}
.response-progress-card::before {{
  content:''; position:absolute; left:0; right:0; top:0; height:4px;
  background:linear-gradient(90deg,#6F8FEF,#9887E8,#E98C7C);
}}
.response-progress-head {{ display:flex; align-items:flex-start; justify-content:space-between; gap:18px; }}
.response-progress-label {{
  color:var(--teal-dark); font-size:12px; font-weight:700;
  letter-spacing:.45px; text-transform:uppercase;
}}
.response-progress-value {{
  margin-top:11px; color:var(--text-hi); font-family:{FONT_MONO};
  font-size:29px; font-weight:650; line-height:1.25;
}}
.response-progress-note {{ color:var(--teal-dark); font-size:12px; line-height:1.5; margin-top:7px; }}
.response-progress-icon {{
  width:68px; height:68px; flex:0 0 68px; display:flex; align-items:center; justify-content:center;
  background:#F2F0FF; border:1px solid #DDD8FF; border-radius:18px;
}}
.response-progress-icon .ui-icon {{ width:42px; height:42px; }}
.response-track {{
  height:18px; overflow:hidden; margin-top:28px; border-radius:999px;
  background:#E7F0EE; border:1px solid #D2E5E1;
}}
.response-fill {{
  height:100%; min-width:2px; border-radius:999px;
  background:linear-gradient(90deg,#6F8FEF 0%,#9887E8 48%,#E98C7C 100%);
}}
.response-progress-meta {{
  display:flex; align-items:center; justify-content:space-between; gap:15px;
  color:var(--teal-dark); font-size:12px; font-weight:600; margin-top:10px;
}}
.chart-panel-label {{
  margin:0 0 9px 3px; color:var(--text-hi);
  font-family:{FONT_DISPLAY}; font-size:16px; font-weight:700;
}}

/* Plotly containers act as clean white chart cards */
div[data-testid="stPlotlyChart"] {{
  background:#FFFFFF; border:1.25px solid #A9D5CF;
  border-radius:18px; padding:5px 7px; box-shadow:var(--shadow);
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
  background:#FFFFFF !important; border:1px solid var(--border-light);
  border-radius:16px; overflow:hidden; box-shadow:var(--shadow);
  color:var(--text-hi) !important;
}}
[data-testid="stDataFrame"] [role="columnheader"] {{
  background:var(--deep-teal) !important;
  color:#FFFFFF !important;
}}
[data-testid="stDataFrame"] [role="columnheader"] * {{
  color:#FFFFFF !important;
}}
[data-testid="stDataFrame"] [role="gridcell"] {{
  background:#FFFFFF !important;
  color:var(--text-hi) !important;
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
  background:linear-gradient(135deg,var(--deep-teal),var(--teal-dark));
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
  margin-top:14px; padding:10px 14px;
  background:var(--deep-teal); border:1px solid var(--deep-teal);
  border-radius:14px; color:#FFFFFF; font-size:11px; text-align:center;
  box-shadow:0 10px 22px rgba(10,79,74,.17);
}}

/* Wide section navigation cards with replaceable icons */
.section-nav-shell {{
  --section-count:4;
  display:grid;
  grid-template-columns:repeat(var(--section-count),minmax(0,1fr));
  gap:9px; padding:7px; margin:2px 0 10px;
  background:#FFFFFF;
  border:1px solid var(--border-light); border-radius:17px;
  box-shadow:0 10px 25px rgba(28,94,88,.10);
}}
.section-nav-link {{
  min-height:58px; display:flex; align-items:center; gap:11px;
  padding:8px 12px; border:1px solid transparent; border-radius:12px;
  color:var(--text-hi) !important; text-decoration:none !important;
  font-size:12px; font-weight:700; line-height:1.25;
  transition:transform .18s ease, box-shadow .18s ease, background .18s ease;
}}
.section-nav-link:hover {{
  background:#F4FBF9; border-color:var(--border-light);
  transform:translateY(-1px); box-shadow:0 8px 18px rgba(28,94,88,.10);
}}
.section-nav-link.active {{
  color:#FFFFFF !important;
  background:linear-gradient(135deg,var(--deep-teal),var(--teal-dark));
  box-shadow:0 10px 23px rgba(10,79,74,.28);
}}
.section-nav-icon-box {{
  width:42px; height:42px; flex:0 0 42px;
  display:flex; align-items:center; justify-content:center;
  border-radius:11px; background:#ECF8F5; border:1px solid #D2ECE7;
}}
.section-nav-link.active .section-nav-icon-box {{
  background:#FFFFFF; border-color:rgba(255,255,255,.78);
}}
.section-nav-icon {{
  width:28px; height:28px; object-fit:contain; display:block;
}}
@media(max-width:980px) {{
  .section-nav-shell {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
}}

/* Section heading with a dedicated icon area */
.section-heading-main {{
  display:flex; align-items:center; gap:12px; min-width:0;
}}
.section-heading-icon {{
  width:48px; height:48px; flex:0 0 48px;
  display:flex; align-items:center; justify-content:center;
  border-radius:13px; background:linear-gradient(145deg,#EFF8FF,#FFFFFF);
  border:1px solid #D7E6F4; box-shadow:0 8px 19px rgba(82,112,148,.13);
}}
.section-heading-icon-img {{
  width:31px; height:31px; object-fit:contain; display:block;
}}

/* Wide page navigation cards inside Dashboard Settings */
.sidebar-page-nav {{
  display:flex; flex-direction:column; gap:8px; margin:6px 0 15px;
}}
.sidebar-page-link {{
  width:100%; min-height:58px; box-sizing:border-box;
  display:flex; align-items:center; gap:11px;
  padding:9px 10px; border-radius:12px;
  background:#FFFFFF; border:1px solid var(--border-light);
  color:var(--text-hi) !important; text-decoration:none !important;
  font-size:12px; font-weight:700; line-height:1.3;
  box-shadow:0 6px 16px rgba(28,94,88,.07);
  transition:transform .18s ease, box-shadow .18s ease, background .18s ease;
}}
.sidebar-page-link:hover {{
  transform:translateY(-1px); background:#FFFFFF;
  border-color:var(--border-strong); box-shadow:0 9px 20px rgba(28,94,88,.11);
}}
.sidebar-page-link.active {{
  color:#FFFFFF !important;
  background:linear-gradient(135deg,var(--deep-teal),var(--teal-dark));
  border-color:transparent; box-shadow:0 10px 24px rgba(10,79,74,.28);
}}
.sidebar-page-icon-box {{
  width:40px; height:40px; flex:0 0 40px;
  display:flex; align-items:center; justify-content:center;
  border-radius:10px; background:#ECF8F5; border:1px solid #D2ECE7;
}}
.sidebar-page-link.active .sidebar-page-icon-box {{
  background:#FFFFFF; border-color:rgba(255,255,255,.76);
}}
.sidebar-page-icon {{
  width:27px; height:27px; object-fit:contain; display:block;
}}
/* Compact 1920 x 1080 presentation canvas */
@media (min-width:1500px) and (min-height:850px) {{
  [data-testid="stSidebar"] {{ min-width:285px; max-width:285px; }}
  .section-title {{ font-size:16px; }}
  .section-desc {{ font-size:11.5px; line-height:1.35; }}
  .section-tag {{ font-size:9px; padding:4px 7px; }}
  .kpi-card {{ min-height:108px; }}
  [data-testid="stDataFrame"] {{ font-size:11px; }}
  [data-testid="stForm"] {{ padding:14px 16px; }}
  .panel-heading {{ margin-bottom:10px; }}
  .panel-icon-box {{ width:48px; height:48px; flex-basis:48px; border-radius:14px; }}
  .panel-icon-img {{ width:31px; height:31px; }}
  .panel-heading-title {{ font-size:17px; }}
  .panel-heading-sub {{ font-size:10.5px; }}
}}

/* Stable visual system: browser/OS dark mode does not recolor dashboard assets. */
html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"],
[data-testid="stForm"], [data-testid="stDataFrame"], div[data-testid="stPlotlyChart"] {{
  color-scheme: light only !important;
}}
[data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"],
[data-baseweb="select"] > div, [data-baseweb="input"] > div,
[data-testid="stNumberInput"] input, [data-testid="stDateInput"] input {{
  background:#FFFFFF !important;
  color:var(--text-hi) !important;
}}
[data-baseweb="popover"] *, [data-baseweb="menu"] *, [role="listbox"] * {{
  color:var(--text-hi) !important;
}}
@media (prefers-color-scheme: dark) {{
  html, body, [data-testid="stAppViewContainer"], .stApp {{
    background:
      radial-gradient(circle at 8% 3%, rgba(191,235,221,.75) 0, rgba(191,235,221,0) 26%),
      radial-gradient(circle at 92% 12%, rgba(82,190,180,.15) 0, rgba(82,190,180,0) 28%),
      linear-gradient(180deg, var(--page-bg) 0%, #F8FCFB 48%, #F2FAF8 100%) !important;
    color:var(--text-hi) !important;
  }}
  [data-testid="stSidebar"] {{
    background:linear-gradient(180deg,#F5FCFA,#EAF7F4) !important;
  }}
  .hop-topbar, .hop-card, .kpi-card, .insight-card,
  [data-testid="stForm"], div[data-testid="stPlotlyChart"],
  [data-testid="stDataFrame"], .sidebar-page-link,
  .section-nav-shell, .hop-nav-shell {{
    background:#FFFFFF !important;
    color:var(--text-hi) !important;
  }}
  .sidebar-page-link.active, .section-nav-link.active, .hop-nav-item.active {{
    background:linear-gradient(135deg,var(--deep-teal),var(--teal-dark)) !important;
    color:#FFFFFF !important;
  }}
}}

/* =====================================================================
   FINAL UX OVERRIDES
   - Charts stay flat and no longer jump on hover.
   - Sidebar is permanently dark teal.
   - Page and section hierarchy uses explicit numbering.
   ===================================================================== */

/* Flat interactive charts: no clipped shadows and no hover movement. */
div[data-testid="stPlotlyChart"],
div[data-testid="stPlotlyChart"]:hover,
.st-key-sankey_chart div[data-testid="stPlotlyChart"],
.st-key-sankey_chart div[data-testid="stPlotlyChart"]:hover {{
  background:#FFFFFF !important;
  border:2px solid #86C4BC !important;
  border-radius:18px !important;
  box-shadow:none !important;
  transform:none !important;
  transition:border-color .16s ease !important;
}}
div[data-testid="stPlotlyChart"]:hover {{
  border-color:#5EAFA5 !important;
}}

/* Dark-teal settings panel. Every text item sitting on the dark surface is white. */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
  background:linear-gradient(180deg,#073F3B 0%,#0A4F4A 52%,#0C625C 100%) !important;
  border-right:1px solid rgba(255,255,255,.18) !important;
}}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] summary,
[data-testid="stSidebar"] summary *,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] * {{
  color:#FFFFFF !important;
}}
[data-testid="stSidebar"] hr {{
  border-color:rgba(255,255,255,.20) !important;
}}
[data-testid="stSidebar"] [data-testid="stExpander"] {{
  background:rgba(255,255,255,.07) !important;
  border:1px solid rgba(255,255,255,.20) !important;
  border-radius:12px !important;
}}

/* Sidebar fields remain white for contrast, with dark-teal field text. */
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] > div,
[data-testid="stSidebar"] [data-testid="stDateInput"] > div,
[data-testid="stSidebar"] [data-testid="stDateInput"] input {{
  background:#FFFFFF !important;
  border-color:rgba(255,255,255,.72) !important;
  color:var(--deep-teal) !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] > div *,
[data-testid="stSidebar"] [data-baseweb="input"] > div *,
[data-testid="stSidebar"] [data-testid="stDateInput"] input {{
  color:var(--deep-teal) !important;
  -webkit-text-fill-color:var(--deep-teal) !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] svg,
[data-testid="stSidebar"] [data-testid="stDateInput"] svg {{
  color:var(--deep-teal) !important;
  fill:var(--deep-teal) !important;
}}

/* Page cards on the dark sidebar. */
[data-testid="stSidebar"] .sidebar-page-link {{
  background:rgba(255,255,255,.08) !important;
  border:1px solid rgba(255,255,255,.24) !important;
  color:#FFFFFF !important;
  box-shadow:none !important;
}}
[data-testid="stSidebar"] .sidebar-page-link:hover {{
  background:rgba(255,255,255,.15) !important;
  border-color:rgba(255,255,255,.48) !important;
  transform:none !important;
  box-shadow:none !important;
}}
[data-testid="stSidebar"] .sidebar-page-link:not(.active) *,
[data-testid="stSidebar"] .sidebar-page-link:not(.active) .sidebar-page-kicker,
[data-testid="stSidebar"] .sidebar-page-link:not(.active) .sidebar-page-label {{
  color:#FFFFFF !important;
}}
[data-testid="stSidebar"] .sidebar-page-link.active {{
  background:#FFFFFF !important;
  border-color:#FFFFFF !important;
  box-shadow:0 10px 24px rgba(0,0,0,.18) !important;
}}
[data-testid="stSidebar"] .sidebar-page-link.active *,
[data-testid="stSidebar"] .sidebar-page-link.active .sidebar-page-kicker,
[data-testid="stSidebar"] .sidebar-page-link.active .sidebar-page-label {{
  color:var(--deep-teal) !important;
}}
[data-testid="stSidebar"] .sidebar-page-icon-box {{
  background:rgba(255,255,255,.13) !important;
  border-color:rgba(255,255,255,.28) !important;
}}
[data-testid="stSidebar"] .sidebar-page-link.active .sidebar-page-icon-box {{
  background:#EAF7F4 !important;
  border-color:#CFE9E4 !important;
}}

/* Clear page-level context before the user chooses a section. */
.page-context-bar {{
  display:flex;
  align-items:center;
  gap:10px;
  flex-wrap:wrap;
  padding:10px 13px;
  margin:3px 0 8px;
  background:#E7F5F2;
  border:1px solid #BFDCD7;
  border-left:5px solid var(--deep-teal);
  border-radius:13px;
}}
.page-context-kicker {{
  display:inline-flex;
  align-items:center;
  padding:5px 8px;
  border-radius:7px;
  background:var(--deep-teal);
  color:#FFFFFF;
  font-family:var(--font-mono);
  font-size:10px;
  font-weight:700;
  letter-spacing:.55px;
}}
.page-context-title {{
  color:var(--deep-teal);
  font-family:var(--font-display);
  font-size:15px;
  font-weight:750;
}}
.page-context-hint {{
  margin-left:auto;
  color:var(--teal-dark);
  font-size:10.5px;
  font-weight:600;
}}

/* Two-level labels inside page and section cards. */
.sidebar-page-copy,
.section-nav-copy {{
  min-width:0;
  display:flex;
  flex-direction:column;
  align-items:flex-start;
  gap:2px;
}}
.sidebar-page-kicker,
.section-nav-kicker {{
  display:block;
  font-family:var(--font-mono);
  font-size:8.5px;
  font-weight:700;
  letter-spacing:.55px;
  opacity:.82;
}}
.sidebar-page-label,
.section-nav-label {{
  display:block;
  font-size:12px;
  font-weight:750;
  line-height:1.25;
}}
.section-nav-link.active .section-nav-kicker,
.section-nav-link.active .section-nav-label {{
  color:#FFFFFF !important;
}}
.section-nav-link:not(.active) .section-nav-kicker {{
  color:var(--teal-dark) !important;
}}
.section-nav-link:not(.active) .section-nav-label {{
  color:var(--text-hi) !important;
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


STAGE_LABELS = {
    "Selecting Student by Company": "Pemilihan oleh perusahaan",
    "CDC Briefing Student": "Pembekalan CDC",
    "Study Case": "Studi kasus",
    "Interview User": "Wawancara pengguna",
    "Final Interview": "Wawancara akhir",
    "Placement": "Ditempatkan",
    "Rejected": "Ditolak",
    "Ghosting": "Tanpa kabar",
    "FU 1": "Tindak lanjut 1",
    "FU 2": "Tindak lanjut 2",
    "FU 3": "Tindak lanjut 3",
}

OUTCOME_LABELS = {
    "Placement": "Ditempatkan",
    "Ghosting": "Tanpa kabar",
    "Rejection Interview User": "Ditolak setelah wawancara pengguna",
    "Rejection Screening CV": "Ditolak saat seleksi CV",
    "Rejection Study Case": "Ditolak setelah studi kasus",
    "Rejection Final Interview": "Ditolak setelah wawancara akhir",
}

ACTIVE_STAGES = [
    "Selecting Student by Company",
    "CDC Briefing Student",
    "Study Case",
    "Interview User",
    "Final Interview",
    "FU 1",
    "FU 2",
    "FU 3",
]


def stage_label(value: object) -> str:
    return STAGE_LABELS.get(str(value), str(value))


def query_param_value(name: str, default: str) -> str:
    """Read one query parameter safely across Streamlit versions."""
    value = st.query_params.get(name, default)
    if isinstance(value, list):
        return str(value[-1]) if value else default
    return str(value)


def section_navigation(
    page_key: str,
    options: dict[str, tuple[str, str]],
) -> str:
    """Render numbered section cards so page and section hierarchy is obvious."""
    page_context = {
        "executive": ("1", "Ringkasan Penempatan"),
        "matching": ("2", "Temukan Kandidat"),
        "operations": ("3", "Pantau Proses Seleksi"),
    }
    page_number, page_title = page_context.get(page_key, ("-", "Dashboard"))

    keys = list(options)
    current_section = query_param_value("section", keys[0])
    if current_section not in options:
        current_section = keys[0]

    # Clear page-level context before the section-level navigation.
    st.markdown(
        f"""
        <div class="page-context-bar">
          <span class="page-context-kicker">HALAMAN {html.escape(page_number)}</span>
          <span class="page-context-title">{html.escape(page_title)}</span>
          <span class="page-context-hint">Pilih bagian analisis di bawah</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    items = [
        f'<div class="section-nav-shell" style="--section-count:{len(keys)};">'
    ]
    for index, (key, (label, icon_key)) in enumerate(options.items(), start=1):
        active_class = " active" if key == current_section else ""
        section_number = f"{page_number}.{index}"
        items.append(
            f'<a class="section-nav-link{active_class}" '
            f'href="?page={html.escape(page_key)}&section={html.escape(key)}" target="_self">'
            f'<span class="section-nav-icon-box">'
            f'{icon_html(icon_key, "section-nav-icon")}</span>'
            f'<span class="section-nav-copy">'
            f'<span class="section-nav-kicker">BAGIAN {html.escape(section_number)}</span>'
            f'<span class="section-nav-label">{html.escape(label)}</span>'
            f'</span></a>'
        )
    items.append("</div>")
    st.markdown("".join(items), unsafe_allow_html=True)
    return current_section


def normalize_wa_number(value: object) -> str | None:
    """Normalize an Indonesian phone number into wa.me-compatible digits (62xxxxxxxxx)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    digits = re.sub(r"\D", "", str(value))
    if not digits:
        return None
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    elif digits.startswith("8"):
        digits = "62" + digits
    elif not digits.startswith("62"):
        digits = "62" + digits
    return digits


def wa_followup_link(number: object, student_name: str, company: str, stage: str) -> float | str:
    wa_number = normalize_wa_number(number)
    if not wa_number:
        return np.nan
    message = (
        f"Halo {student_name}, kami dari CDC ingin menanyakan perkembangan proses seleksi "
        f"di {company} pada tahap {stage}. Mohon info terbarunya, terima kasih."
    )
    return f"https://wa.me/{wa_number}?text={quote(message)}"


try:
    DATA = load_data(str(CLEAN_DIR))
except FileNotFoundError as exc:
    st.error("Dashboard belum dapat membaca hasil ETL.")
    st.code(
        "py etl.py\npy -m streamlit run app_revised_dark_teal_v2.py",
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

# The response-age calculation should follow the newest active selection record.
# Sync dates can be much newer than the actual recruitment history and would
# otherwise make every process look hundreds of days late.
_active_update_dates = pd.to_datetime(
    tracking_student.loc[
        tracking_student.get("progress_student", pd.Series("", index=tracking_student.index)).isin(ACTIVE_STAGES),
        "last_update",
    ],
    errors="coerce",
).dropna()

if not _active_update_dates.empty:
    DEFAULT_AS_OF = _active_update_dates.max().normalize()
else:
    DEFAULT_AS_OF = max_valid_date(
        tracking_student.get("last_update", pd.Series(dtype="datetime64[ns]")),
        tracking_company.get("send_date", pd.Series(dtype="datetime64[ns]")),
        talent_request.get("request_date", pd.Series(dtype="datetime64[ns]")),
    ).normalize()



# =============================================================================
# SIDEBAR SETTINGS AND PAGE NAVIGATION
# =============================================================================
PAGE_OPTIONS = {
    "executive": ("1", "Ringkasan Penempatan", "nav_executive", "overview"),
    "matching": ("2", "Temukan Kandidat", "nav_matching", "setup"),
    "operations": ("3", "Pantau Proses Seleksi", "nav_operations", "pipeline"),
}

current_page_key = query_param_value("page", "executive")
if current_page_key not in PAGE_OPTIONS:
    current_page_key = "executive"

with st.sidebar:
    st.markdown("### Pengaturan Dashboard")
    st.caption("Pilih halaman utama")
    page_nav_html = ['<div class="sidebar-page-nav">']
    for page_key, (page_number, page_label, page_icon, default_section) in PAGE_OPTIONS.items():
        active_class = " active" if page_key == current_page_key else ""
        page_nav_html.append(
            f'<a class="sidebar-page-link{active_class}" '
            f'href="?page={html.escape(page_key)}&section={html.escape(default_section)}" target="_self">'
            f'<span class="sidebar-page-icon-box">'
            f'{icon_html(page_icon, "sidebar-page-icon")}</span>'
            f'<span class="sidebar-page-copy">'
            f'<span class="sidebar-page-kicker">HALAMAN {html.escape(page_number)}</span>'
            f'<span class="sidebar-page-label">{html.escape(page_label)}</span>'
            f'</span></a>'
        )
    page_nav_html.append("</div>")
    st.markdown("".join(page_nav_html), unsafe_allow_html=True)

    as_of_date = st.date_input(
        "Tanggal acuan",
        value=DEFAULT_AS_OF.date(),
        help="Tanggal awal otomatis mengikuti pembaruan terbaru pada proses seleksi aktif.",
    )
    privacy_mode = st.selectbox(
        "Tampilan identitas",
        ["Disamarkan untuk lomba", "Tampilkan untuk internal CDC"],
        help="Mode lomba menyamarkan nama dan NIM mahasiswa.",
    )
    st.markdown("---")
    st.caption(
        "Pilih HALAMAN di panel ini, lalu pilih BAGIAN bernomor di area utama."
    )
    with st.expander("Periksa ikon dan aset"):
        st.caption("Kode mencari PNG/SVG di assets/, assets/icons/, dan folder project.")
        for asset_key, configured_path in ICON_PATHS.items():
            resolved_path = resolve_asset_path(configured_path)
            status_text = "Terdeteksi" if resolved_path else "Belum ditemukan"
            shown_path = str(resolved_path.relative_to(BASE_DIR)) if resolved_path else configured_path
            st.write(f"**{asset_key}** · {status_text}: `{shown_path}`")

AS_OF = pd.Timestamp(as_of_date)
IS_PUBLIC = privacy_mode == "Disamarkan untuk lomba"


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
        template="plotly_white",
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font={"family": "Roboto Flex", "color": DEEP_TEAL, "size": 12},
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


def section_header(
    title: str,
    description: str,
    tag: str,
    icon_key: str,
) -> None:
    """Section heading with a named title and a replaceable icon area."""
    st.markdown(
        f"""
        <div class="section-row">
          <div class="section-heading-main">
            <span class="section-heading-icon">
              {icon_html(icon_key, "section-heading-icon-img")}
            </span>
            <div>
              <div class="section-title">{html.escape(title)}</div>
              <div class="section-desc">{html.escape(description)}</div>
            </div>
          </div>
          <span class="section-tag">{html.escape(tag)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(
    label: str,
    value: str,
    foot: str,
    icon_key: str,
    value_kind: str = "number",
) -> None:
    """Render a KPI card with a replaceable icon from ICON_PATHS.

    Set value_kind="text" when the main value is a long stage or company name.
    """
    value_class = "kpi-value kpi-value-text" if value_kind == "text" else "kpi-value"
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-icon">{icon_html(icon_key)}</div>
          <div class="kpi-label">{html.escape(label)}</div>
          <div class="{value_class}" title="{html.escape(value)}">{html.escape(value)}</div>
          <div class="kpi-foot">{html.escape(foot)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def response_progress_card(
    overdue_count: int,
    total_active: int,
    overdue_rate: float,
    icon_key: str = "response_progress",
) -> None:
    """Large progress card for the response-monitoring section."""
    safe_rate = min(max(float(overdue_rate), 0.0), 100.0)
    within_sla = max(int(total_active) - int(overdue_count), 0)
    st.markdown(
        f"""
        <div class="response-progress-card">
          <div class="response-progress-head">
            <div>
              <div class="response-progress-label">Cakupan proses melewati SLA</div>
              <div class="response-progress-value">
                {html.escape(format_int(overdue_count))} dari {html.escape(format_int(total_active))}
              </div>
              <div class="response-progress-note">proses aktif memerlukan tindak lanjut</div>
            </div>
            <div class="response-progress-icon">{icon_html(icon_key)}</div>
          </div>
          <div class="response-track" aria-label="{safe_rate:.1f}% proses melewati SLA">
            <div class="response-fill" style="width:{safe_rate:.1f}%;"></div>
          </div>
          <div class="response-progress-meta">
            <span>{safe_rate:.1f}% melewati SLA</span>
            <span>{html.escape(format_int(within_sla))} masih dalam SLA</span>
          </div>
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
# HEADER
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
st.caption(f"Tim: **{TEAM_NAME}** · Nomor peserta: **{PARTICIPANT_NUMBER}**")


# =============================================================================
# PAGE 1: RINGKASAN PENEMPATAN
# Dibagi menjadi empat bagian agar setiap tampilan nyaman pada layar 1920 × 1080.
# =============================================================================
if current_page_key == "executive":
    executive_section = section_navigation(
        "executive",
        {
            "overview": ("Ringkasan Utama", "section_executive_overview"),
            "placement": ("Penempatan Mahasiswa", "section_executive_placement"),
            "partners": ("Mitra dan Wilayah", "section_executive_partners"),
            "insights": ("Insight Penting", "section_executive_insights"),
        },
    )

    total_students = student_all["NIM"].astype(str).nunique()
    active_students = readiness.loc[readiness.get("status", "").eq("Active"), "NIM"].nunique()
    total_placed = len(placed_nims)
    placement_rate = safe_divide(total_placed, active_students) * 100
    total_companies = company["id_company"].nunique()
    total_requests = talent_request["id_talent_req"].nunique()

    valid_send = tracking_company.dropna(subset=["request_date", "send_date"]).copy()
    valid_send["days_to_send"] = (valid_send["send_date"] - valid_send["request_date"]).dt.days
    avg_send_days = valid_send.loc[valid_send["days_to_send"] >= 0, "days_to_send"].mean()

    status_dedup = (
        status_student.sort_values("sync_date", na_position="first")
        .drop_duplicates("NIM", keep="last")
    )
    status_counts = (
        status_dedup.get("status", pd.Series(dtype=str))
        .fillna("Belum diketahui")
        .value_counts()
    )
    active_set = set(
        status_dedup.loc[status_dedup.get("status", "").eq("Active"), "NIM"].astype(str)
    )
    placed_active_set = placed_nims.intersection(active_set)
    available_active_set = set(
        status_dedup.loc[
            status_dedup.get("status", "").eq("Active")
            & status_dedup.get("ketersediaan", "").eq("Available"),
            "NIM",
        ].astype(str)
    ) - placed_active_set
    other_active_set = active_set - placed_active_set - available_active_set

    placement_sector = placed_unique[
        placed_unique["NIM"].astype(str).isin(placed_active_set)
    ].copy()
    placement_sector["industry_sector"] = placement_sector.get(
        "industry_sector", "Tidak diketahui"
    ).fillna("Tidak diketahui")
    sector_counts = (
        placement_sector.groupby("industry_sector")["NIM"]
        .nunique()
        .sort_values(ascending=False)
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

    relocation = placed_unique.merge(
        readiness[["NIM", "domisili"]].drop_duplicates("NIM"),
        on="NIM",
        how="left",
    ).dropna(subset=["domisili", "kota"])
    relocation["same_city"] = (
        relocation["domisili"].astype(str).str.strip().str.lower()
        == relocation["kota"].astype(str).str.strip().str.lower()
    )
    same_city = int(relocation["same_city"].sum())
    relocate = int((~relocation["same_city"]).sum())

    partner_summary = (
        placement_mart.groupby(
            ["id_company", "company_name", "industry_sector", "kota"],
            dropna=False,
        )
        .agg(
            candidates_sent=("id_tracking_student", "nunique"),
            placed=("canonical_outcome", lambda s: int((s == "Placement").sum())),
            ghosting=("canonical_outcome", lambda s: int((s == "Ghosting").sum())),
        )
        .reset_index()
    )
    partner_summary = partner_summary[partner_summary["candidates_sent"] >= 5].copy()
    partner_summary["success_rate"] = (
        partner_summary["placed"] / partner_summary["candidates_sent"] * 100
    )
    partner_summary["ghosting_rate"] = (
        partner_summary["ghosting"] / partner_summary["candidates_sent"] * 100
    )
    partner_summary = partner_summary.sort_values(
        ["success_rate", "placed"], ascending=False
    )

    if executive_section == "overview":
        section_header(
            "Ringkasan Penempatan",
            "Gambaran cepat kondisi mahasiswa, mitra, dan perjalanan menuju penempatan.",
            "RINGKASAN",
            "section_executive_overview",
        )
        k1, k2, k3, k4 = st.columns(4, gap="medium")
        with k1:
            kpi_card(
                "Mahasiswa Aktif",
                format_int(active_students),
                f"{format_int(total_students)} mahasiswa pada data utama",
                "student",
            )
        with k2:
            kpi_card(
                "Mahasiswa Ditempatkan",
                format_int(total_placed),
                f"Tingkat penempatan {format_pct(placement_rate)}",
                "placement",
            )
        with k3:
            kpi_card(
                "Perusahaan Mitra",
                format_int(total_companies),
                f"{format_int(total_requests)} kebutuhan kandidat tercatat",
                "company",
            )
        with k4:
            send_text = f"{avg_send_days:.1f} hari" if pd.notna(avg_send_days) else "Belum tersedia"
            kpi_card(
                "Waktu Kirim Kandidat",
                send_text,
                "Dari kebutuhan diterima hingga kandidat dikirim",
                "clock",
            )

        section_header(
            "Perjalanan Mahasiswa hingga Penempatan",
            "Alur dari data mahasiswa, status aktif, ketersediaan, hingga sektor tempat bekerja.",
            "ALUR DATA",
            "section_executive_flow",
        )

        labels = ["Semua Mahasiswa"]
        sources: list[int] = []
        targets: list[int] = []
        values: list[int] = []
        node_colors = [CHART_COLORS[0]]
        link_colors: list[str] = []

        def rgba(hex_color: str, alpha: float = 0.24) -> str:
            clean = hex_color.lstrip("#")
            red, green, blue = (
                int(clean[0:2], 16),
                int(clean[2:4], 16),
                int(clean[4:6], 16),
            )
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

        status_display = {
            "Active": "Aktif",
            "Inactive": "Tidak aktif",
            "Cuti": "Cuti",
            "Lulus": "Lulus",
            "Belum diketahui": "Belum diketahui",
        }
        status_color = {
            "Active": CHART_COLORS[6],
            "Inactive": CHART_COLORS[8],
            "Cuti": CHART_COLORS[3],
            "Lulus": CHART_COLORS[1],
        }
        known_status_total = 0
        for status_name, count in status_counts.items():
            known_status_total += int(count)
            add_link(
                "Semua Mahasiswa",
                status_display.get(str(status_name), str(status_name)),
                int(count),
                status_color.get(str(status_name), TEXT_LOW),
            )
        add_link(
            "Semua Mahasiswa",
            "Belum terhubung ke status",
            max(total_students - known_status_total, 0),
            TEXT_LOW,
        )
        add_link("Aktif", "Ditempatkan", len(placed_active_set), CHART_COLORS[0])
        add_link("Aktif", "Tersedia", len(available_active_set), CHART_COLORS[5])
        add_link("Aktif", "Status aktif lainnya", len(other_active_set), CHART_COLORS[2])

        top_sectors = sector_counts.head(7)
        remainder = max(len(placed_active_set) - int(top_sectors.sum()), 0)
        if remainder:
            top_sectors.loc["Sektor lain / belum terpetakan"] = remainder
        for sector, count in top_sectors.items():
            add_link(
                "Ditempatkan",
                str(sector),
                int(count),
                CHART_COLORS[(len(labels) + int(count)) % len(CHART_COLORS)],
            )

        sankey = go.Figure(
            go.Sankey(
                arrangement="snap",
                node={
                    "pad": 17,
                    "thickness": 17,
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
        style_figure(sankey, 455)
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

    elif executive_section == "placement":
        section_header(
            "Penempatan Mahasiswa",
            "Bandingkan program studi, perpindahan kota, dan sektor tujuan penempatan.",
            "PENEMPATAN",
            "section_executive_placement",
        )
        left, right = st.columns([1.28, 0.72], gap="large")

        with left:
            st.markdown(
                '<div class="chart-panel-label">Penempatan berdasarkan Program Studi</div>',
                unsafe_allow_html=True,
            )
            prodi_show = (
                prodi_summary.sort_values("placed_students", ascending=False)
                .head(12)
                .sort_values("placed_students")
            )
            fig_prodi = px.bar(
                prodi_show,
                x="placed_students",
                y="program_studi",
                orientation="h",
                text="placed_students",
                custom_data=["placement_rate", "total_students"],
            )
            fig_prodi.update_traces(
                marker_color=[
                    CHART_COLORS[i % len(CHART_COLORS)]
                    for i in range(len(prodi_show))
                ],
                textposition="outside",
                hovertemplate=(
                    "<b>%{y}</b><br>Ditempatkan: %{x:,.0f}"
                    "<br>Total mahasiswa: %{customdata[1]:,.0f}"
                    "<br>Tingkat penempatan: %{customdata[0]:.1f}%<extra></extra>"
                ),
            )
            style_figure(fig_prodi, 555)
            fig_prodi.update_layout(
                xaxis_title="Mahasiswa ditempatkan",
                yaxis_title=None,
                margin={"l": 12, "r": 32, "t": 8, "b": 30},
            )
            st.plotly_chart(fig_prodi, use_container_width=True, config=PLOTLY_CONFIG)

        with right:
            st.markdown(
                '<div class="chart-panel-label">Kota Asal dan Lokasi Kerja</div>',
                unsafe_allow_html=True,
            )
            donut_data = pd.DataFrame(
                {
                    "Kategori": ["Kota sama", "Bekerja di kota lain"],
                    "Jumlah": [same_city, relocate],
                }
            )
            fig_donut = px.pie(
                donut_data,
                names="Kategori",
                values="Jumlah",
                hole=0.64,
                color="Kategori",
                color_discrete_map={
                    "Kota sama": CHART_COLORS[5],
                    "Bekerja di kota lain": CHART_COLORS[1],
                },
            )
            fig_donut.update_traces(
                textinfo="percent+label",
                hovertemplate="%{label}: %{value:,.0f}<extra></extra>",
            )
            style_figure(fig_donut, 255)
            fig_donut.update_layout(showlegend=False)
            st.plotly_chart(fig_donut, use_container_width=True, config=PLOTLY_CONFIG)

            st.markdown(
                '<div class="chart-panel-label">Sektor Penempatan Terbanyak</div>',
                unsafe_allow_html=True,
            )
            sector_show = (
                sector_counts.head(6)
                .rename_axis("Sektor")
                .reset_index(name="Jumlah")
                .sort_values("Jumlah")
            )
            fig_sector = px.bar(
                sector_show,
                x="Jumlah",
                y="Sektor",
                orientation="h",
                text="Jumlah",
            )
            fig_sector.update_traces(
                marker_color=[
                    CHART_COLORS[(i + 2) % len(CHART_COLORS)]
                    for i in range(len(sector_show))
                ],
                textposition="outside",
                hovertemplate="%{y}: %{x:,.0f}<extra></extra>",
            )
            style_figure(fig_sector, 255)
            fig_sector.update_layout(
                xaxis_title=None,
                yaxis_title=None,
                margin={"l": 8, "r": 28, "t": 5, "b": 12},
            )
            st.plotly_chart(fig_sector, use_container_width=True, config=PLOTLY_CONFIG)

    elif executive_section == "partners":
        section_header(
            "Mitra dan Wilayah",
            "Lihat persebaran perusahaan serta mitra dengan hasil penempatan terbaik.",
            "MITRA",
            "section_executive_partners",
        )
        map_col, table_col = st.columns([1.02, 0.98], gap="large")

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
        city_counts = (
            company.get("kota", pd.Series(dtype=str))
            .value_counts()
            .rename_axis("kota")
            .reset_index(name="jumlah_perusahaan")
        )
        city_counts["lat"] = city_counts["kota"].map(
            lambda x: CITY_COORDINATES.get(str(x), (np.nan, np.nan))[0]
        )
        city_counts["lon"] = city_counts["kota"].map(
            lambda x: CITY_COORDINATES.get(str(x), (np.nan, np.nan))[1]
        )
        geo_data = city_counts.dropna(subset=["lat", "lon"])

        with map_col:
            st.markdown(
                '<div class="chart-panel-label">Sebaran Perusahaan Mitra</div>',
                unsafe_allow_html=True,
            )
            if not geo_data.empty:
                map_fig = px.scatter_mapbox(
                    geo_data,
                    lat="lat",
                    lon="lon",
                    size="jumlah_perusahaan",
                    color="jumlah_perusahaan",
                    hover_name="kota",
                    hover_data={
                        "lat": False,
                        "lon": False,
                        "jumlah_perusahaan": ":,.0f",
                    },
                    color_continuous_scale=[
                        [0, CHART_COLORS[5]],
                        [0.5, CHART_COLORS[1]],
                        [1, CHART_COLORS[2]],
                    ],
                    size_max=40,
                    zoom=4.3,
                    center={"lat": -7.2, "lon": 110.5},
                )
                map_fig.update_layout(
                    mapbox_style="carto-positron",
                    coloraxis_showscale=False,
                )
                style_figure(map_fig, 535)
                st.plotly_chart(
                    map_fig,
                    use_container_width=True,
                    config=PLOTLY_CONFIG,
                )
            else:
                st.info("Belum ada kota yang dapat dipetakan.")

        with table_col:
            st.markdown(
                '<div class="chart-panel-label">Mitra dengan Hasil Penempatan Terbaik</div>',
                unsafe_allow_html=True,
            )
            partner_display = (
                partner_summary.head(12)
                .rename(
                    columns={
                        "company_name": "Perusahaan",
                        "industry_sector": "Sektor",
                        "kota": "Kota",
                        "candidates_sent": "Kandidat Dikirim",
                        "placed": "Ditempatkan",
                        "success_rate": "Tingkat Keberhasilan (%)",
                        "ghosting_rate": "Tanpa Kabar (%)",
                    }
                )[
                    [
                        "Perusahaan",
                        "Sektor",
                        "Kota",
                        "Kandidat Dikirim",
                        "Ditempatkan",
                        "Tingkat Keberhasilan (%)",
                        "Tanpa Kabar (%)",
                    ]
                ]
            )
            st.dataframe(
                partner_display,
                use_container_width=True,
                hide_index=True,
                height=535,
                column_config={
                    "Tingkat Keberhasilan (%)": st.column_config.ProgressColumn(
                        "Tingkat Keberhasilan (%)",
                        min_value=0,
                        max_value=100,
                        format="%.1f%%",
                    ),
                    "Tanpa Kabar (%)": st.column_config.NumberColumn(format="%.1f%%"),
                },
            )

    else:
        section_header(
            "Insight Penting",
            "Ringkasan temuan yang dapat membantu CDC menentukan fokus tindakan.",
            "INSIGHT",
            "section_executive_insights",
        )
        top_prodi = (
            prodi_summary.sort_values("placed_students", ascending=False).iloc[0]
            if not prodi_summary.empty
            else None
        )
        best_partner = partner_summary.iloc[0] if not partner_summary.empty else None
        mobility_rate = safe_divide(relocate, same_city + relocate) * 100

        i1, i2, i3 = st.columns(3, gap="large")
        with i1:
            insight_card(
                "Sumber kandidat terbesar",
                (
                    f"{top_prodi['program_studi']} menyumbang "
                    f"{format_int(top_prodi['placed_students'])} mahasiswa ditempatkan, "
                    f"dengan tingkat penempatan {top_prodi['placement_rate']:.1f}%."
                    if top_prodi is not None
                    else "Belum ada data program studi yang dapat dirangkum."
                ),
                icon_key="talent_source",
            )
        with i2:
            insight_card(
                "Mitra paling efektif",
                (
                    f"{best_partner['company_name']} mencatat tingkat keberhasilan "
                    f"{best_partner['success_rate']:.1f}% dari "
                    f"{format_int(best_partner['candidates_sent'])} kandidat."
                    if best_partner is not None
                    else "Belum ada mitra yang memenuhi batas minimum kandidat."
                ),
                icon_key="partner_effective",
            )
        with i3:
            insight_card(
                "Mobilitas penempatan",
                f"{mobility_rate:.1f}% penempatan yang terpetakan berlangsung di luar kota asal mahasiswa.",
                icon_key="mobility",
            )

        st.markdown('<div style="height:18px;"></div>', unsafe_allow_html=True)
        summary_left, summary_right = st.columns(2, gap="large")
        with summary_left:
            st.markdown(
                f"""
                <div class="hop-card">
                  <div class="card-title">Peluang tindakan</div>
                  <div class="card-sub">
                    Prioritaskan program studi dengan jumlah mahasiswa aktif besar tetapi
                    tingkat penempatan masih rendah. Gunakan bagian “Penempatan Mahasiswa”
                    untuk membandingkannya.
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with summary_right:
            st.markdown(
                f"""
                <div class="hop-card">
                  <div class="card-title">Catatan untuk kemitraan</div>
                  <div class="card-sub">
                    Pertahankan hubungan dengan mitra yang memiliki tingkat keberhasilan tinggi,
                    lalu evaluasi mitra dengan banyak kandidat tetapi hasil penempatan rendah.
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# =============================================================================
# PAGE 2: TEMUKAN KANDIDAT
# Dibagi menjadi dua bagian: pengaturan dan hasil.
# =============================================================================
elif current_page_key == "matching":
    matching_section = section_navigation(
        "matching",
        {
            "setup": ("Atur Kriteria", "section_matching_setup"),
            "results": ("Lihat Kandidat", "section_matching_results"),
        },
    )

    request_mart = talent_request.merge(
        company[["id_company", "kota", "company_name", "industry_sector"]]
        .drop_duplicates("id_company"),
        on="id_company",
        how="left",
        suffixes=("", "_master"),
    )
    request_mart["request_age"] = (
        AS_OF - request_mart["request_date"]
    ).dt.days.clip(lower=0)
    request_mart["priority_score"] = (
        request_mart["request_age"] * 0.60
        + request_mart["headcount"].fillna(0) * 0.40
    )

    latest_tc = (
        tracking_company.sort_values("request_date", na_position="first")
        .drop_duplicates("id_talent_req", keep="last")
    )
    request_mart = request_mart.merge(
        latest_tc[["id_talent_req", "progress", "send_date"]],
        on="id_talent_req",
        how="left",
    )
    request_mart["is_open"] = request_mart["progress"].fillna("Draft").ne("Closed")
    open_requests = request_mart[request_mart["is_open"]].copy()

    readiness_latest = (
        readiness.sort_values("sync_date", na_position="first")
        .drop_duplicates("NIM", keep="last")
        .copy()
    )
    candidate_ready_mask = (
        readiness_latest.get("status", "").eq("Active")
        & readiness_latest.get("ketersediaan", "").eq("Available")
        & readiness_latest.get("CV", "").eq("Ada")
        & ~readiness_latest["is_placed"]
    )
    candidate_ready_count = int(
        readiness_latest.loc[candidate_ready_mask, "NIM"].nunique()
    )
    active_available_count = int(
        readiness_latest.loc[
            readiness_latest.get("status", "").eq("Active")
            & readiness_latest.get("ketersediaan", "").eq("Available"),
            "NIM",
        ].nunique()
    )
    profile_complete_mask = (
        readiness_latest.get(
            "IPK", pd.Series(np.nan, index=readiness_latest.index)
        ).notna()
        & readiness_latest.get(
            "program_studi", pd.Series("", index=readiness_latest.index)
        ).fillna("").astype(str).str.strip().ne("")
        & readiness_latest.get(
            "domisili", pd.Series("", index=readiness_latest.index)
        ).fillna("").astype(str).str.strip().ne("")
        & readiness_latest.get(
            "CV", pd.Series("", index=readiness_latest.index)
        ).eq("Ada")
        & readiness_latest.get(
            "tools_normalized",
            pd.Series([[] for _ in range(len(readiness_latest))], index=readiness_latest.index),
        ).map(bool)
    )
    profile_complete_count = int(
        readiness_latest.loc[profile_complete_mask, "NIM"].nunique()
    )
    profile_complete_rate = (
        safe_divide(profile_complete_count, readiness_latest["NIM"].nunique()) * 100
    )
    active_request_count = int(open_requests["id_talent_req"].nunique())
    active_headcount = int(
        open_requests.get("headcount", pd.Series(dtype=float)).fillna(0).sum()
    )

    TOOL_ALIASES = {
        "python": ["python"],
        "r": [" r ", "python/r"],
        "sql": ["sql"],
        "power bi": ["power bi", "powerbi"],
        "tableau": ["tableau"],
        "excel": ["excel", "microsoft excel"],
        "figma": ["figma"],
        "adobe xd": ["adobe xd"],
        "autocad": ["autocad"],
        "solidworks": ["solidworks"],
        "sap": ["sap"],
        "spss": ["spss"],
        "javascript": ["javascript"],
        "react": ["react"],
        "html/css": ["html/css", "html", "css"],
        "git": ["git"],
        "seo": ["seo"],
        "matlab": ["matlab"],
        "arcgis": ["arcgis"],
        "qgis": ["qgis"],
        "myob": ["myob"],
        "accurate": ["accurate"],
        "canva": ["canva"],
    }

    def extract_request_tools(text_value: object) -> list[str]:
        padded = f" {normalize_text(text_value)} "
        return [
            canonical
            for canonical, aliases in TOOL_ALIASES.items()
            if any(alias in padded for alias in aliases)
        ]

    def jaccard(left: Iterable[str], right: Iterable[str]) -> float:
        a, b = set(left), set(right)
        return len(a & b) / len(a | b) if a and b else 0.0

    def prodi_similarity(student_prodi: object, requirement: object) -> float:
        student_value = normalize_text(student_prodi)
        needed = [normalize_text(item) for item in str(requirement or "").split(",")]
        if student_value in needed:
            return 1.0
        student_words = {word for word in student_value.split() if len(word) > 3}
        return 0.5 if any(
            student_words.intersection(set(item.split())) for item in needed
        ) else 0.0

    if matching_section == "setup":
        section_header(
            "Pencocokan Kandidat",
            "Pilih kebutuhan perusahaan, atur syarat kandidat, lalu cari kandidat yang paling sesuai.",
            "PENCOCOKAN",
            "section_matching_setup",
        )
        s1, s2, s3 = st.columns(3, gap="large")
        with s1:
            kpi_card(
                "Kandidat Siap",
                format_int(candidate_ready_count),
                f"{format_int(active_available_count)} mahasiswa aktif dan tersedia",
                "candidate_ready",
            )
        with s2:
            kpi_card(
                "Profil Lengkap",
                format_pct(profile_complete_rate),
                f"{format_int(profile_complete_count)} profil siap dianalisis",
                "profile_complete",
            )
        with s3:
            kpi_card(
                "Kebutuhan Aktif",
                format_int(active_request_count),
                f"Total kebutuhan {format_int(active_headcount)} kandidat",
                "request_active",
            )

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        with st.form("matching_form"):
            f1, f2, f3 = st.columns([1.0, 1.0, 1.2], gap="large")

            with f1:
                panel_heading(
                    "Syarat Dasar",
                    "Atur batas minimum kandidat",
                    "panel_eligibility",
                )
                ipk_min = st.slider("IPK minimum", 2.00, 4.00, 2.50, 0.05)
                semester_min = st.slider("Semester minimum", 1, 14, 1)
                cv_required = st.checkbox("Harus memiliki CV", value=True)
                portfolio_required = st.checkbox(
                    "Harus memiliki portofolio", value=False
                )

            with f2:
                panel_heading(
                    "Penyaring Kandidat",
                    "Persempit kandidat sesuai kebutuhan",
                    "panel_filter",
                )
                domicile_options = ["Semua kota"] + sorted(
                    readiness["domisili"].dropna().astype(str).unique().tolist()
                )
                prodi_options = ["Semua program studi"] + sorted(
                    readiness["program_studi"].dropna().astype(str).unique().tolist()
                )
                domicile_filter = st.selectbox("Kota asal", domicile_options)
                prodi_filter = st.selectbox("Program studi", prodi_options)
                placement_filter = st.selectbox(
                    "Jenis kesempatan",
                    ["Semua", "Magang", "Part-time", "Full-time"],
                )

            with f3:
                panel_heading(
                    "Kebutuhan Perusahaan",
                    "Pilih posisi yang ingin dicari kandidatnya",
                    "panel_request",
                )
                request_view = open_requests.copy()
                if placement_filter != "Semua":
                    request_view = request_view[
                        request_view["jenis_penempatan"] == placement_filter
                    ]
                request_view = request_view.sort_values(
                    "priority_score", ascending=False
                ).head(1000)
                if request_view.empty:
                    request_view = open_requests.sort_values(
                        "priority_score", ascending=False
                    ).head(1000)
                    st.warning(
                        "Tidak ada kebutuhan pada jenis ini. Seluruh kebutuhan aktif ditampilkan."
                    )

                selected_request = None
                if not request_view.empty:
                    request_view["label"] = (
                        request_view["id_talent_req"].astype(str)
                        + " · "
                        + request_view["nama_posisi"].astype(str)
                        + " | "
                        + request_view["nama_perusahaan"].astype(str)
                    )
                    selected_label = st.selectbox(
                        "Pilih kebutuhan", request_view["label"].tolist()
                    )
                    selected_request = request_view.loc[
                        request_view["label"] == selected_label
                    ].iloc[0]
                    st.caption(
                        f"Urutan prioritas {selected_request['priority_score']:.1f} · "
                        f"dibuka {int(selected_request['request_age'])} hari · "
                        f"membutuhkan {int(selected_request['headcount'])} orang"
                    )
                else:
                    st.info("Belum ada kebutuhan perusahaan yang aktif.")

            run_matching = st.form_submit_button(
                "Cari Kandidat Terbaik",
                use_container_width=True,
                disabled=selected_request is None,
            )

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

            request_tools = extract_request_tools(
                request_row.get("deskripsi_requirement", "")
            )
            working_arrangement = normalize_text(
                request_row.get("working_arrangement", "")
            )
            request_city = normalize_text(request_row.get("kota", ""))
            minimum_semester = float(
                request_row.get("minimum_semester", 0) or 0
            )

            rows = []
            for candidate in pool.itertuples(index=False):
                candidate_data = candidate._asdict()
                candidate_tools = set(
                    candidate_data.get("tools_normalized", [])
                )
                tool_score = jaccard(candidate_tools, request_tools)
                academic_score = (
                    1.0
                    if float(candidate_data.get("semester", 0) or 0)
                    >= minimum_semester
                    else 0.0
                )
                study_score = prodi_similarity(
                    candidate_data.get("program_studi"),
                    request_row.get("bidang_studi_dibutuhkan"),
                )
                location_score = (
                    1.0
                    if "wfh" in working_arrangement
                    else (
                        1.0
                        if normalize_text(candidate_data.get("domisili"))
                        == request_city
                        else 0.0
                    )
                )
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
                        "Kota Asal": candidate_data.get("domisili", "-"),
                        "Keahlian yang Cocok": ", ".join(common_tools)
                        if common_tools
                        else "-",
                        "Kecocokan Keahlian (%)": tool_score * 100,
                        "Kecocokan Program Studi (%)": study_score * 100,
                        "Kecocokan Lokasi (%)": location_score * 100,
                        "Tingkat Kecocokan (%)": total_score,
                    }
                )
            result = pd.DataFrame(rows)
            return (
                result.sort_values(
                    ["Tingkat Kecocokan (%)", "IPK"], ascending=False
                ).head(40)
                if not result.empty
                else result
            )

        if run_matching and selected_request is not None:
            with st.spinner("Mencari kandidat yang paling sesuai..."):
                st.session_state["matching_results"] = compute_matching_results(
                    selected_request
                )
                st.session_state["matching_request"] = selected_request.to_dict()
            # UX: hasil langsung dibuka setelah pengguna menekan tombol pencarian.
            st.query_params["page"] = "matching"
            st.query_params["section"] = "results"
            st.rerun()

    else:
        section_header(
            "Hasil Kandidat",
            "Tinjau kandidat berdasarkan tingkat kecocokan dan kebutuhan posisi.",
            "HASIL",
            "section_matching_results",
        )
        _, edit_filter_col = st.columns([4.8, 1.2])
        with edit_filter_col:
            if st.button(
                "Ubah Kriteria",
                use_container_width=True,
                key="edit_matching_criteria",
            ):
                st.query_params["page"] = "matching"
                st.query_params["section"] = "setup"
                st.rerun()

        if "matching_results" not in st.session_state:
            st.markdown(
                """
                <div class="hop-card" style="padding:34px;text-align:center;">
                  <div class="card-title">Belum ada hasil pencocokan</div>
                  <div class="card-sub">
                    Buka bagian “Atur Pencocokan”, pilih kebutuhan perusahaan,
                    lalu tekan tombol “Cari Kandidat Terbaik”.
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            result = st.session_state["matching_results"].copy()
            request_info = st.session_state["matching_request"]
            info_col, action_col = st.columns([1.5, 1.0], gap="large")
            with info_col:
                st.markdown(
                    f"""
                    <div class="hop-card">
                      <div class="card-title">{html.escape(str(request_info.get('nama_posisi', '-')))}</div>
                      <div class="card-sub">
                        {html.escape(str(request_info.get('nama_perusahaan', '-')))} ·
                        {html.escape(str(request_info.get('jenis_penempatan', '-')))} ·
                        {html.escape(str(request_info.get('working_arrangement', '-')))} ·
                        kebutuhan {int(request_info.get('headcount', 0) or 0)} orang
                      </div>
                      <div class="card-sub" style="margin-top:8px;">
                        {html.escape(str(request_info.get('deskripsi_requirement', '-')))}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if result.empty:
                st.warning(
                    "Belum ada kandidat yang memenuhi seluruh syarat. Longgarkan penyaring lalu coba lagi."
                )
            else:
                display_result = result.copy()
                if IS_PUBLIC:
                    display_result["Nama"] = display_result["Nama"].map(mask_name)
                    display_result["NIM"] = display_result["NIM"].map(mask_nim)

                with action_col:
                    raw_nim = result["NIM"].map(mask_nim) if IS_PUBLIC else result["NIM"].astype(str)
                    raw_name = result["Nama"].map(mask_name) if IS_PUBLIC else result["Nama"].astype(str)
                    selection_labels = (
                        raw_nim
                        + " · "
                        + raw_name
                        + " · "
                        + result["Tingkat Kecocokan (%)"].round(1).astype(str)
                        + "%"
                    ).tolist()
                    selected_candidates = st.multiselect(
                        "Pilih kandidat untuk daftar kirim",
                        selection_labels,
                        max_selections=int(request_info.get("headcount", 1) or 1) * 3,
                    )
                    if st.button("Tambahkan ke Daftar Kirim", use_container_width=True):
                        if selected_candidates:
                            st.success(
                                f"{len(selected_candidates)} kandidat ditambahkan ke daftar simulasi."
                            )
                        else:
                            st.warning("Pilih minimal satu kandidat.")

                st.dataframe(
                    display_result,
                    use_container_width=True,
                    hide_index=True,
                    height=515,
                    column_config={
                        "IPK": st.column_config.NumberColumn(format="%.2f"),
                        "Kecocokan Keahlian (%)": st.column_config.NumberColumn(format="%.0f%%"),
                        "Kecocokan Program Studi (%)": st.column_config.NumberColumn(format="%.0f%%"),
                        "Kecocokan Lokasi (%)": st.column_config.NumberColumn(format="%.0f%%"),
                        "Tingkat Kecocokan (%)": st.column_config.ProgressColumn(
                            "Tingkat Kecocokan (%)",
                            min_value=0,
                            max_value=100,
                            format="%.1f%%",
                        ),
                    },
                )


# =============================================================================
# PAGE 3: PANTAU PROSES SELEKSI
# Dibagi menjadi empat bagian agar tidak memerlukan scroll panjang.
# =============================================================================
else:
    operations_section = section_navigation(
        "operations",
        {
            "pipeline": ("Tahapan Seleksi", "section_operations_pipeline"),
            "delays": ("Respons Terlambat", "section_operations_delays"),
            "followup": ("Daftar Tindak Lanjut", "section_operations_followup"),
            "outcomes": ("Hasil Akhir Seleksi", "section_operations_outcomes"),
        },
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
    funnel_df["Tahap Tampilan"] = funnel_df["Tahap"].map(stage_label)

    ews = placement_mart[
        placement_mart.get("progress_student", "").isin(ACTIVE_STAGES)
    ].copy()
    if "jenis_penempatan" not in ews.columns and "id_talent_req" in ews.columns:
        ews = ews.merge(
            talent_request[
                ["id_talent_req", "jenis_penempatan"]
            ].drop_duplicates("id_talent_req"),
            on="id_talent_req",
            how="left",
        )

    ews["days_idle"] = (
        AS_OF - pd.to_datetime(ews["last_update"], errors="coerce")
    ).dt.days.clip(lower=0)
    ews["base_sla"] = np.where(
        ews["progress_student"].eq("Final Interview"), 14, 7
    )
    ews["days_over_sla"] = (
        ews["days_idle"] - ews["base_sla"]
    ).fillna(0).astype(int)
    ews["is_overdue"] = ews["days_over_sla"] > 0
    ews["duration_bucket"] = np.select(
        [
            ews["days_over_sla"] <= 0,
            ews["days_over_sla"].between(1, 7),
            ews["days_over_sla"].between(8, 30),
            ews["days_over_sla"].between(31, 90),
        ],
        [
            "Dalam batas waktu",
            "1–7 hari",
            "8–30 hari",
            "31–90 hari",
        ],
        default=">90 hari",
    )
    ews["priority"] = np.select(
        [
            ews["days_over_sla"] > 90,
            ews["days_over_sla"] > 30,
            ews["days_over_sla"] > 7,
            ews["days_over_sla"] > 0,
        ],
        ["Segera", "Tinggi", "Menengah", "Pantau"],
        default="Dalam batas waktu",
    )

    total_active_processes = int(len(ews))
    overdue = ews[ews["is_overdue"]].copy()
    overdue_count = int(len(overdue))
    overdue_rate = safe_divide(overdue_count, total_active_processes) * 100
    median_wait = (
        int(round(overdue["days_idle"].median())) if not overdue.empty else 0
    )
    overdue_by_stage = overdue["progress_student"].value_counts()
    stalled_stage = (
        str(overdue_by_stage.index[0]) if not overdue_by_stage.empty else "Belum ada"
    )
    stalled_stage_count = (
        int(overdue_by_stage.iloc[0]) if not overdue_by_stage.empty else 0
    )
    company_column = "company" if "company" in ews.columns else "company_name"
    company_series = overdue.get(company_column, pd.Series(dtype=str))
    affected_companies = int(company_series.dropna().astype(str).nunique())

    if operations_section == "pipeline":
        section_header(
            "Tahapan Proses Seleksi",
            "Jumlah proses pada setiap tahap saat ini. Angka ini bukan tingkat kelulusan antartahap.",
            "TAHAP SELEKSI",
            "section_operations_pipeline",
        )
        funnel_col, status_col = st.columns([1.0, 1.0], gap="large")
        with funnel_col:
            st.markdown(
                '<div class="chart-panel-label">Sebaran Tahap Utama</div>',
                unsafe_allow_html=True,
            )
            funnel_fig = go.Figure(
                go.Funnel(
                    y=funnel_df["Tahap Tampilan"],
                    x=funnel_df["Kandidat"],
                    textinfo="value",
                    marker={
                        "color": [
                            CHART_COLORS[5],
                            CHART_COLORS[0],
                            CHART_COLORS[1],
                            CHART_COLORS[3],
                            CHART_COLORS[2],
                            CHART_COLORS[6],
                        ]
                    },
                    connector={"line": {"color": "#7A8A99", "width": 1.1}},
                )
            )
            style_figure(funnel_fig, 500)
            st.plotly_chart(
                funnel_fig,
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )

        with status_col:
            st.markdown(
                '<div class="chart-panel-label">Seluruh Status Proses</div>',
                unsafe_allow_html=True,
            )
            progress_dist = (
                tracking_student.get("progress_student", pd.Series(dtype=str))
                .value_counts()
                .head(12)
            )
            progress_df = (
                progress_dist.rename_axis("Status")
                .reset_index(name="Jumlah")
                .sort_values("Jumlah")
            )
            progress_df["Status Tampilan"] = progress_df["Status"].map(stage_label)
            status_fig = px.bar(
                progress_df,
                x="Jumlah",
                y="Status Tampilan",
                orientation="h",
                text="Jumlah",
            )
            status_fig.update_traces(
                marker_color=[
                    CHART_COLORS[6]
                    if status == "Placement"
                    else CHART_COLORS[2]
                    if status == "Rejected"
                    else CHART_COLORS[4]
                    if status == "Ghosting"
                    else CHART_COLORS[i % len(CHART_COLORS)]
                    for i, status in enumerate(progress_df["Status"])
                ],
                textposition="outside",
                hovertemplate="%{y}: %{x:,.0f}<extra></extra>",
            )
            style_figure(status_fig, 500)
            status_fig.update_layout(
                xaxis_title=None,
                yaxis_title=None,
                margin={"l": 8, "r": 30, "t": 8, "b": 15},
            )
            st.plotly_chart(
                status_fig,
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )

        losses = [
            (first, second, int(funnel_counts[first] - funnel_counts[second]))
            for first, second in zip(funnel_order[:-1], funnel_order[1:])
        ]
        losses = sorted(losses, key=lambda item: item[2], reverse=True)
        if losses:
            first, second, loss = losses[0]
            insight_card(
                "Perbedaan volume terbesar",
                (
                    f"Selisih terbesar berada antara {stage_label(first)} dan "
                    f"{stage_label(second)}, yaitu {format_int(max(loss, 0))} proses."
                ),
                "PERHATIAN",
                icon_key="bottleneck",
            )

    elif operations_section == "delays":
        section_header(
            "Respons dan Tindak Lanjut",
            "Lihat jumlah proses terlambat, lama keterlambatan, dan tahap yang paling perlu diperhatikan.",
            "TINDAK LANJUT",
            "section_operations_delays",
        )
        m1, m2, m3, m4 = st.columns(4, gap="large")
        with m1:
            kpi_card(
                "Melewati Batas Waktu",
                format_int(overdue_count),
                f"{format_pct(overdue_rate)} dari proses aktif",
                "overdue",
            )
        with m2:
            kpi_card(
                "Waktu Tunggu Tipikal",
                f"{format_int(median_wait)} hari",
                "Nilai tengah sejak pembaruan terakhir",
                "median_wait",
            )
        with m3:
            kpi_card(
                "Tahap Paling Tertahan",
                stage_label(stalled_stage),
                f"{format_int(stalled_stage_count)} proses terlambat",
                "stage_stalled",
                value_kind="text",
            )
        with m4:
            kpi_card(
                "Perusahaan Perlu Dihubungi",
                format_int(affected_companies),
                "Memiliki minimal satu proses terlambat",
                "affected_companies",
            )

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        aging_col, stage_col = st.columns([1.02, 0.98], gap="large")

        with aging_col:
            st.markdown(
                '<div class="chart-panel-label">Lama Keterlambatan</div>',
                unsafe_allow_html=True,
            )
            aging_order = ["1–7 hari", "8–30 hari", "31–90 hari", ">90 hari"]
            aging_colors = {
                "1–7 hari": "#7FA6E8",
                "8–30 hari": "#A18BE0",
                "31–90 hari": "#E7B75F",
                ">90 hari": "#E99082",
            }
            aging_counts = (
                overdue["duration_bucket"]
                .value_counts()
                .reindex(aging_order)
                .fillna(0)
                .astype(int)
            )
            aging_total = int(aging_counts.sum())
            aging_fig = go.Figure()
            aging_legend_labels = {
                "1–7 hari": "1–7 hari · baru melewati batas",
                "8–30 hari": "8–30 hari · perlu dipantau",
                "31–90 hari": "31–90 hari · prioritas tinggi",
                ">90 hari": ">90 hari · segera ditindaklanjuti",
            }
            for bucket in aging_order:
                count = int(aging_counts[bucket])
                percentage = safe_divide(count, aging_total) * 100
                aging_fig.add_trace(
                    go.Bar(
                        y=["Proses terlambat"],
                        x=[count],
                        name=aging_legend_labels[bucket],
                        legendgroup=bucket,
                        orientation="h",
                        marker_color=aging_colors[bucket],
                        text=[
                            f"{format_int(count)}<br>{percentage:.1f}%"
                            if count > 0
                            else ""
                        ],
                        textposition="inside",
                        insidetextanchor="middle",
                        hovertemplate=(
                            f"<b>{bucket}</b><br>Jumlah: %{{x:,.0f}}"
                            f"<br>Bagian: {percentage:.1f}%<extra></extra>"
                        ),
                    )
                )
            style_figure(aging_fig, 315)
            aging_fig.update_layout(
                barmode="stack",
                xaxis_title="Jumlah proses",
                yaxis_title=None,
                legend={
                    "title": {
                        "text": "<b>Keterangan warna</b>",
                        "font": {"size": 11, "color": DEEP_TEAL},
                    },
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.05,
                    "xanchor": "left",
                    "x": 0,
                    "traceorder": "normal",
                    "font": {"size": 10.5, "color": DEEP_TEAL},
                    "bgcolor": "rgba(255,255,255,.96)",
                    "bordercolor": BORDER_LIGHT,
                    "borderwidth": 1,
                    "itemsizing": "constant",
                },
                margin={"l": 15, "r": 15, "t": 88, "b": 30},
            )
            aging_fig.update_yaxes(showticklabels=False)
            st.plotly_chart(
                aging_fig,
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )

        with stage_col:
            st.markdown(
                '<div class="chart-panel-label">Proses Terlambat per Tahap</div>',
                unsafe_allow_html=True,
            )
            stage_delay_df = (
                overdue.groupby("progress_student", dropna=False)
                .size()
                .rename("Jumlah")
                .reset_index()
                .rename(columns={"progress_student": "Tahap"})
                .sort_values("Jumlah")
            )
            stage_delay_df["Tahap Tampilan"] = stage_delay_df["Tahap"].map(stage_label)
            if stage_delay_df.empty:
                st.info("Belum ada proses yang melewati batas waktu.")
            else:
                stage_delay_fig = px.bar(
                    stage_delay_df,
                    x="Jumlah",
                    y="Tahap Tampilan",
                    orientation="h",
                    text="Jumlah",
                )
                stage_delay_fig.update_traces(
                    marker_color=[
                        CHART_COLORS[(index + 1) % len(CHART_COLORS)]
                        for index in range(len(stage_delay_df))
                    ],
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>Jumlah: %{x:,.0f}<extra></extra>",
                )
                style_figure(stage_delay_fig, 315)
                stage_delay_fig.update_layout(
                    xaxis_title="Jumlah proses",
                    yaxis_title=None,
                    margin={"l": 10, "r": 28, "t": 8, "b": 30},
                )
                st.plotly_chart(
                    stage_delay_fig,
                    use_container_width=True,
                    config=PLOTLY_CONFIG,
                )

    elif operations_section == "followup":
        section_header(
            "Daftar Tindak Lanjut",
            "Saring proses yang perlu dihubungi, lalu gunakan tombol WhatsApp untuk meminta pembaruan.",
            "PRIORITAS",
            "section_operations_followup",
        )
        company_options = sorted(
            ews.get(company_column, pd.Series(dtype=str))
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        placement_options = sorted(
            ews.get("jenis_penempatan", pd.Series(dtype=str))
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        filter1, filter2, filter3, filter4 = st.columns(
            [1.15, 1.0, 1.0, 1.0], gap="medium"
        )
        with filter1:
            company_filter = st.selectbox(
                "Perusahaan", ["Semua perusahaan"] + company_options
            )
        with filter2:
            stage_filter = st.selectbox(
                "Tahap",
                ["Semua tahap"] + ACTIVE_STAGES,
                format_func=lambda value: (
                    value if value == "Semua tahap" else stage_label(value)
                ),
            )
        with filter3:
            duration_filter = st.selectbox(
                "Lama keterlambatan",
                [
                    "Semua durasi",
                    "Dalam batas waktu",
                    "1–7 hari",
                    "8–30 hari",
                    "31–90 hari",
                    ">90 hari",
                ],
            )
        with filter4:
            placement_filter_ews = st.selectbox(
                "Jenis kesempatan",
                ["Semua jenis"] + placement_options,
            )

        ews_view = ews.copy()
        if company_filter != "Semua perusahaan":
            ews_view = ews_view[
                ews_view[company_column].astype(str).eq(company_filter)
            ]
        if stage_filter != "Semua tahap":
            ews_view = ews_view[
                ews_view["progress_student"].eq(stage_filter)
            ]
        if duration_filter != "Semua durasi":
            ews_view = ews_view[
                ews_view["duration_bucket"].eq(duration_filter)
            ]
        if (
            placement_filter_ews != "Semua jenis"
            and "jenis_penempatan" in ews_view.columns
        ):
            ews_view = ews_view[
                ews_view["jenis_penempatan"]
                .astype(str)
                .eq(placement_filter_ews)
            ]

        priority_order = pd.CategoricalDtype(
            ["Segera", "Tinggi", "Menengah", "Pantau", "Dalam batas waktu"],
            ordered=True,
        )
        ews_view["priority"] = ews_view["priority"].astype(priority_order)
        ews_view = ews_view.sort_values(
            ["priority", "days_idle"], ascending=[True, False]
        ).head(120)
        ews_view["priority"] = ews_view["priority"].astype(str)

        wa_lookup = (
            status_student.sort_values("sync_date", na_position="first")
            .drop_duplicates("NIM", keep="last")[["NIM", "no_whatsapp"]]
            .copy()
        )
        wa_lookup["NIM"] = wa_lookup["NIM"].astype(str)
        ews_view["NIM"] = ews_view["NIM"].astype(str)
        ews_view = ews_view.merge(wa_lookup, on="NIM", how="left")

        display_columns = [
            "NIM",
            "student_name",
            "position",
            company_column,
            "progress_student",
            "last_update",
            "days_idle",
            "priority",
            "no_whatsapp",
        ]
        if "jenis_penempatan" in ews_view.columns:
            display_columns.insert(5, "jenis_penempatan")
        ews_display = ews_view[display_columns].copy()
        ews_display["stage_display"] = ews_display["progress_student"].map(stage_label)
        ews_display["wa_followup_link"] = [
            wa_followup_link(
                row["no_whatsapp"],
                row["student_name"],
                row[company_column],
                stage_label(row["progress_student"]),
            )
            for _, row in ews_display.iterrows()
        ]
        ews_display = ews_display.drop(
            columns=["no_whatsapp", "progress_student"]
        )
        if IS_PUBLIC:
            ews_display["student_name"] = ews_display["student_name"].map(mask_name)
            ews_display["NIM"] = ews_display["NIM"].map(mask_nim)

        rename_columns = {
            "student_name": "Mahasiswa",
            "position": "Posisi",
            company_column: "Perusahaan",
            "stage_display": "Tahap",
            "jenis_penempatan": "Jenis Kesempatan",
            "last_update": "Pembaruan Terakhir",
            "days_idle": "Hari Menunggu",
            "priority": "Prioritas",
        }
        ews_display = ews_display.rename(columns=rename_columns)

        if ews_display.empty:
            st.info("Tidak ada proses yang sesuai dengan pilihan saat ini.")
        else:
            priority_colors = {
                "Segera": "#E5484D",
                "Tinggi": "#F2994A",
                "Menengah": "#D9A72B",
                "Pantau": "#4299B8",
                "Dalam batas waktu": "#27AE60",
            }
            # Gunakan emoji percakapan agar tombol lebih ringan, konsisten,
            # dan tidak bergantung pada file ikon eksternal.
            chat_icon_html = "<span class='ews-wa-emoji' aria-hidden='true'>💬</span>"
            table_columns = [
                column
                for column in ews_display.columns
                if column != "wa_followup_link"
            ]
            header_html = "".join(
                f"<th>{html.escape(str(col))}</th>" for col in table_columns
            )
            header_html += "<th>Hubungi</th>"

            rows_html = []
            for _, row in ews_display.iterrows():
                cells = []
                for col in table_columns:
                    value = row[col]
                    if col == "Pembaruan Terakhir" and pd.notna(value):
                        cells.append(
                            f"<td>{pd.to_datetime(value).strftime('%d %b %Y')}</td>"
                        )
                    elif col == "Hari Menunggu" and pd.notna(value):
                        cells.append(
                            f"<td class='ews-num'>{format_int(value)} hari</td>"
                        )
                    elif col == "Prioritas":
                        color = priority_colors.get(str(value), "#8FA3B0")
                        cells.append(
                            f"<td><span class='ews-badge' "
                            f"style='background:{color}22;color:{color};'>"
                            f"{html.escape(str(value))}</span></td>"
                        )
                    else:
                        shown = (
                            html.escape(str(value))
                            if pd.notna(value) and str(value).strip()
                            else "-"
                        )
                        cells.append(f"<td>{shown}</td>")

                wa_link = row["wa_followup_link"]
                if pd.notna(wa_link):
                    cells.append(
                        f"<td><a class='ews-wa-btn' href='{wa_link}' "
                        f"target='_blank'>{chat_icon_html} WhatsApp</a></td>"
                    )
                else:
                    cells.append(
                        f"<td><span class='ews-wa-btn ews-wa-btn--disabled'>"
                        f"{chat_icon_html} WhatsApp</span></td>"
                    )
                rows_html.append(f"<tr>{''.join(cells)}</tr>")

            table_html = f"""
            <style>
            .ews-table-wrap {{
                max-height: 510px; overflow: auto; border-radius: 18px;
                border: 1px solid #CFE7E2; background: #FFFFFF;
                box-shadow: 0 18px 42px rgba(28,94,88,.13);
                scrollbar-color: #A9D8D1 #F3FAF8;
                scrollbar-width: thin;
            }}
            .ews-table-wrap::-webkit-scrollbar {{ width: 10px; height: 10px; }}
            .ews-table-wrap::-webkit-scrollbar-track {{ background: #F3FAF8; }}
            .ews-table-wrap::-webkit-scrollbar-thumb {{
                background: #A9D8D1; border-radius: 999px; border: 2px solid #F3FAF8;
            }}
            .ews-table {{
                width: 100%; border-collapse: separate; border-spacing: 0; font-size: 12px;
                font-family: {FONT_BODY}; color: #153B39; white-space: nowrap;
                background: #FFFFFF;
            }}
            .ews-table thead th {{
                position: sticky; top: 0; z-index: 2;
                background: #0A4F4A; color: #FFFFFF; text-align: left;
                font-size: 10.8px; font-weight: 750; letter-spacing: .2px;
                padding: 12px 13px; border-bottom: 1px solid #CFE7E2;
                box-shadow: 0 1px 0 rgba(20,112,107,.06);
            }}
            .ews-table thead th:first-child {{ border-top-left-radius: 17px; }}
            .ews-table thead th:last-child {{ border-top-right-radius: 17px; }}
            .ews-table tbody td {{
                padding: 10px 13px; background: #FFFFFF;
                border-bottom: 1px solid #E5F0EE; color: #234D49;
                transition: background-color .16s ease, color .16s ease;
            }}
            .ews-table tbody tr:nth-child(even) td {{ background: #FBFEFD; }}
            .ews-table tbody tr:hover td {{
                background: #DDF5F1 !important; color: #0B5F5A;
            }}
            .ews-table tbody tr:hover {{ cursor: default; }}
            .ews-table tbody tr:last-child td {{ border-bottom: 0; }}
            .ews-table .ews-num {{
                text-align: right; font-family: {FONT_MONO}; color: #0C706B;
            }}
            .ews-badge {{
                display: inline-flex; align-items: center;
                padding: 4px 9px; border-radius: 999px; font-size: 10.7px; font-weight: 750;
            }}
            .ews-wa-btn {{
                display: inline-flex !important; align-items: center; justify-content: center;
                gap: 6px; min-width: 102px; padding: 7px 12px; border-radius: 10px;
                border: 1px solid rgba(16,140,79,.12); font-size: 11.5px;
                font-weight: 750 !important; text-decoration: none !important;
                color: #FFFFFF !important;
                background: linear-gradient(135deg, #26C66C, #169C55);
                box-shadow: 0 7px 15px rgba(22,156,85,.18);
                transition: transform .16s ease, box-shadow .16s ease, filter .16s ease;
            }}
            .ews-wa-btn:hover {{
                transform: translateY(-1px); filter: brightness(1.03);
                box-shadow: 0 10px 20px rgba(22,156,85,.24);
            }}
            .ews-wa-emoji {{
                display: inline-flex; align-items: center; justify-content: center;
                font-size: 14px; line-height: 1;
            }}
            .ews-wa-btn--disabled {{
                background: #EDF3F2; color: #91A5A2 !important;
                border-color: #DFE9E7; box-shadow: none;
            }}
            .ews-wa-btn--disabled:hover {{ transform: none; filter: none; box-shadow: none; }}
            </style>
            <div class="ews-table-wrap">
              <table class="ews-table">
                <thead><tr>{header_html}</tr></thead>
                <tbody>{''.join(rows_html)}</tbody>
              </table>
            </div>
            """
            st.markdown(table_html, unsafe_allow_html=True)

    else:
        section_header(
            "Hasil Akhir Proses Seleksi",
            "Lihat penempatan, penolakan, dan proses tanpa kabar untuk menentukan perbaikan berikutnya.",
            "HASIL SELEKSI",
            "section_operations_outcomes",
        )
        rejection_counts = (
            tracking_student.get("rejection", pd.Series(dtype=str))
            .replace("On Progress", np.nan)
            .dropna()
            .value_counts()
            .rename_axis("Outcome")
            .reset_index(name="Jumlah")
        )
        if rejection_counts.empty:
            st.info("Belum ada hasil akhir seleksi yang dapat ditampilkan.")
        else:
            rejection_counts["Hasil"] = rejection_counts["Outcome"].map(
                lambda value: OUTCOME_LABELS.get(str(value), str(value))
            )
            rejection_show = rejection_counts.sort_values("Jumlah")
            rejection_fig = px.bar(
                rejection_show,
                x="Jumlah",
                y="Hasil",
                orientation="h",
                text="Jumlah",
            )
            rejection_fig.update_traces(
                marker_color=[
                    CHART_COLORS[6]
                    if outcome == "Placement"
                    else CHART_COLORS[4]
                    if outcome == "Ghosting"
                    else CHART_COLORS[(i + 1) % len(CHART_COLORS)]
                    for i, outcome in enumerate(rejection_show["Outcome"])
                ],
                textposition="outside",
                hovertemplate="%{y}: %{x:,.0f}<extra></extra>",
            )
            style_figure(rejection_fig, 570)
            rejection_fig.update_layout(
                xaxis_title="Jumlah proses",
                yaxis_title=None,
                margin={"l": 15, "r": 35, "t": 12, "b": 35},
            )
            st.plotly_chart(
                rejection_fig,
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )
# =============================================================================
# FOOTER
# =============================================================================
st.markdown(
    f"""
    <div class="hop-footer">
      {html.escape(DASHBOARD_TITLE)} · Dashboard Penempatan CDC · SSDC 2026 ·
      {html.escape(TEAM_NAME)} · {html.escape(PARTICIPANT_NUMBER)} · Data per {AS_OF.strftime('%d %B %Y')}
    </div>
    """,
    unsafe_allow_html=True,
)