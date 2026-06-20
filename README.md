# pv26-finalproject-mygts

## MyGTS — My Gangsar Treasure System

Aplikasi desktop manajemen inventaris sanggar berbasis **PySide6** dan **Supabase** (PostgreSQL cloud).
Mengelola penyewaan inventaris (kostum, aksesoris, properti, alat musik, make up, dll.) secara digital, lengkap dengan dokumentasi foto dan perhitungan denda otomatis.

---

## Anggota Kelompok

| Nama | NIM | Peran |
|------|-----|-------|
| Lalu MUhammad Farhan | F1D02310119 | UI / View Layer |
| Baiq Adelia Dwi Savitri | F1D02310006 | Logic / Controller |
| Syamsul Rijal | F1D02310025 | Database / Model |

---

## Fitur Utama

- 🔐 Login & autentikasi dua role: **Customer** dan **Owner**
- 📦 Manajemen inventaris per kategori dengan search + filter + sorting
- 📋 Alur penyewaan lengkap: pemesanan → konfirmasi → pengambilan → pengembalian
- 📷 Upload foto wajib pada pengambilan dan pengembalian sebagai bukti
- 💰 Perhitungan denda keterlambatan otomatis (Rp 10.000/hari)
- 📊 Dashboard ringkasan & visualisasi data (chart)
- 📄 Export laporan ke **PDF** dan **CSV**
- 🌙 Tema gelap / terang (dark / light mode)
- 🔔 Notifikasi status penyewaan

---

## Struktur Proyek

```
mygts/
├── main.py               # Entry point aplikasi
├── requirements.txt      # Dependensi Python
├── .env                  # Konfigurasi Supabase (tidak di-commit)
├── .env.example          # Template konfigurasi
├── ui/                   # View layer — semua halaman PySide6
│   ├── main_window.py    # Window utama + QStackedWidget
│   └── pages/            # Setiap halaman di file terpisah
├── controllers/          # Business logic
│   ├── auth_controller.py
│   ├── inventory_controller.py
│   └── rental_controller.py
├── models/               # Data access layer
│   ├── user.py
│   ├── inventory.py
│   └── rental.py
├── api/                  # Konfigurasi Supabase client
│   └── supabase_client.py
├── database/             # Schema SQL
│   └── schema.sql
├── utils/                # Helper functions
│   ├── export.py         # Export PDF & CSV
│   ├── photo_upload.py   # Upload foto ke Supabase Storage
│   └── validators.py     # Validasi input form
├── assets/
│   ├── qss/style.qss     # Global stylesheet
│   ├── icons/
│   └── images/
├── tests/                # Unit tests
└── exports/              # File hasil export (di-gitignore)
```

---

## Cara Menjalankan

### 1. Clone repository
```bash
git clone https://github.com/username/pv26-finalproject-mygts.git
cd pv26-finalproject-mygts
```

### 2. Install dependensi
```bash
pip install -r requirements.txt
```

### 3. Setup Supabase
- Buat project di [supabase.com](https://supabase.com)
- Jalankan `database/schema.sql` di Supabase SQL Editor
- Salin `.env.example` menjadi `.env` dan isi dengan URL + Key project Anda:
```bash
cp .env.example .env
```

### 4. Jalankan aplikasi
```bash
python main.py
```

### 5. Login default (owner)
- **Email:** owner@mygts.com
- **Password:** owner123

### Akun Customer
- **Adelia** → adelia@mygts.com / password: customer123
- **Aan** → aan@mygts.com / password: customer123
- **Rijal** → rijal@mygts.com / password: customer123

---

## Setup Database

Jalankan file `database/schema.sql` di **Supabase SQL Editor** untuk membuat tabel:
- `users` — data pengguna + role
- `inventories` — data inventaris per kategori
- `rentals` — data transaksi sewa

---

## Pembagian Tugas

| Anggota | Layer | File yang dikerjakan |
|---------|-------|----------------------|
| Nama 1 | View (UI) | `ui/`, `assets/qss/` |
| Nama 2 | Controller (Logic) | `controllers/`, `utils/export.py` |
| Nama 3 | Model (Database) | `models/`, `api/`, `database/` |

---

## Screenshot

> *(tambahkan screenshot di sini setelah UI selesai)*

---

## Teknologi

- **Python 3.11+**
- **PySide6** — GUI framework
- **Supabase** — Backend as a Service (PostgreSQL + Storage)
- **ReportLab** — Export PDF
- **Pandas** — Export CSV & manipulasi data
- **Matplotlib** — Visualisasi chart
