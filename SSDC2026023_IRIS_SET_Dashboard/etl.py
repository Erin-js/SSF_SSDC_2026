"""
ETL Pipeline - Student Placement System (SSDC 2026)
Membersihkan & menyeragamkan format tanggal antar tabel, lalu menyimpan
versi bersih (parquet) yang dipakai oleh dashboard Streamlit.
"""
import pandas as pd
import numpy as np
import os

BASE_DIR = os.path.dirname(__file__)
# Prefer the original expected folder, but fall back to simpler data/ locations if missing
candidate_dirs = [

    os.path.join(BASE_DIR, "..", "data", "Database SSDC 2026 UNZIP"),
    os.path.join(BASE_DIR, "data"),
    os.path.join(BASE_DIR, "..", "data"),
]
RAW_DIR = next((d for d in candidate_dirs if os.path.isdir(d)), candidate_dirs[0])
OUT_DIR = os.path.join(BASE_DIR, "clean_data")
os.makedirs(OUT_DIR, exist_ok=True)


def load_raw():
    company = pd.read_csv(os.path.join(RAW_DIR, "company.csv"), encoding="utf-8-sig")
    talent_request = pd.read_csv(os.path.join(RAW_DIR, "talent_request.csv"), encoding="utf-8-sig")
    student_all = pd.read_csv(os.path.join(RAW_DIR, "student_all.csv"), encoding="utf-8-sig")
    status_student = pd.read_csv(os.path.join(RAW_DIR, "status_student.csv"), sep=";", encoding="utf-8-sig")
    tracking_company = pd.read_csv(os.path.join(RAW_DIR, "tracking_company.csv"), encoding="utf-8-sig")
    tracking_student = pd.read_csv(os.path.join(RAW_DIR, "tracking_student.csv"), encoding="utf-8-sig")
    return company, talent_request, student_all, status_student, tracking_company, tracking_student


def clean():
    company, talent_request, student_all, status_student, tracking_company, tracking_student = load_raw()

    # --- Standarisasi tipe key sebagai string ---
    for df, col in [(company, "id_company"), (talent_request, "id_talent_req"),
                     (talent_request, "id_company"), (student_all, "NIM"),
                     (status_student, "NIM"), (tracking_company, "id_tracking_company"),
                     (tracking_company, "id_talent_req"), (tracking_company, "id_company"),
                     (tracking_student, "NIM"), (tracking_student, "id_tracking_company")]:
        df[col] = df[col].astype(str).str.strip()

    # --- ETL Tanggal ---
    # company.created_at -> YYYY-MM-DD (sudah standar)
    company["created_at"] = pd.to_datetime(company["created_at"], format="%Y-%m-%d", errors="coerce")

    # talent_request.request_date -> YYYY-MM-DD (standar)
    talent_request["request_date"] = pd.to_datetime(talent_request["request_date"], format="%Y-%m-%d", errors="coerce")

    # tracking_company.request_date & send_date -> DD/MM/YYYY (perlu dikonversi)
    tracking_company["request_date"] = pd.to_datetime(tracking_company["request_date"], format="%d/%m/%Y", errors="coerce")
    tracking_company["send_date"] = pd.to_datetime(tracking_company["send_date"], format="%d/%m/%Y", errors="coerce")

    # tracking_student.last_update -> YYYY-MM-DD (standar)
    tracking_student["last_update"] = pd.to_datetime(tracking_student["last_update"], format="%Y-%m-%d", errors="coerce")

    # status_student.sync_date -> DD/MM/YYYY (perlu dikonversi, sesuai sampel data)
    status_student["sync_date"] = pd.to_datetime(status_student["sync_date"], format="%d/%m/%Y", errors="coerce")

    # --- Bersihkan tools jadi list ---
    status_student["tools_list"] = status_student["tools"].fillna("").apply(
        lambda x: [t.strip() for t in x.split(",") if t.strip()]
    )

    # --- Bersihkan list_nim di tracking_company jadi list ---
    tracking_company["list_nim_list"] = tracking_company["list_nim"].fillna("").apply(
        lambda x: [t.strip() for t in x.split(",") if t.strip()]
    )

    # Simpan
    company.to_parquet(os.path.join(OUT_DIR, "company.parquet"))
    talent_request.to_parquet(os.path.join(OUT_DIR, "talent_request.parquet"))
    student_all.to_parquet(os.path.join(OUT_DIR, "student_all.parquet"))
    status_student.to_parquet(os.path.join(OUT_DIR, "status_student.parquet"))
    tracking_company.to_parquet(os.path.join(OUT_DIR, "tracking_company.parquet"))
    tracking_student.to_parquet(os.path.join(OUT_DIR, "tracking_student.parquet"))

    return company, talent_request, student_all, status_student, tracking_company, tracking_student


if __name__ == "__main__":
    dfs = clean()
    for name, df in zip(
        ["company", "talent_request", "student_all", "status_student", "tracking_company", "tracking_student"], dfs
    ):
        print(name, df.shape)




