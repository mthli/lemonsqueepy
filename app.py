import secrets
import uuid

from quart import Quart, abort, json, request, session
from quart_auth import QuartAuth
from quart_cors import cors
from quart_session import Session
from werkzeug.exceptions import HTTPException

from constants import APPLICATION_JSON
from lemon import check_signing_secret, parse_event, dispatch_event
from oauth.google import build_google_oauth_url, \
    exchange_code_for_access_token_and_id_token
from logger import logger

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


# ?redirect_uri=str
@app.get('/api/google/oauth')
async def get_google_oauth_url():
    redirect_uri = request.args.get('redirect_uri', '').strip()
    if not redirect_uri:
        abort(400, '"redirect_uri" not exists')

    state = str(uuid.uuid4())
    session['state'] = state
    url = build_google_oauth_url(redirect_uri, state)

    return {
        'url': url,
    }


# ?code=str&redirect_uri=str&state=str
@app.post('/api/google/oauth')
async def on_google_oauth_success():
    state = request.args.get('state', '').strip()
    if not state:
        abort(400, '"state" not exists')
    if state != session['state']:
        abort(403, f'invalid state, state={state}')

    code = request.args.get('code', '').strip()
    if not code:
        abort(400, '"code" not exists')

    redirect_uri = request.args.get('redirect_uri', '').strip()
    if not redirect_uri:
        abort(400, '"redirect_uri" not exists')

    # TODO (Matthew Lee) ...
    await exchange_code_for_access_token_and_id_token(code, redirect_uri)
