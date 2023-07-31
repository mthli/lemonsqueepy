from pymongo import MongoClient

_client = MongoClient('mongodb://localhost:27017')  # default host and port.
_db = _client['lemonsqueezy']  # database.

orders = _db['orders']  # collection.
licenses = _db['licenses']  # collection.
subscriptions = _db['subscriptions']  # collection.
