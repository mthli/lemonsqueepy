import json
import time

from dataclasses import asdict
from uuid import uuid4

from quart import Quart, abort, request
from quart_cors import cors
from werkzeug.exceptions import HTTPException

from lemon import check_signing_secret, parse_event, dispatch_event
from logger import logger
from mongo.db import convert_id_to_str_in_json, \
    convert_fields_to_datetime_in_json
from mongo.licenses import setup_licenses, \
    find_latest_license, \
    find_license_receipt, \
    convert_license_to_response
from mongo.orders import setup_orders, \
    find_latest_order, \
    convert_order_to_response
from mongo.subscriptions import setup_subscriptions, \
    setup_subscription_payments, \
    find_latest_subscription, \
    find_subscription_invoice_url, \
    convert_subscription_to_response
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
        user_token=_parse_str_from_dict(body, 'user_token', required=False),
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
    convert_id_to_str_in_json(body)
    convert_fields_to_datetime_in_json(body)
    await dispatch_event(event, body)

    return {}  # 200.


# ?user_token=str  required.
# &store_id=str    required.
# &product_id=str  required.
# &variant_id=str  optional; default is '1'.
# &test_mode=bool  optional; default is `false`.
#
# TODO (Matthew Lee) add redis cache.
@app.get('/api/orders/latest')
async def check_latest_order():
    user_token = _parse_str_from_dict(request.args, 'user_token')
    store_id = _parse_str_from_dict(request.args, 'store_id')
    product_id = _parse_str_from_dict(request.args, 'product_id')
    variant_id = _parse_str_from_dict(request.args, 'variant_id', default='1', required=False)  # nopep8.
    test_mode = request.args.get('test_mode', False, bool)

    res = await find_latest_order(
        user_id=decrypt_user_token(user_token).user_id,
        store_id=store_id,
        product_id=product_id,
        variant_id=variant_id,
        test_mode=test_mode,
    )

    if not res:
        abort(404, 'order not found')

    return convert_order_to_response(res)


# ?user_token=str  required.
# &store_id=str    required.
# &product_id=str  required.
# &variant_id=str  optional; default is '1'.
# &test_mode=bool  optional; default is `false`.
#
# TODO (Matthew Lee) add redis cache.
@app.get('/api/subscriptions/latest')
async def check_latest_subscription():
    user_token = _parse_str_from_dict(request.args, 'user_token')
    store_id = _parse_str_from_dict(request.args, 'store_id')
    product_id = _parse_str_from_dict(request.args, 'product_id')
    variant_id = _parse_str_from_dict(request.args, 'variant_id', default='1', required=False)  # nopep8.
    test_mode = request.args.get('test_mode', False, bool)

    res = await find_latest_subscription(
        user_id=decrypt_user_token(user_token).user_id,
        store_id=store_id,
        product_id=product_id,
        variant_id=variant_id,
        test_mode=test_mode,
    )

    if not res:
        abort(404, 'subscription not found')

    invoice_url = await find_subscription_invoice_url(res)
    if not invoice_url:
        abort(500, 'invoice not found')

    return convert_subscription_to_response(res, invoice_url)


# ?user_token=str  required.
# &store_id=str    required.
# &product_id=str  required.
# &key=str         required.
# &test_mode=bool  optional; default is `false`.
#
# TODO (Matthew Lee) add redis cache.
@app.get('/api/licenses/latest')
async def check_latest_license():
    user_token = _parse_str_from_dict(request.args, 'user_token')
    store_id = _parse_str_from_dict(request.args, 'store_id')
    product_id = _parse_str_from_dict(request.args, 'product_id')
    key = _parse_str_from_dict(request.args, 'key')
    test_mode = request.args.get('test_mode', False, bool)

    res = await find_latest_license(
        user_id=decrypt_user_token(user_token).user_id,
        store_id=store_id,
        product_id=product_id,
        key=key,
        test_mode=test_mode,
    )

    if not res:
        abort(404, 'license not found')

    receipt = await find_license_receipt(res)
    if not receipt:
        abort(500, 'receipt not found')

    return convert_license_to_response(res, receipt)


def _parse_str_from_dict(
    data: dict,
    key: str,
    default: str = '',
    required: bool = True,
) -> str:
    value = data.get(key, default)
    if not isinstance(value, str):
        if required:
            abort(400, f'"{key}" must be string')

    value = value.strip()
    if not value:
        if required:
            abort(400, f'"{key}" must not empty')

    return value
