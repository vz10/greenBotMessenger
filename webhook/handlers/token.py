from azfunc_helper import write_http_response
from config import FB_VERIFY_TOKEN


def handle_token(query_params):
    mode = query_params.get('hub.mode')
    token = query_params.get('hub.verify_token')
    challenge = query_params.get('hub.challenge')

    if mode == 'subscribe' and token == FB_VERIFY_TOKEN:
        write_http_response(200, body=challenge)
    else:
        write_http_response(403)
