"""
Model: Rental
Tabel: rentals
Kolom: id, user_id, inventory_id, start_date, end_date, return_date,
       status (pending/confirmed/returned), pickup_photo_url, return_photo_url,
       fine_amount, notes, created_at
"""
from api.supabase_client import get_client

TABLE = "rentals"

def get_all():
    return get_client().table(TABLE).select("*, users(*), inventories(*)").execute().data

def get_by_user(user_id: str):
    return get_client().table(TABLE).select("*, inventories(*)").eq("user_id", user_id).execute().data

def get_by_inventory(inventory_id: str):
    return get_client().table(TABLE).select("*, users(*)").eq("inventory_id", inventory_id).execute().data

def get_by_status(status: str):
    return get_client().table(TABLE).select("*, users(*), inventories(*)").eq("status", status).execute().data

def create(data: dict):
    return get_client().table(TABLE).insert(data).execute().data

def update(rental_id: str, data: dict):
    return get_client().table(TABLE).update(data).eq("id", rental_id).execute().data

def delete(rental_id: str):
    return get_client().table(TABLE).delete().eq("id", rental_id).execute().data
