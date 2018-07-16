# -*- coding: utf-8 -*-

import json
from datetime import datetime

import redis
import requests

from azfunc_helper import write_http_response
from config import FB_PAGE_ACCESS_TOKEN, REDIS_HOST, REDIS_PASSWD
from webhook.azure_db import upsert_docs_to_db, quick_replies, results_voting, config_voting, config_sensors, \
    get_user_vote_or_empty, \
    sensors_latest


def send_response(sender_psid, message):
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


def send_buttons(sender_psid):
    message_body = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "button",
                "text": "What do you want to do next?",
                "buttons": [
                    {
                        "type": "postback",
                        "title": "See sensors data",
                        "payload": "sensors_latest"
                    },
                    {
                        "type": "postback",
                        "title": "Vote",
                        "payload": "vote"
                    },
                    {
                        "type": "postback",
                        "title": "See voting results",
                        "payload": "voting_result"
                    },
                ]
            }
        }
    }
    send_response(sender_psid, message_body)


def is_processed(id):
    # this function is used to avoid responses duplication:
    # facebook resend events to the webhook if doesn't get 200 response in 20 seconds
    # so on function cold start bot may get duplicated messages
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=6380, password=REDIS_PASSWD, ssl=True, db=0)
    if not redis_client.get(id):
        redis_client.set(id, "1")
        redis_client.expire(id, 90)  # expire in 1.5 minutes
        return False
    return True


def handle_message(data):
    if data.get("object") == "page":
        for webhook_event in [entry["messaging"][0] for entry in data.get("entry") if "messaging" in entry]:
            # from request get postback
            postback = webhook_event.get("postback", {})
            # from request get recipient id
            sender_psid = webhook_event["sender"]["id"]
            timestamp = webhook_event.get("timestamp")
            # from request get message
            message = webhook_event.get("message", {})

            if message.get("quick_reply") and not is_processed(message["mid"]):

                # handle sender's choice
                result_vote = get_user_vote_or_empty(sender_psid)
                result_vote["vote"] = message["text"]
                result_vote["payload"] = message["quick_reply"]["payload"]
                result_vote["sender_id"] = sender_psid
                result_vote["timestamp"] = str(datetime.now())
                upsert_docs_to_db(result_vote, config_voting)
                send_buttons(sender_psid)

            # handle start button
            elif postback and not is_processed("{}{}".format(sender_psid, timestamp)):
                if postback.get("payload") == "get_started":
                    send_buttons(sender_psid)

                # handle vote
                elif postback.get("payload") == "vote":
                    message_body = {
                        "text": "What should I do with the plant?",
                        "quick_replies": quick_replies
                    }
                    send_response(sender_psid, message_body)

                # handle results of voting
                elif postback.get("payload") == "voting_result":
                    message_body = {"text": results_voting(config_voting)}
                    send_response(sender_psid, message_body)
                    send_buttons(sender_psid)

                elif postback.get("payload") == "sensors_latest":
                    message_body = {"text": sensors_latest(config_sensors)}
                    send_response(sender_psid, message_body)
                    send_buttons(sender_psid)

            # handle any text from sender
            elif message.get("text") and not is_processed(message["mid"]):
                send_buttons(sender_psid)

    # notify facebook that message is received
    write_http_response(200)
