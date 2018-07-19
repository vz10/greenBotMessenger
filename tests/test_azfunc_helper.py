from contextlib import contextmanager
import json
import os
import unittest

from mock import patch, mock_open

from common.azfunc_helper import HttpRequest, write_http_response


@contextmanager
def set_env(varsdict):
    for key in varsdict:
        os.environ[key] = varsdict[key]
    yield
    for key in varsdict:
        del os.environ[key]


class TestHttpRequest(unittest.TestCase):

    @patch("__builtin__.open", new_callable=mock_open, read_data='{"param1":"A","param2":123}')
    def test_http_request_post(self, mo):
        with set_env({"REQ_METHOD": "POST",
                      "req": "post_body_contained_file",
                      "REQ_HEADERS_X-ORIGINAL-URL": "someurl",
                      "REQ_HEADERS_CONTENT-TYPE": "application/json"}):
            request = HttpRequest()
            self.assertEquals(request.method, "POST")
            # check read from correct file
            mo.assert_called_with("post_body_contained_file", "r")
            # check POST body is read from file and parsed to dict
            self.assertEquals(request.POST, {"param1": "A", "param2": 123})
            self.assertEquals(request.GET, {})

    def test_http_request_get(self):
        with set_env({"REQ_METHOD": "GET",
                      "REQ_HEADERS_X-ORIGINAL-URL": "someurl?arg1=111&arg2=hello"}):
            request = HttpRequest()
            self.assertEquals(request.method, "GET")
            self.assertEquals(request.GET, {"arg1": "111", "arg2": "hello"})
            self.assertEquals(request.POST, {})


class TestWriteHttpResponse(unittest.TestCase):

    @patch("__builtin__.open", new_callable=mock_open)
    def test_write_http_response_with_body(self, mo):
        with set_env({"res": "response_output_file"}):
            write_http_response(200, body="some_response")
            call_dict = {
                "status": 200,
                "headers": {"Content-Type": "text/html"},
                "body": "some_response"
            }
            # check correct data is written to file
            # mo.return_value is mock for file object, returned by mock_open
            mo.return_value.write.assert_called_with(json.dumps(call_dict))

    @patch("__builtin__.open", new_callable=mock_open)
    def test_write_http_response_code_only(self, mo):
        with set_env({"res": "response_output_file"}):
            write_http_response(401)
            call_dict = {
                "status": 401,
                "headers": {"Content-Type": "text/html"}
            }
            mo.return_value.write.assert_called_with(json.dumps(call_dict))
