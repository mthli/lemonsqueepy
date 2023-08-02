from dataclasses import dataclass, asdict
from typing import Optional

from mongo.db import customers


@dataclass
class Customer:
    id: str = ''      # required; uuid, as primary key.
    email: str = ''   # required; should be unique too.
    name: str = ''    # optional.
    avatar: str = ''  # optional.


# MongoDB does not recreate the index if it already exists.
# https://www.mongodb.com/community/forums/t/behavior-of-createindex-for-an-existing-index/2248/2
async def setup_customers():
    await customers.create_index('id', unique=True, background=True)
    await customers.create_index('email', unique=True, background=True)


async def find_customer_by_email(email: str) -> Optional[Customer]:
    res: dict = await customers.find_one({'email': email})
    if not res:
        return None

    return Customer(
        id=res['id'],
        email=res['email'],
        name=res['name'],
        avatar=res['avatar'],
    )


async def upsert_customer(customer: Customer):
    await customers.update_one(
        {'id': customer.id},
        {'$set': asdict(customer)},
        upsert=True,
    )
