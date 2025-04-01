import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)


class APIClient:

    @staticmethod
    def send_request(url: str, method: str, headers: dict, data=None, params=None, ssl_verify=False):
        """
        :param url: The URL to which the request is sent.
        :param method: The HTTP method to use for the request. Supported methods are "POST" and "GET".
        :param headers: A dictionary of HTTP headers to send with the request.
        :param data: The data to send in the body of the request (for POST requests).
        :param params: The URL parameters to send with the request (for GET requests).
        :param ssl_verify: Whether to verify the server's SSL certificate.
        :return: The response object from the request.
        """
        print(f"Sending {method} request to {url}")
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, verify=ssl_verify)
                return response
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, data=data, verify=ssl_verify)
                return response
        except requests.RequestException as e:
            print(f"An error occurred while sending the request: {e}")
            return None
