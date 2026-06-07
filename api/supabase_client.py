"""
Supabase client singleton — digunakan oleh semua model.
Fallback ke mock client jika .env tidak dikonfigurasi (mode demo).
"""

import os
from dotenv import load_dotenv

load_dotenv()

_client = None
_mock_client = None
_DEMO_MODE = False


def is_demo_mode() -> bool:
    return _DEMO_MODE


def get_client():
    global _client, _mock_client, _DEMO_MODE

    if _client is not None:
        return _client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if url and key:
        from supabase import create_client, Client
        _client = create_client(url, key)
        return _client

    if _mock_client is None:
        from api.mock_client import MockClient
        _mock_client = MockClient()
        _DEMO_MODE = True
        print("[DEMO MODE] Menggunakan data lokal (mock). Untuk mode live,"
              " set SUPABASE_URL dan SUPABASE_KEY di .env")

    return _mock_client
