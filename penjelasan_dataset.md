# Penjelasan Dataset SSDC 2026

## 1. Identitas Dataset

**Nama sistem:** Student Placement System  
**Fokus:** Talent Placement Management for Internship & Employment  
**Pengguna utama:** Career Development Center (CDC) perguruan tinggi  
**Jumlah tabel:** 6  
**Jumlah kolom gabungan:** 79

Dataset dirancang untuk mendukung pengelolaan penempatan mahasiswa ke perusahaan mitra. Sistem mempertemukan dua sisi:

1. Mahasiswa yang mencari pengalaman kerja atau kesempatan kerja.
2. Perusahaan yang membutuhkan talent untuk magang, part-time, atau full-time.

Data mencakup seluruh siklus placement, mulai dari pendaftaran perusahaan, pengajuan kebutuhan talent, pendataan mahasiswa, pemeriksaan kelayakan, pengiriman kandidat, pemantauan seleksi, sampai hasil akhir penempatan.

---

## 2. Gambaran Skenario

Career Development Center bertugas menghubungkan mahasiswa aktif dengan perusahaan mitra. Setiap semester, perusahaan mengajukan kebutuhan tenaga kerja untuk berbagai posisi, seperti:

- programmer;
- data analyst;
- UI/UX designer;
- business analyst;
- staf administrasi;
- marketing;
- dan posisi lainnya.

Di sisi lain, mahasiswa mendaftarkan diri ke program CDC untuk mendapatkan kesempatan magang, part-time, atau full-time.

Tantangan utama CDC adalah:

1. Mencocokkan kebutuhan perusahaan dengan profil mahasiswa.
2. Memastikan mahasiswa memenuhi syarat sebelum dikirim.
3. Memantau satu mahasiswa yang mungkin mengikuti beberapa seleksi sekaligus.
4. Menghindari proses seleksi yang terbengkalai.
5. Menangani *ghosting* dari mahasiswa atau perusahaan.
6. Menyusun laporan placement secara periodik.
7. Menjaga sinkronisasi dan kualitas data.

---

## 3. Alur Proses Bisnis

### Tahap 1 — Registrasi Perusahaan

Perusahaan mendaftar sebagai mitra CDC. Profil perusahaan diverifikasi dan disimpan dalam tabel `company`.

### Tahap 2 — Pengajuan Talent Request

Perusahaan mengisi formulir kebutuhan talent, meliputi posisi, jumlah kandidat, persyaratan, skema kerja, durasi, dan remunerasi. Data disimpan dalam tabel `talent_request`.

### Tahap 3 — Seleksi Kandidat oleh CDC

CDC memeriksa mahasiswa pada tabel `status_student` berdasarkan:

- status aktif;
- ketersediaan;
- program studi;
- semester;
- IPK;
- kelengkapan CV;
- portofolio;
- domisili;
- tools atau kemampuan teknis.

### Tahap 4 — Pengiriman Kandidat

CDC mengirim profil kandidat kepada perusahaan. Informasi request, tanggal kirim, jumlah permintaan, dan jumlah kandidat yang dikirim dicatat dalam `tracking_company`.

### Tahap 5 — Proses Seleksi Perusahaan

Perusahaan melakukan tahapan seleksi seperti:

- screening CV;
- study case;
- briefing;
- interview user;
- final interview;
- placement atau rejection.

Setiap proses mahasiswa dicatat dalam `tracking_student`.

### Tahap 6 — Monitoring dan Follow Up

CDC memantau proses seleksi. Apabila belum ada respons, CDC dapat melakukan:

- FU 1;
- FU 2;
- FU 3;
- penandaan Ghosting.

### Tahap 7 — Placement

Apabila mahasiswa diterima:

- `tracking_student.progress_student` berubah menjadi `Placement`;
- `status_student.ketersediaan` dapat berubah menjadi `Placed`.

---

## 4. Business Task

Dataset dirancang untuk menjawab delapan kelompok kebutuhan utama.

