"""Mock Supabase client — mimics real API without network connection."""

import re
import uuid
from datetime import datetime
from api.mock_data import USERS, INVENTORIES, RENTALS as _SEED_RENTALS

# ── Runtime stores (data hidup di sini selama app jalan) ──────────────────
_USERS       = [dict(u) for u in USERS]
_INVENTORIES = [dict(i) for i in INVENTORIES]
_RENTALS     = [dict(r) for r in _SEED_RENTALS]


def _reset():
    """Reset ke data awal (untuk testing)."""
    global _USERS, _INVENTORIES, _RENTALS
    _USERS       = [dict(u) for u in USERS]
    _INVENTORIES = [dict(i) for i in INVENTORIES]
    _RENTALS     = [dict(r) for r in _SEED_RENTALS]


def _get_store(name):
    return {"users": _USERS, "inventories": _INVENTORIES, "rentals": _RENTALS}.get(name, [])


# ── Enrich rental dengan relasi users & inventories ───────────────────────
def _enrich_rental(r: dict) -> dict:
    r = dict(r)
    uid = r.get("user_id")
    iid = r.get("inventory_id")
    users_map = {u["id"]: u for u in _USERS}
    inv_map   = {i["id"]: i for i in _INVENTORIES}
    if uid in users_map:
        r["users"] = dict(users_map[uid])
    if iid in inv_map:
        r["inventories"] = dict(inv_map[iid])
    return r


# ─────────────────────────────────────────────────────────────────────────────

class MockResult:
    def __init__(self, data):
        self.data = data


class MockQuery:
    def __init__(self, data, table_name=""):
        self._data      = list(data)
        self._table     = table_name
        self._enrich    = (table_name == "rentals")

    def _maybe_enrich(self, rows):
        if self._enrich:
            return [_enrich_rental(r) for r in rows]
        return rows

    def execute(self):
        return MockResult(self._maybe_enrich(self._data))

    def eq(self, field, value):
        filtered = [d for d in self._data if d.get(field) == value]
        q = MockQuery(filtered, self._table)
        return q

    def neq(self, field, value):
        filtered = [d for d in self._data if d.get(field) != value]
        return MockQuery(filtered, self._table)

    def ilike(self, field, pattern):
        regex    = pattern.replace("%", ".*")
        filtered = [
            d for d in self._data
            if re.search(regex, str(d.get(field, "")), re.IGNORECASE)
        ]
        return MockQuery(filtered, self._table)

    def order(self, field, **kw):
        reverse = kw.get("desc", False)
        sorted_ = sorted(self._data, key=lambda d: str(d.get(field, "")), reverse=reverse)
        return MockQuery(sorted_, self._table)

    def limit(self, n):
        return MockQuery(self._data[:n], self._table)

    def single(self):
        return MockSingleQuery(self._data[:1], self._table)

    def select(self, *_):
        return self


class MockSingleQuery(MockQuery):
    def execute(self):
        if not self._data:
            return MockResult(None)
        rows = self._maybe_enrich(self._data)
        return MockResult(rows[0])


class MockTable:
    def __init__(self, name: str):
        self._name = name

    @property
    def _store(self):
        return _get_store(self._name)

    def select(self, *_):
        return MockQuery(list(self._store), self._name)

    def insert(self, payload: dict):
        new = dict(payload)
        new.setdefault("id",         uuid.uuid4().hex[:12])
        new.setdefault("created_at", datetime.now().isoformat())
        self._store.append(new)
        print(f"[MockDB] INSERT {self._name}: {new.get('id')}")
        return MockResult([new])

    def update(self, payload: dict):
        return MockUpdateQuery(self._store, payload, self._name)

    def delete(self):
        return MockDeleteQuery(self._store, self._name)


class MockUpdateQuery:
    def __init__(self, store: list, payload: dict, table_name: str):
        self._store   = store    # referensi langsung ke list global
        self._payload = payload
        self._table   = table_name

    def eq(self, field, value):
        updated = []
        for d in self._store:
            if d.get(field) == value:
                d.update(self._payload)   # ubah dict in-place di list global
                updated.append(d)
                print(f"[MockDB] UPDATE {self._table} id={value} → {self._payload}")
        return MockResult(updated)


class MockDeleteQuery:
    def __init__(self, store: list, table_name: str):
        self._store = store
        self._table = table_name

    def eq(self, field, value):
        before = len(self._store)
        removed = [d for d in self._store if d.get(field) == value]
        self._store[:] = [d for d in self._store if d.get(field) != value]
        print(f"[MockDB] DELETE {self._table} {field}={value} — removed {before - len(self._store)} rows")
        return MockResult(removed)


class MockBucket:
    def upload(self, path, file_obj, options=None):
        print(f"[MockStorage] upload → {path}")

    def get_public_url(self, path):
        return f"https://mock.storage/rental-photos/{path}"


class MockStorage:
    def from_(self, bucket):
        return MockBucket()


class MockClient:
    def __init__(self):
        self._storage_mock = MockStorage()

    def table(self, name: str) -> MockTable:
        return MockTable(name)

    @property
    def storage(self):
        return self._storage_mock