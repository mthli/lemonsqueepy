from mongo.db import subscriptions
from mongo.db import subscription_payments


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
async def insert_subscription(subscription: dict):
    await subscriptions.insert_one(subscription)


# https://docs.lemonsqueezy.com/api/subscription-invoices#the-subscription-invoice-object
async def insert_subscription_payment(payment: dict):
    await subscription_payments.insert_one(payment)
