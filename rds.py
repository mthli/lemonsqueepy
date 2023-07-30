import redis

# https://github.com/aio-libs/aioredis-py
from redis import asyncio as aioredis

LEMONSQUEEZY_API_KEY = 'lemonsqueezy_api_key'  # string.

# Default host and port.
rds = redis.from_url('redis://localhost:6379')
ards = aioredis.from_url('redis://localhost:6379')
