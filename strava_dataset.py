"""
Title: Strava Dataset API
Purpose: To extract the relevant data from Strava using API calls.
Author: Kieran Gash
Date: 21/03/2024
"""

import pandas as pd
import requests
import urllib3

from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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

    access_token = authorise_data_access()

    header = {'Authorization': 'Bearer ' + access_token}
    param = {'per_page': 200, 'page': 1}
    activities = requests.get(activities_url, headers=header, params=param).json()

    return activities


def get_route_stream(activity_id, activity_num):
    data_stream_url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    start_time = '2024-01-21T09:17:36Z'

    access_token = authorise_data_access()

    # Get Route Data Streams
    header = {'Authorization': 'Bearer ' + access_token}
    stream_param = {'keys': 'time,latlng,altitude', 'key_by_type': True}
    route_stream = requests.get(data_stream_url, headers=header, params=stream_param).json()
    activity_time = route_stream['time']['data']
    activity_latlng = route_stream['latlng']['data']
    activity_altitude = route_stream['altitude']['data']

    # Create dataframe to store data
    data = pd.DataFrame([*activity_latlng], columns=['lat', 'long'])
    data['altitude'] = activity_altitude
    start = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
    data['time'] = [(start + timedelta(seconds=t)) for t in activity_time]

    data.to_csv(f'dist\\strava_activity{activity_num}', index=False)

    return data


def get_activity_id(activity_name, activities):
    """
    Search the activity dataset for the names required and return the associated id
    """
    activity_id = 0

    # Search through the full activities list and find the ID associated with the name
    for index, entry in enumerate(activities):
        if activity_name == activities[index]['name']:
            activity_id = activities[index]['id']
            break

    return activity_id