| ID | Nama Task | Tujuan |
|---|---|---|
| BT-01 | Matching Talent | Menemukan mahasiswa paling sesuai berdasarkan program studi, semester, tools, IPK, ketersediaan, dan domisili |
| BT-02 | Monitoring Progress Seleksi | Memantau setiap tahapan seleksi mahasiswa di setiap perusahaan |
| BT-03 | Manajemen Talent Request | Mengelola dan memprioritaskan request berdasarkan tanggal, headcount, dan jenis penempatan |
| BT-04 | Analisis Tingkat Keberhasilan | Mengukur persentase placement dan perusahaan dengan acceptance tertinggi |
| BT-05 | Deteksi Ghosting | Menemukan mahasiswa atau perusahaan yang tidak merespons |
| BT-06 | Kelayakan Mahasiswa | Memastikan hanya mahasiswa yang aktif, eligible, dan memiliki dokumen lengkap yang dikirim |
| BT-07 | Pelaporan Periodik | Membuat rekap placement per semester, program studi, perusahaan, dan jenis penempatan |
| BT-08 | Manajemen Data Mahasiswa | Memastikan sinkronisasi data antara `student_all` dan `status_student` |

---

## 5. Gambaran Struktur ERD

Secara konseptual, ERD membentuk dua aliran utama yang bertemu pada proses seleksi mahasiswa.

```text
SISI PERUSAHAAN

company
   |
   | 1-to-many melalui id_company
   v
talent_request
   |
   | 1-to-one / 1-to-many melalui id_talent_req
   v
tracking_company
   |
   | 1-to-many melalui id_tracking_company
   v
tracking_student


SISI MAHASISWA

student_all
   |
   | 1-to-one melalui NIM
   v
status_student

student_all
   |
   | 1-to-many melalui NIM
   v
tracking_student
```

Gambaran keseluruhan:

```text
company ───────────────┐
   │                    │
   ▼                    ▼
talent_request ──► tracking_company ──► tracking_student
                                              ▲
                                              │
student_all ─────► status_student              │
     └────────────────────────────────────────┘
```

---

## 6. Relasi Antar Tabel

| Relasi | Kardinalitas | Key | Penjelasan |
|---|---|---|---|
| `company` → `talent_request` | One-to-Many | `id_company` | Satu perusahaan dapat mengajukan banyak talent request |
| `company` → `tracking_company` | One-to-Many | `id_company` | Satu perusahaan dapat memiliki banyak record tracking |
| `talent_request` → `tracking_company` | One-to-One / One-to-Many | `id_talent_req` | Satu request dapat memiliki satu atau beberapa batch pengiriman |
| `student_all` → `status_student` | One-to-One | `NIM` | Setiap mahasiswa seharusnya mempunyai satu status terkini |
| `student_all` → `tracking_student` | One-to-Many | `NIM` | Satu mahasiswa dapat mengikuti beberapa proses seleksi |
| `tracking_company` → `tracking_student` | One-to-Many | `id_tracking_company` | Satu batch pengiriman dapat memuat banyak mahasiswa |

---

# 7. Penjelasan Tiap Tabel

## 7.1 Tabel `company`

### Fungsi

Tabel `company` merupakan master data seluruh perusahaan mitra yang terdaftar dalam sistem CDC.

### Grain

```text
1 baris = 1 perusahaan
```

### Primary Key

```text
id_company
```

### Struktur Kolom

| Kolom | Tipe | Key | Deskripsi |
|---|---|---|---|
| `id_company` | VARCHAR | PK | ID unik perusahaan, format `C` + 3 digit |
| `company_name` | VARCHAR |  | Nama resmi perusahaan |
| `company_type` | VARCHAR |  | Jenis perusahaan, seperti Startup, UMKM, Corporate, BUMN, NGO, Pemerintah |
| `industry_sector` | VARCHAR |  | Sektor industri, seperti teknologi, keuangan, logistik, kesehatan, media |
| `kota` | VARCHAR |  | Kota lokasi kantor utama |
| `skala_perusahaan` | VARCHAR |  | Skala operasi: Lokal, Nasional, Multinasional |
| `pic_name` | VARCHAR |  | Nama PIC utama perusahaan |
| `pic_phone` | VARCHAR |  | Nomor WhatsApp PIC |
| `created_at` | DATE |  | Tanggal perusahaan pertama kali terdaftar |

### Peran Analitis

Tabel ini dapat digunakan untuk menganalisis:

