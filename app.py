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
from mongo.licenses import setup_licenses, \
    check_latest_license as check_latest_license_internal
from mongo.orders import setup_orders, \
    check_latest_order as check_latest_order_internal
from mongo.subscriptions import setup_subscriptions, \
    setup_subscription_payments, \
    check_latest_subscription as check_latest_subscription_internal
from mongo.users import User, setup_users, upsert_user
from oauth import generate_user_token, \
    decrypt_user_token, \
    upsert_user_from_google_oauth

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
        credential=_parse_str_from_dict(body, 'credential'),
        user_token=_parse_str_from_dict(body, 'user_token', False),
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


# ?user_token=str  required.
# &store_id=int    required; must > 0.
# &product_id=int  required; must > 0.
# &variant_id=int  optional; must > 0, default is 1.
# &test_mode=bool  optional; default is false.
#
# TODO (Matthew Lee) add redis cache.
@app.get('/api/orders/latest/check')
async def check_latest_order():
    user_token = _parse_str_from_dict(request.args, 'user_token')
    test_mode = request.args.get('test_mode', False, bool)

    store_id = request.args.get('store_id', 0, int)
    if store_id <= 0:
        abort(400, '"store_id" must > 0')

    product_id = request.args.get('product_id', 0, int)
    if product_id <= 0:
        abort(400, '"product_id" must > 0')

    variant_id = request.args.get('variant_id', 1, int)
    if variant_id <= 0:
        abort(400, '"variant_id" must > 0')

    res = await check_latest_order_internal(
        user_id=decrypt_user_token(user_token).user_id,
        store_id=store_id,
        product_id=product_id,
        variant_id=variant_id,
        test_mode=test_mode,
    )

    return {
        'available': res,
    }


# ?user_token=str  required.
# &store_id=int    required; must > 0.
# &product_id=int  required; must > 0.
# &variant_id=int  optional; must > 0, default is 1.
# &test_mode=bool  optional; default is false.
#
# TODO (Matthew Lee) add redis cache.
@app.get('/api/subscriptions/latest/check')
async def check_latest_subscription():
    user_token = _parse_str_from_dict(request.args, 'user_token')
    test_mode = request.args.get('test_mode', False, bool)

    store_id = request.args.get('store_id', 0, int)
    if store_id <= 0:
        abort(400, '"store_id" must > 0')

    product_id = request.args.get('product_id', 0, int)
    if product_id <= 0:
        abort(400, '"product_id" must > 0')

    variant_id = request.args.get('variant_id', 1, int)
    if variant_id <= 0:
        abort(400, '"variant_id" must > 0')

    res = await check_latest_subscription_internal(
        user_id=decrypt_user_token(user_token).user_id,
        store_id=store_id,
        product_id=product_id,
        variant_id=variant_id,
        test_mode=test_mode,
    )

    return {
        'available': res,
    }


# ?user_token=str  required.
# &store_id=int    required; must > 0.
# &product_id=int  required; must > 0.
# &key=int         required.
# &test_mode=bool  optional; default is false.
#
# TODO (Matthew Lee) add redis cache.
@app.get('/api/licenses/latest/check')
async def check_latest_license():
    user_token = _parse_str_from_dict(request.args, 'user_token')
    key = _parse_str_from_dict(request.args, 'key')
    test_mode = request.args.get('test_mode', False, bool)

    store_id = request.args.get('store_id', 0, int)
    if store_id <= 0:
        abort(400, '"store_id" must > 0')

    product_id = request.args.get('product_id', 0, int)
    if product_id <= 0:
        abort(400, '"product_id" must > 0')

    res = await check_latest_license_internal(
        user_id=decrypt_user_token(user_token).user_id,
        store_id=store_id,
        product_id=product_id,
        key=key,
        test_mode=test_mode,
    )

    return {
        'available': res,
    }


def _parse_str_from_dict(data: dict, key: str, required: bool = True) -> str:
    value = data.get(key, '')
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
