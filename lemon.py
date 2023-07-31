import hashlib
import hmac

from quart import abort
from werkzeug.datastructures import Headers

from rds import rds, LEMONSQUEEZY_SIGNING_SECRET


# https://docs.lemonsqueezy.com/help/webhooks#signing-requests
def check_signing_secret(headers: Headers, body: bytes):
    secret = rds.get(LEMONSQUEEZY_SIGNING_SECRET).decode()
    if not secret:
        abort(500, f'"{LEMONSQUEEZY_SIGNING_SECRET}" not exists')

    signature = headers.get(key='X-Signature', default='', type=str)
    if not signature:
        abort(400, f'"X-Signature" not exists')

    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, signature):
        abort(400, f'invalid signature, signature={signature}')
