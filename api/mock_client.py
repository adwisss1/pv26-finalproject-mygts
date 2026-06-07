"""Mock Supabase client — mimics real API without network connection."""

import re
from datetime import datetime

from api.mock_data import USERS, INVENTORIES, RENTALS as RAW_RENTALS


class MockResult:
    def __init__(self, data):
        self.data = data


class MockQuery:
    def __init__(self, data):
        self._data = list(data)

    def execute(self):
        return MockResult(self._data)

    def eq(self, field, value):
        return MockQuery(d for d in self._data if d.get(field) == value)

    def neq(self, field, value):
        return MockQuery(d for d in self._data if d.get(field) != value)

    def single(self):
        return MockSingleQuery(self._data[:1])

    def ilike(self, field, pattern):
        regex = pattern.replace("%", ".*")
        return MockQuery(
            d for d in self._data
            if re.search(regex, str(d.get(field, "")), re.IGNORECASE)
        )

    def order(self, field, **kw):
        reverse = kw.get("desc", False)
        return MockQuery(
            sorted(self._data, key=lambda d: str(d.get(field, "")), reverse=reverse)
        )

    def limit(self, n):
        return MockQuery(self._data[:n])


class MockSingleQuery(MockQuery):
    """Query that returns a single dict (not list) on execute().data."""

    def execute(self):
        if not self._data:
            return MockResult(None)
        return MockResult(self._data[0])


class MockTable:
    def __init__(self, data_factory):
        self._data_factory = data_factory

    @property
    def _data(self):
        return list(self._data_factory())

    def select(self, *_):
        return MockQuery(self._data)

    def insert(self, payload):
        new = dict(payload)
        new.setdefault("id", __import__("uuid").uuid4().hex[:12])
        new.setdefault("created_at", datetime.now().isoformat())
        return MockResult([new])

    def update(self, payload):
        return MockUpdateQuery(self._data, payload)

    def delete(self):
        return MockQuery([])


class MockUpdateQuery:
    def __init__(self, data, payload):
        self._data = data
        self._payload = payload

    def eq(self, field, value):
        for d in self._data:
            if d.get(field) == value:
                d.update(self._payload)
        return MockResult(self._data)


class MockBucket:
    def __init__(self):
        self._files = {}

    def upload(self, path, file_obj, options=None):
        self._files[path] = file_obj

    def get_public_url(self, path):
        return f"https://mock.supabase.co/storage/v1/rental-photos/{path}"


class MockStorage:
    def from_(self, bucket):
        return MockBucket()


def _build_rentals():
    users_map = {u["id"]: u for u in USERS}
    inv_map = {i["id"]: i for i in INVENTORIES}
    enriched = []
    for r in RAW_RENTALS:
        r = dict(r)
        uid = r.get("user_id")
        iid = r.get("inventory_id")
        if uid in users_map:
            r["users"] = dict(users_map[uid])
        if iid in inv_map:
            r["inventories"] = dict(inv_map[iid])
        enriched.append(r)
    return enriched


def _get_tables():
    return {
        "users": lambda: USERS,
        "inventories": lambda: INVENTORIES,
        "rentals": _build_rentals,
    }


class MockClient:
    def __init__(self):
        self._tables = _get_tables()
        self._storage_mock = MockStorage()

    def table(self, name):
        factory = self._tables.get(name)
        if factory is None:
            return MockTable(list)
        return MockTable(factory)

    @property
    def storage(self):
        return self._storage_mock
