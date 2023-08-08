from enum import unique
from typing import Optional

from async_lru import alru_cache
from strenum import StrEnum

from mongo.db import orders, convert_datetime_to_isoformat_with_z


@unique
class Status(StrEnum):
    PENDING = 'pending'
    PAID = 'paid'
    FAILED = 'failed'
    REFUNDED = 'refunded'


async def setup_orders():
    await orders.create_index('meta.event_name', background=True)              # nopep8; str.
    await orders.create_index('meta.custom_data.user_id', background=True)     # nopep8; str.

    await orders.create_index('data.id', background=True)                      # nopep8; str, as the `order_id`.
    await orders.create_index('data.attributes.store_id', background=True)     # nopep8; str.
    await orders.create_index('data.attributes.customer_id', background=True)  # nopep8; str.
    await orders.create_index('data.attributes.identifier', background=True)   # nopep8; str.

    await orders.create_index('data.attributes.user_email', background=True)   # nopep8; str.
    await orders.create_index('data.attributes.status', background=True)       # nopep8; str.

    await orders.create_index('data.attributes.first_order_item.id', background=True)          # nopep8; str, as the `order_item_id`.
    await orders.create_index('data.attributes.first_order_item.order_id', background=True)    # nopep8; str, as the `order_id`.
    await orders.create_index('data.attributes.first_order_item.product_id', background=True)  # nopep8; str, as the `product_id`.
    await orders.create_index('data.attributes.first_order_item.variant_id', background=True)  # nopep8; str, as the `variant_id`.

    await orders.create_index('data.attributes.created_at', background=True)   # nopep8; datetime.
    await orders.create_index('data.attributes.updated_at', background=True)   # nopep8; datetime.


# https://docs.lemonsqueezy.com/api/orders#the-order-object
# https://docs.lemonsqueezy.com/help/webhooks#example-payloads
#
# You will notice that the `data` in the payload is the order object,
# plus some `meta` and the usual `relationships` and `links`.
async def insert_order(order: dict):
    await orders.insert_one(order)
    find_latest_order.cache_clear()


@alru_cache(ttl=10)
async def find_latest_order(
    user_id: str,
    store_id: str,
    product_id: str,
    variant_id: str,
    test_mode: bool = False,
) -> Optional[dict]:
    cursor = orders \
        .find({
            'meta.custom_data.user_id': user_id,
            'data.attributes.store_id': store_id,
            'data.attributes.first_order_item.product_id': product_id,
            'data.attributes.first_order_item.variant_id': variant_id,
            'data.attributes.test_mode': test_mode,
        }) \
        .sort('data.attributes.updated_at', -1) \
        .limit(1)

    res: list[dict] = []
    async for order in cursor:
        res.append(order)

    return res[0] if res else None


def convert_order_to_response(order: dict) -> dict:
    status = order['data']['attributes']['status']

    created_at = order['data']['attributes']['created_at']
    created_at = convert_datetime_to_isoformat_with_z(created_at)

    updated_at = order['data']['attributes']['updated_at']
    created_at = convert_datetime_to_isoformat_with_z(updated_at)

    return {
        'available': status == str(Status.PAID),
        'status': status,
        'created_at': created_at,
        'updated_at': updated_at,
    }