- jumlah perusahaan mitra;
- distribusi perusahaan per sektor;
- jenis perusahaan;
- skala perusahaan;
- persebaran kota;
- pertumbuhan mitra dari waktu ke waktu;
- perusahaan yang paling aktif mengajukan kebutuhan.

### Catatan

`company` sebaiknya menjadi sumber utama untuk identitas perusahaan, terutama `company_name`, `company_type`, `industry_sector`, dan `kota`.

---

## 7.2 Tabel `talent_request`

### Fungsi

Tabel `talent_request` merekam setiap kebutuhan talent yang diajukan perusahaan kepada CDC.

### Grain

```text
1 baris = 1 permintaan posisi dari perusahaan
```

### Key

```text
PK: id_talent_req
FK: id_company → company.id_company
```

### Struktur Kolom

| Kolom | Tipe | Key | Deskripsi |
|---|---|---|---|
| `id_talent_req` | VARCHAR | PK | ID unik request, format `TR` + 3 digit |
| `id_company` | VARCHAR | FK | Referensi ke perusahaan |
| `nama_perusahaan` | VARCHAR |  | Nama perusahaan yang didenormalisasi |
| `alamat_kantor` | TEXT |  | Alamat lokasi penempatan |
| `industri_sektor` | VARCHAR |  | Sektor industri pada saat request |
| `nama_pic` | VARCHAR |  | PIC khusus untuk proses rekrutmen |
| `no_whatsapp` | VARCHAR |  | Nomor WhatsApp PIC request |
| `nama_posisi` | VARCHAR |  | Nama posisi yang dibutuhkan |
| `jenis_penempatan` | VARCHAR |  | Magang, Part-time, atau Full-time |
| `headcount` | INT |  | Jumlah mahasiswa yang dibutuhkan |
| `bidang_studi_dibutuhkan` | VARCHAR |  | Program studi yang direkomendasikan atau disyaratkan |
| `minimum_semester` | INT |  | Semester minimum kandidat |
| `deskripsi_requirement` | TEXT |  | Deskripsi pekerjaan dan persyaratan teknis/nonteknis |
| `working_arrangement` | VARCHAR |  | WFH, WFO, atau Hybrid |
| `working_arrangement_detail` | TEXT |  | Detail hari kerja, jam operasional, dan fleksibilitas |
| `durasi` | VARCHAR |  | Lama penempatan |
| `renumerasi` | VARCHAR |  | Kompensasi, uang saku, tunjangan, atau Non-Paid |
| `request_date` | DATE |  | Tanggal request diajukan |
| `sumber_baris_form` | VARCHAR |  | Asal data, seperti Google Form, Manual, Email, atau WhatsApp |

### Peran Analitis

Tabel ini dapat digunakan untuk:

- menghitung jumlah request;
- menghitung total headcount;
- melihat posisi paling dibutuhkan;
- menganalisis permintaan per program studi;
- melihat distribusi jenis penempatan;
- membandingkan WFO, WFH, dan Hybrid;
- menganalisis durasi dan remunerasi;
- menentukan prioritas request berdasarkan umur request.

### Catatan Denormalisasi

Beberapa kolom mengulang data dari `company`, seperti:

- `nama_perusahaan`;
- `industri_sektor`.

Untuk analisis final, identitas perusahaan sebaiknya diambil dari master `company`, sedangkan data di `talent_request` dapat digunakan untuk validasi.

---

## 7.3 Tabel `student_all`

### Fungsi

Tabel `student_all` merupakan master data mahasiswa yang mengikuti program CDC.

### Grain

```text
1 baris = 1 mahasiswa
```

### Primary Key

```text
NIM
```

### Struktur Kolom

| Kolom | Tipe | Key | Deskripsi |
|---|---|---|---|
| `NIM` | VARCHAR | PK | Nomor Induk Mahasiswa |
| `nama` | VARCHAR |  | Nama mahasiswa |
| `program_studi` | VARCHAR |  | Program studi mahasiswa |
| `semester` | INT |  | Semester aktif |
| `hp` | VARCHAR |  | Nomor telepon mahasiswa |
| `email_pribadi` | VARCHAR |  | E-mail personal |
| `email_kampus` | VARCHAR |  | E-mail institusi |
| `bidang_minat` | VARCHAR |  | Bidang karier yang diminati |
| `jenis_penempatan_diminati` | VARCHAR |  | Preferensi magang, part-time, full-time, atau kombinasi |
| `bulan_masuk` | VARCHAR |  | Bulan dan tahun pertama masuk kuliah |

