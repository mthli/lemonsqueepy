import json
import time

from dataclasses import asdict
from uuid import uuid4

from quart import Quart, abort, request
from quart_cors import cors
from werkzeug.exceptions import HTTPException

from lemon import check_signing_secret, parse_event, dispatch_event
from logger import logger
from mongo.db import convert_fields_to_datetime_in_json
from mongo.licenses import setup_licenses
from mongo.orders import setup_orders
from mongo.subscriptions import setup_subscriptions, setup_subscription_payments
from mongo.users import User, setup_users, upsert_user
from oauth import generate_user_token, upsert_user_from_google_oauth

app = Quart(__name__)
app = cors(app, allow_origin='*')


# https://pgjones.gitlab.io/quart/how_to_guides/startup_shutdown.html
@app.before_serving
async def before_serving():
    logger.info('setup collections before serving')
    await setup_users()
    await setup_orders()
    await setup_licenses()
    await setup_subscriptions()
    await setup_subscription_payments()


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
    timestamp = int(time.time())
    token = generate_user_token(user_id, timestamp)

    user = User(
        id=user_id,
        token=token,
        create_timestamp=timestamp,
        update_timestamp=timestamp,
    )

    await upsert_user(user)
    return asdict(user)


# {
#   'credential': required; str.
#   'user_token': optional; str.
# }
@app.post('/api/user/oauth/google')
async def google_oauth():
    body: dict = await request.get_json() or {}

    user = await upsert_user_from_google_oauth(
        credential=_parse_str_from_body(body, 'credential'),
        user_token=_parse_str_from_body(body, 'user_token', False),
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
    convert_fields_to_datetime_in_json(body)
    await dispatch_event(event, body)

    return {}  # 200.


def _parse_str_from_body(body: dict, key: str, required: bool = True) -> str:
    value = body.get(key, '')
    if not isinstance(value, str):
        if required:
            abort(400, f'"{key}" must be string')
        return ''

    value = value.strip()
    if not value:
        if required:
            abort(400, f'"{key}" must not empty')
        return ''

    return value
