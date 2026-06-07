from api.supabase_client import get_client

print("=== TES KONEKSI DATABASE SUPABASE ===")
try:
    client = get_client()
    
    # Memaksa Python mengambil SEMUA data di tabel users
    response = client.table("users").select("*").execute()
    data_users = response.data
    
    print(f"Berhasil konek! Jumlah akun di database: {len(data_users)}")
    print("-" * 30)
    
    for user in data_users:
        print(f"Email di DB : '{user.get('email')}'")
        print(f"Role        : {user.get('role')}")
        print("-" * 30)
        
except Exception as e:
    print(f"JATUH/ERROR: {e}")