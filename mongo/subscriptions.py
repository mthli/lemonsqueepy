from mongo.db import subscriptions
from mongo.db import subscription_payments


# https://docs.lemonsqueezy.com/api/subscriptions#the-subscription-object
async def insert_subscription(subscription: dict):
    await subscriptions.insert_one(subscription)


# https://docs.lemonsqueezy.com/api/subscription-invoices#the-subscription-invoice-object
async def insert_subscription_payment(payment: dict):
    await subscription_payments.insert_one(payment)
