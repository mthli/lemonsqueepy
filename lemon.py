import hashlib
import hmac

from enum import unique

from quart import abort
from strenum import StrEnum
from werkzeug.datastructures import Headers

from mongo.licenses import insert_license
from mongo.orders import insert_order
from mongo.subscriptions import insert_subscription, insert_subscription_payment
from rds import get_str_from_rds, LEMONSQUEEZY_SIGNING_SECRET


# https://docs.lemonsqueezy.com/help/webhooks#event-types
@unique
class Event(StrEnum):
    ORDER_CREATED = 'order_created'
    ORDER_REFUNDED = 'order_refunded'
    SUBSCRIPTION_CREATED = 'subscription_created'
    SUBSCRIPTION_UPDATED = 'subscription_updated'
    SUBSCRIPTION_CANCELLED = 'subscription_cancelled'
    SUBSCRIPTION_RESUMED = 'subscription_resumed'
    SUBSCRIPTION_EXPIRED = 'subscription_expired'
    SUBSCRIPTION_PAUSED = 'subscription_paused'
    SUBSCRIPTION_UNPAUSED = 'subscription_unpaused'
    SUBSCRIPTION_PAYMENT_SUCCESS = 'subscription_payment_success'
    SUBSCRIPTION_PAYMENT_FAILED = 'subscription_payment_failed'
    SUBSCRIPTION_PAYMENT_RECOVERED = 'subscription_payment_recovered'
    LICENSE_KEY_CREATED = 'license_key_created'
    LICENSE_KEY_UPDATED = 'license_key_updated'


# https://docs.lemonsqueezy.com/help/webhooks#signing-requests
def check_signing_secret(headers: Headers, body: bytes):
    signature = headers.get(key='X-Signature', default='', type=str)
    if not signature:
        abort(400, f'"X-Signature" not exists')

    secret = get_str_from_rds(LEMONSQUEEZY_SIGNING_SECRET)
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, signature):
        abort(400, f'invalid "X-Signature", signature={signature}')


# https://docs.lemonsqueezy.com/help/webhooks#webhook-requests
def parse_event(headers: Headers) -> Event:
    event = headers.get(key='X-Event-Name', default='', type=str)
    if not event:
        abort(400, '"X-Event-Name" not exists')

    try:
        return Event[event.upper()]
    except Exception:
        abort(400, f'invalid "X-Event-Name", event={event}')


# https://docs.lemonsqueezy.com/help/webhooks#webhook-requests
async def dispatch_event(event: Event, body: dict):
    if str(event).startswith('order_'):
        await insert_order(body)
    elif str(event).startswith('subscription_payment_'):
        await insert_subscription_payment(body)
    elif str(event).startswith('subscription_'):
        await insert_subscription(body)
    elif str(event).startswith('license_'):
        await insert_license(body)
    else:
        abort(400, f'unsupported event, event={str(event)}')
