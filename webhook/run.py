import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../venv/Lib/site-packages')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from azfunc_helper import HttpRequest  # noqa
from handlers import handle_token, handle_message  # noqa


def process_request():
    request = HttpRequest()

    if request.method == 'GET':
        handle_token(request.GET)
    elif request.method == 'POST':
        handle_message(request.POST)


if __name__ == "__main__":
    process_request()
