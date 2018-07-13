import json
from datetime import datetime

import redis
import requests

from azfunc_helper import write_http_response
from config import FB_PAGE_ACCESS_TOKEN, REDIS_HOST, REDIS_PASSWD
from webhook.azure_db import get_docs_from_db, put_docs_to_db, upsert_docs_to_db, quick_replies, results_voting, \
    config_voting, get_user_vote_or_empty


def send_response(sender_psid, message):
    request_body = {
        "recipient": {
            "id": sender_psid
        },
        "message": message
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

                    # if sender wants to vote
                    if message["text"] == "vote":
                        message_body = {
                            "text": "What should I do with the plant?",
                            "quick_replies": quick_replies
                        }
                        send_response(sender_psid, message_body)

                    # if sender wants to view results of voting
                    elif message["text"] == "voting_result":
                        message_body = {"text": results_voting(config_voting)}
                        send_response(sender_psid, message_body)

                    # handle voting of sender
                    elif message.get("quick_reply"):
                        result_vote = get_user_vote_or_empty(sender_psid)
                        result_vote["vote"] = message["text"]
                        result_vote["sender_id"] = sender_psid
                        result_vote["timestamp"] = str(datetime.now())
                        upsert_docs_to_db(result_vote, config_voting)

            # if pushed the start button
            elif webhook_event["postback"]["payload"] == "get_started":
                message_body = {
                    "text": "you push the button"
                }
                # message_body = {
                #     "attachment": {
                #         "type": "template",
                #         "payload": {
                #             "template_type": "button",
                #             "text": "What do you want to do next?",
                #             "buttons": [
                #                 {
                #                     "type": "postback",
                #                     "title": "vote",
                #                     "payload": "vote"
                #                 },
                #                 {
                #                     "type": "postback",
                #                     "title": "results",
                #                     "payload": "voting_result"
                #                 },
                #             ]
                #         }
                #     }
                # }
                send_response(sender_psid, message_body)

    # notify facebook that message is received
    write_http_response(200)

