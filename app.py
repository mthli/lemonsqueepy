import json
import time

from distutils.util import strtobool
from dataclasses import asdict
from uuid import uuid4

from quart import Quart, abort, request
from quart_cors import cors
from werkzeug.exceptions import HTTPException

from lemon import check_signing_secret, \
    parse_event, \
    dispatch_event, \
    activate_license as activate_license_internal
from logger import logger
from mongo.db import convert_id_to_str_in_json, \
    convert_fields_to_datetime_in_json
from mongo.licenses import setup_licenses, \
    find_latest_license, \
    convert_license_to_response
from mongo.orders import setup_orders, \
    find_latest_order, \
    convert_order_to_response
from mongo.subscriptions import setup_subscriptions, \
    setup_subscription_payments, \
    find_latest_subscription, \
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
        'name': e.name,  # as JavaScript Error `name`.
        'message': e.description,  # as JavaScript Error `message`.
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
#   'verify_exp': optional; boolean.
# }
@app.post('/api/user/oauth/google')
async def google_oauth():
    body: dict = await request.get_json() or {}

    user = await upsert_user_from_google_oauth(
        credential=_parse_str_from_dict(body, 'credential'),
        user_token=_parse_str_from_dict(body, 'user_token', required=False),
        verify_exp=bool(body.get('verify_exp', False)),
    )

    return asdict(user)


# https://docs.lemonsqueezy.com/help/webhooks#webhook-requests
#
# FIXME (Matthew Lee)
# Currently we strongly depends webhooks usability,
# but when it not available,
# we need to fallback to manual request Lemon Squeezy APIs.
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
# &variant_id=str  required.
# &test_mode=bool  optional; default is `false`.
@app.get('/api/orders/check')
async def check_order():
    user_token = _parse_str_from_dict(request.args, 'user_token')
    store_id = _parse_str_from_dict(request.args, 'store_id')
    product_id = _parse_str_from_dict(request.args, 'product_id')
    variant_id = _parse_str_from_dict(request.args, 'variant_id')
    test_mode = bool(strtobool(request.args.get('test_mode', 'false')))

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
# &variant_id=str  required.
# &test_mode=bool  optional; default is `false`.
@app.get('/api/subscriptions/check')
async def check_subscription():
    user_token = _parse_str_from_dict(request.args, 'user_token')
    store_id = _parse_str_from_dict(request.args, 'store_id')
    product_id = _parse_str_from_dict(request.args, 'product_id')
    variant_id = _parse_str_from_dict(request.args, 'variant_id')
    test_mode = bool(strtobool(request.args.get('test_mode', 'false')))

    res = await find_latest_subscription(
        user_id=decrypt_user_token(user_token).user_id,
        store_id=store_id,
        product_id=product_id,
        variant_id=variant_id,
        test_mode=test_mode,
    )

    if not res:
        abort(404, 'subscription not found')

    return convert_subscription_to_response(res)


# ?user_token=str   required.
# &license_key=str  required.
# &test_mode=bool   optional; default is `false`.
@app.get('/api/licenses/check')
async def check_license():
    user_token = _parse_str_from_dict(request.args, 'user_token')
    license_key = _parse_str_from_dict(request.args, 'license_key')
    test_mode = bool(strtobool(request.args.get('test_mode', 'false')))

    res = await find_latest_license(
        user_id=decrypt_user_token(user_token).user_id,
        license_key=license_key,
        test_mode=test_mode,
    )

    if not res:
        abort(404, 'license not found')

    return convert_license_to_response(res)


# {
#   'user_token':    required; str.
#   'license_key':   required; str.
#   'instance_name': optional; str.
#   'test_mode':     optional; bool, default is `false`.
# }
@app.post('/api/licenses/activate')
async def activate_license():
    # Always record api body for debugging.
    body: dict = await request.get_json() or {}
    logger.info(f'/api/licenses/activate, body={json.dumps(body)}')

    user_token = _parse_str_from_dict(body, 'user_token')
    license_key = _parse_str_from_dict(body, 'license_key')
    test_mode = bool(body.get('test_mode', False))

    instance_name = _parse_str_from_dict(
        data=body,
        key='instance_name',
        default=str(int(time.time())),  # activate timestamp in seconds.
        required=False,
    )

    # Check the user ownership.
    res = await find_latest_license(
        user_id=decrypt_user_token(user_token).user_id,
        license_key=license_key,
        test_mode=test_mode,
    )

    if not res:
        abort(404, 'license not found')

    res = await activate_license_internal(license_key, instance_name)
    return convert_license_to_response(res)


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
