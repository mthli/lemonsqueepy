from mongo.db import licenses


# https://docs.lemonsqueezy.com/api/license-keys#the-license-key-object
async def insert_license(license: dict):
    await licenses.insert_one(license)
