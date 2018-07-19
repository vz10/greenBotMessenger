import json
import requests

from common.config import FB_PAGE_ACCESS_TOKEN


def send_fb_message(sender_psid, message):
    request_body = {
        "recipient": {
            "id": sender_psid
        },
        "message": message
    }

    requests.post(url="https://graph.facebook.com/v2.6/me/messages",
                  params={"access_token": FB_PAGE_ACCESS_TOKEN},
                  headers={'content-type': 'application/json'},
                  data=json.dumps(request_body))
