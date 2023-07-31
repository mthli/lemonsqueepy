from quart import Quart, json, request
from quart_cors import cors
from werkzeug.exceptions import HTTPException

from lemon import check_signing_secret
from logger import logger

app = Quart(__name__)
app = cors(app, allow_origin='*')


# https://flask.palletsprojects.com/en/2.2.x/errorhandling/#generic-exception-handler
#
# If no handler is registered,
# HTTPException subclasses show a generic message about their code,
# while other exceptions are converted to a generic "500 Internal Server Error".
@app.errorhandler(HTTPException)
def handle_exception(e: HTTPException):
    response = e.get_response()
    response.data = json.dumps({
        'code': e.code,
        'name': e.name,
        'description': e.description,
    })
    response.content_type = 'application/json'
    logger.error(f'errorhandler, data={response.data}')
    return response


# https://docs.lemonsqueezy.com/help/webhooks#event-types
@app.post('/api/webhooks')
async def webhooks():
    body: dict = await request.get_json() or {}
    logger.info(f'webhooks, body={json.dumps(body)}')  # always record.

    data = await request.get_data()  # raw body.
    check_signing_secret(request.headers, data)

    # TODO (Matthew Lee) dispatch events...
