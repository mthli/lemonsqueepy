from mongo.db import orders


# https://docs.lemonsqueezy.com/api/orders#the-order-object
# https://docs.lemonsqueezy.com/help/webhooks#example-payloads
#
# You will notice that the `data` in the payload is the order object,
# plus some `meta` and the usual `relationships` and `links`.
async def insert_order(order: dict):
    await orders.insert_one(order)


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
            'data.type': 'orders',  # make sure is 'orders'.
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

    return bool(res)
