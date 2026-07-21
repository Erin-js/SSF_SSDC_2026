"""
==================================================================================
DASHBOARD EKOSISTEM PENEMPATAN MAHASISWA - CAREER DEVELOPMENT CENTER (CDC)
Sebelas Maret Statistics Dashboard Competition (SSDC) 2026
Tema: "Hop Through Data, Discover Deeper Insights"
==================================================================================
Komponen:
  C-01 Mesin Pencocokan Otomatis (Matching Engine)
  C-02 Kanban Pelacakan Progress (Pipeline Progress Tracker)
  C-03 Antrean Prioritas Permintaan (Request Prioritization Queue)
  C-04 Sistem Peringatan Dini / EWS (Ghosting & SLA)
  C-05 Pelaporan Eksekutif IKU (Executive Analytics)
  C-06 Pusat Sinkronisasi Data (Sync & Data Health Monitor)
==================================================================================
Cara menjalankan:
    pip install streamlit pandas plotly pyarrow
    streamlit run app.py
==================================================================================
"""

import os
import difflib
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# KONFIGURASI HALAMAN
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="CDC Placement Dashboard | SSDC 2026",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY = "#4338CA"
ACCENT = "#F59E0B"
GREEN = "#16A34A"
RED = "#DC2626"
GREY = "#6B7280"

BASE_DIR = os.path.dirname(__file__)
CLEAN_DIR = os.path.join(BASE_DIR, "clean_data")


# ----------------------------------------------------------------------------
# LOAD DATA (ETL sudah dijalankan sebelumnya -> clean_data/*.parquet)
# Lihat etl.py untuk detail transformasi tanggal DD/MM/YYYY -> datetime
# ----------------------------------------------------------------------------
@st.cache_data
def load_data():
    company = pd.read_parquet(os.path.join(CLEAN_DIR, "company.parquet"))
    talent_request = pd.read_parquet(os.path.join(CLEAN_DIR, "talent_request.parquet"))
    student_all = pd.read_parquet(os.path.join(CLEAN_DIR, "student_all.parquet"))
    status_student = pd.read_parquet(os.path.join(CLEAN_DIR, "status_student.parquet"))
    tracking_company = pd.read_parquet(os.path.join(CLEAN_DIR, "tracking_company.parquet"))
    tracking_student = pd.read_parquet(os.path.join(CLEAN_DIR, "tracking_student.parquet"))
    return company, talent_request, student_all, status_student, tracking_company, tracking_student


company, talent_request, student_all, status_student, tracking_company, tracking_student = load_data()

# Tanggal acuan "hari ini" untuk simulasi (data historis 2023-2024).
# Dashboard nyata akan memakai datetime.now(); di sini memakai tanggal
# terbaru pada dataset agar KPI SLA/ghosting relevan dengan isi data.
MAX_DATE = max(
    tracking_student["last_update"].max(),
    tracking_company["send_date"].max(),
    status_student["sync_date"].max(),
)

# session_state untuk menyimpan perubahan interaktif (Kanban drag & drop, sync)
if "ts_live" not in st.session_state:
    st.session_state.ts_live = tracking_student.copy()
if "ss_live" not in st.session_state:
    st.session_state.ss_live = status_student.copy()

ts_live = st.session_state.ts_live
ss_live = st.session_state.ss_live


# ----------------------------------------------------------------------------
# SIDEBAR - RBAC & NAVIGASI
# ----------------------------------------------------------------------------
st.sidebar.markdown("## 🎓 CDC Placement Dashboard")
st.sidebar.caption("Sebelas Maret Statistics Fair 2026")

role = st.sidebar.selectbox(
    "Tingkat Akses (RBAC)",
    ["Administrator CDC (Akses Penuh)", "Perusahaan Mitra (Akses Terbatas)", "Mahasiswa (Akses Mandiri)"],
)

