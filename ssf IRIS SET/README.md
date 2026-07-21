# CDC Placement Dashboard — SSDC 2026

Dashboard ekosistem penempatan mahasiswa Career Development Center (CDC),
dibangun untuk babak penyisihan **Sebelas Maret Statistics Dashboard
Competition (SSDC) 2026**.

## Struktur folder
```
app/
├── app.py             # Aplikasi dashboard utama (Streamlit)
├── etl.py             # Pipeline ETL (pembersihan & standarisasi tanggal)
├── requirements.txt
├── clean_data/        # Output ETL (parquet), dibuat otomatis oleh etl.py
└── README.md
```

## Cara menjalankan
```bash
pip install -r requirements.txt

# 1) Jalankan ETL sekali untuk membentuk clean_data/*.parquet
python etl.py

# 2) Jalankan dashboard
streamlit run app.py
```
Dashboard akan terbuka di `http://localhost:8501`.

## Isi Dashboard (6 komponen sesuai cetak biru)
| Komponen | Business Task |
|---|---|
| C-01 Mesin Pencocokan Otomatis | BT-01, BT-06 |
| C-02 Kanban Pelacakan Progress | BT-02, BT-04 |
| C-03 Antrean Prioritas Permintaan | BT-03 |
| C-04 Sistem Peringatan Dini (EWS) | BT-05 |
| C-05 Pelaporan Eksekutif IKU | BT-04, BT-07 |
| C-06 Pusat Sinkronisasi Data | BT-08 |

Ditambah halaman **Ringkasan KPI** berisi 4 metrik utama: Placement Rate,
Offer Yield, Matching Velocity, dan Ghosting Rate.

## Catatan penting untuk pengumpulan lomba
- Format submission untuk Streamlit adalah file **.py** (skrip python) atau link
  (mis. Streamlit Community Cloud). File `app.py` ini dapat langsung diunggah
  atau di-deploy.
- Sebelum deploy publik, jalankan `etl.py` dan sertakan folder `clean_data/`
  bersama `app.py`, atau panggil `etl.clean()` di awal `app.py` bila ingin
  fully self-contained (tanpa file parquet terpisah).
- Ganti nama file mengikuti ketentuan panitia:
  `NomorPeserta_NamaTim_Dashboard` sebelum diunggah.
