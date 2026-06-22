"""
Supabase client — otomatis pilih real atau mock
berdasarkan ada tidaknya file .env
Implementasi connection pooling untuk performa lebih baik
"""
import os
import threading
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

_client = None
_client_lock = threading.Lock()  # Thread-safe client creation

def get_client():
    """
    Get or create Supabase client (singleton pattern dengan thread safety)
    """
    global _client
    
    # Double-checked locking pattern untuk thread safety
    if _client is not None:
        return _client
    
    with _client_lock:
        if _client is not None:
            return _client
        
        if SUPABASE_URL and SUPABASE_KEY and "supabase.co" in SUPABASE_URL:
            try:
                from supabase import create_client
                _client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print(f"[DB] ✅ Terhubung ke Supabase: {SUPABASE_URL}")
            except Exception as e:
                print(f"[DB] ⚠️  Gagal konek Supabase: {e} — beralih ke mock")
                from api.mock_client import MockClient
                _client = MockClient()
        else:
            print("[DB] ℹ️  .env tidak ditemukan — menggunakan mock data")
            from api.mock_client import MockClient
            _client = MockClient()
    
    return _client