from mongo.db import subscriptions


# https://docs.lemonsqueezy.com/api/subscriptions#the-subscription-object
# https://docs.lemonsqueezy.com/api/subscription-invoices#the-subscription-invoice-object
async def insert_subscription(subscription: dict):
    res = await subscriptions.insert_one(subscription)
    return res.inserted_id
