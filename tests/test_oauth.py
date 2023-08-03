import time
import uuid

from oauth import generate_user_token, decrypt_user_token

# Make sure that secret is a **16 characters length** string.
_LEMONSQUEEZY_SIGNING_SECRET = '0123456789abcdef'


def test_generate_user_token():
    assert generate_user_token(
        user_id=str(uuid.uuid4()),
        timestamp=int(time.time()),
        secret=_LEMONSQUEEZY_SIGNING_SECRET,
    )


def test_decrypt_user_token():
    user_id = str(uuid.uuid4())
    timestamp = int(time.time())

    token = generate_user_token(
        user_id=user_id,
        timestamp=timestamp,
        secret=_LEMONSQUEEZY_SIGNING_SECRET,
    )

    info = decrypt_user_token(
        token=token,
        secret=_LEMONSQUEEZY_SIGNING_SECRET,
    )

    assert info
    assert info.user_id == user_id
    assert info.generate_timestamp == timestamp
