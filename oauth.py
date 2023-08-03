import json
import time

import jwt
import validators

from base64 import b64encode, b64decode
from dataclasses import asdict
from typing import Optional
from uuid import uuid4

from Crypto.Cipher import AES
from jwt import PyJWKClient
from quart import abort, request
from validators import ValidationFailure

from mongo.users import User, Token, TokenInfo, \
    find_user_by_email, \
    find_user_by_token, \
    upsert_user
from rds import rds, get_str_from_rds, \
    GOOGLE_OAUTH_CLIENT_IDS, \
    LEMONSQUEEZY_SIGNING_SECRET

# FIXME (Matthew Lee) not support asyncio for now.
_google_jwk_client = PyJWKClient(
    uri='https://www.googleapis.com/oauth2/v3/certs',
    cache_jwk_set=True,
    lifespan=86400,  # seconds of 1 day.
    timeout=10,  # seconds.
)


# https://onboardbase.com/blog/aes-encryption-decryption/
def generate_user_token(user_id: str, timestamp: int, secret: str = '') -> str:
    secret = secret.strip()
    if not secret:
        secret = get_str_from_rds(LEMONSQUEEZY_SIGNING_SECRET)
    if len(secret) != 16:
        abort(500, f'"{LEMONSQUEEZY_SIGNING_SECRET}" must be 16 characters length string')  # nopep8.

    info = TokenInfo(user_id=user_id, generate_timestamp=timestamp)
    info = json.dumps(asdict(info)).encode()

    cipher = AES.new(secret, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(info)
    nonce = cipher.nonce

    token = Token(ciphertext=ciphertext, tag=tag, nonce=nonce)
    token = json.dumps(asdict(token)).encode()
    return b64encode(token).decode()


# https://onboardbase.com/blog/aes-encryption-decryption/
def decrypt_user_token(token: str, secret: str = '') -> Optional[TokenInfo]:
    secret = secret.strip()
    if not secret:
        secret = get_str_from_rds(LEMONSQUEEZY_SIGNING_SECRET)
    if len(secret) != 16:
        abort(500, f'"{LEMONSQUEEZY_SIGNING_SECRET}" must be 16 characters length string')  # nopep8.

    token: Token = Token(**json.loads(b64decode(token)))
    cipher = AES.new(secret, AES.MODE_EAX, token.nonce)
    info = cipher.decrypt_and_verify(token.ciphertext, token.tag)
    return TokenInfo(**json.loads(info))


async def parse_user_token_from_request(required: bool = True) -> str:
    auth = request.authorization
    if not auth:
        if required:
            abort(400, '"Authorization" not exists')
        return ''

    if auth.type != 'Bearer':
        if required:
            abort(400, f'"Authorization" type must be "Bearer", type={auth.type}')  # nopep8.
        return ''

    token = (auth.token if auth.token else '').strip()
    if not token:
        if required:
            abort(400, '"Authorization" token must not empty')
        return ''

    if required:
        user = await find_user_by_token(token)
        if not user:
            abort(403, f'invalid "Authorization", token={token}')

    return token


async def upsert_user_from_google_oauth(credential: str, user_token: str = '') -> User:
    payload: dict = {}

    client_ids = rds.smembers(GOOGLE_OAUTH_CLIENT_IDS)
    for cid in client_ids:
        try:
            payload = _decode_google_oauth_credential(credential, cid.decode())
        except Exception:
            pass  # DO NOTHING.
    if not payload:
        abort(403, f'invalid credential "aud", credential={credential}')

    email = payload.get('email', '').strip()
    if not email:
        abort(403, '"email" not exists')
    if isinstance(validators.email(email), ValidationFailure):
        abort(403, f'invalid "email", email={email}')

    name = payload.get('name', '').strip()
    avatar = payload.get('picture', '').strip()
    timestamp = int(time.time())

    user: User | None = None
    if user_token:  # first priority.
        user = find_user_by_token(user_token)
    if not user:  # second priority.
        user = find_user_by_email(email)

    if not user:  # is new user.
        user_id = str(uuid4())
        user = User(
            id=user_id,
            token=generate_user_token(user_id, timestamp),
            email=email,
            name=name,
            avatar=avatar,
            create_timestamp=timestamp,
            update_timestamp=timestamp,
        )
    else:
        # FIXME (Matthew Lee) should renew user token here?
        # user.token = generate_user_token(user.id, timestamp)
        user.email = email
        user.name = name
        user.avatar = avatar
        user.update_timestamp = timestamp

    await upsert_user(user)
    return user


# https://developers.google.com/identity/gsi/web/guides/verify-google-id-token
# https://pyjwt.readthedocs.io/en/stable/usage.html#retrieve-rsa-signing-keys-from-a-jwks-endpoint
def _decode_google_oauth_credential(credential: str, client_id: str) -> dict:
    signing_key = _google_jwk_client.get_signing_key_from_jwt(credential)
    return jwt.decode(
        jwt=credential,
        key=signing_key.key,
        algorithms=['RS256'],
        audience=client_id,
        issuer='https://accounts.google.com',
    )
