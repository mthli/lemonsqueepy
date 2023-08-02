from motor.motor_asyncio import AsyncIOMotorClient

# Default host and port.
_client = AsyncIOMotorClient('localhost', 27017)
_db = _client['lemonsqueezy']  # database.

users = _db['users']  # collection.
licenses = _db['licenses']  # collection.
orders = _db['orders']  # collection.
subscriptions = _db['subscriptions']  # collection.
subscription_payments = _db['subscription_payments']  # collection.
