from motor.motor_asyncio import AsyncIOMotorClient

# Default host and port.
_client = AsyncIOMotorClient('localhost', 27017)
_db = _client['lemonsqueezy']  # database.

customers = _db['customers']  # collection.
licenses = _db['licenses']  # collection.
orders = _db['orders']  # collection.
subscriptions = _db['subscriptions']  # collection.
