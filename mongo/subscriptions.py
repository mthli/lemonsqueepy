from mongo.db import subscriptions


# https://motor.readthedocs.io/en/stable/tutorial-asyncio.html#inserting-a-document
async def insert_subscription(document: dict):
    res = await subscriptions.insert_one(document)
    return res.inserted_id