### Peran Analitis

Tabel ini dapat digunakan untuk:

- menghitung jumlah mahasiswa;
- distribusi mahasiswa per program studi;
- distribusi semester;
- preferensi jenis penempatan;
- bidang minat;
- estimasi tahun masuk dan tahun lulus;
- profil supply talent.

### Catatan

Tabel ini bersifat relatif statis dan sebaiknya menjadi sumber utama identitas mahasiswa.

---

## 7.4 Tabel `status_student`

### Fungsi

Tabel `status_student` menyimpan informasi dinamis tentang kesiapan dan kelayakan mahasiswa untuk placement.

### Grain

```text
1 baris = 1 mahasiswa dengan status terkininya
```

### Key

```text
PK: id_status
FK: NIM → student_all.NIM
```

Relasi dengan `student_all` seharusnya one-to-one.

### Struktur Kolom

| Kolom | Tipe | Key | Deskripsi |
|---|---|---|---|
| `id_status` | VARCHAR | PK | ID unik status, format `SS` + 3 digit |
| `NIM` | VARCHAR | FK | Referensi ke mahasiswa |
| `email` | VARCHAR |  | E-mail aktif |
| `nama` | VARCHAR |  | Nama mahasiswa yang didenormalisasi |
| `semester` | INT |  | Semester terkini |
| `program_studi` | VARCHAR |  | Program studi terkini |
| `no_whatsapp` | VARCHAR |  | Nomor WhatsApp aktif |
| `CV` | VARCHAR |  | Status CV: Ada atau Tidak Ada |
| `portofolio` | VARCHAR |  | Status portofolio: Ada atau Tidak Ada |
| `IPK` | DECIMAL |  | Indeks Prestasi Kumulatif |
| `status` | VARCHAR |  | Active, Inactive, Cuti, atau Lulus |
| `domisili` | VARCHAR |  | Kota tempat tinggal mahasiswa |
| `ketersediaan` | VARCHAR |  | Available, Placed, atau Tidak Aktif |
| `tools` | TEXT |  | Tools atau software yang dikuasai, dipisahkan koma |
| `sync_date` | DATE |  | Tanggal terakhir sinkronisasi data |

### Peran Analitis

Tabel ini dapat digunakan untuk:

- kelayakan dasar mahasiswa;
- kesiapan dokumen;
- jumlah mahasiswa available;
- jumlah mahasiswa placed;
- distribusi IPK;
- tools yang dikuasai;
- kecocokan domisili;
- deteksi data lama berdasarkan `sync_date`.

### Catatan Penting tentang Eligible

Dokumentasi menyebut `eligible` sebagai penentu utama kelayakan. Namun, pada struktur tabel dan ERD tidak terdapat kolom bernama `eligible`.

Karena itu, variabel eligible kemungkinan perlu dibentuk dari aturan, misalnya:

```text
basic_eligible =
    status == "Active"
    AND ketersediaan == "Available"
    AND CV == "Ada"
```

Untuk kecocokan request tertentu:

```text
request_eligible =
    basic_eligible
    AND semester >= minimum_semester
    AND program_studi sesuai
    AND jenis_penempatan sesuai
```

Portofolio dapat dijadikan syarat tambahan hanya jika posisi membutuhkannya.

### Catatan Denormalisasi

Kolom berikut mengulang data dari `student_all`:

- `nama`;
- `semester`;
- `program_studi`;
- `email`.

Sumber utama identitas sebaiknya tetap `student_all`, sedangkan `status_student` digunakan untuk kondisi terkini.

---

## 7.5 Tabel `tracking_company`

### Fungsi

Tabel `tracking_company` mencatat proses pengiriman kandidat dari CDC ke perusahaan untuk suatu talent request.

Tabel ini menjadi penghubung antara `talent_request` dan `tracking_student`.

### Grain

```text
1 baris = 1 proses atau batch pengiriman kandidat untuk 1 talent request
```

### Key

```text
PK: id_tracking_company
FK: id_talent_req → talent_request.id_talent_req
FK: id_company → company.id_company
```

