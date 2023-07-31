from urllib.parse import urlencode

from rds import get_key_from_rds, GOOGLE_OAUTH_CLIENT_ID


# https://developers.google.com/identity/openid-connect/openid-connect#sendauthrequest
def build_google_oauth_url(redirect_uri: str, state: str) -> str:
    params = {
        'client_id': get_key_from_rds(GOOGLE_OAUTH_CLIENT_ID),
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'offline',
        'display': 'popup',  # or 'page'.
        'include_granted_scopes': True,
        'prompt': 'consent',
    }

    return f'https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}'
