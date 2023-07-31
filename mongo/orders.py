from mongo.db import orders


# https://docs.lemonsqueezy.com/api/orders#the-order-object
async def insert_order(order: dict) -> str:
    res = await orders.insert_one(order)
    return res.inserted_id
