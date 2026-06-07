"""
Controller: Rental
Alur penyewaan: buat sewa, konfirmasi, upload foto, hitung denda, pengembalian.
"""
from datetime import date, datetime
from models import rental as RentalModel

FINE_PER_DAY = 10000  # Rp 10.000 per hari keterlambatan


def calculate_fine(end_date: str, return_date: str) -> int:
    """Hitung denda keterlambatan dalam rupiah."""
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    ret = datetime.strptime(return_date, "%Y-%m-%d").date()
    late_days = (ret - end).days
    return max(0, late_days * FINE_PER_DAY)


def create_rental(user_id: str, inventory_id: str, start_date: str, end_date: str, notes: str = "") -> dict | None:
    try:
        return RentalModel.create({
            "user_id": user_id,
            "inventory_id": inventory_id,
            "start_date": start_date,
            "end_date": end_date,
            "status": "pending",
            "notes": notes,
        })
    except Exception as e:
        print(f"[rental_controller] create_rental error: {e}")
        return None


def confirm_rental(rental_id: str) -> bool:
    try:
        RentalModel.update(rental_id, {"status": "confirmed"})
        return True
    except Exception:
        return False


def reject_rental(rental_id: str) -> bool:
    try:
        RentalModel.update(rental_id, {"status": "rejected"})
        return True
    except Exception:
        return False


def set_pickup_photo(rental_id: str, photo_url: str) -> bool:
    try:
        RentalModel.update(rental_id, {"pickup_photo_url": photo_url, "status": "active"})
        return True
    except Exception:
        return False


def process_return(rental_id: str, return_date: str, photo_url: str, end_date: str) -> dict:
    fine = calculate_fine(end_date, return_date)
    try:
        RentalModel.update(rental_id, {
            "return_date": return_date,
            "return_photo_url": photo_url,
            "fine_amount": fine,
            "status": "returned",
        })
        return {"success": True, "fine": fine}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_rentals_for_owner():
    return RentalModel.get_all()


def get_rentals_for_customer(user_id: str):
    return RentalModel.get_by_user(user_id)

def get_rentals_by_inventory(inventory_id: str):
    return RentalModel.get_by_inventory(inventory_id)
