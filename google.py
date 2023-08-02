import uuid

import jwt
import validators

from jwt import PyJWKClient
from quart import abort
from validators import ValidationFailure

from mongo.customers import Customer, find_customer_by_email, upsert_customer
from rds import get_key_from_rds, GOOGLE_OAUTH_CLIENT_ID

# FIXME (Matthew Lee) not support asyncio for now.
_jwk_client = PyJWKClient(
    uri='https://www.googleapis.com/oauth2/v3/certs',
    cache_jwk_set=True,
    lifespan=86400,  # seconds of 1 day.
    timeout=10,  # seconds.
)


async def upsert_customer_from_google_oauth(credential: str) -> Customer:
    payload = _decode_google_oauth_credential(credential)

    email = payload.get('email', '').strip()
    if not email:
        abort(400, '"email" not exists')
    if isinstance(validators.email(email), ValidationFailure):
        abort(400, f'invalid "email", email={email}')

    name = payload.get('name', '').strip()
    avatar = payload.get('picture', '').strip()

    customer = await find_customer_by_email(email)
    if not customer:
        customer = Customer(
            id=str(uuid.uuid4()),
            email=email,
            name=name,
            avatar=avatar,
        )
    else:
        customer.name = name
        customer.avatar = avatar

    await upsert_customer(customer)
    return customer


# https://developers.google.com/identity/gsi/web/guides/verify-google-id-token
# https://pyjwt.readthedocs.io/en/stable/usage.html#retrieve-rsa-signing-keys-from-a-jwks-endpoint
def _decode_google_oauth_credential(credential: str) -> dict:
    signing_key = _jwk_client.get_signing_key_from_jwt(credential)
    return jwt.decode(
        jwt=credential,
        key=signing_key.key,
        algorithms=['RS256'],
        audience=get_key_from_rds(GOOGLE_OAUTH_CLIENT_ID),
        issuer='https://accounts.google.com',
    )
