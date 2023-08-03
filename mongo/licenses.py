from mongo.db import licenses


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
