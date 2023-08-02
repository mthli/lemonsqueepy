import redis

from quart import abort

# For checking whether the credential issuer is our own.
# https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid#get_your_google_api_client_id
GOOGLE_OAUTH_CLIENT_ID = 'google_oauth_client_id'  # string.

# For checking whether the requests are sent from lemonsqueezy.
# https://docs.lemonsqueezy.com/help/webhooks#signing-requests
#
# We also use this secret to generate user token with AES-128 algorithm,
# so please make sure that this secret is a **16 characters length** string,
# and do not contain any leading and trailing whitespace characters.
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
