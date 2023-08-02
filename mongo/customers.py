from dataclasses import dataclass, asdict
from typing import Optional

from mongo.db import customers


@dataclass
class Customer:
    id: str = ''      # required; uuid, as primary key.
    email: str = ''   # required; should be unique too.
    token: str = ''   # required; should be unique too.
    name: str = ''    # optional.
    avatar: str = ''  # optional.


@dataclass
class Token:
    ciphertext: str = ''  # required.
    tag: str = ''         # required.
    nonce: str = ''       # required.


@dataclass
class TokenInfo:
    id: str = ''        # required; the customer id.
    email: str = ''     # required; the customer email.
    timestamp: int = 0  # required; the generate time in seconds.


# MongoDB does not recreate the index if it already exists.
# https://www.mongodb.com/community/forums/t/behavior-of-createindex-for-an-existing-index/2248/2
async def setup_customers():
    await customers.create_index('id', unique=True, background=True)
    await customers.create_index('email', unique=True, background=True)
    await customers.create_index('token', unique=True, background=True)


async def find_customer_by_email(email: str) -> Optional[Customer]:
    return await _find_customer_by_('email', email)


async def find_customer_by_token(token: str) -> Optional[Customer]:
    return await _find_customer_by_('token', token)


async def _find_customer_by_(key: str, value: str) -> Optional[Customer]:
    res: dict = await customers.find_one({key: value})
    if not res:
        return None

    return Customer(
        id=res['id'],
        email=res['email'],
        token=res['token'],
        name=res['name'],
        avatar=res['avatar'],
    )


async def upsert_customer(customer: Customer):
    await customers.update_one(
        {'id': customer.id},
        {'$set': asdict(customer)},
        upsert=True,
    )