TODAY = st.sidebar.date_input("Tanggal Acuan Sistem (simulasi 'hari ini')", value=MAX_DATE.date())
TODAY = pd.Timestamp(TODAY)

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navigasi Komponen",
    [
        "🏠 Ringkasan KPI",
        "C-01 Mesin Pencocokan Otomatis",
        "C-02 Kanban Pelacakan Progress",
        "C-03 Antrean Prioritas Permintaan",
        "C-04 Sistem Peringatan Dini (EWS)",
        "C-05 Pelaporan Eksekutif IKU",
        "C-06 Pusat Sinkronisasi Data",
    ],
)
st.sidebar.markdown("---")
st.sidebar.caption(
    "Dataset: 6 tabel relasional, 79 kolom gabungan "
    f"({len(company)} perusahaan, {len(student_all)} mahasiswa, "
    f"{len(talent_request)} talent request, {len(tracking_student)} rekaman tracking)."
)

if role != "Administrator CDC (Akses Penuh)":
    st.sidebar.info(
        "Mode akses terbatas: sebagian data (kontak pribadi, kandidat perusahaan lain) "
        "disamarkan sesuai kebijakan RBAC pada bagian Tata Kelola Data."
    )


# ----------------------------------------------------------------------------
# FUNGSI BANTU / KPI ENGINE
# ----------------------------------------------------------------------------
def mask_phone(phone):
    phone = str(phone)
    if len(phone) <= 4:
        return phone
    return phone[:4] + "*" * (len(phone) - 6) + phone[-2:]


def compute_kpis(ts_df, ss_df, tc_df):
    placed = (ss_df["ketersediaan"] == "Placed").sum()
    eligible = ss_df[
        (ss_df["status"] == "Active") & (ss_df["CV"] == "Ada") & (ss_df["ketersediaan"].isin(["Available", "Placed"]))
    ].shape[0]
    placement_rate = placed / eligible * 100 if eligible else 0

    placement_ts = (ts_df["rejection"] == "Placement").sum()
    sent = tc_df["jumlah_dikirimkan"].sum()
    offer_yield = placement_ts / sent * 100 if sent else 0

    tc_valid = tc_df.dropna(subset=["send_date", "request_date"])
    velocity_days = (tc_valid["send_date"] - tc_valid["request_date"]).dt.days
    matching_velocity = velocity_days.mean() if len(velocity_days) else np.nan

    ghost = ((ts_df["progress_student"] == "Ghosting") | (ts_df["rejection"] == "Ghosting")).sum()
    ghosting_rate = ghost / len(ts_df) * 100 if len(ts_df) else 0

    return {
        "placement_rate": placement_rate,
        "placed": placed,
        "eligible": eligible,
        "offer_yield": offer_yield,
        "placement_ts": placement_ts,
        "sent": sent,
        "matching_velocity": matching_velocity,
        "ghosting_rate": ghosting_rate,
        "ghost": ghost,
        "total_tracking": len(ts_df),
    }


