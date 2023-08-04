from enum import unique
from typing import Optional

from async_lru import alru_cache
from strenum import StrEnum

from mongo.db import licenses, orders, \
    convert_datetime_to_isoformat_with_z


@unique
class Status(StrEnum):
    INACTIVE = 'inactive'
    ACTIVE = 'active'
    EXPIRED = 'expired'
    DISABLED = 'disabled'


async def setup_licenses():
    await licenses.create_index('meta.event_name', background=True)                # nopep8; str.
    await licenses.create_index('meta.custom_data.user_id', background=True)       # nopep8; str.

    await licenses.create_index('data.id', background=True)                        # nopep8; str, as the `license_id`.
    await licenses.create_index('data.attributes.store_id', background=True)       # nopep8; str.
    await licenses.create_index('data.attributes.customer_id', background=True)    # nopep8; str.
    await licenses.create_index('data.attributes.order_id', background=True)       # nopep8; str.
    await licenses.create_index('data.attributes.order_item_id', background=True)  # nopep8; str.
    await licenses.create_index('data.attributes.product_id', background=True)     # nopep8; str.

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
    find_latest_license.cache_clear()


@alru_cache()
async def find_latest_license(
    user_id: str,
    store_id: str,
    product_id: str,
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


async def find_license_receipt(license: dict) -> str:
    store_id = license['data']['attributes']['store_id']
    order_id = license['data']['attributes']['order_id']

    order = await orders.find_one({
        'data.id': order_id,
        'data.attributes.store_id': store_id,
    })

    return order['data']['attributes']['urls']['receipt'] if order else ''


async def convert_license_to_response(license: dict) -> dict:
    status = license['data']['attributes']['status']
    receipt = await find_license_receipt(license)

    created_at = license['data']['attributes']['created_at']
    created_at = convert_datetime_to_isoformat_with_z(created_at)

    updated_at = license['data']['attributes']['updated_at']
    created_at = convert_datetime_to_isoformat_with_z(updated_at)

    return {
        'available': status == str(Status.ACTIVE),
        'status': status,
        'receipt': receipt,
        'created_at': created_at,
        'updated_at': updated_at,
    }
