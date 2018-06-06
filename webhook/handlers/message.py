import json
import redis
import requests

from azfunc_helper import write_http_response
from config import FB_PAGE_ACCESS_TOKEN, REDIS_HOST, REDIS_PASSWD


def send_response(sender_psid, msg_txt):
    request_body = {
        "recipient": {
            "id": sender_psid
        },
        "message": {"text":
                    "PONG" if msg_txt.lower() == "ping" else ("WHAT \"%s\"?" % msg_txt)}
    }

    resp = requests.post(url="https://graph.facebook.com/v2.6/me/messages",
                         params={"access_token": FB_PAGE_ACCESS_TOKEN},
                         headers={'content-type': 'application/json'},
                         data=json.dumps(request_body))


def handle_message(data):
    # notify facebook that message is received:
    write_http_response(200)

    if data.get("object") == "page":
        for entry in data.get("entry"):
            webhook_event = entry["messaging"][0]
            sender_psid = webhook_event["sender"]["id"]
            message = webhook_event.get("message")

            if message and message.get("text"):
                redis_client = redis.StrictRedis(host=REDIS_HOST, port=6380, password=REDIS_PASSWD, ssl=True, db=0)
                if not redis_client.get(message["mid"]):
                    redis_client.set(message["mid"], "1")
                    redis_client.expire(message["mid"], 90)  # expire in 1.5 minutes
                    send_response(sender_psid, message["text"])