def jaccard(a, b):
    a, b = set(a), set(b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def kpi_card(col, label, value, suffix, target_text, good):
    color = GREEN if good else RED
    col.markdown(
        f"""
        <div style="border:1px solid #E5E7EB;border-radius:12px;padding:16px 18px;background:white;">
            <div style="font-size:13px;color:{GREY};font-weight:600;letter-spacing:.02em;">{label}</div>
            <div style="font-size:32px;font-weight:800;color:{color};margin-top:4px;">{value}{suffix}</div>
            <div style="font-size:12px;color:{GREY};margin-top:6px;">{target_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# 🏠 RINGKASAN KPI
# ============================================================================
if menu == "🏠 Ringkasan KPI":
    st.title("🎓 Dashboard Ekosistem Penempatan Mahasiswa CDC")
    st.caption(
        "Cetak biru integrasi 6 tabel relasional (COMPANY, TALENT REQUEST, STUDENT ALL, "
        "STATUS STUDENT, TRACKING COMPANY, TRACKING STUDENT) — Business Task BT-01 s.d. BT-08."
    )

    k = compute_kpis(ts_live, ss_live, tracking_company)
    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "PLACEMENT RATE", f"{k['placement_rate']:.1f}", "%", "Target institusi ≥ 80%", k["placement_rate"] >= 80)
    kpi_card(c2, "OFFER YIELD", f"{k['offer_yield']:.1f}", "%", "Ambang batas sehat ≥ 60%", k["offer_yield"] >= 60)
    kpi_card(c3, "MATCHING VELOCITY (SLA)", f"{k['matching_velocity']:.1f}", " hari", "Ideal < 7 hari kerja", k["matching_velocity"] < 7)
    kpi_card(c4, "GHOSTING RATE", f"{k['ghosting_rate']:.1f}", "%", "Ambang batas waspada ≤ 5%", k["ghosting_rate"] <= 5)

    st.markdown("")
    colA, colB = st.columns([1, 1.3])
    with colA:
        st.subheader("Proporsi Status Ketersediaan Mahasiswa")
        dist = ss_live["ketersediaan"].value_counts().reset_index()
        dist.columns = ["Status", "Jumlah"]
        fig = px.pie(dist, names="Status", values="Jumlah", hole=0.55,
                     color="Status",
                     color_discrete_map={"Placed": PRIMARY, "Available": GREEN, "Tidak Aktif": GREY})
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)
    with colB:
        st.subheader("Funnel Tahapan Seleksi (TRACKING STUDENT)")
        order = ["Selecting Student by Company", "Study Case", "CDC Briefing Student",
                 "Interview User", "Final Interview", "Placement"]
        funnel = ts_live[ts_live["progress_student"].isin(order)]["progress_student"].value_counts().reindex(order).fillna(0)
        figf = go.Figure(go.Funnel(y=funnel.index, x=funnel.values, marker={"color": PRIMARY}))
        figf.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(figf, use_container_width=True)

    st.info(
        "💡 **Insight cepat:** Offer Yield dan Matching Velocity berada di luar ambang sehat pada data saat ini — "
        "lihat detail akar masalah pada **C-03 Antrean Prioritas** (kecepatan respon CDC) dan "
        "**C-04 EWS** (kemandekan komunikasi)."
    )


# ============================================================================
# C-01 MESIN PENCOCOKAN OTOMATIS
# ============================================================================
elif menu == "C-01 Mesin Pencocokan Otomatis":
    st.title("🧩 C-01 — Mesin Pencocokan Otomatis (Matching Engine)")
    st.caption("Menyelesaikan BT-01 (Matching Talent) & BT-06 (Kelayakan Mahasiswa)")

    tr_options = talent_request.copy()
    tr_options["label"] = tr_options["id_talent_req"] + " — " + tr_options["nama_posisi"] + " (" + tr_options["nama_perusahaan"] + ")"
    pick = st.selectbox("Pilih Talent Request aktif:", tr_options["label"])
    req = tr_options[tr_options["label"] == pick].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bidang Studi Dicari", req["bidang_studi_dibutuhkan"])
    c2.metric("Min. Semester", int(req["minimum_semester"]))
    c3.metric("Headcount", int(req["headcount"]))
    c4.metric("Skema Kerja", req["working_arrangement"])
    st.caption(f"**Deskripsi requirement:** {req['deskripsi_requirement']}")

    comp_row = company[company["id_company"] == req["id_company"]]
    req_city = comp_row["kota"].iloc[0] if len(comp_row) else None

    # FILTER WAJIB
    filtered = ss_live[(ss_live["status"] == "Active") & (ss_live["CV"] == "Ada") & (ss_live["ketersediaan"] == "Available")].copy()

    prodi_wanted = [p.strip() for p in str(req["bidang_studi_dibutuhkan"]).split(",")]
    req_keywords = [w.strip(".,").lower() for w in str(req["deskripsi_requirement"]).replace(",", " ").split() if len(w) > 3]

    def match_score(row):
        prodi_match = 1.0 if row["program_studi"] in prodi_wanted else (
            0.5 if any(difflib.SequenceMatcher(None, row["program_studi"], p).ratio() > 0.6 for p in prodi_wanted) else 0.0
        )
        tools_score = jaccard(row["tools_list"], req_keywords)
        geo_score = 1.0 if req_city and row["domisili"] == req_city else 0.0
        semester_ok = row["semester"] >= req["minimum_semester"]
        composite = prodi_match * 0.45 + tools_score * 0.35 + geo_score * 0.20
        if not semester_ok:
            composite *= 0.5
        return pd.Series({"prodi_match": prodi_match, "tools_score": tools_score,
                           "geo_score": geo_score, "semester_ok": semester_ok, "match_pct": round(composite * 100, 1)})

    st.markdown(f"**{len(filtered)}** kandidat lolos filter wajib (Active / CV Ada / Available). Menghitung indeks kecocokan...")

    scored = filtered.join(filtered.apply(match_score, axis=1))
    scored = scored.sort_values("match_pct", ascending=False).head(25)

    show_cols = ["NIM", "nama", "program_studi", "semester", "domisili", "IPK", "match_pct"]
    display_df = scored[show_cols].rename(columns={"match_pct": "Kecocokan (%)"})
    if role != "Administrator CDC (Akses Penuh)":
        display_df = display_df.drop(columns=[])  # NIM tetap perlu utk aksi kirim; kontak disembunyikan (tidak ditampilkan di sini)

    st.subheader("🏆 Kandidat Terbaik (Top 25)")
    st.dataframe(
        display_df.style.background_gradient(subset=["Kecocokan (%)"], cmap="Greens"),
        use_container_width=True, hide_index=True,
    )

    st.markdown("##### ➕ Draf Pengiriman Kandidat")
    picked = st.multiselect("Pilih NIM untuk dimasukkan ke draf pengiriman ke perusahaan:", scored["NIM"].tolist())
    if st.button("Tambahkan ke Draft TRACKING COMPANY"):
        if picked:
            st.success(f"{len(picked)} NIM ditambahkan ke draf pengiriman untuk {req['nama_posisi']} — {req['nama_perusahaan']}: {', '.join(picked)}")
        else:
            st.warning("Belum ada kandidat dipilih.")


# ============================================================================
# C-02 KANBAN PELACAKAN PROGRESS
# ============================================================================
elif menu == "C-02 Kanban Pelacakan Progress":
    st.title("📋 C-02 — Kanban Pelacakan Progress (Pipeline Progress Tracker)")
    st.caption("Menyelesaikan BT-02 (Monitoring Progress Seleksi)")

    STAGES = ["Selecting Student by Company", "Study Case", "CDC Briefing Student",
              "Interview User", "Final Interview", "Placement"]
    SIDE_STATES = ["FU 1", "FU 2", "FU 3", "Ghosting", "Rejected", "Finish"]

    comp_names = sorted(ts_live["company"].dropna().unique())
    sel_company = st.selectbox("Filter Perusahaan:", ["Semua Perusahaan"] + comp_names)

    view = ts_live.copy()
    if sel_company != "Semua Perusahaan":
        view = view[view["company"] == sel_company]

    st.caption(f"Menampilkan {len(view)} kandidat pada pipeline aktif.")
    cols = st.columns(len(STAGES))
    for i, stage in enumerate(STAGES):
        with cols[i]:
            st.markdown(f"**{stage}**")
            stage_df = view[view["progress_student"] == stage]
            st.caption(f"{len(stage_df)} kandidat")
            for _, r in stage_df.head(8).iterrows():
                st.markdown(
                    f"""<div style="border:1px solid #E5E7EB;border-radius:8px;padding:8px;margin-bottom:6px;background:#FAFAFA;font-size:12px;">
                    <b>{r['student_name']}</b><br>{r['position']}<br>
                    <span style="color:{GREY}">{r['company']}</span><br>
                    <span style="color:{GREY}">Update: {r['last_update'].date() if pd.notna(r['last_update']) else '-'}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )
            if len(stage_df) > 8:
                st.caption(f"+{len(stage_df) - 8} lainnya")

    st.markdown("---")
    st.subheader("🔄 Pindahkan Kandidat (Drag & Drop → Simulasi Update)")
    view["label"] = view["id_tracking_student"] + " — " + view["student_name"] + " (" + view["position"] + ")"
    pick = st.selectbox("Pilih kandidat:", view["label"] if len(view) else ["- tidak ada data -"])
    if len(view):
        row = view[view["label"] == pick].iloc[0]
        new_stage = st.selectbox("Pindahkan ke tahap:", STAGES + SIDE_STATES,
                                  index=(STAGES + SIDE_STATES).index(row["progress_student"]) if row["progress_student"] in STAGES + SIDE_STATES else 0)
        if st.button("Update Status (SQL UPDATE simulasi)"):
            idx = ts_live[ts_live["id_tracking_student"] == row["id_tracking_student"]].index
            st.session_state.ts_live.loc[idx, "progress_student"] = new_stage
            st.session_state.ts_live.loc[idx, "last_update"] = TODAY

            if new_stage == "Placement":
                st.session_state.ts_live.loc[idx, "rejection"] = "Placement"
                nim = row["NIM"]
                ss_idx = ss_live[ss_live["NIM"] == nim].index
                st.session_state.ss_live.loc[ss_idx, "ketersediaan"] = "Placed"
                other_active = st.session_state.ts_live[
                    (st.session_state.ts_live["NIM"] == nim)
                    & (st.session_state.ts_live["id_tracking_student"] != row["id_tracking_student"])
                    & (st.session_state.ts_live["progress_student"].isin(STAGES[:-1] + ["FU 1", "FU 2", "FU 3"]))
                ].index
                st.session_state.ts_live.loc[other_active, "progress_student"] = "Finish"
                st.session_state.ts_live.loc[other_active, "rejection"] = "Rejection Screening CV"
                st.success(f"✅ {row['student_name']} resmi Placement. Status STATUS STUDENT → Placed, "
                           f"dan {len(other_active)} proses aktif lain otomatis ditarik untuk mencegah tumpang tindih.")
            elif new_stage == "Ghosting":
                st.session_state.ts_live.loc[idx, "rejection"] = "Ghosting"
                st.warning(f"⚠️ {row['student_name']} ditandai Ghosting dan masuk daftar tinjauan EWS.")
            elif new_stage == "Rejected":
                st.session_state.ts_live.loc[idx, "rejection"] = "Rejection Interview User"
                nim = row["NIM"]
                ss_idx = ss_live[ss_live["NIM"] == nim].index
                still_active = st.session_state.ts_live[
                    (st.session_state.ts_live["NIM"] == nim) & (st.session_state.ts_live["progress_student"].isin(STAGES + ["FU 1", "FU 2", "FU 3"]))
                ]
                if len(still_active) == 0:
                    st.session_state.ss_live.loc[ss_idx, "ketersediaan"] = "Available"
                st.info(f"{row['student_name']} ditandai Rejected.")
            else:
                st.success(f"Status {row['student_name']} diperbarui menjadi **{new_stage}**.")
            st.rerun()


# ============================================================================
# C-03 ANTREAN PRIORITAS PERMINTAAN
# ============================================================================
elif menu == "C-03 Antrean Prioritas Permintaan":
    st.title("📥 C-03 — Antrean Prioritas Permintaan (Request Prioritization Queue)")
    st.caption("Menyelesaikan BT-03 (Manajemen Talent Request)  |  Priority = (T_elapsed × 0.6) + (Headcount × 0.4)")

    tc_join = tracking_company.merge(
        talent_request[["id_talent_req", "minimum_semester"]], on="id_talent_req", how="left", suffixes=("", "_tr")
    )
    tc_join["t_elapsed"] = (TODAY - tc_join["request_date"]).dt.days.clip(lower=0)
    tc_join["priority_score"] = tc_join["t_elapsed"] * 0.6 + tc_join["jumlah_permintaan"] * 0.4
    tc_join["sla_status"] = np.select(
        [tc_join["t_elapsed"] < 3, tc_join["t_elapsed"] <= 7],
        ["🟢 Baru (<3 hari)", "🟡 Perlu Perhatian (3-7 hari)"],
        default="🔴 Kritis (>7 hari)",
    )

    only_unsent = st.checkbox("Hanya tampilkan yang belum ada pengiriman kandidat (send_date kosong)", value=True)
    q = tc_join.copy()
    if only_unsent:
        q = q[q["send_date"].isna()]
    q = q.sort_values("priority_score", ascending=False)

    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 Kritis (>7 hari)", int((q["sla_status"] == "🔴 Kritis (>7 hari)").sum()))
    c2.metric("🟡 Perlu Perhatian", int((q["sla_status"] == "🟡 Perlu Perhatian (3-7 hari)").sum()))
    c3.metric("🟢 Baru", int((q["sla_status"] == "🟢 Baru (<3 hari)").sum()))

    st.dataframe(
        q[["id_tracking_company", "nama_perusahaan", "posisi", "bidang_studi_dicari",
           "jumlah_permintaan", "t_elapsed", "sla_status", "priority_score"]]
        .rename(columns={"t_elapsed": "Hari Berjalan", "priority_score": "Skor Prioritas", "jumlah_permintaan": "Headcount"})
        .head(50),
        use_container_width=True, hide_index=True,
    )
    st.caption("Diurutkan menurun berdasarkan Skor Prioritas — permintaan besar & lama tanpa pengiriman naik ke puncak antrean.")


# ============================================================================
# C-04 SISTEM PERINGATAN DINI (EWS)
# ============================================================================
elif menu == "C-04 Sistem Peringatan Dini (EWS)":
    st.title("🚨 C-04 — Sistem Peringatan Dini / Early Warning System")
    st.caption("Menyelesaikan BT-05 (Deteksi Ghosting)  |  Toleransi SLA: 7 hari tanpa update")

    active_stage = ["Selecting Student by Company", "Study Case", "CDC Briefing Student", "Interview User", "Final Interview"]
    live = ts_live.copy()
    live["days_no_update"] = (TODAY - live["last_update"]).dt.days
    alerts = live[(live["progress_student"].isin(active_stage)) & (live["days_no_update"] > 7)].sort_values("days_no_update", ascending=False)

    c1, c2 = st.columns(2)
    c1.metric("⚠️ Total Peringatan Aktif", len(alerts))
    c2.metric("📈 Ghosting Rate Keseluruhan", f"{((live['progress_student']=='Ghosting')|(live['rejection']=='Ghosting')).mean()*100:.1f}%")

    st.markdown("##### Daftar Kandidat Berisiko Ghosting")
    for _, r in alerts.head(15).iterrows():
        comp_row = company[company["company_name"] == r["company"]]
        pic_phone = mask_phone(comp_row["pic_phone"].iloc[0]) if len(comp_row) else "-"
        ss_row = ss_live[ss_live["NIM"] == r["NIM"]]
        student_wa = mask_phone(ss_row["no_whatsapp"].iloc[0]) if len(ss_row) else "-"
        with st.container():
            st.markdown(
                f"""
                <div style="border-left:4px solid {RED};background:#FEF2F2;border-radius:8px;padding:10px 14px;margin-bottom:8px;">
                <b>⚠️ {r['student_name']}</b> (NIM: {r['NIM']}) — {r['position']} @ {r['company']}<br>
                <span style="color:{GREY};font-size:13px;">Tahap: {r['progress_student']} | Tanpa update: <b>{r['days_no_update']} hari</b>
                (Batas SLA: 7 hari) | Kontak Mhs: {student_wa} | Kontak PIC: {pic_phone}</span>
                </div>
                """, unsafe_allow_html=True,
            )
    if len(alerts) == 0:
        st.success("Tidak ada kandidat yang melampaui batas SLA saat ini. 🎉")

    st.markdown("---")
    colx, coly = st.columns(2)
    with colx:
        picks = alerts["id_tracking_student"].tolist()
        if picks:
            sel = st.selectbox("Kirim Follow-Up untuk:", picks)
            if st.button("📲 Kirim Follow-Up (FU) & Update Status"):
                idx = ts_live[ts_live["id_tracking_student"] == sel].index
                cur = st.session_state.ts_live.loc[idx, "progress_student"].iloc[0]
                nxt = {"FU 1": "FU 2", "FU 2": "FU 3"}.get(cur, "FU 1") if cur in ["FU 1", "FU 2"] else "FU 1"
                st.session_state.ts_live.loc[idx, "progress_student"] = nxt
                st.session_state.ts_live.loc[idx, "last_update"] = TODAY
                st.success(f"Follow-up **{nxt}** terkirim & tercatat di sistem audit.")
                st.rerun()
    with coly:
        st.markdown("**Distribusi hari tanpa update (kandidat aktif)**")
        active_live = live[live["progress_student"].isin(active_stage)]
        fig = px.histogram(active_live, x="days_no_update", nbins=20, color_discrete_sequence=[ACCENT])
        fig.add_vline(x=7, line_dash="dash", line_color=RED, annotation_text="Batas SLA (7 hari)")
        st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# C-05 PELAPORAN EKSEKUTIF IKU
# ============================================================================
elif menu == "C-05 Pelaporan Eksekutif IKU":
    st.title("📊 C-05 — Pelaporan Eksekutif IKU (Executive Analytics Panel)")
    st.caption("Menyelesaikan BT-04 (Analisis Tingkat Keberhasilan) & BT-07 (Pelaporan Periodik)")

    prodi_filter = st.multiselect("Filter Program Studi:", sorted(ss_live["program_studi"].unique()))
    view = ss_live.copy()
    if prodi_filter:
        view = view[view["program_studi"].isin(prodi_filter)]

    col1, col2 = st.columns([1, 1.4])
    with col1:
        st.subheader(f"Proporsi Status Mahasiswa (N={len(view)})")
        dist = view["ketersediaan"].value_counts().reset_index()
        dist.columns = ["Status", "Jumlah"]
        fig = px.pie(dist, names="Status", values="Jumlah", hole=0.55,
                     color="Status", color_discrete_map={"Placed": PRIMARY, "Available": GREEN, "Tidak Aktif": GREY})
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("Penempatan per Program Studi (Top 10)")
        placed_prodi = view[view["ketersediaan"] == "Placed"]["program_studi"].value_counts().head(10)
        figb = px.bar(placed_prodi[::-1], orientation="h", labels={"value": "Jumlah Placed", "index": "Program Studi"},
                      color_discrete_sequence=[PRIMARY])
        figb.update_layout(showlegend=False)
        st.plotly_chart(figb, use_container_width=True)

    st.subheader("Penempatan berdasarkan Sektor Industri Mitra")
    ts_comp = ts_live.merge(tracking_company[["id_tracking_company", "id_company"]], on="id_tracking_company", how="left")
    ts_comp = ts_comp.merge(company[["id_company", "industry_sector"]], on="id_company", how="left")
    placed_sector = ts_comp[ts_comp["rejection"] == "Placement"]["industry_sector"].value_counts()
    figs = px.bar(placed_sector, color_discrete_sequence=[ACCENT], labels={"value": "Jumlah Penempatan", "index": "Sektor Industri"})
    figs.update_layout(showlegend=False)
    st.plotly_chart(figs, use_container_width=True)

    st.subheader("Ringkasan per Jenis Penempatan")
    jenis_tbl = ts_live.groupby("jenis_penempatan").agg(
        Total=("id_tracking_student", "count"),
        Placement=("rejection", lambda s: (s == "Placement").sum()),
        Ghosting=("rejection", lambda s: (s == "Ghosting").sum()),
    ).reset_index()
    jenis_tbl["Success Rate (%)"] = (jenis_tbl["Placement"] / jenis_tbl["Total"] * 100).round(1)
    st.dataframe(jenis_tbl, use_container_width=True, hide_index=True)

    csv = view.drop(columns=["tools_list"]).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Unduh Laporan Rekapitulasi (CSV)", csv, "laporan_rekap_status_student.csv", "text/csv")


# ============================================================================
# C-06 PUSAT SINKRONISASI DATA
# ============================================================================
elif menu == "C-06 Pusat Sinkronisasi Data":
    st.title("🔄 C-06 — Pusat Sinkronisasi Data (Sync & Data Health Monitor)")
    st.caption("Menyelesaikan BT-08 (Manajemen Data Mahasiswa)  |  Ambang toleransi: 30 hari sejak sync_date")

    live = ss_live.copy()
    live["days_since_sync"] = (TODAY - live["sync_date"]).dt.days
    stale = live[live["days_since_sync"] > 30]

    pct_stale = len(stale) / len(live) * 100
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Record STATUS STUDENT", len(live))
    c2.metric("Belum Sinkron > 30 Hari", len(stale), delta=f"{pct_stale:.1f}% dari total", delta_color="inverse")
    c3.metric("Sehat (≤ 30 hari)", len(live) - len(stale))

    color = RED if pct_stale > 30 else (ACCENT if pct_stale > 10 else GREEN)
    st.markdown(
        f"""
        <div style="border:1px solid #E5E7EB;border-radius:12px;padding:18px;background:white;">
        <b>Data Health Score</b>
        <div style="background:#F3F4F6;border-radius:8px;height:22px;margin-top:8px;">
            <div style="background:{color};width:{min(pct_stale,100):.1f}%;height:22px;border-radius:8px;
            text-align:right;color:white;font-size:12px;padding-right:6px;">{pct_stale:.1f}% usang</div>
        </div>
        </div>
        """, unsafe_allow_html=True,
    )

    st.markdown("##### Mahasiswa dengan Data Paling Usang")
    st.dataframe(
        stale.sort_values("days_since_sync", ascending=False)[["NIM", "nama", "program_studi", "semester", "sync_date", "days_since_sync"]].head(20),
        use_container_width=True, hide_index=True,
    )

    st.markdown("---")
    if st.button("🔃 Sinkronisasi Sekarang (tarik semester, IPK*, prodi terbaru dari STUDENT ALL)"):
        merged = st.session_state.ss_live.merge(
            student_all[["NIM", "semester", "program_studi"]], on="NIM", how="left", suffixes=("", "_new")
        )
        n_updated = (merged["semester"] != merged["semester_new"]).sum()
        st.session_state.ss_live["semester"] = merged["semester_new"].values
        st.session_state.ss_live["program_studi"] = merged["program_studi_new"].values
        st.session_state.ss_live["sync_date"] = TODAY
        st.success(f"✅ Sinkronisasi selesai. {n_updated} record semester diperbarui, sync_date direset ke {TODAY.date()}.")
        st.rerun()

    st.caption("*IPK bersumber dari sistem akademik terpisah (SIAKAD) dan tidak tersedia di STUDENT ALL pada dataset ini; "
               "field ini tetap mengikuti nilai STATUS STUDENT terakhir.")
