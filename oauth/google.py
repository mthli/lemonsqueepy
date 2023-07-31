from urllib.parse import urlencode
from uuid import uuid4

from rds import rds, \
    get_key_from_rds, \
    GOOGLE_OAUTH_CLIENT_ID, \
    GOOGLE_OAUTH_REDIRECT_URI


# https://developers.google.com/identity/openid-connect/openid-connect#sendauthrequest
def build_google_oauth_url() -> str:
    state = str(uuid4())
    # TODO (Matthew Lee) save state to session.

    params = {
        'client_id': get_key_from_rds(GOOGLE_OAUTH_CLIENT_ID),
        'redirect_uri': get_key_from_rds(GOOGLE_OAUTH_REDIRECT_URI),
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'offline',
        'display': 'popup',  # or 'page'.
        'include_granted_scopes': True,
        'prompt': 'consent',
    }

    return f'https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}'
