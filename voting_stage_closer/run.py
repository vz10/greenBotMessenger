import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../venv/Lib/site-packages')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.azfunc_helper import HttpRequest  # noqa
from common.fb_message import send_fb_message


def handle_iot_message():
    pass


def process_request():
    request = HttpRequest()

    if request.method == 'POST':
        handle_iot_message(request.POST)


if __name__ == "__main__":
    process_request()
