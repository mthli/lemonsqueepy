import redis

from quart import abort

# For checking whether the credential issuer is our own.
# https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid#get_your_google_api_client_id
#
# You may have multiple client ids, it's ok,
# just execute `SADD google_oauth_client_ids "..."` in redis-cli.
GOOGLE_OAUTH_CLIENT_IDS = 'google_oauth_client_ids'  # set.

# For checking whether the requests are sent from Lemon Squeezy.
# https://docs.lemonsqueezy.com/help/webhooks#signing-requests
#
# We also use this secret to generate user token with AES-128 algorithm,
# so please make sure that this secret is a **16 characters length** string,
# and do not contain any leading and trailing whitespace characters,
# for example "0123456789abcdef" (don't use it, just a example, haha).
LEMONSQUEEZY_SIGNING_SECRET = 'lemonsqueezy_signing_secret'  # string.

# Interact with the Lemon Squeezy backend.
# https://docs.lemonsqueezy.com/guides/developer-guide/getting-started#api-overview
LEMONSQUEEZY_API_KEY = 'lemonsqueezy_api_key'  # string.

# Default host and port.
rds = redis.from_url('redis://localhost:6379')


def get_str_from_rds(key: str) -> str:
    value = rds.get(key)
    if not value:
        abort(500, f'"{key}" not exists')

    value = value.decode().strip()
    if not value:
        abort(500, f'"{key}" is empty')

    return value
