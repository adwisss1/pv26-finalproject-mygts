-- ============================================================
--  MyGTS — Seed Data Awal
--  Jalankan di Supabase SQL Editor SETELAH schema.sql
-- ============================================================

-- ── Users ────────────────────────────────────────────────────
INSERT INTO users (id, name, email, password_hash, role, phone) VALUES
(
    '00000000-0000-0000-0000-000000000001',
    'Admin Sanggar',
    'owner@mygts.com',
    '43a0d17178a9d26c9e0fe9a74b0b45e38d32f27aed887a008a54bf6e033bf7b9',
    'owner',
    '081111111111'
),
(
    '00000000-0000-0000-0000-000000000002',
    'Adelia',
    'adelia@mygts.com',
    'b041c0aeb35bb0fa4aa668ca5a920b590196fdaf9a00eb852c9b7f4d123cc6d6',
    'customer',
    '081234567890'
),
(
    '00000000-0000-0000-0000-000000000003',
    'Aan',
    'aan@mygts.com',
    'b041c0aeb35bb0fa4aa668ca5a920b590196fdaf9a00eb852c9b7f4d123cc6d6',
    'customer',
    '081298765432'
),
(
    '00000000-0000-0000-0000-000000000004',
    'Rijal',
    'rijal@mygts.com',
    'b041c0aeb35bb0fa4aa668ca5a920b590196fdaf9a00eb852c9b7f4d123cc6d6',
    'customer',
    '081345678901'
)
ON CONFLICT (email) DO NOTHING;

-- ── Inventaris ───────────────────────────────────────────────
INSERT INTO inventories (id, name, category, description, stock, price_per_day, condition, image_url) VALUES
('10000000-0000-0000-0000-000000000001', 'Kostum Tari Merak',        'Kostum',     'Kostum tari merak warna hijau-emas, ukuran M',       5,  75000,  'Baik',         ''),
('10000000-0000-0000-0000-000000000002', 'Kostum Tari Kecak',        'Kostum',     'Kostum tari kecak motif kotak-kotak, ukuran L',      8,  50000,  'Baik',         ''),
('10000000-0000-0000-0000-000000000003', 'Mahkota Pengantin',        'Aksesoris',  'Mahkota pengantin emas dengan ornamen bunga',         3,  100000, 'Baik',         ''),
('10000000-0000-0000-0000-000000000004', 'Anting Tradisional',       'Aksesoris',  'Anting tradisional perak kombinasi emas',             10, 25000,  'Baik',         ''),
('10000000-0000-0000-0000-000000000005', 'Tombak dan Tameng',        'Properti',   'Set tombak dan tameng kayu ukiran',                  6,  35000,  'Baik',         ''),
('10000000-0000-0000-0000-000000000006', 'Kipas Tari',               'Properti',   'Kipas tari sutra warna-warni',                       12, 15000,  'Baik',         ''),
('10000000-0000-0000-0000-000000000007', 'Gamelan Jawa',             'Alat Musik', 'Seperangkat gamelan jawa laras slendro',              1,  500000, 'Baik',         ''),
('10000000-0000-0000-0000-000000000008', 'Kendang Sunda',            'Alat Musik', 'Kendang sunda ukuran sedang',                        4,  80000,  'Rusak Ringan', ''),
('10000000-0000-0000-0000-000000000009', 'Foundation Set',           'Make Up',    'Set foundation profesional 12 warna',                2,  60000,  'Baik',         ''),
('10000000-0000-0000-0000-000000000010', 'Kuas Make Up Set',         'Make Up',    'Set kuas make up 20 pcs profesional',                7,  30000,  'Baik',         ''),
('10000000-0000-0000-0000-000000000011', 'Topeng Bali',              'Properti',   'Topeng bali kayu ukir tangan, berbagai karakter',    9,  20000,  'Baik',         ''),
('10000000-0000-0000-0000-000000000012', 'Sandal Properti',          'Lainnya',    'Sandal ukuran 43-45 untuk properti pertunjukan',     15, 5000,   'Baik',         '')
ON CONFLICT (id) DO NOTHING;

-- ── Rentals Contoh ───────────────────────────────────────────
INSERT INTO rentals (user_id, inventory_id, start_date, end_date, return_date, status, fine_amount, notes) VALUES
(
    '00000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '2025-03-01', '2025-03-05', '2025-03-05',
    'returned', 0, 'Untuk pentas hari Minggu'
),
(
    '00000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000003',
    '2025-04-01', '2025-04-03', '2025-04-05',
    'returned', 20000, 'Terlambat 2 hari'
),
(
    '00000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000009',
    CURRENT_DATE, CURRENT_DATE + INTERVAL '2 days', NULL,
    'pending', 0, 'Untuk acara kondangan'
)
ON CONFLICT DO NOTHING;