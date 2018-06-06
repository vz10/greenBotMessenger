import unittest

from mock import patch

from webhook.run import process_request


class TestRun(unittest.TestCase):

    @patch('webhook.run.HttpRequest')
    @patch('webhook.run.handle_token')
    def test_process_request_get(self, mock_handle_token, mock_request):
        mock_request.return_value.method = 'GET'
        process_request()
        mock_handle_token.assert_called_with(mock_request.return_value.GET)

    @patch('webhook.run.HttpRequest')
    @patch('webhook.run.handle_message')
    def test_process_request_post(self, mock_handle_message, mock_request):
        mock_request.return_value.method = 'POST'
        process_request()
        mock_handle_message.assert_called_with(mock_request.return_value.POST)
