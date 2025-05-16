import requests
from requests.auth import HTTPBasicAuth

from qrisp.interface.qunicorn.token_manager import TokenManager


class RequestManager:
    """
        A class for managing HTTP requests with optional HTTP basic authentication.

        Attributes:
            base_url (str): The base URL for all requests.
            session (requests.Session): A session object to manage HTTP connections.

        Methods:
            __init__(self, base_url, username=None, password=None):
                Initializes the RequestManager with the base URL and optional credentials.

            set_credentials(self, username, password):
                Sets HTTP basic authentication credentials for the session.

            get(self, endpoint, **kwargs):
                Sends a GET request to the specified endpoint.

            post(self, endpoint, data=None, json=None, **kwargs):
                Sends a POST request to the specified endpoint.

             post(self, endpoint, data=None, json=None, **kwargs):
                Sends a DELETE request to the specified endpoint.

            close(self):
                Closes the session and cleans up associated resources.
        """

    def __init__(self, base_url: str, username: str = None, password: str = None, token_manager: TokenManager = None):
        self.base_url = base_url
        self.session = requests.Session()
        self.token_manager = token_manager
        if username is not None and password is not None:
            self.set_credentials(username, password)

    def set_credentials(self, username: str, password: str):
        """Set HTTP basic authentication credentials."""
        self.session.auth = HTTPBasicAuth(username, password)

    def get(self, endpoint: str, **kwargs):
        """Execute GET request. """
        url = f"{self.base_url}{endpoint}"
        if self.token_manager:
            headers = self.token_manager.get_auth_headers()
            response = self.session.get(url, headers=headers, **kwargs)
        else:
            response = self.session.get(url, **kwargs)
        return response

    def post(self, endpoint: str, data=None, json=None, **kwargs):
        """Execute POST request. """
        url = f"{self.base_url}{endpoint}"
        if self.token_manager:
            headers = self.token_manager.get_auth_headers()
            response = self.session.post(url, data=data, json=json, headers=headers, **kwargs)
        else:
            response = self.session.post(url, data=data, json=json, **kwargs)
        return response

    def delete(self, endpoint: str, data=None, json=None, **kwargs):
        """Execute POST request. """
        url = f"{self.base_url}{endpoint}"
        if self.token_manager:
            headers = self.token_manager.get_auth_headers()
            response = self.session.post(url, data=data, json=json, headers=headers, **kwargs)
        else:
            response = self.session.delete(url, data=data, json=json, **kwargs)
        return response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the session."""
        self.session.close()
