from mongo.db import licenses


# https://motor.readthedocs.io/en/stable/tutorial-asyncio.html#inserting-a-document
async def insert_license(document: dict) -> str:
    res = await licenses.insert_one(document)
    return res.inserted_id
