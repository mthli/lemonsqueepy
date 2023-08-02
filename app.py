import secrets

from quart import Quart, abort, json, request
from quart_auth import QuartAuth
from quart_cors import cors
from quart_session import Session
from werkzeug.exceptions import HTTPException

from lemon import check_signing_secret, parse_event, dispatch_event
from logger import logger
from mongo.customers import setup_customers
from oauth import decode_google_oauth_credential

app = Quart(__name__)
app = cors(app, allow_origin='*')

# Default host and port.
# https://github.com/kroketio/quart-session
app.config['SESSION_TYPE'] = 'redis'
Session(app)

# https://github.com/pgjones/quart-auth
app.config['QUART_AUTH_MODE'] = 'bearer'
app.secret_key = secrets.token_urlsafe(16)
auth_manager = QuartAuth(app)


# https://pgjones.gitlab.io/quart/how_to_guides/startup_shutdown.html
@app.before_serving
async def before_serving():
    await setup_customers()


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
    response.content_type = 'application/json'
    logger.error(f'errorhandler, data={response.data}')
    return response


# https://docs.lemonsqueezy.com/help/webhooks#webhook-requests
@app.post('/api/lemonsqueezy/webhooks')
async def lemonsqueezy_webhooks():
    # Always record webhooks body for debugging.
    body: dict = await request.get_json() or {}
    logger.info(f'/api/lemonsqueezy/webhooks, body={json.dumps(body)}')

    data = await request.get_data()  # raw body.
    check_signing_secret(request.headers, data)

    event = parse_event(request.headers)
    await dispatch_event(event, body)

    return {}  # 200.


# {
#   'credential': '...',
# }
@app.post('/api/google/oauth')
async def on_google_oauth_success():
    body: dict = await request.get_json() or {}

    credential = body.get('credential', '')
    if not isinstance(credential, str):
        abort(400, '"credential" must be string')
    credential = credential.strip()
    if not credential:
        abort(400, '"credential" must not empty')

    decoded = decode_google_oauth_credential(credential)
    # TODO (Matthew Lee) ...
