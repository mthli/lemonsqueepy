import validators

from validators import ValidationFailure


# https://miguendes.me/how-to-check-if-a-string-is-a-valid-url-in-python
def is_url(url: str) -> bool:
    if not url:
        return False
    res = validators.url(url)
    return False if isinstance(res, ValidationFailure) else res
