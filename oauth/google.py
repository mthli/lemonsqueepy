import httpx

from urllib.parse import urlencode, urlparse

from quart import abort

from rds import get_key_from_rds, \
    GOOGLE_OAUTH_CLIENT_ID, \
    GOOGLE_OAUTH_CLIENT_SECRET, \
    GOOGLE_OAUTH_REDIRECT_HOST
from utils import is_url

GOOGLE_OAUTH_REDIRECT_PATH = '/api/google/oauth/redirect'


# https://developers.google.com/identity/openid-connect/openid-connect#sendauthrequest
def build_google_oauth_url(state: str) -> str:
    params = {
        'client_id': get_key_from_rds(GOOGLE_OAUTH_CLIENT_ID),
        'redirect_uri': _build_google_oauth_redirect_uri(),
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'offline',
        'display': 'popup',  # or 'page'.
        'include_granted_scopes': True,
        'prompt': 'consent',
    }

    return f'https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}'


# https://developers.google.com/identity/openid-connect/openid-connect#exchangecode
async def exchange_code_for_access_token_and_id_token(code: str):
    data = {
        'client_id': get_key_from_rds(GOOGLE_OAUTH_CLIENT_ID),
        'client_secret': get_key_from_rds(GOOGLE_OAUTH_CLIENT_SECRET),
        'code': code,
        'redirect_uri': _build_google_oauth_redirect_uri(),
        'grant_type': 'authorization_code',
    }

    url = 'https://oauth2.googleapis.com/token'
    response = await _send_form_encoded_data(url, data)
    body: dict = response.json()

    id_token = body.get('id_token', '').strip()
    if not id_token:
        abort(500, '"id_token" not exists')

    # TODO (Matthew Lee) ...


# https://developers.google.com/identity/openid-connect/openid-connect#setredirecturi
def _build_google_oauth_redirect_uri() -> str:
    host = get_key_from_rds(GOOGLE_OAUTH_REDIRECT_HOST).rstrip('/')
    if not host:
        abort(500, f'"{GOOGLE_OAUTH_REDIRECT_HOST}" not exists')

    url = f'{host}{GOOGLE_OAUTH_REDIRECT_PATH}'
    if not is_url(url):
        abort(500, f'invalid "{GOOGLE_OAUTH_REDIRECT_HOST}"')

    parsed = urlparse(url)
    if not parsed.scheme:
        url = f'https://{url}'

    return url


async def _send_form_encoded_data(url: str, data: dict) -> httpx.Response:
    transport = httpx.AsyncHTTPTransport(retries=2)
    client = httpx.AsyncClient(transport=transport)

    try:
        # Content-Type must be 'application/x-www-form-urlencoded'
        response = await client.post(
            url=url,
            data=data,
            timeout=10,  # seconds.
            follow_redirects=True,
        )
    finally:
        await client.aclose()

    if not response.is_success:
        abort(response.status_code, response.text)

    # Automatically .aclose() if the response body is read to completion.
    return response
