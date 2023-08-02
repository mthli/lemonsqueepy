import jwt

from jwt import PyJWKClient

from rds import get_key_from_rds, GOOGLE_OAUTH_CLIENT_ID

# FIXME (Matthew Lee) not support asyncio for now.
_jwk_client = PyJWKClient(
    uri='https://www.googleapis.com/oauth2/v3/certs',
    cache_jwk_set=True,
    lifespan=86400,  # seconds of 1 day.
    timeout=10,  # seconds.
)


# https://pyjwt.readthedocs.io/en/stable/usage.html#retrieve-rsa-signing-keys-from-a-jwks-endpoint
def decode_google_oauth_credential(credential: str) -> dict:
    signing_key = _jwk_client.get_signing_key_from_jwt(credential)
    return jwt.decode(
        jwt=credential,
        key=signing_key.key,
        algorithms=['RS256'],
        audience=get_key_from_rds(GOOGLE_OAUTH_CLIENT_ID),
        issuer='https://accounts.google.com',
    )
