"""
Setup Database MyGTS
Jalankan dari folder project: python database/setup_db.py
Pastikan sudah isi .env dulu!
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("❌ SUPABASE_URL atau SUPABASE_KEY belum diisi di .env!")
    sys.exit(1)

sb = create_client(url, key)

print("🔗 Koneksi ke Supabase:", url)
print()

import hashlib
def h(p): return hashlib.sha256(p.encode()).hexdigest()

# ── Insert Users ──────────────────────────────────────────────
print("📥 Memasukkan data users...")
users = [
    {
        "id":            "00000000-0000-0000-0000-000000000001",
        "name":          "Admin Sanggar",
        "email":         "owner@mygts.com",
        "password_hash": h("owner123"),
        "role":          "owner",
        "phone":         "081111111111",
    },
    {
        "id":            "00000000-0000-0000-0000-000000000002",
        "name":          "Budi Santoso",
        "email":         "customer@mygts.com",
        "password_hash": h("customer123"),
        "role":          "customer",
        "phone":         "081234567890",
    },
    {
        "id":            "00000000-0000-0000-0000-000000000003",
        "name":          "Siti Rahayu",
        "email":         "customer2@mygts.com",
        "password_hash": h("customer123"),
        "role":          "customer",
        "phone":         "081298765432",
    },
]
for u in users:
    try:
        sb.table("users").insert(u).execute()
        print(f"  ✅ User: {u['email']}")
    except Exception as e:
        print(f"  ⚠️  {u['email']}: {e}")

# ── Insert Inventaris ─────────────────────────────────────────
print("\n📥 Memasukkan data inventaris...")
items = [
    {"id":"10000000-0000-0000-0000-000000000001","name":"Kostum Tari Merak",   "category":"Kostum",    "description":"Kostum tari merak warna hijau-emas, ukuran M", "stock":5,  "price_per_day":75000,  "condition":"Baik",        "image_url":""},
    {"id":"10000000-0000-0000-0000-000000000002","name":"Kostum Tari Kecak",   "category":"Kostum",    "description":"Kostum tari kecak motif kotak-kotak, ukuran L","stock":8,  "price_per_day":50000,  "condition":"Baik",        "image_url":""},
    {"id":"10000000-0000-0000-0000-000000000003","name":"Mahkota Pengantin",   "category":"Aksesoris", "description":"Mahkota pengantin emas dengan ornamen bunga",  "stock":3,  "price_per_day":100000, "condition":"Baik",        "image_url":""},
    {"id":"10000000-0000-0000-0000-000000000004","name":"Anting Tradisional",  "category":"Aksesoris", "description":"Anting tradisional perak kombinasi emas",      "stock":10, "price_per_day":25000,  "condition":"Baik",        "image_url":""},
    {"id":"10000000-0000-0000-0000-000000000005","name":"Tombak dan Tameng",   "category":"Properti",  "description":"Set tombak dan tameng kayu ukiran",            "stock":6,  "price_per_day":35000,  "condition":"Baik",        "image_url":""},
    {"id":"10000000-0000-0000-0000-000000000006","name":"Kipas Tari",          "category":"Properti",  "description":"Kipas tari sutra warna-warni",                 "stock":12, "price_per_day":15000,  "condition":"Baik",        "image_url":""},
    {"id":"10000000-0000-0000-0000-000000000007","name":"Gamelan Jawa",        "category":"Alat Musik","description":"Seperangkat gamelan jawa laras slendro",       "stock":1,  "price_per_day":500000, "condition":"Baik",        "image_url":""},
    {"id":"10000000-0000-0000-0000-000000000008","name":"Kendang Sunda",       "category":"Alat Musik","description":"Kendang sunda ukuran sedang",                  "stock":4,  "price_per_day":80000,  "condition":"Rusak Ringan","image_url":""},
    {"id":"10000000-0000-0000-0000-000000000009","name":"Foundation Set",      "category":"Make Up",   "description":"Set foundation profesional 12 warna",          "stock":2,  "price_per_day":60000,  "condition":"Baik",        "image_url":""},
    {"id":"10000000-0000-0000-0000-000000000010","name":"Kuas Make Up Set",    "category":"Make Up",   "description":"Set kuas make up 20 pcs profesional",          "stock":7,  "price_per_day":30000,  "condition":"Baik",        "image_url":""},
    {"id":"10000000-0000-0000-0000-000000000011","name":"Topeng Bali",         "category":"Properti",  "description":"Topeng bali kayu ukir tangan",                 "stock":9,  "price_per_day":20000,  "condition":"Baik",        "image_url":""},
    {"id":"10000000-0000-0000-0000-000000000012","name":"Sandal Properti",     "category":"Lainnya",   "description":"Sandal ukuran 43-45 untuk properti pertunjukan","stock":15, "price_per_day":5000,   "condition":"Baik",        "image_url":""},
]
for item in items:
    try:
        sb.table("inventories").insert(item).execute()
        print(f"  ✅ Item: {item['name']}")
    except Exception as e:
        print(f"  ⚠️  {item['name']}: {e}")

print("\n🎉 Setup selesai! Coba jalankan aplikasi: python main.py")