### Struktur Kolom

| Kolom | Tipe | Key | Deskripsi |
|---|---|---|---|
| `id_tracking_company` | VARCHAR | PK | ID tracking, format `TC` + 3 digit |
| `id_talent_req` | VARCHAR | FK | Referensi ke talent request |
| `id_company` | VARCHAR | FK | Referensi ke perusahaan |
| `nama_perusahaan` | VARCHAR |  | Nama perusahaan yang didenormalisasi |
| `posisi` | VARCHAR |  | Posisi yang sedang ditracking |
| `jenis_penempatan` | VARCHAR |  | Magang, Part-time, atau Full-time |
| `bidang_studi_dicari` | VARCHAR |  | Program studi yang dibutuhkan |
| `progress` | VARCHAR |  | Status proses perusahaan |
| `request_date` | DATE |  | Tanggal request diterima CDC |
| `send_date` | DATE |  | Tanggal kandidat dikirim; kosong jika belum dikirim |
| `jumlah_permintaan` | INT |  | Jumlah kandidat yang diminta |
| `jumlah_dikirimkan` | INT |  | Jumlah kandidat yang dikirim |
| `list_nim` | TEXT |  | Daftar NIM kandidat yang dipisahkan koma |

### Nilai Progress

Nilai yang disebutkan:

- Draft
- Submitted
- On Review
- Shortlisted
- Closed

### Peran Analitis

Tabel ini dapat digunakan untuk:

- menghitung request yang belum dikirim;
- mengukur waktu dari request ke pengiriman;
- membandingkan jumlah permintaan dan jumlah dikirim;
- menghitung coverage ratio;
- memantau status perusahaan;
- menentukan request yang perlu diprioritaskan.

### Contoh Metrik

```text
days_to_send = send_date - request_date
```

```text
candidate_gap = jumlah_permintaan - jumlah_dikirimkan
```

```text
coverage_ratio = jumlah_dikirimkan / jumlah_permintaan
```

### Catatan tentang `list_nim`

`list_nim` menyimpan beberapa NIM dalam satu sel, contohnya:

```text
2021001,2021002,2021003
```

Struktur ini tidak ternormalisasi. Untuk analisis:

1. `list_nim` dapat dipecah menjadi beberapa baris;
2. atau digunakan hanya sebagai validasi;
3. tabel `tracking_student` tetap menjadi sumber utama analisis kandidat individual.

---

## 7.6 Tabel `tracking_student`

### Fungsi

Tabel `tracking_student` adalah pusat monitoring seleksi pada level mahasiswa.

### Grain

```text
1 baris = 1 mahasiswa dalam 1 proses seleksi perusahaan
```

Jika seorang mahasiswa mengikuti tiga proses seleksi, NIM tersebut dapat muncul tiga kali.

### Key

```text
PK: id_tracking_student
FK: NIM → student_all.NIM
FK: id_tracking_company → tracking_company.id_tracking_company
```

### Struktur Kolom

| Kolom | Tipe | Key | Deskripsi |
|---|---|---|---|
| `id_tracking_student` | VARCHAR | PK | ID unik tracking mahasiswa, format `TS` + 3 digit |
| `NIM` | VARCHAR | FK | Referensi ke mahasiswa |
| `id_tracking_company` | VARCHAR | FK | Referensi ke batch pengiriman perusahaan |
| `student_name` | VARCHAR |  | Nama mahasiswa yang didenormalisasi |
| `internship_semester` | INT |  | Semester mahasiswa saat placement |
| `company` | VARCHAR |  | Nama perusahaan yang didenormalisasi |
| `position` | VARCHAR |  | Posisi yang dilamar |
| `jenis_penempatan` | VARCHAR |  | Magang, Part-time, atau Full-time |
| `progress_student` | VARCHAR |  | Tahap seleksi terkini |
| `last_update` | DATE |  | Tanggal terakhir status diperbarui |
| `rejection` | VARCHAR |  | Outcome atau alasan akhir proses |

### Nilai Valid `progress_student`

