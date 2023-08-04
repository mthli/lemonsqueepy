from datetime import datetime
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


# FIXME (Matthew Lee)
# https://lemonsqueezy.nolt.io/234
#
# The `data.id` is str instead of int in origin webhooks request,
# don't know why, but we should convert it to int.
def convert_data_id_to_int(data: dict):
    data['data']['id'] = int(data['data']['id'])


# Assume that `data` is created from `json.loads()`,
# convert all ISO-8601 formatted date-time string fields to datetime type,
# so we don't need to use MongoDB Aggregation Operations in those fields.
#
# Same as:
# https://pymongo.readthedocs.io/en/stable/examples/datetimes.html
def convert_fields_to_datetime_in_json(data: Any):
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


# https://stackoverflow.com/a/42777551
def convert_datetime_to_isoformat_with_z(dt: datetime) -> str:
    return dt.isoformat().replace('+00:00', 'Z')
