"""
Controller: Inventory
Logika pencarian, filter, pengadaan inventaris baru.
"""
from models import inventory as InventoryModel

CATEGORIES = ["Kostum", "Aksesoris", "Properti", "Alat Musik", "Make Up", "Lainnya"]


def get_all_inventory():
    return InventoryModel.get_all()

def get_inventory_by_id(item_id: str):
    return InventoryModel.get_by_id(item_id)


def get_by_category(category: str):
    return InventoryModel.get_by_category(category)


def search_inventory(keyword: str):
    return InventoryModel.search(keyword)


def add_inventory(name: str, category: str, description: str, stock: int,
                  price_per_day: int, condition: str = "Baik", image_url: str = "") -> bool:
    try:
        InventoryModel.create({
            "name": name, "category": category, "description": description,
            "stock": stock, "price_per_day": price_per_day,
            "condition": condition, "image_url": image_url,
        })
        return True
    except Exception:
        return False


def update_inventory(item_id: str, data: dict) -> bool:
    try:
        InventoryModel.update(item_id, data)
        return True
    except Exception:
        return False


def delete_inventory(item_id: str) -> bool:
    try:
        InventoryModel.delete(item_id)
        return True
    except Exception:
        return False