| Nilai | Penjelasan |
|---|---|
| Selecting Student by Company | Perusahaan meninjau kandidat |
| Study Case | Kandidat menjalani tes atau studi kasus |
| CDC Briefing Student | CDC memberikan briefing |
| Interview User | Kandidat menjalani wawancara dengan user/hiring manager |
| Final Interview | Kandidat menjalani wawancara tahap akhir |
| Placement | Kandidat diterima dan ditempatkan |
| FU 1 | Follow up pertama |
| FU 2 | Follow up kedua |
| FU 3 | Follow up ketiga |
| Ghosting | Tidak ada respons setelah beberapa follow up |
| Rejected | Kandidat tidak lolos |
| Finish | Proses selesai dan tidak ada tindak lanjut |

### Nilai Valid `rejection`

- On Progress
- Placement
- Rejection Screening CV
- Rejection Interview User
- Rejection Study Case
- Rejection Final Interview
- Ghosting

### Peran Analitis

Tabel ini dapat digunakan untuk:

- funnel seleksi;
- jumlah kandidat pada setiap tahap;
- placement rate;
- rejection rate;
- ghosting rate;
- alasan penolakan;
- proses yang lama tidak diperbarui;
- performa perusahaan;
- performa mahasiswa atau program studi.

### Catatan Outcome

`progress_student` menunjukkan tahapan terkini, sedangkan `rejection` lebih cocok digunakan untuk outcome akhir.

Kolom turunan yang disarankan:

```text
canonical_outcome
```

Contoh aturan:

```text
Jika rejection == "Placement"          → Placement
Jika rejection == "Ghosting"           → Ghosting
Jika rejection diawali "Rejection"      → Rejected
Selain itu                             → On Progress
```

`Finish` tidak otomatis berarti placement karena dapat menunjukkan proses selesai, baik berhasil maupun tidak.

---

# 8. Primary Key dan Foreign Key

## 8.1 Primary Key

| Tabel | Primary Key |
|---|---|
| `company` | `id_company` |
| `talent_request` | `id_talent_req` |
| `student_all` | `NIM` |
| `status_student` | `id_status` |
| `tracking_company` | `id_tracking_company` |
| `tracking_student` | `id_tracking_student` |

## 8.2 Foreign Key

| Tabel | Foreign Key | Referensi |
|---|---|---|
| `talent_request` | `id_company` | `company.id_company` |
| `status_student` | `NIM` | `student_all.NIM` |
| `tracking_company` | `id_talent_req` | `talent_request.id_talent_req` |
| `tracking_company` | `id_company` | `company.id_company` |
| `tracking_student` | `NIM` | `student_all.NIM` |
| `tracking_student` | `id_tracking_company` | `tracking_company.id_tracking_company` |

---

# 9. Grain dan Risiko Double Counting

Grain adalah unit observasi setiap tabel.

| Tabel | Grain |
|---|---|
| `company` | satu perusahaan |
| `talent_request` | satu request posisi |
| `student_all` | satu mahasiswa |
| `status_student` | satu status terkini per mahasiswa |
| `tracking_company` | satu batch pengiriman |
| `tracking_student` | satu mahasiswa × satu proses seleksi |

Jangan langsung menggabungkan semua tabel lalu menjumlahkan kolom numerik. Relasi one-to-many dapat menggandakan nilai.

Contoh:

```text
Satu talent request memiliki headcount = 3.
Request tersebut memiliki 5 kandidat di tracking_student.
```

Setelah join, nilai `headcount = 3` dapat muncul lima kali. Jika dijumlahkan, hasilnya menjadi 15, padahal kebutuhan sebenarnya tetap 3.

Solusi:

1. Tentukan grain analisis.
2. Agregasikan sebelum join.
3. Gunakan `COUNT DISTINCT` untuk entity unik.
4. Bedakan metrik pada level request, batch, dan kandidat.

---

# 10. Kolom Didenormalisasi

Dataset menyimpan beberapa informasi berulang untuk mempermudah pembacaan tanpa join.

### Identitas Perusahaan

- `company.company_name`
- `talent_request.nama_perusahaan`
- `tracking_company.nama_perusahaan`
- `tracking_student.company`

### Posisi

- `talent_request.nama_posisi`
- `tracking_company.posisi`
- `tracking_student.position`

### Identitas Mahasiswa

- `student_all.nama`
- `status_student.nama`
- `tracking_student.student_name`

### Program Studi dan Semester

