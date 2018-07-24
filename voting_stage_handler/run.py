# -*- coding: utf-8 -*-
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../venv/Lib/site-packages')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.azure_db import Vote  # noqa
from common.fb_message import send_fb_message, send_buttons  # noqa
import requests  # noqa


def process_voting_stage():
    auth_code = os.environ.get('AUTH_FUNCTION_KEY')
    host = os.environ.get('WEBSITE_HOSTNAME')
    top_score = Vote.get_top_score()

    if not top_score:
        return  # noting to do or not configured

    participators = Vote.get_participators()
    resp = requests.post(url="https://{}/api/iot_caller".format(host),
                         params={"code": auth_code},
                         headers={'content-type': 'application/json'},
                         data=json.dumps({'action': top_score}))
    if resp.status_code == 200:
        Vote.clear_docs()
        text = u"⌛ 🎉 🎈 Choice '{}' wins. Action performed".format(top_score.replace(u'_', u' '))
        message_body = {"text": text}
        for participator_id in participators:
            send_fb_message(participator_id, message_body)
            send_buttons(participator_id)
    else:
        print(resp.status_code, resp.text)
        admin_fb_id = os.environ.get("ADMIN_FB_SENDER_IDS")
        if admin_fb_id:
            send_fb_message(admin_fb_id, {"text": "ALERT: Something wrong with with IoT handler!\n"
                                                  "Code: {}\n{}".format(resp.status_code, resp.text)})


if __name__ == "__main__":
    process_voting_stage()
