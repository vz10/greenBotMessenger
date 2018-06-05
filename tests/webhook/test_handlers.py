import unittest

from mock import patch

from webhook.handlers import handle_token

FAKE_TOKEN = 'fake_token_123'


class TestHandleToken(unittest.TestCase):

    @patch('webhook.handlers.token.FB_VERIFY_TOKEN', FAKE_TOKEN)
    @patch('webhook.handlers.token.write_http_response')
    def tests_handle_token_correct(self, mock_write_http_response):
        params = {'hub.mode': 'subscribe', 'hub.verify_token': FAKE_TOKEN, 'hub.challenge': 'challenge_accepted'}
        handle_token(params)
        mock_write_http_response.assert_called_with(200, body=params['hub.challenge'])

    @patch('webhook.handlers.token.FB_VERIFY_TOKEN', FAKE_TOKEN)
    @patch('webhook.handlers.token.write_http_response')
    def test_handle_token_wrong(self, mock_write_http_response):
        params = {'hub.mode': 'subscribe', 'hub.verify_token': 'WRONG_TOKEN', 'hub.challenge': 'challenge_accepted'}
        handle_token(params)
        mock_write_http_response.assert_called_with(403)
