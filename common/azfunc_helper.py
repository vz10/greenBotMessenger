import json
import os
import urlparse


class HttpRequest(object):
    def __init__(self):
        # Azure Functions platform saves request data into environment variable
        self.method = os.environ.get('REQ_METHOD')
        self.CONTENT_TYPE = os.environ.get('REQ_HEADERS_CONTENT-TYPE')

        self.POST = {}
        if self.method == 'POST':
            # Post body is stored into the file, which name is kept into environment variable ('req' by default)
            raw_req = open(os.environ['req'], 'r').read()
            if raw_req:
                if self.CONTENT_TYPE != 'application/json':
                    raise NotImplementedError("Decoding POST body is implemented only for JSON requests")
                self.POST = json.loads(raw_req)

        req_url_headers = os.environ.get('REQ_HEADERS_X-ORIGINAL-URL')
        query_params = urlparse.parse_qs(urlparse.urlparse(req_url_headers).query)
        # parse_qs parses single values into lists
        self.GET = dict((k, v if len(v) > 1 else v[0]) for k, v in query_params.iteritems())
        self.HOST = os.environ.get('WEBSITE_HOSTNAME')
        self.REQUESTER_HOST = os.environ.get('REQ_HEADERS_HOST')


def write_http_response(status, content_type='text/html', body=None, http_output_env_name='res'):
    return_dict = {
        "status": status,
        "headers": {
            "Content-Type": content_type
        }
    }
    if body:
        return_dict["body"] = body
    # Azure Functions take response data from the file, which name is kept into environment variable ('res' by default)
    output = open(os.environ[http_output_env_name], 'w')
    output.write(json.dumps(return_dict))
