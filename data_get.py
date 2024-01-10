import requests
import urllib3
import pandas as pd
import gpxpy.gpx
from datetime import datetime, timedelta
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

auth_url = "https://www.strava.com/oauth/token"
activites_url = "https://www.strava.com/api/v3/athlete/activities"
data_stream_url = "https://www.strava.com/api/v3/activities/9904677699/streams"

payload = {
    'client_id': "111838",
    'client_secret': '089f8aaa0ef4bed4e4578ed6418fd1adea243d6d',
    'refresh_token': '78d50fd790f7a15619ab3f08a30cd590abab6f76',
    'grant_type': "refresh_token",
    'f': 'json'
}

print("Requesting Token...\n")
res = requests.post(auth_url, data=payload, verify=False)
access_token = res.json()['access_token']
print("Access Token = {}\n".format(access_token))

# Get Athlete Activities
header = {'Authorization': 'Bearer ' + access_token}
param = {'per_page': 200, 'page': 1}
my_dataset = requests.get(activites_url, headers=header, params=param).json()

# Get Route Data Streams
stream_param = {'keys': 'time,latlng,distance', 'key_by_type': True}
route_stream = requests.get(data_stream_url, headers=header, params=stream_param).json()
print(f"Time: {route_stream['time']['data']}\n")
print(f"LatLong: {route_stream['latlng']['data']}\n")
print(f"Distance: {route_stream['distance']['data']}\n")

#####################################

# print(f"Most Recent Activity: {my_dataset[0]['name']}")
# print(len(my_dataset))

# print(my_dataset[0])
