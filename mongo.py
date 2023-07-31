from motor.motor_asyncio import AsyncIOMotorClient

# Default host and port.
_client = AsyncIOMotorClient('localhost', 27017)
_db = _client['lemonsqueezy']  # database.

orders = _db['orders']  # collection.
licenses = _db['licenses']  # collection.
subscriptions = _db['subscriptions']  # collection.
