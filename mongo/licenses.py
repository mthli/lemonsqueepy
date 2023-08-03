from enum import unique
from typing import Optional

from strenum import StrEnum

from mongo.db import licenses


@unique
class Status(StrEnum):
    INACTIVE = 'inactive'
    ACTIVE = 'active'
    EXPIRED = 'expired'
    DISABLED = 'disabled'


async def setup_licenses():
    await licenses.create_index('meta.event_name', background=True)                # nopep8; str.
    await licenses.create_index('meta.custom_data.user_id', background=True)       # nopep8; str.
    await licenses.create_index('data.attributes.store_id', background=True)       # nopep8; int.
    await licenses.create_index('data.attributes.customer_id', background=True)    # nopep8; int.
    await licenses.create_index('data.attributes.order_id', background=True)       # nopep8; int.
    await licenses.create_index('data.attributes.order_item_id', background=True)  # nopep8; int.
    await licenses.create_index('data.attributes.product_id', background=True)     # nopep8; int.
    await licenses.create_index('data.attributes.user_email', background=True)     # nopep8; str.
    await licenses.create_index('data.attributes.key', background=True)            # nopep8; str.
    await licenses.create_index('data.attributes.key_short', background=True)      # nopep8; str.
    await licenses.create_index('data.attributes.status', background=True)         # nopep8; str.
    await licenses.create_index('data.attributes.created_at', background=True)     # nopep8; datetime.
    await licenses.create_index('data.attributes.updated_at', background=True)     # nopep8; datetime.


# https://docs.lemonsqueezy.com/api/license-keys#the-license-key-object
# https://docs.lemonsqueezy.com/help/webhooks#example-payloads
#
# You will notice that the `data` in the payload is the order object,
# plus some `meta` and the usual `relationships` and `links`.
async def insert_license(license: dict):
    await licenses.insert_one(license)


async def find_latest_license(
    user_id: str,
    store_id: int,
    product_id: int,
    key: str,
    test_mode: bool = False,
) -> Optional[dict]:
    cursor = licenses \
        .find({
            'meta.custom_data.user_id': user_id,
            'data.attributes.store_id': store_id,
            'data.attributes.product_id': product_id,
            'data.attributes.key': key,
            'data.attributes.test_mode': test_mode,
        }) \
        .sort('data.attributes.updated_at', -1) \
        .limit(1)

    res: list[dict] = []
    async for order in cursor:
        res.append(order)

    return res[0] if res else None


async def has_available_license(
    user_id: str,
    store_id: int,
    product_id: int,
    key: str,
    test_mode: bool = False,
) -> bool:
    latest = await find_latest_license(
        user_id=user_id,
        store_id=store_id,
        product_id=product_id,
        key=key,
        test_mode=test_mode,
    )

    # Check whether the latest license status is "active".
    return latest['status'] == str(Status.ACTIVE) if latest else False
