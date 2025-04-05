#for checkout and housekeeping service
import requests

SUPPORTED_HTTP_METHODS = set([
    "GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"
])

def invoke_http(url, method='GET', json=None, **kwargs):
    """A simple wrapper for requests methods.
       url: the url of the http service;
       method: the http method;
       data: the JSON input when needed by the http method;
       return: the JSON reply content from the http service if the call succeeds;
            otherwise, return a JSON object with a "code" name-value pair.
    """
    try:
        if method.upper() in SUPPORTED_HTTP_METHODS:
            r = requests.request(method, url, json=json, **kwargs)
        else:
            raise Exception("HTTP method {} unsupported.".format(method))

        # Try to parse the response as JSON
        try:
            result = r.json() if len(r.content) > 0 else {}
        except Exception as e:
            return {"code": 500, "message": "Invalid JSON output from service: " + url + ". " + str(e)}

        # If the response has a code field, use that
        if isinstance(result, dict) and "code" in result:
            return result

        # Otherwise, create a response based on the status code
        if r.status_code in range(200, 300):
            return {"code": r.status_code, "data": result}
        else:
            return {"code": r.status_code, "message": "HTTP error: " + str(r.status_code)}

    except Exception as e:
        return {"code": 500, "message": "invocation of service fails: " + url + ". " + str(e)}
