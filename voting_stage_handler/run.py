# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../venv/Lib/site-packages')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.azure_db import Vote  # noqa
from common.fb_message import send_fb_message, send_buttons  # noqa


def process_voting_stage():
    top_score = Vote.get_top_score()
    participators = Vote.get_participators()

    if not top_score:
        return  # noting to do

    # TODO: call to IoT device
    Vote.clear_docs()

    vote_text = " ".join((top_score[0].split()[-2], top_score[0].split()[-1]))
    text = "⌛ 🎉 🎈 Choice '{}' wins. Action performed".format(vote_text)
    message_body = {"text": text}
    for participator_id in participators:
        send_fb_message(participator_id, message_body)
        send_buttons(participator_id)


if __name__ == "__main__":
    process_voting_stage()
