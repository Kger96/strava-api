"""
Title: Strava Authorisation
Purpose: Execute the authorisation procedure to enable athlete access
Author: Kieran Gash
Date: 25/05/2024
"""
import http.server
import socketserver
import urllib.parse
import webbrowser
import requests

# Constants
CLIENT_ID = "111838"
CLIENT_SECRET = '089f8aaa0ef4bed4e4578ed6418fd1adea243d6d'


class TokenDatabase:
    def __init__(self):
        self.auth_code = None
        self.access_token = None
        self.refresh_token = None


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, data=None, **kwargs):
        self.auth_data = data
        super().__init__(*args, **kwargs)

    def do_GET(self):
        # Parse the URL path and Query component
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)

        if 'code' in query_params:
            # Retrieve authorisation code and send OK status.
            auth_code = query_params['code'][0]
            self.auth_data.auth_code = auth_code
            self.send_response(200)

            # Adds successful message to HTTP window
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Authorization code received. You can close this window.")

        else:
            # Send ERROR status
            self.send_response(400)

            # Adds unsuccessful message to HTTP window
            self.end_headers()
            self.wfile.write(b"Authorization code not found in the URL.")


class AuthorisationManager:
    def __init__(self, token_data):
        # Create a shared data instance
        # self.shared_data = TokenDatabase()
        self.token_data = token_data

        self.auth_url = "https://www.strava.com/oauth/authorize"
        self.token_url = "https://www.strava.com/oauth/token"
        self.auth_code = None
        self.access_token = None
        self.refresh_token = None

    def user_authorisation(self):
        payload = {
            'client_id': CLIENT_ID,
            'redirect_uri': "http://localhost:8000",
            'response_type': "code",
            'scope': "activity:read_all"
        }

        # Construct the full URL with parameters
        url_parts = list(urllib.parse.urlparse(self.auth_url))
        query = urllib.parse.urlencode(payload)
        url_parts[4] = query
        authorization_url = urllib.parse.urlunparse(url_parts)

        # Open URL using webbrowser
        webbrowser.open(authorization_url)

        def handler(*args, **kwargs):
            RequestHandler(*args, data=self.token_data, **kwargs)

        # Start the local server to handle the redirect
        with socketserver.TCPServer(("", 8000), handler) as httpd:
            # Handle only a single request, then exit
            httpd.handle_request()

        self.first_time_get_tokens()

    def first_time_get_tokens(self):
        payload = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': self.token_data.auth_code,
            'grant_type': "authorization_code",
            'f': 'json'
        }

        res = requests.post(self.token_url, data=payload, verify=False)
        self.access_token = res.json()['access_token']
        self.refresh_token = res.json()['refresh_token']

        self.token_data.access_token = self.access_token
        self.token_data.refresh_token = self.refresh_token

    def get_tokens(self):
        payload = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': "refresh_token",
            'refresh_token': self.token_data.refresh_token,
            'f': 'json'
        }

        res = requests.post(self.token_url, data=payload, verify=False)
        self.access_token = res.json()['access_token']
        self.refresh_token = res.json()['refresh_token']

        self.token_data.access_token = self.access_token
        self.token_data.refresh_token = self.refresh_token

        return self.access_token
