import redis

from quart import abort

GOOGLE_OAUTH_CLIENT_ID = 'google_oauth_client_id'  # string.

LEMONSQUEEZY_SIGNING_SECRET = 'lemonsqueezy_signing_secret'  # string.

# Default host and port.
rds = redis.from_url('redis://localhost:6379')


def get_key_from_rds(key: str) -> str:
    value = rds.get(key)
    if not value:
        abort(500, f'"{key}" not exists')

    value = value.decode().strip()
    if not value:
        abort(500, f'"{key}" is empty')

    return value
