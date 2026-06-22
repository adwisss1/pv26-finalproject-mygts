#!/usr/bin/env python
"""Quick test script untuk rental page"""

try:
    print("[1] Testing rental_page import...")
    from ui.pages.customer.rental_page import RentalPage
    print("    ✓ RentalPage imported OK")
except Exception as e:
    print(f"    ✗ Error importing RentalPage: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

try:
    print("[2] Testing history_page import...")
    from ui.pages.customer.history_page import HistoryPage
    print("    ✓ HistoryPage imported OK")
except Exception as e:
    print(f"    ✗ Error importing HistoryPage: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n✓ All imports successful!")
