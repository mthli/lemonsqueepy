from enum import unique

from strenum import StrEnum

from mongo.db import orders


@unique
class Status(StrEnum):
    PENDING = 'pending'
    PAID = 'paid'
    FAILED = 'failed'
    REFUNDED = 'refunded'


# FIXME (Matthew Lee) where is the `order_id` or something like that?
async def setup_orders():
    await orders.create_index('meta.event_name', background=True)              # nopep8; str.
    await orders.create_index('meta.custom_data.user_id', background=True)     # nopep8; str.
    await orders.create_index('data.attributes.store_id', background=True)     # nopep8; int.
    await orders.create_index('data.attributes.customer_id', background=True)  # nopep8; int.
    await orders.create_index('data.attributes.identifier', background=True)   # nopep8; str.
    await orders.create_index('data.attributes.user_email', background=True)   # nopep8; str.
    await orders.create_index('data.attributes.status', background=True)       # nopep8; str.
    await orders.create_index('data.attributes.first_order_item.product_id', background=True)  # nopep8; int.
    await orders.create_index('data.attributes.first_order_item.variant_id', background=True)  # nopep8; int.
    await orders.create_index('data.attributes.created_at', background=True)   # nopep8; datetime.
    await orders.create_index('data.attributes.updated_at', background=True)   # nopep8; datetime.


# https://docs.lemonsqueezy.com/api/orders#the-order-object
# https://docs.lemonsqueezy.com/help/webhooks#example-payloads
#
# You will notice that the `data` in the payload is the order object,
# plus some `meta` and the usual `relationships` and `links`.
async def insert_order(order: dict):
    await orders.insert_one(order)


# Check whether the latest order status is "paid".
async def has_available_order(
    user_id: str,
    store_id: int,
    product_id: int,
    variant_id: int = 1,  # as the "default" variant.
    test_mode: bool = False,
) -> bool:
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

    return res[0]['status'] == str(Status.PAID) if res else False
