from mongo.db import orders


# https://docs.lemonsqueezy.com/api/orders#the-order-object
async def insert_order(order: dict):
    await orders.insert_one(order)
