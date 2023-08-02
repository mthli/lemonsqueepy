import json
import time

import jwt
import validators

from base64 import b64encode
from dataclasses import asdict
from uuid import uuid4

from Crypto.Cipher import AES
from jwt import PyJWKClient
from quart import abort
from validators import ValidationFailure

from mongo.customers import Customer, Token, TokenInfo, find_customer_by_email, upsert_customer
from rds import get_key_from_rds, GOOGLE_OAUTH_CLIENT_ID, LEMONSQUEEZY_SIGNING_SECRET

# FIXME (Matthew Lee) not support asyncio for now.
_jwk_client = PyJWKClient(
    uri='https://www.googleapis.com/oauth2/v3/certs',
    cache_jwk_set=True,
    lifespan=86400,  # seconds of 1 day.
    timeout=10,  # seconds.
)


# Looks like we don't need to decode the customer token for now.
def generate_customer_token(id: str, secret: str = '') -> str:
    secret = secret.strip()
    if not secret:
        secret = get_key_from_rds(LEMONSQUEEZY_SIGNING_SECRET)
    if len(secret) != 16:
        abort(500, f'"{LEMONSQUEEZY_SIGNING_SECRET}" must be 16 characters length string')  # nopep8.

    info = TokenInfo(id=id, create_timestamp=int(time.time()))
    info = json.dumps(asdict(info)).encode()

    cipher = AES.new(secret, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(info)
    nonce = cipher.nonce

    token = Token(ciphertext=ciphertext, tag=tag, nonce=nonce)
    token = json.dumps(asdict(token)).encode()
    return b64encode(token)


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
        id = str(uuid4())
        customer = Customer(
            id=id,
            email=email,
            token=generate_customer_token(id),
            name=name,
            avatar=avatar,
        )
    else:
        customer.token = generate_customer_token(customer.id)  # renew.
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
