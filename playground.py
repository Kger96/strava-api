import requests
import urllib3
import webbrowser
import urllib.parse
import http.server
import socketserver

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SharedData:
    def __init__(self):
        self.auth_code = None


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, shared_data=None, **kwargs):
        self.shared_data = shared_data
        super().__init__(*args, **kwargs)

    def do_GET(self):
        # Parse the URL path and Query component
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)

        if 'code' in query_params:
            # Retrieve authorisation code and send OK status.
            auth_code = query_params['code'][0]
            self.shared_data.auth_code = auth_code
            self.send_response(200)

            # Adds successful message to HTTP window
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Authorization code received. You can close this window.")
            return auth_code

        else:
            # Send ERROR status
            self.send_response(400)

            # Adds unsuccessful message to HTTP window
            self.end_headers()
            self.wfile.write(b"Authorization code not found in the URL.")


def user_authorisation():
    auth_url = "https://www.strava.com/oauth/authorize"
    payload = {
        'client_id': "111838",
        'redirect_uri': "http://localhost:8000",
        'response_type': "code",
        'scope': "activity:read_all"
    }

    # Construct the full URL with parameters
    url_parts = list(urllib.parse.urlparse(auth_url))
    query = urllib.parse.urlencode(payload)
    url_parts[4] = query
    authorization_url = urllib.parse.urlunparse(url_parts)

    # Open URL using webbrowser
    webbrowser.open(authorization_url)

    shared_data = SharedData()

    def handler(*args, **kwargs):
        RequestHandler(*args, shared_data=shared_data, **kwargs)

    # Start the local server to handle the redirect
    with socketserver.TCPServer(("", 8000), handler) as httpd:
        # Handle only a single request, then exit
        httpd.handle_request()

    user_code = shared_data.auth_code

    return user_code


def get_tokens(user_code):
    auth_url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': "111838",
        'client_secret': '089f8aaa0ef4bed4e4578ed6418fd1adea243d6d',
        'code': user_code,
        'grant_type': "authorization_code",
        'f': 'json'
    }

    res = requests.post(auth_url, data=payload, verify=False)
    # refresh_token = res.json()['refresh_token']
    access_token = res.json()['access_token']
    return access_token


def authorise_data_access():
    auth_url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': "111838",
        'client_secret': '089f8aaa0ef4bed4e4578ed6418fd1adea243d6d',
        'refresh_token': '78d50fd790f7a15619ab3f08a30cd590abab6f76',
        'grant_type': "refresh_token",
        'f': 'json'
    }

    res = requests.post(auth_url, data=payload, verify=False)
    access_token = res.json()['access_token']

    return access_token


def get_activities():
    activities_url = "https://www.strava.com/api/v3/athlete/activities"

    user_code = user_authorisation()

    access_token = get_tokens(user_code=user_code)

    header = {'Authorization': 'Bearer ' + access_token}
    param = {'per_page': 200, 'page': 1}
    activities = requests.get(activities_url, headers=header, params=param).json()

    return activities


if __name__ == "__main__":
    activities = get_activities()
    print(activities[0])
