from typing import Any

from dateutil import parser
from motor.motor_asyncio import AsyncIOMotorClient

# Default host and port.
_client = AsyncIOMotorClient('localhost', 27017)
_db = _client['lemonsqueezy']  # database.

users = _db['users']  # collection.
orders = _db['orders']  # collection.
licenses = _db['licenses']  # collection.
subscriptions = _db['subscriptions']  # collection.
subscription_payments = _db['subscription_payments']  # collection.


# Assume that `data` is created from `json.loads()`,
# convert all ISO-8601 formatted date-time string fields to datetime type,
# so we don't need to use MongoDB Aggregation Operations in those fields.
#
# Same as:
# https://pymongo.readthedocs.io/en/stable/examples/datetimes.html
def convert_fields_to_datetime_in_json(data: Any | None):
    if isinstance(data, list):
        for item in data:
            convert_fields_to_datetime_in_json(item)
    elif isinstance(data, dict):
        for key, value in data.items():
            if not isinstance(value, str):
                convert_fields_to_datetime_in_json(value)
                continue
            try:
                data[key] = parser.isoparse(value)
            except Exception:
                pass  # DO NOTHING.
