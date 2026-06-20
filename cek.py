import sys, os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
print("URL:", url)
print("KEY:", key[:20] if key else "KOSONG")

sb = create_client(url, key)
result = sb.table('users').select('email, password_hash').execute()
print("Data di DB:", result.data)