- `student_all.program_studi`
- `status_student.program_studi`
- `student_all.semester`
- `status_student.semester`
- `tracking_student.internship_semester`

Kolom-kolom tersebut perlu diperiksa konsistensinya.

Sumber utama yang disarankan:

- perusahaan: `company`;
- request dan posisi: `talent_request`;
- identitas mahasiswa: `student_all`;
- status kesiapan: `status_student`;
- progres seleksi: `tracking_student`.

---

# 11. Pemeriksaan Kualitas Data

## 11.1 Validasi Primary Key

Periksa apakah setiap primary key:

- tidak kosong;
- unik;
- mengikuti format ID yang sesuai.

## 11.2 Validasi Foreign Key

Periksa apakah:

- seluruh `talent_request.id_company` terdapat pada `company`;
- seluruh `tracking_company.id_talent_req` terdapat pada `talent_request`;
- seluruh `tracking_company.id_company` terdapat pada `company`;
- seluruh `status_student.NIM` terdapat pada `student_all`;
- seluruh `tracking_student.NIM` terdapat pada `student_all`;
- seluruh `tracking_student.id_tracking_company` terdapat pada `tracking_company`.

## 11.3 Validasi Relasi One-to-One

Satu NIM seharusnya hanya muncul sekali pada `status_student`.

```text
student_all.NIM 1 ─── 1 status_student.NIM
```

## 11.4 Standarisasi Kategori

Kolom yang berpotensi tidak konsisten:

- program studi;
- jenis penempatan;
- company type;
- sektor industri;
- skala perusahaan;
- working arrangement;
- status mahasiswa;
- ketersediaan;
- CV;
- portofolio;
- progress;
- progress_student;
- rejection;
- domisili;
- tools.

Contoh variasi:

```text
Magang
magang
MAGANG
Internship
PKL
```

Kategori tersebut perlu dipetakan ke label yang konsisten.

## 11.5 Tipe Data

Kolom tanggal:

- `created_at`
- `request_date`
- `send_date`
- `sync_date`
- `last_update`

Kolom numerik:

- `headcount`
- `jumlah_permintaan`
- `jumlah_dikirimkan`
- `semester`
- `minimum_semester`
- `internship_semester`
- `IPK`

Kolom yang harus tetap teks:

- NIM;
- ID;
- nomor telepon;
- nomor WhatsApp.

## 11.6 Kolom Multivalue

Beberapa kolom dapat menyimpan lebih dari satu nilai:

- `tools`;
- `bidang_studi_dibutuhkan`;
- `jenis_penempatan_diminati`;
- `list_nim`;
- `deskripsi_requirement`.

Kolom tersebut dapat dipisahkan dengan delimiter, dinormalisasi, atau diekstrak menjadi fitur.

---

# 12. Struktur Analisis yang Disarankan

## 12.1 Mart Student Readiness

Gabungan:

```text
student_all
LEFT JOIN status_student USING (NIM)
```

Grain:

```text
1 baris = 1 mahasiswa
```

Digunakan untuk:

- kesiapan mahasiswa;
- kelengkapan dokumen;
- eligibility;
- program studi;
- tools;
- IPK;
- preferensi;
- ketersediaan.

## 12.2 Mart Request

Gabungan:

```text
company
JOIN talent_request USING (id_company)
LEFT JOIN tracking_company USING (id_talent_req)
```

Grain harus ditentukan sebagai:

```text
1 baris = 1 talent request
```

atau:

```text
1 baris = 1 batch tracking company
```

Digunakan untuk:

- demand talent;
- headcount;
- request age;
- waktu pengiriman;
- coverage;
- backlog;
- status perusahaan.

## 12.3 Mart Candidate Pipeline

Gabungan:

```text
tracking_student
JOIN tracking_company USING (id_tracking_company)
JOIN talent_request USING (id_talent_req)
JOIN company USING (id_company)
LEFT JOIN student_all USING (NIM)
LEFT JOIN status_student USING (NIM)
```

Grain:

```text
1 baris = 1 mahasiswa × 1 proses seleksi
```

Digunakan untuk:

- funnel;
- placement;
- rejection;
- ghosting;
- acceptance rate;
- follow-up;
- analisis performa perusahaan dan program studi.

---

