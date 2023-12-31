from enum import unique
from typing import Optional

from async_lru import alru_cache
from strenum import StrEnum

from mongo.db import licenses, convert_datetime_to_isoformat_with_z


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


# Based on the upper API specs, the `license_key` is unique in all stores.
# https://docs.lemonsqueezy.com/api/license-keys#retrieve-a-license-key
@alru_cache(ttl=10)
async def find_latest_license(
    license_key: str,
    test_mode: bool = False,
) -> Optional[dict]:
    cursor = licenses \
        .find({
            'data.attributes.key': license_key,
            'data.attributes.test_mode': test_mode,
        }) \
        .sort('data.attributes.updated_at', -1) \
        .limit(1)

    res: list[dict] = []
    async for order in cursor:
        res.append(order)

    return res[0] if res else None


def convert_license_to_response(license: dict) -> dict:
    status = license['data']['attributes']['status']
    activation_limit = license['data']['attributes']['activation_limit']
    instances_count = license['data']['attributes']['instances_count']

    created_at = license['data']['attributes']['created_at']
    created_at = convert_datetime_to_isoformat_with_z(created_at)

    updated_at = license['data']['attributes']['updated_at']
    updated_at = convert_datetime_to_isoformat_with_z(updated_at)

    return {
        'available': status == str(Status.ACTIVE),
        'status': status,
        'activation_limit': activation_limit,
        'instances_count': instances_count,
        'created_at': created_at,
        'updated_at': updated_at,
    }
