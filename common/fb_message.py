# -*- coding: utf-8 -*-
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


def send_buttons(sender_psid):
    """
    Send buttons with options
    :param sender_psid: sender's id
    """
    message_body = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "button",
                "text": "☘️ What do you want to do next?",
                "buttons": [
                    {
                        "type": "postback",
                        "title": "Sensors data️ 🎛",
                        "payload": "sensors_latest"
                    },
                    {
                        "type": "postback",
                        "title": "Vote ✍️",
                        "payload": "vote"
                    },
                    {
                        "type": "postback",
                        "title": "Voting results 📊",
                        "payload": "voting_result"
                    },
                ]
            }
        }
    }
    send_fb_message(sender_psid, message_body)
