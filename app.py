import hashlib
import hmac

from quart import Quart, abort, json, request
from quart_cors import cors
from werkzeug.datastructures import Headers
from werkzeug.exceptions import HTTPException

from constants import APPLICATION_JSON
from logger import logger
from rds import rds, LEMONSQUEEZY_SIGNING_SECRET

app = Quart(__name__)
app = cors(app, allow_origin='*')


# https://flask.palletsprojects.com/en/2.2.x/errorhandling/#generic-exception-handler
#
# If no handler is registered,
# HTTPException subclasses show a generic message about their code,
# while other exceptions are converted to a generic "500 Internal Server Error".
@app.errorhandler(HTTPException)
def handle_exception(e: HTTPException):
    response = e.get_response()
    response.data = json.dumps({
        'code': e.code,
        'name': e.name,
        'description': e.description,
    })
    response.content_type = APPLICATION_JSON
    logger.error(f'errorhandler, data={response.data}')
    return response


# https://docs.lemonsqueezy.com/help/webhooks#event-types
@app.post('/api/webhooks')
async def webhooks():
    body: dict = await request.get_json() or {}
    logger.info(f'webhooks, body={json.dumps(body)}')  # always record.

    data = await request.get_data()  # raw body.
    _check_signing_secret(request.headers, data)

    # TODO (Matthew Lee) dispatch events...


# https://docs.lemonsqueezy.com/help/webhooks#signing-requests
def _check_signing_secret(headers: Headers, body: bytes):
    secret = rds.get(LEMONSQUEEZY_SIGNING_SECRET).decode()
    if not secret:
        abort(500, f'"{LEMONSQUEEZY_SIGNING_SECRET}" not exists')

    signature = headers.get(key='X-Signature', default='', type=str)
    if not signature:
        abort(400, f'"X-Signature" not exists')

    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, signature):
        abort(400, f'invalid signature, signature={signature}')
