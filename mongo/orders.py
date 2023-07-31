from mongo.db import orders


# https://motor.readthedocs.io/en/stable/tutorial-asyncio.html#inserting-a-document
async def insert_order(document: dict) -> str:
    res = await orders.insert_one(document)
    return res.inserted_id
