from dataclasses import dataclass, asdict
from typing import Optional

from mongo.db import users


@dataclass(kw_only=True)
class User:
    id: str = ''      # required; uuid, as primary key.
    token: str = ''   # required; should be unique too.
    email: str = ''   # optional; have to exist after oauth.
    name: str = ''    # optional; maybe exist even if oauth.
    avatar: str = ''  # optional; maybe exist even if oauth.
    create_timestamp: int = 0  # required.
    update_timestamp: int = 0  # required.


@dataclass(kw_only=True)
class Token:
    ciphertext: str = ''  # required.
    tag: str = ''         # required.
    nonce: str = ''       # required.


@dataclass(kw_only=True)
class TokenInfo:
    user_id: str = ''            # required.
    generate_timestamp: int = 0  # required; in seconds.


# MongoDB does not recreate the index if it already exists.
# https://www.mongodb.com/community/forums/t/behavior-of-createindex-for-an-existing-index/2248/2
async def setup_users():
    await users.create_index('id', unique=True, background=True)     # str.
    await users.create_index('token', unique=True, background=True)  # str.
    await users.create_index('email', background=True)               # str.
    await users.create_index('create_timestamp', background=True)    # int.
    await users.create_index('update_timestamp', background=True)    # int.


async def find_user_by_email(email: str) -> Optional[User]:
    return await _find_user_by_('email', email)


async def find_user_by_token(token: str) -> Optional[User]:
    return await _find_user_by_('token', token)


async def _find_user_by_(key: str, value: str) -> Optional[User]:
    res: dict = await users.find_one({key: value})
    if not res:
        return None

    return User(
        id=res['id'],
        email=res['email'],
        token=res['token'],
        name=res['name'],
        avatar=res['avatar'],
        create_timestamp=res['create_timestamp'],
        update_timestamp=res['update_timestamp'],
    )


async def upsert_user(user: User):
    await users.update_one(
        {'id': user.id},
        {'$set': asdict(user)},
        upsert=True,
    )