# 13. Metrik Turunan yang Relevan

## 13.1 Request Age

```text
request_age = tanggal_acuan - request_date
```

## 13.2 Time to Send

```text
time_to_send = send_date - request_date
```

## 13.3 Candidate Gap

```text
candidate_gap = jumlah_permintaan - jumlah_dikirimkan
```

## 13.4 Coverage Ratio

```text
coverage_ratio = jumlah_dikirimkan / jumlah_permintaan
```

## 13.5 Acceptance Rate

```text
acceptance_rate =
jumlah proses Placement / jumlah proses kandidat dikirim
```

## 13.6 Fill Rate

```text
fill_rate =
jumlah mahasiswa Placement / total headcount
```

## 13.7 Rejection Rate

```text
rejection_rate =
jumlah proses Rejected / jumlah proses kandidat
```

## 13.8 Ghosting Rate

```text
ghosting_rate =
jumlah proses Ghosting / jumlah proses kandidat
```

## 13.9 Days Since Update

```text
days_since_update =
tanggal_acuan - last_update
```

## 13.10 Sync Lag

```text
sync_lag =
tanggal_acuan - sync_date
```

---

# 14. Keterbatasan Dataset

1. Tidak tersedia riwayat perubahan status secara lengkap.
2. Hanya tersedia `last_update`, bukan tanggal untuk setiap tahapan seleksi.
3. Tidak terdapat kolom minimum IPK secara eksplisit pada request.
4. Requirement teknis tersimpan dalam teks bebas.
5. `list_nim` menyimpan banyak nilai dalam satu sel.
6. Kolom `eligible` disebut dalam dokumentasi, tetapi tidak terdapat pada struktur tabel.
7. Status Ghosting tidak menjelaskan pihak yang tidak merespons.
8. `Finish` tidak menjelaskan outcome akhir secara otomatis.
9. Beberapa identitas didenormalisasi dan berpotensi tidak konsisten.
10. Data kontak dan identitas mahasiswa bersifat sensitif sehingga perlu dilindungi.

---

# 15. Privasi dan Etika

Dataset memuat data sensitif seperti:

- NIM;
- nama mahasiswa;
- e-mail;
- nomor telepon;
- nomor WhatsApp;
- IPK;
- CV dan portofolio;
- nama PIC perusahaan;
- nomor PIC;
- status seleksi;
- alasan penolakan.

Untuk dashboard publik:

1. Samarkan nama mahasiswa.
2. Jangan tampilkan NIM lengkap.
3. Jangan tampilkan nomor telepon atau e-mail.
4. Jangan menampilkan identitas PIC.
5. Gunakan agregasi untuk analisis publik.
6. Batasi data individual untuk kebutuhan operasional internal.
7. Hindari ranking yang dapat merugikan mahasiswa tanpa konteks.
8. Jelaskan aturan matching agar tidak menjadi kotak hitam.

---

# 16. Kesimpulan

Dataset SSDC 2026 menggambarkan ekosistem placement mahasiswa dari hulu sampai hilir:

```text
Perusahaan terdaftar
        ↓
Perusahaan mengajukan kebutuhan
        ↓
CDC mencari kandidat
        ↓
Kandidat dikirim
        ↓
Perusahaan melakukan seleksi
        ↓
CDC memantau dan melakukan follow up
        ↓
Placement / Rejected / Ghosting / Finish
```

Enam tabelnya dapat dikelompokkan menjadi tiga lapisan:

```text
MASTER DATA
company, student_all, status_student

DEMAND DAN TRANSAKSI
talent_request, tracking_company

PROSES DAN OUTCOME
tracking_student
```

Kekuatan dataset ini terletak pada kemampuannya mendukung analisis:

- supply dan demand talent;
- matching mahasiswa;
- prioritas request;
- monitoring funnel;
- placement rate;
- rejection dan ghosting;
- follow-up;
- kualitas dan sinkronisasi data.

Agar analisis akurat, setiap proses harus mempertahankan grain tabel, menghindari double counting, memvalidasi primary key dan foreign key, serta memperhatikan kolom yang didenormalisasi.

---

## Sumber

Dokumen ini disusun berdasarkan:

- **Penjelasan Dataset SSDC 2026**
- **ERD_SSDC.png**
