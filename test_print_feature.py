#!/usr/bin/env python3
"""
Test script untuk fitur print nota penyewaan (Point #6)
"""
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.export import print_rental_receipt

# Sample rental data untuk testing
sample_rental = {
    "id": "rental_abc123xyz789",
    "status": "confirmed",
    "start_date": "2024-01-15",
    "end_date": "2024-01-20",
    "return_date": None,
    "fine_amount": 0,
    "notes": "Penyewaan untuk acara pentas seni tanggal 20 Januari",
    "users": {
        "id": "user_123",
        "name": "Adelia Dwi Savitri",
        "email": "adelia@mygts.com"
    },
    "inventories": {
        "id": "inv_456",
        "name": "Kostum Penari Bali Premium",
        "category": "Kostum",
        "price_per_day": 50000
    }
}

def test_print_nota():
    """Test fungsi print_rental_receipt"""
    print("[TEST] Membuat nota penyewaan...")
    try:
        # Panggil fungsi print
        path = print_rental_receipt(sample_rental)
        print(f"✅ SUCCESS: Nota berhasil dibuat di: {path}")
        
        # Verifikasi file exists
        if os.path.exists(path):
            file_size = os.path.getsize(path)
            print(f"✅ File exists: {file_size} bytes")
        else:
            print(f"❌ ERROR: File tidak ditemukan di {path}")
            return False
            
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_print_nota_with_fine():
    """Test print dengan denda"""
    print("\n[TEST] Membuat nota penyewaan dengan denda...")
    
    rental_with_fine = sample_rental.copy()
    rental_with_fine["status"] = "returned"
    rental_with_fine["return_date"] = "2024-01-25"
    rental_with_fine["fine_amount"] = 50000  # 5 hari keterlambatan
    
    try:
        path = print_rental_receipt(rental_with_fine)
        print(f"✅ SUCCESS: Nota dengan denda berhasil dibuat di: {path}")
        
        if os.path.exists(path):
            file_size = os.path.getsize(path)
            print(f"✅ File exists: {file_size} bytes")
        else:
            print(f"❌ ERROR: File tidak ditemukan di {path}")
            return False
            
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Test Fitur Cetak Nota Penyewaan (Point #6)")
    print("=" * 60)
    
    results = []
    results.append(("Test 1: Nota standar", test_print_nota()))
    results.append(("Test 2: Nota dengan denda", test_print_nota_with_fine()))
    
    print("\n" + "=" * 60)
    print("HASIL TEST:")
    print("=" * 60)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(success for _, success in results)
    
    print("=" * 60)
    if all_passed:
        print("✅ SEMUA TEST PASSED!")
    else:
        print("❌ BEBERAPA TEST FAILED!")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)
