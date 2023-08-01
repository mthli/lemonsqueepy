from dataclasses import dataclass, asdict

from mongo.db import customers


@dataclass
class Customer:
    id: str = ''      # required; as primary key.
    email: str = ''   # required.
    name: str = ''    # optional.
    avatar: str = ''  # optional.


# MongoDB does not recreate the index if it already exists.
# https://www.mongodb.com/community/forums/t/behavior-of-createindex-for-an-existing-index/2248/2
async def setup_customers():
    await customers.create_index('id', unique=True, background=True)
    await customers.create_index('email', background=True)


async def upsert_customer(customer: Customer):
    await customers.update_one(
        {'id': customer.id},
        {'$set': asdict(customer)},
        upsert=True,
    )
