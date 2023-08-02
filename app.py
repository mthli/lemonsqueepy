from dataclasses import asdict
from uuid import uuid4

from quart import Quart, abort, json, request
from quart_cors import cors
from werkzeug.exceptions import HTTPException

from lemon import check_signing_secret, parse_event, dispatch_event
from logger import logger
from mongo.customers import Customer, setup_customers, upsert_customer
from oauth import generate_customer_token, upsert_customer_from_google_oauth

app = Quart(__name__)
app = cors(app, allow_origin='*')


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


# Register anonymous customer.
@app.post('/api/customer/register')
async def register():
    id = str(uuid4())
    token = generate_customer_token(id)
    customer = Customer(id=id, token=token)
    await upsert_customer(customer)
    return asdict(customer)


# {
#   'credential': required; str.
# }
@app.post('/api/customer/oauth/google')
async def google_oauth():
    body: dict = await request.get_json() or {}

    credential = body.get('credential', '')
    if not isinstance(credential, str):
        abort(400, '"credential" must be string')
    credential = credential.strip()
    if not credential:
        abort(400, '"credential" must not empty')

    customer = await upsert_customer_from_google_oauth(credential)
    return asdict(customer)


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
