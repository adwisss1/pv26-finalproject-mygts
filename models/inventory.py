"""
Model: Inventory
Tabel: inventories
Kolom: id, name, category, description, stock, price_per_day, condition, image_url, created_at
"""
from api.supabase_client import get_client

TABLE = "inventories"

def get_all():
    return get_client().table(TABLE).select("*").execute().data

def get_by_id(item_id: str):
    return get_client().table(TABLE).select("*").eq("id", item_id).single().execute().data

def get_by_category(category: str):
    return get_client().table(TABLE).select("*").eq("category", category).execute().data

def search(keyword: str):
    return get_client().table(TABLE).select("*").ilike("name", f"%{keyword}%").execute().data

def create(data: dict):
    return get_client().table(TABLE).insert(data).execute().data

def update(item_id: str, data: dict):
    return get_client().table(TABLE).update(data).eq("id", item_id).execute().data

def delete(item_id: str):
    return get_client().table(TABLE).delete().eq("id", item_id).execute().data
