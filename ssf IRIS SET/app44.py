"""
CDC Talent Dashboard — Streamlit multi-page app
Jalankan dengan: streamlit run app.py
Struktur folder:
  app.py
  data/
    company.parquet
    status_student.parquet
    student_all.parquet
    talent_request.parquet
    tracking_company.parquet
    tracking_student.parquet
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="CDC Talent Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).parent / "clean_data"

COLORS = {
    "primary": "#378ADD", "secondary": "#7F77DD", "accent": "#1D9E75",
    "warn": "#D85A30", "pink": "#D4537E", "amber": "#BA7517",
    "seq_blue": px.colors.sequential.Blues,
    "seq_teal": ["#E1F5EE", "#9FE1CB", "#5DCAA5", "#1D9E75", "#0F6E56"],
    "cat": ["#378ADD", "#7F77DD", "#1D9E75", "#D85A30", "#D4537E",
            "#BA7517", "#85B7EB", "#AFA9EC"],
}

CITY_COORDS = {
    "Surakarta": (-7.5755, 110.8243), "Semarang": (-6.9932, 110.4203),
    "Yogyakarta": (-7.7956, 110.3695), "Jakarta": (-6.2088, 106.8456),
    "Depok": (-6.4025, 106.7942), "Malang": (-7.9666, 112.6326),
    "Bandung": (-6.9175, 107.6191), "Surabaya": (-7.2575, 112.7521),
    "Bekasi": (-6.2383, 106.9756), "Tangerang": (-6.1783, 106.6319),
    "Bogor": (-6.5971, 106.8060),
}

PLOTLY_CONFIG = {"displayModeBar": False}
HOVER_FONT = dict(bgcolor="white", font_size=12, font_family="Arial")


# ----------------------------------------------------------------------------
# STYLING
# ----------------------------------------------------------------------------
st.markdown("""
<style>
    .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        background: #F7F8FA; border-radius: 10px; padding: 12px 16px;
        border: 1px solid #ECEEF1;
    }
    div[data-testid="stMetric"] label {font-size: 12px !important; color: #6B7280 !important;}
    div[data-testid="stMetricValue"] {font-size: 26px !important; font-weight: 700 !important; color: #111827 !important;}
    div[data-testid="stMetricDelta"] {font-size: 12px !important;}
    div[data-testid="stMetricDelta"] svg {width: 14px !important; height: 14px !important;}
    .section-card {
        background: white; border-radius: 12px; padding: 14px 16px 6px 16px;
        border: 1px solid #ECEEF1; margin-bottom: 14px;
    }
    .section-title {font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 4px;}
    .dash-header {font-size: 26px; font-weight: 700; margin-bottom: 0;}
    .dash-sub {font-size: 13px; color: #6B7280; margin-top: -6px; margin-bottom: 12px;}
    section[data-testid="stSidebar"] {background: #101828;}
    section[data-testid="stSidebar"] * {color: #E5E7EB !important;}
    section[data-testid="stSidebar"] .stRadio label {font-size: 14px;}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# DATA LOADING
# ----------------------------------------------------------------------------
@st.cache_data
def load_data():
    company = pd.read_parquet(DATA_DIR / "company.parquet")
    status_student = pd.read_parquet(DATA_DIR / "status_student.parquet")
    student_all = pd.read_parquet(DATA_DIR / "student_all.parquet")
    talent_request = pd.read_parquet(DATA_DIR / "talent_request.parquet")
    tracking_company = pd.read_parquet(DATA_DIR / "tracking_company.parquet")
    tracking_student = pd.read_parquet(DATA_DIR / "tracking_student.parquet")

    company["year"] = company["created_at"].dt.year
    company["month"] = company["created_at"].dt.to_period("M").astype(str)
    talent_request["year"] = talent_request["request_date"].dt.year
    talent_request["month"] = talent_request["request_date"].dt.to_period("M").astype(str)
    tracking_student["year"] = tracking_student["last_update"].dt.year
    tracking_student["month"] = tracking_student["last_update"].dt.to_period("M").astype(str)

    return {
        "company": company, "status_student": status_student,
        "student_all": student_all, "talent_request": talent_request,
        "tracking_company": tracking_company, "tracking_student": tracking_student,
    }


data = load_data()


# ----------------------------------------------------------------------------
# SIDEBAR — NAVIGATION + GLOBAL FILTERS
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📊 CDC Talent Dashboard")
    st.caption("Sebelas Maret Statistics Dashboard Competition")
    st.markdown("---")

    page = st.radio(
        "Pilih halaman",
        [
            "🏢 Company & Employer Landscape",
            "🎓 Student & Talent Pool",
            "📋 Recruitment Funnel",
            "🎯 Matching & Placement",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("**Filter global**")

    all_years = sorted(set(
        data["company"]["year"].dropna().unique().tolist()
        + data["talent_request"]["year"].dropna().unique().tolist()
    ))
    year_sel = st.multiselect("Tahun", all_years, default=all_years)

    all_kota = sorted(data["company"]["kota"].dropna().unique().tolist())
    kota_sel = st.multiselect("Kota", all_kota, default=all_kota)

    all_industry = sorted(data["company"]["industry_sector"].dropna().unique().tolist())
    industry_sel = st.multiselect("Industri", all_industry, default=all_industry)

    st.markdown("---")
    st.caption("Sumber data: company, student, talent_request, tracking · update terakhir 31 Jan 2025")

if not year_sel:
    year_sel = all_years
if not kota_sel:
    kota_sel = all_kota
if not industry_sel:
    industry_sel = all_industry


def kpi_card(col, label, value, delta=None, help_text=None, delta_color="normal"):
    col.metric(label, value, delta=delta, delta_color=delta_color, help=help_text)


def mom_delta(series_by_month, mode="pct", suffix=" vs bulan lalu"):
    """series_by_month: pandas Series indexed by 'YYYY-MM' (sorted), value = count/metric.
    mode='pct' -> tampilkan %perubahan, mode='diff' -> tampilkan selisih absolut."""
    s = series_by_month.dropna().sort_index()
    if len(s) < 2:
        return None
    cur, prev = s.iloc[-1], s.iloc[-2]
    if mode == "pct":
        if prev == 0:
            return None
        pct = (cur - prev) / prev * 100
        return f"{pct:+.1f}%{suffix}"
    else:
        diff = cur - prev
        return f"{diff:+.0f}{suffix}"


# ============================================================================
# PAGE 1 — COMPANY & EMPLOYER LANDSCAPE
# ============================================================================
def page_company():
    st.markdown('<p class="dash-header">Company & Employer Landscape</p>', unsafe_allow_html=True)
    st.markdown('<p class="dash-sub">Page 1 dari 4 — profil perusahaan mitra CDC</p>', unsafe_allow_html=True)

    comp = data["company"]
    tr = data["talent_request"]
    comp_f = comp[
        comp["year"].isin(year_sel) & comp["kota"].isin(kota_sel) & comp["industry_sector"].isin(industry_sel)
    ]

    # KPI row
    growth = comp_f.groupby("month").size().sort_index()
    cumulative = growth.cumsum()
    pct_multi_month = comp_f.groupby("month").apply(
        lambda d: d["skala_perusahaan"].eq("Multinasional").mean() * 100
    ).sort_index()

    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "Total company", f"{len(comp_f):,}", delta=mom_delta(cumulative, "pct"))
    kpi_card(c2, "Kota coverage", f"{comp_f['kota'].nunique()}")
    pct_multi = (comp_f["skala_perusahaan"].eq("Multinasional").mean() * 100) if len(comp_f) else 0
    kpi_card(c3, "% Multinasional", f"{pct_multi:.1f}%", delta=mom_delta(pct_multi_month, "diff", " pt vs bulan lalu"))
    delta_new = int(growth.iloc[-1]) if len(growth) else 0
    kpi_card(c4, "Company baru (bulan terakhir)", f"{delta_new}", delta=mom_delta(growth, "diff"))

    st.markdown("<br>", unsafe_allow_html=True)
    r1c1, r1c2, r1c3 = st.columns([1.3, 1, 1])

    with r1c1:
        st.markdown('<div class="section-card"><div class="section-title">1. Company per industry sector (top 10)</div>', unsafe_allow_html=True)
        top_ind = comp_f["industry_sector"].value_counts().nlargest(10).reset_index()
        top_ind.columns = ["industry_sector", "count"]
        fig = px.bar(top_ind, x="count", y="industry_sector", orientation="h",
                     color="count", color_continuous_scale="Blues",
                     labels={"count": "Jumlah company", "industry_sector": ""})
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False,
                           yaxis={"categoryorder": "total ascending"})
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Jumlah company: %{x}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r1c2:
        st.markdown('<div class="section-card"><div class="section-title">2. Company type</div>', unsafe_allow_html=True)
        ct = comp_f["company_type"].value_counts().reset_index()
        ct.columns = ["company_type", "count"]
        fig = px.pie(ct, names="company_type", values="count", hole=0.55,
                     color_discrete_sequence=COLORS["cat"])
        fig.update_traces(textinfo="percent", hovertemplate="<b>%{label}</b><br>%{value} company (%{percent})<extra></extra>")
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), showlegend=True,
                           legend=dict(orientation="h", y=-0.15, font=dict(size=9)))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r1c3:
        st.markdown('<div class="section-card"><div class="section-title">9. Skala perusahaan</div>', unsafe_allow_html=True)
        sk = comp_f["skala_perusahaan"].value_counts().reset_index()
        sk.columns = ["skala", "count"]
        fig = px.pie(sk, names="skala", values="count", hole=0.55,
                     color_discrete_sequence=COLORS["seq_teal"][1:])
        fig.update_traces(textinfo="percent", hovertemplate="<b>%{label}</b><br>%{value} company (%{percent})<extra></extra>")
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), showlegend=True,
                           legend=dict(orientation="h", y=-0.15, font=dict(size=9)))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown('<div class="section-card"><div class="section-title">3. Company per kota</div>', unsafe_allow_html=True)
        kt = comp_f["kota"].value_counts().reset_index()
        kt.columns = ["kota", "count"]
        fig = px.bar(kt, x="count", y="kota", orientation="h", color="count",
                     color_continuous_scale="Oranges", labels={"count": "Jumlah company", "kota": ""})
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False,
                           yaxis={"categoryorder": "total ascending"})
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Jumlah company: %{x}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r2c2:
        st.markdown('<div class="section-card"><div class="section-title">4. Stacked bar — skala perusahaan per industry (top 8)</div>', unsafe_allow_html=True)
        top8 = comp_f["industry_sector"].value_counts().nlargest(8).index
        stk = comp_f[comp_f["industry_sector"].isin(top8)].groupby(["industry_sector", "skala_perusahaan"]).size().reset_index(name="count")
        fig = px.bar(stk, x="industry_sector", y="count", color="skala_perusahaan", barmode="stack",
                     color_discrete_sequence=COLORS["seq_teal"][1:],
                     labels={"count": "Jumlah", "industry_sector": "", "skala_perusahaan": "Skala"})
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), xaxis_tickangle=-30,
                           legend=dict(orientation="h", y=1.15, font=dict(size=9)))
        fig.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    r3c1, r3c2 = st.columns(2)
    with r3c1:
        st.markdown('<div class="section-card"><div class="section-title">5. Tren company baru per bulan</div>', unsafe_allow_html=True)
        tren = comp_f.groupby("month").size().reset_index(name="count")
        fig = px.line(tren, x="month", y="count", markers=True, color_discrete_sequence=[COLORS["primary"]])
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="", yaxis_title="Jumlah company baru")
        fig.update_traces(hovertemplate="<b>%{x}</b><br>Company baru: %{y}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r3c2:
        st.markdown('<div class="section-card"><div class="section-title">10. Company type vs skala perusahaan (grouped)</div>', unsafe_allow_html=True)
        grp = comp_f.groupby(["company_type", "skala_perusahaan"]).size().reset_index(name="count")
        fig = px.bar(grp, x="company_type", y="count", color="skala_perusahaan", barmode="group",
                     color_discrete_sequence=COLORS["cat"],
                     labels={"count": "Jumlah", "company_type": "", "skala_perusahaan": "Skala"})
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), xaxis_tickangle=-20,
                           legend=dict(orientation="h", y=1.15, font=dict(size=9)))
        fig.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    r4c1, r4c2, r4c3 = st.columns([1, 1, 1])
    with r4c1:
        st.markdown('<div class="section-card"><div class="section-title">6. Sebaran company per kota (bubble map)</div>', unsafe_allow_html=True)
        kt2 = comp_f["kota"].value_counts().reset_index()
        kt2.columns = ["kota", "count"]
        kt2["lat"] = kt2["kota"].map(lambda k: CITY_COORDS.get(k, (None, None))[0])
        kt2["lon"] = kt2["kota"].map(lambda k: CITY_COORDS.get(k, (None, None))[1])
        kt2 = kt2.dropna(subset=["lat", "lon"])
        fig = px.scatter_mapbox(kt2, lat="lat", lon="lon", size="count", color="count",
                                 hover_name="kota", size_max=35, zoom=4.2,
                                 color_continuous_scale="Teal",
                                 center={"lat": -6.5, "lon": 108.5})
        fig.update_layout(mapbox_style="carto-positron", height=300,
                           margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False)
        fig.update_traces(hovertemplate="<b>%{hovertext}</b><br>Jumlah company: %{marker.size}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r4c2:
        st.markdown('<div class="section-card"><div class="section-title">7. Treemap: industry x skala</div>', unsafe_allow_html=True)
        tm = comp_f.groupby(["industry_sector", "skala_perusahaan"]).size().reset_index(name="count")
        fig = px.treemap(tm, path=["industry_sector", "skala_perusahaan"], values="count",
                          color="count", color_continuous_scale="Purp")
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False)
        fig.update_traces(hovertemplate="<b>%{label}</b><br>Jumlah: %{value}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r4c3:
        st.markdown('<div class="section-card"><div class="section-title">8. Top 10 company paling aktif request</div>', unsafe_allow_html=True)
        active = tr[tr["id_company"].isin(comp_f["id_company"])].groupby("nama_perusahaan").size().nlargest(10).reset_index(name="jumlah_request")
        st.dataframe(active, use_container_width=True, height=300, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================================
# PAGE 2 — STUDENT & TALENT POOL
# ============================================================================
def page_student():
    st.markdown('<p class="dash-header">Student & Talent Pool</p>', unsafe_allow_html=True)
    st.markdown('<p class="dash-sub">Page 2 dari 4 — profil dan kesiapan mahasiswa</p>', unsafe_allow_html=True)

    ss = data["status_student"].copy()
    sa = data["student_all"]
    ss["month"] = ss["sync_date"].dt.to_period("M").astype(str)

    growth = ss.groupby("month").size().sort_index()
    cumulative = growth.cumsum()
    ipk_month = ss.groupby("month")["IPK"].mean().sort_index()
    avail_month = ss.groupby("month").apply(lambda d: d["ketersediaan"].eq("Available").mean() * 100).sort_index()

    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "Total mahasiswa", f"{len(ss):,}", delta=mom_delta(cumulative, "pct"))
    kpi_card(c2, "Rata-rata IPK", f"{ss['IPK'].mean():.2f}", delta=mom_delta(ipk_month, "diff", " vs bulan lalu"))
    pct_avail = (ss["ketersediaan"].eq("Available").mean() * 100)
    kpi_card(c3, "% Available", f"{pct_avail:.1f}%", delta=mom_delta(avail_month, "diff", " pt vs bulan lalu"))
    kpi_card(c4, "Jumlah program studi", f"{ss['program_studi'].nunique()}")

    st.markdown("<br>", unsafe_allow_html=True)
    r1c1, r1c2, r1c3 = st.columns([1.3, 1, 1])
    with r1c1:
        st.markdown('<div class="section-card"><div class="section-title">1. Mahasiswa per program studi (top 10)</div>', unsafe_allow_html=True)
        prodi = ss["program_studi"].value_counts().nlargest(10).reset_index()
        prodi.columns = ["program_studi", "count"]
        fig = px.bar(prodi, x="count", y="program_studi", orientation="h", color="count",
                     color_continuous_scale="Blues", labels={"count": "Jumlah mahasiswa", "program_studi": ""})
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False,
                           yaxis={"categoryorder": "total ascending"})
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Jumlah: %{x}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r1c2:
        st.markdown('<div class="section-card"><div class="section-title">2. Status mahasiswa</div>', unsafe_allow_html=True)
        stt = ss["status"].value_counts().reset_index()
        stt.columns = ["status", "count"]
        fig = px.pie(stt, names="status", values="count", hole=0.55, color_discrete_sequence=COLORS["cat"])
        fig.update_traces(hovertemplate="<b>%{label}</b><br>%{value} (%{percent})<extra></extra>")
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                           legend=dict(orientation="h", y=-0.15, font=dict(size=9)))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r1c3:
        st.markdown('<div class="section-card"><div class="section-title">3. Ketersediaan mahasiswa</div>', unsafe_allow_html=True)
        ket = ss["ketersediaan"].value_counts().reset_index()
        ket.columns = ["ketersediaan", "count"]
        fig = px.pie(ket, names="ketersediaan", values="count", hole=0.55, color_discrete_sequence=COLORS["seq_teal"][1:])
        fig.update_traces(hovertemplate="<b>%{label}</b><br>%{value} (%{percent})<extra></extra>")
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                           legend=dict(orientation="h", y=-0.15, font=dict(size=9)))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown('<div class="section-card"><div class="section-title">4. Distribusi IPK</div>', unsafe_allow_html=True)
        fig = px.histogram(ss, x="IPK", nbins=25, color_discrete_sequence=[COLORS["primary"]])
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="Jumlah mahasiswa")
        fig.update_traces(hovertemplate="IPK: %{x}<br>Jumlah: %{y}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r2c2:
        st.markdown('<div class="section-card"><div class="section-title">5. Mahasiswa per domisili (top 10)</div>', unsafe_allow_html=True)
        dom = ss["domisili"].value_counts().nlargest(10).reset_index()
        dom.columns = ["domisili", "count"]
        fig = px.bar(dom, x="domisili", y="count", color="count", color_continuous_scale="Oranges",
                     labels={"count": "Jumlah", "domisili": ""})
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False, xaxis_tickangle=-30)
        fig.update_traces(hovertemplate="<b>%{x}</b><br>Jumlah: %{y}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    r3c1, r3c2, r3c3 = st.columns(3)
    with r3c1:
        st.markdown('<div class="section-card"><div class="section-title">6. Mahasiswa per semester</div>', unsafe_allow_html=True)
        sem = ss["semester"].value_counts().sort_index().reset_index()
        sem.columns = ["semester", "count"]
        fig = px.bar(sem, x="semester", y="count", color_discrete_sequence=[COLORS["secondary"]])
        fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0))
        fig.update_traces(hovertemplate="Semester %{x}<br>Jumlah: %{y}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r3c2:
        st.markdown('<div class="section-card"><div class="section-title">7. Top 10 tools/skill terpopuler</div>', unsafe_allow_html=True)
        tools_exp = ss.explode("tools_list")
        top_tools = tools_exp["tools_list"].value_counts().nlargest(10).reset_index()
        top_tools.columns = ["tool", "count"]
        fig = px.bar(top_tools, x="count", y="tool", orientation="h", color="count",
                     color_continuous_scale="Purp", labels={"count": "Jumlah mahasiswa", "tool": ""})
        fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False,
                           yaxis={"categoryorder": "total ascending"})
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Jumlah: %{x}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r3c3:
        st.markdown('<div class="section-card"><div class="section-title">8. Bidang minat mahasiswa</div>', unsafe_allow_html=True)
        bm = sa["bidang_minat"].value_counts().reset_index()
        bm.columns = ["bidang_minat", "count"]
        fig = px.pie(bm, names="bidang_minat", values="count", hole=0.5, color_discrete_sequence=COLORS["cat"])
        fig.update_traces(hovertemplate="<b>%{label}</b><br>%{value} (%{percent})<extra></extra>")
        fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0),
                           legend=dict(orientation="h", y=-0.2, font=dict(size=8)))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    r4c1, r4c2 = st.columns(2)
    with r4c1:
        st.markdown('<div class="section-card"><div class="section-title">9. Jenis penempatan diminati</div>', unsafe_allow_html=True)
        jp = sa["jenis_penempatan_diminati"].value_counts().reset_index()
        jp.columns = ["jenis", "count"]
        fig = px.bar(jp, x="jenis", y="count", color="jenis", color_discrete_sequence=COLORS["cat"])
        fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
        fig.update_traces(hovertemplate="<b>%{x}</b><br>Jumlah: %{y}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r4c2:
        st.markdown('<div class="section-card"><div class="section-title">10. Kelengkapan CV & portofolio</div>', unsafe_allow_html=True)
        comp_stat = pd.DataFrame({
            "dokumen": ["CV", "CV", "Portofolio", "Portofolio"],
            "status": ["Ada", "Tidak Ada", "Ada", "Tidak Ada"],
            "count": [
                (ss["CV"] == "Ada").sum(), (ss["CV"] != "Ada").sum(),
                (ss["portofolio"] == "Ada").sum(), (ss["portofolio"] != "Ada").sum(),
            ],
        })
        fig = px.bar(comp_stat, x="dokumen", y="count", color="status", barmode="stack",
                     color_discrete_sequence=[COLORS["accent"], "#F0997B"])
        fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=1.15))
        fig.update_traces(hovertemplate="<b>%{x}</b> — %{fullData.name}<br>Jumlah: %{y}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================================
# PAGE 3 — RECRUITMENT FUNNEL
# ============================================================================
def page_funnel():
    st.markdown('<p class="dash-header">Talent Request & Recruitment Funnel</p>', unsafe_allow_html=True)
    st.markdown('<p class="dash-sub">Page 3 dari 4 — permintaan perusahaan dan proses seleksi</p>', unsafe_allow_html=True)

    tr = data["talent_request"]
    tc = data["tracking_company"]
    tr_f = tr[tr["year"].isin(year_sel)]

    req_month = tr_f.groupby("month").size().sort_index()
    req_cumulative = req_month.cumsum()
    headcount_month = tr_f.groupby("month")["headcount"].sum().sort_index()

    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "Total talent request", f"{len(tr_f):,}", delta=mom_delta(req_cumulative, "pct"))
    kpi_card(c2, "Total headcount dibutuhkan", f"{tr_f['headcount'].sum():,}", delta=mom_delta(headcount_month, "diff"))
    kpi_card(c3, "Rata-rata min. semester", f"{tr_f['minimum_semester'].mean():.1f}")
    kpi_card(c4, "Perusahaan yang request", f"{tr_f['id_company'].nunique():,}")

    st.markdown("<br>", unsafe_allow_html=True)
    r1c1, r1c2 = st.columns([1, 1])
    with r1c1:
        st.markdown('<div class="section-card"><div class="section-title">1. Funnel progress tracking company</div>', unsafe_allow_html=True)
        order = ["Draft", "Submitted", "On Review", "Shortlisted", "Closed"]
        fcount = tc["progress"].value_counts().reindex(order).fillna(0)
        fig = go.Figure(go.Funnel(
            y=order, x=fcount.values,
            marker={"color": COLORS["cat"][:5]},
            hovertemplate="<b>%{y}</b><br>Jumlah: %{x}<extra></extra>",
        ))
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r1c2:
        st.markdown('<div class="section-card"><div class="section-title">2. Jenis penempatan yang diminta</div>', unsafe_allow_html=True)
        jp = tr_f["jenis_penempatan"].value_counts().reset_index()
        jp.columns = ["jenis", "count"]
        fig = px.pie(jp, names="jenis", values="count", hole=0.55, color_discrete_sequence=COLORS["cat"])
        fig.update_traces(hovertemplate="<b>%{label}</b><br>%{value} (%{percent})<extra></extra>")
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1:
        st.markdown('<div class="section-card"><div class="section-title">3. Working arrangement</div>', unsafe_allow_html=True)
        wa = tr_f["working_arrangement"].value_counts().reset_index()
        wa.columns = ["arrangement", "count"]
        fig = px.bar(wa, x="arrangement", y="count", color="arrangement", color_discrete_sequence=COLORS["cat"])
        fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
        fig.update_traces(hovertemplate="<b>%{x}</b><br>Jumlah: %{y}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r2c2:
        st.markdown('<div class="section-card"><div class="section-title">4. Sumber form request</div>', unsafe_allow_html=True)
        sf = tr_f["sumber_baris_form"].value_counts().reset_index()
        sf.columns = ["sumber", "count"]
        fig = px.bar(sf, x="sumber", y="count", color="sumber", color_discrete_sequence=COLORS["cat"])
        fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, xaxis_tickangle=-15)
        fig.update_traces(hovertemplate="<b>%{x}</b><br>Jumlah: %{y}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r2c3:
        st.markdown('<div class="section-card"><div class="section-title">5. Durasi magang</div>', unsafe_allow_html=True)
        dur = tr_f["durasi"].value_counts().reset_index()
        dur.columns = ["durasi", "count"]
        fig = px.bar(dur, x="durasi", y="count", color="durasi", color_discrete_sequence=COLORS["cat"])
        fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, xaxis_tickangle=-15)
        fig.update_traces(hovertemplate="<b>%{x}</b><br>Jumlah: %{y}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    r3c1, r3c2 = st.columns(2)
    with r3c1:
        st.markdown('<div class="section-card"><div class="section-title">6. Top bidang studi paling dibutuhkan</div>', unsafe_allow_html=True)
        bs = tr_f["bidang_studi_dibutuhkan"].str.split(", ").explode().value_counts().nlargest(10).reset_index()
        bs.columns = ["bidang_studi", "count"]
        fig = px.bar(bs, x="count", y="bidang_studi", orientation="h", color="count",
                     color_continuous_scale="Blues", labels={"count": "Jumlah request", "bidang_studi": ""})
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False,
                           yaxis={"categoryorder": "total ascending"})
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Jumlah: %{x}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r3c2:
        st.markdown('<div class="section-card"><div class="section-title">7. Tren request per bulan</div>', unsafe_allow_html=True)
        tren = tr_f.groupby("month").size().reset_index(name="count")
        fig = px.line(tren, x="month", y="count", markers=True, color_discrete_sequence=[COLORS["warn"]])
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="", yaxis_title="Jumlah request")
        fig.update_traces(hovertemplate="<b>%{x}</b><br>Request: %{y}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    r4c1, r4c2, r4c3 = st.columns(3)
    with r4c1:
        st.markdown('<div class="section-card"><div class="section-title">8. Top posisi paling diminta</div>', unsafe_allow_html=True)
        pos = tr_f["nama_posisi"].value_counts().nlargest(10).reset_index()
        pos.columns = ["posisi", "jumlah_request"]
        st.dataframe(pos, use_container_width=True, height=280, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with r4c2:
        st.markdown('<div class="section-card"><div class="section-title">9. Efektivitas pengiriman kandidat</div>', unsafe_allow_html=True)
        eff = tc.groupby("jenis_penempatan")[["jumlah_permintaan", "jumlah_dikirimkan"]].sum().reset_index()
        fig = px.bar(eff, x="jenis_penempatan", y=["jumlah_permintaan", "jumlah_dikirimkan"], barmode="group",
                     color_discrete_sequence=[COLORS["primary"], COLORS["accent"]],
                     labels={"value": "Jumlah", "jenis_penempatan": "", "variable": ""})
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=1.15))
        fig.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r4c3:
        st.markdown('<div class="section-card"><div class="section-title">10. Industri dengan request terbanyak</div>', unsafe_allow_html=True)
        ind = tr_f["industri_sektor"].value_counts().nlargest(8).reset_index()
        ind.columns = ["industri", "count"]
        fig = px.bar(ind, x="count", y="industri", orientation="h", color="count",
                     color_continuous_scale="Purp", labels={"count": "Jumlah request", "industri": ""})
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False,
                           yaxis={"categoryorder": "total ascending"})
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Jumlah: %{x}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================================
# PAGE 4 — MATCHING & PLACEMENT PERFORMANCE
# ============================================================================
def page_matching():
    st.markdown('<p class="dash-header">Matching & Placement Performance</p>', unsafe_allow_html=True)
    st.markdown('<p class="dash-sub">Page 4 dari 4 — hasil akhir proses rekrutmen mahasiswa</p>', unsafe_allow_html=True)

    ts = data["tracking_student"]
    comp = data["company"]
    ts_f = ts[ts["year"].isin(year_sel)] if year_sel else ts

    track_month = ts_f.groupby("month").size().sort_index()
    track_cumulative = track_month.cumsum()
    placement_month = ts_f.groupby("month").apply(lambda d: d["rejection"].eq("Placement").mean() * 100).sort_index()
    rejection_month = ts_f.groupby("month").apply(
        lambda d: d["rejection"].str.startswith("Rejection", na=False).mean() * 100
    ).sort_index()
    ghosting_month = ts_f.groupby("month").apply(lambda d: d["rejection"].eq("Ghosting").mean() * 100).sort_index()

    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "Total mahasiswa ditrack", f"{len(ts_f):,}", delta=mom_delta(track_cumulative, "pct"))
    placement_rate = ts_f["rejection"].eq("Placement").mean() * 100
    kpi_card(c2, "Placement rate", f"{placement_rate:.1f}%", delta=mom_delta(placement_month, "diff", " pt vs bulan lalu"))
    rejection_rate = ts_f["rejection"].str.startswith("Rejection", na=False).mean() * 100
    kpi_card(c3, "Rejection rate", f"{rejection_rate:.1f}%",
              delta=mom_delta(rejection_month, "diff", " pt vs bulan lalu"), delta_color="inverse")
    ghosting_rate = ts_f["rejection"].eq("Ghosting").mean() * 100
    kpi_card(c4, "Ghosting rate", f"{ghosting_rate:.1f}%",
              delta=mom_delta(ghosting_month, "diff", " pt vs bulan lalu"), delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)
    r1c1, r1c2 = st.columns([1.1, 1])
    with r1c1:
        st.markdown('<div class="section-card"><div class="section-title">1. Funnel progress mahasiswa</div>', unsafe_allow_html=True)
        order = ["CDC Briefing Student", "Study Case", "Interview User", "Final Interview", "Placement", "Finish"]
        fcount = ts_f["progress_student"].value_counts().reindex(order).fillna(0)
        fig = go.Figure(go.Funnel(
            y=order, x=fcount.values, marker={"color": COLORS["cat"][:6]},
            hovertemplate="<b>%{y}</b><br>Jumlah: %{x}<extra></extra>",
        ))
        fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r1c2:
        st.markdown('<div class="section-card"><div class="section-title">2. Breakdown status akhir (rejection)</div>', unsafe_allow_html=True)
        rej = ts_f["rejection"].value_counts().reset_index()
        rej.columns = ["status", "count"]
        fig = px.pie(rej, names="status", values="count", hole=0.5, color_discrete_sequence=COLORS["cat"])
        fig.update_traces(hovertemplate="<b>%{label}</b><br>%{value} (%{percent})<extra></extra>")
        fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=-0.25, font=dict(size=8)))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown('<div class="section-card"><div class="section-title">3. Alasan rejection terbanyak</div>', unsafe_allow_html=True)
        rej_only = ts_f[ts_f["rejection"].str.startswith("Rejection", na=False)]
        rr = rej_only["rejection"].value_counts().reset_index()
        rr.columns = ["alasan", "count"]
        fig = px.bar(rr, x="count", y="alasan", orientation="h", color="count",
                     color_continuous_scale="Reds", labels={"count": "Jumlah", "alasan": ""})
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False,
                           yaxis={"categoryorder": "total ascending"})
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Jumlah: %{x}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r2c2:
        st.markdown('<div class="section-card"><div class="section-title">4. Jenis penempatan hasil tracking</div>', unsafe_allow_html=True)
        jp = ts_f["jenis_penempatan"].value_counts().reset_index()
        jp.columns = ["jenis", "count"]
        fig = px.bar(jp, x="jenis", y="count", color="jenis", color_discrete_sequence=COLORS["cat"])
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
        fig.update_traces(hovertemplate="<b>%{x}</b><br>Jumlah: %{y}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    r3c1, r3c2 = st.columns(2)
    with r3c1:
        st.markdown('<div class="section-card"><div class="section-title">5. Tren progress per bulan</div>', unsafe_allow_html=True)
        tren = ts_f.groupby("month").size().reset_index(name="count")
        fig = px.line(tren, x="month", y="count", markers=True, color_discrete_sequence=[COLORS["pink"]])
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="", yaxis_title="Jumlah update")
        fig.update_traces(hovertemplate="<b>%{x}</b><br>Update: %{y}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r3c2:
        st.markdown('<div class="section-card"><div class="section-title">6. Top perusahaan dengan placement rate tertinggi</div>', unsafe_allow_html=True)
        cr = ts_f.groupby("company")["rejection"].apply(lambda x: (x == "Placement").mean() * 100)
        cnt = ts_f.groupby("company").size()
        rank = pd.DataFrame({"placement_rate_%": cr, "total_kandidat": cnt}).query("total_kandidat >= 3")
        rank = rank.sort_values("placement_rate_%", ascending=False).head(10).round(1).reset_index()
        st.dataframe(rank, use_container_width=True, height=280, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    r4c1, r4c2, r4c3 = st.columns(3)
    with r4c1:
        st.markdown('<div class="section-card"><div class="section-title">7. Distribusi semester mahasiswa ditrack</div>', unsafe_allow_html=True)
        sem = ts_f["internship_semester"].value_counts().sort_index().reset_index()
        sem.columns = ["semester", "count"]
        fig = px.bar(sem, x="semester", y="count", color_discrete_sequence=[COLORS["secondary"]])
        fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0))
        fig.update_traces(hovertemplate="Semester %{x}<br>Jumlah: %{y}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r4c2:
        st.markdown('<div class="section-card"><div class="section-title">8. Top posisi vs progress</div>', unsafe_allow_html=True)
        top_pos = ts_f["position"].value_counts().nlargest(6).index
        pv = ts_f[ts_f["position"].isin(top_pos)].groupby(["position", "progress_student"]).size().reset_index(name="count")
        fig = px.bar(pv, x="position", y="count", color="progress_student", barmode="stack",
                     color_discrete_sequence=COLORS["cat"])
        fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), xaxis_tickangle=-25,
                           legend=dict(font=dict(size=7)))
        fig.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    with r4c3:
        st.markdown('<div class="section-card"><div class="section-title">9. Overall conversion rate</div>', unsafe_allow_html=True)
        conv = placement_rate
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=conv,
            number={"suffix": "%"},
            gauge={"axis": {"range": [0, 100]}, "bar": {"color": COLORS["accent"]}},
        ))
        fig.update_layout(height=260, margin=dict(l=10, r=10, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">10. Heatmap company (top 10) x progress_student</div>', unsafe_allow_html=True)
    top_comp = ts_f["company"].value_counts().nlargest(10).index
    hm = ts_f[ts_f["company"].isin(top_comp)].pivot_table(
        index="company", columns="progress_student", values="id_tracking_student", aggfunc="count", fill_value=0
    )
    fig = px.imshow(hm, color_continuous_scale="Blues", aspect="auto",
                     labels=dict(x="Progress", y="Company", color="Jumlah"))
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0))
    fig.update_traces(hovertemplate="Company: %{y}<br>Progress: %{x}<br>Jumlah: %{z}<extra></extra>")
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
    st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# ROUTER
# ----------------------------------------------------------------------------
if page.startswith("🏢"):
    page_company()
elif page.startswith("🎓"):
    page_student()
elif page.startswith("📋"):
    page_funnel()
else:
    page_matching()