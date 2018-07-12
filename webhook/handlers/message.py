import json
from datetime import datetime

import redis
import requests

from azfunc_helper import write_http_response
from config import FB_PAGE_ACCESS_TOKEN, REDIS_HOST, REDIS_PASSWD
from webhook.azure_db import get_docs_from_db, put_docs_to_db, config_options, config_voting


def send_response(sender_psid):
    # get options from database
    docs = get_docs_from_db(config_options)
    quick_replies = []
    for doc in docs:
        reply = {
            "content_type": "text",
            "title": str(doc["title"]),
            "payload": str(doc["payload"])
        }
        quick_replies.append(reply)

    request_body = {
        "recipient": {
            "id": sender_psid
        },
        "message": {
            "text": "What should I do with the plant?",
            "quick_replies": quick_replies},
    }

    resp = requests.post(url="https://graph.facebook.com/v2.6/me/messages",
                         params={"access_token": FB_PAGE_ACCESS_TOKEN},
                         headers={'content-type': 'application/json'},
                         data=json.dumps(request_body))


def handle_message(data):
    if data.get("object") == "page":
        for entry in data.get("entry"):
            webhook_event = entry["messaging"][0]
            # from request get recipient id
            sender_psid = webhook_event["sender"]["id"]
            # from request get message
            message = webhook_event.get("message")

            if message and message.get("text"):
                redis_client = redis.StrictRedis(host=REDIS_HOST, port=6380, password=REDIS_PASSWD, ssl=True, db=0)
                # facebook resend events to the webhook if doesn't get 200 response in 20 seconds
                # so on function cold start bot may get duplicated messages, that is why this is here
                if not redis_client.get(message["mid"]):
                    redis_client.set(message["mid"], "1")
                    redis_client.expire(message["mid"], 90)  # expire in 1.5 minutes

                    # handle the sender's choice
                    if message["text"] == "/vote":
                        send_response(sender_psid)
                    elif message["text"] == "/voting_result":
                        docs = get_docs_from_db(config_voting)
                        for doc in docs:
                            pass
                    else:
                        pass
                    if message.get("quick_reply"):
                        result_vote = {
                            "sender_id": sender_psid,
                            "timestamp": datetime.now().strftime("%d-%m-%y %H:%M"),
                            "vote": message["text"]
                        }
                        put_docs_to_db(result_vote, config_voting)

    # notify facebook that message is received
    write_http_response(200)
