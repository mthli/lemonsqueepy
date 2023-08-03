from enum import unique

from strenum import StrEnum

from mongo.db import subscriptions
from mongo.db import subscription_payments


@unique
class Status(StrEnum):
    ON_TRIAL = 'on_trial'
    ACTIVE = 'active'
    PAUSED = 'paused'
    PAST_DUE = 'past_due'
    UNPAID = 'unpaid'
    CANCELLED = 'cancelled'
    EXPIRED = 'expired'


@unique
class BillingReason(StrEnum):
    INITIAL = 'initial'
    RENEWAL = 'renewal'
    UPDATED = 'updated'


# FIXME (Matthew Lee) where is the `subscription_id` or something like that?
async def setup_subscriptions():
    await subscriptions.create_index('meta.event_name', background=True)              # nopep8; str.
    await subscriptions.create_index('meta.custom_data.user_id', background=True)     # nopep8; str.
    await subscriptions.create_index('data.attributes.store_id', background=True)     # nopep8; int.
    await subscriptions.create_index('data.attributes.customer_id', background=True)  # nopep8; int.
    await subscriptions.create_index('data.attributes.order_id', background=True)     # nopep8; int.
    await subscriptions.create_index('data.attributes.product_id', background=True)   # nopep8; int.
    await subscriptions.create_index('data.attributes.variant_id', background=True)   # nopep8; int.
    await subscriptions.create_index('data.attributes.user_email', background=True)   # nopep8; str.
    await subscriptions.create_index('data.attributes.status', background=True)       # nopep8; str.
    await subscriptions.create_index('data.attributes.created_at', background=True)   # nopep8; datetime.
    await subscriptions.create_index('data.attributes.updated_at', background=True)   # nopep8; datetime.


async def setup_subscription_payments():
    await subscription_payments.create_index('meta.event_name', background=True)                  # nopep8; str.
    await subscription_payments.create_index('meta.custom_data.user_id', background=True)         # nopep8; str.
    await subscription_payments.create_index('data.attributes.store_id', background=True)         # nopep8; int.
    await subscription_payments.create_index('data.attributes.subscription_id', background=True)  # nopep8; int.
    await subscription_payments.create_index('data.attributes.billing_reason', background=True)   # nopep8; str.
    await subscription_payments.create_index('data.attributes.status', background=True)           # nopep8; str.
    await subscription_payments.create_index('data.attributes.created_at', background=True)       # nopep8; datetime.
    await subscription_payments.create_index('data.attributes.updated_at', background=True)       # nopep8; datetime.


# https://docs.lemonsqueezy.com/api/subscriptions#the-subscription-object
# https://docs.lemonsqueezy.com/help/webhooks#example-payloads
#
# You will notice that the `data` in the payload is the subscription object,
# plus some `meta` and the usual `relationships` and `links`.
async def insert_subscription(subscription: dict):
    await subscriptions.insert_one(subscription)


# https://docs.lemonsqueezy.com/api/subscription-invoices#the-subscription-invoice-object
# https://docs.lemonsqueezy.com/help/webhooks#example-payloads
#
# You will notice that the `data` in the payload is the subscription invoice object,
# plus some `meta` and the usual `relationships` and `links`.
async def insert_subscription_payment(payment: dict):
    await subscription_payments.insert_one(payment)
