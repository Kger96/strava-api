import requests
import urllib3
import pandas as pd
import gpxpy.gpx
from datetime import datetime, timedelta
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

auth_url = "https://www.strava.com/oauth/token"
activites_url = "https://www.strava.com/api/v3/athlete/activities"
data_stream_url = "https://www.strava.com/api/v3/activities/10600868306/streams"
start_time = '2024-01-21T09:17:36Z'

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
stream_param = {'keys': 'time,latlng,altitude', 'key_by_type': True}
route_stream = requests.get(data_stream_url, headers=header, params=stream_param).json()
activity_time = route_stream['time']['data']
activity_latlng = route_stream['latlng']['data']
activity_altitude = route_stream['altitude']['data']
# print(f"Time: {activity_time}\n")
# print(f"Lat/Long: {activity_latlng}\n")
# print(f"Distance: {activity_distance}\n")

# Create dataframe to store data
data = pd.DataFrame([*activity_latlng], columns=['lat', 'long'])
data['altitude'] = activity_altitude
start = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
data['time'] = [(start+timedelta(seconds=t)) for t in activity_time]

print(data)

# Create GPX File
gpx = gpxpy.gpx.GPX()
# Create first track in our GPX:
gpx_track = gpxpy.gpx.GPXTrack()
gpx.tracks.append(gpx_track)
# Create first segment in our GPX track:
gpx_segment = gpxpy.gpx.GPXTrackSegment()
gpx_track.segments.append(gpx_segment)
# Create points:
for idx in data.index:
    gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(
                data.loc[idx, 'lat'],
                data.loc[idx, 'long'],
                elevation=data.loc[idx, 'altitude'],
                time=data.loc[idx, 'time']
    ))
# Write data to gpx file
with open('output.gpx', 'w') as f:
    f.write(gpx.to_xml())

#####################################

# print(f"Most Recent Activity: {my_dataset[0]['name']}")
# print(len(my_dataset))

# print(my_dataset[0])
