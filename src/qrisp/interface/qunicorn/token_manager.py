import requests
import time

class TokenManager:
    def __init__(self, token_url, basic_auth_header):
        self.token_url = token_url
        self.basic_auth_header = basic_auth_header  # e.g., "Basic YWxhZGRpbjpvcGVuc2VzYW1l"

        self.token = None
        self.expiry = 0

    def get_token(self):
        if self.token and time.time() < self.expiry:
            return self.token

        headers = {
            'Authorization': self.basic_auth_header,
        }
        data = {'grant_type': 'client_credentials'}
        response = requests.post(self.token_url, data=data,  headers=headers)

        if response.status_code != 200:
            raise Exception(f"Token request failed: {response.status_code} - {response.text}")

        token_data = response.json()
        self.token = token_data['access_token']
        self.expiry = time.time() + token_data.get('expires_in', 3600) - 60  # Buffer
        return self.token

    def get_auth_headers(self):
        token = self.get_token()
        return {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
