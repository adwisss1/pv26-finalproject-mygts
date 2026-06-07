# """
# Controller: Auth
# Bertanggung jawab atas login, logout, registrasi, dan manajemen sesi.
# """
# import hashlib
# from models import user as UserModel

# _current_user: dict | None = None


# def hash_password(password: str) -> str:
#     return hashlib.sha256(password.encode()).hexdigest()


# def login(email: str, password: str) -> dict | None:
#     """Login user. Return user dict jika berhasil, None jika gagal."""
#     global _current_user
#     try:
#         data = UserModel.get_by_email(email)
#         if data and data["password_hash"] == hash_password(password):
#             _current_user = data
#             return data
#         return None
#     except Exception:
#         return None


# def logout():
#     global _current_user
#     _current_user = None


# def register(name: str, email: str, password: str, phone: str = "") -> bool:
#     try:
#         UserModel.create(name, email, hash_password(password), "customer", phone)
#         return True
#     except Exception:
#         return False


# def get_current_user() -> dict | None:
#     return _current_user


# def is_owner() -> bool:
#     return _current_user is not None and _current_user.get("role") == "owner"


"""
Controller: Auth
Bertanggung jawab atas login, logout, registrasi, dan manajemen sesi.
"""
import hashlib
from models import user as UserModel

_current_user: dict | None = None


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def login(email: str, password: str) -> dict | None:
    """Login user. Return user dict jika berhasil, None jika gagal."""
    global _current_user
    try:
        print(f"--- DEBUGGING LOGIN ---")
        print(f"Mencoba mencari email: {email}")
        
        data = UserModel.get_by_email(email)
        print(f"Data dari Supabase: {data}")
        
        hash_input = hash_password(password)
        print(f"Hash dari input: {hash_input}")
        
        if data:
            print(f"Hash di DB: {data.get('password_hash')}")
            if data["password_hash"] == hash_input:
                _current_user = data
                print("LOGIN SUKSES!")
                return data
            else:
                print("Gagal: Hash Password tidak cocok!")
        else:
            print("Gagal: Data email tidak ditemukan di database!")
            
        return None
        
    except Exception as e:
        # Menampilkan error sistem ke terminal
        print(f"ERROR SISTEM/DATABASE: {e}") 
        return None


def logout():
    global _current_user
    _current_user = None


def register(name: str, email: str, password: str, phone: str = "") -> bool:
    try:
        UserModel.create(name, email, hash_password(password), "customer", phone)
        return True
    except Exception:
        return False


def get_current_user() -> dict | None:
    return _current_user


def is_owner() -> bool:
    return _current_user is not None and _current_user.get("role") == "owner"