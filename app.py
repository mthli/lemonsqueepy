import json

from dataclasses import asdict
from uuid import uuid4

from quart import Quart, abort, request
from quart_cors import cors
from werkzeug.exceptions import HTTPException

from lemon import check_signing_secret, parse_event, dispatch_event
from logger import logger
from mongo.users import User, setup_users, upsert_user
from oauth import encrypt_user_token, \
    parse_user_token_from_request, \
    upsert_user_from_google_oauth

app = Quart(__name__)
app = cors(app, allow_origin='*')


# https://pgjones.gitlab.io/quart/how_to_guides/startup_shutdown.html
@app.before_serving
async def before_serving():
    await setup_users()


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


# Register anonymous user.
#
# After register,
# all requests' headers should contain `"Authorization": "Bearer USER_TOKEN"`,
# and the `USER_TOKEN` value comes from `user.token`.
@app.post('/api/user/register')
async def register():
    user_id = str(uuid4())
    token = encrypt_user_token(user_id)
    user = User(id=user_id, token=token)
    await upsert_user(user)
    return asdict(user)


# {
#   'credential': required; str.
# }
@app.post('/api/user/oauth/google')
async def google_oauth():
    body: dict = await request.get_json() or {}

    credential = body.get('credential', '')
    if not isinstance(credential, str):
        abort(400, '"credential" must be string')
    credential = credential.strip()
    if not credential:
        abort(400, '"credential" must not empty')

    user_token = await parse_user_token_from_request()
    user = await upsert_user_from_google_oauth(
        credential=credential,
        user_token=user_token,
    )

    return asdict(user)


# https://docs.lemonsqueezy.com/help/webhooks#webhook-requests
@app.post('/api/webhooks/lemonsqueezy')
async def lemonsqueezy_webhooks():
    # Always record webhooks body for debugging.
    body: dict = await request.get_json() or {}
    logger.info(f'/api/webhooks/lemonsqueezy, body={json.dumps(body)}')

    data = await request.get_data()  # raw body.
    check_signing_secret(request.headers, data)

    event = parse_event(request.headers)
    await dispatch_event(event, body)

    return {}  # 200.
