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


def get_activities(auth_manager):
    activities_url = "https://www.strava.com/api/v3/athlete/activities"

    access_token = auth_manager.get_tokens()

    header = {'Authorization': 'Bearer ' + access_token}
    param = {'per_page': 200, 'page': 1}
    activities = requests.get(activities_url, headers=header, params=param).json()

    return activities


def get_route_stream(activity_id, activity_num, auth_manager):
    data_stream_url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    start_time = '2024-01-21T09:17:36Z'

    access_token = auth_manager.get_tokens()

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

    return data


def get_activity_data(activity_index, activities):
    """
    Search the activity dataset for the names required and return the associated id, distance and moving time
    """
    activity_distance = activities[activity_index]['distance']
    activity_time = activities[activity_index]['moving_time']
    activity_elevation = activities[activity_index]['total_elevation_gain']
    activity_id = activities[activity_index]['id']

    return activity_id, activity_distance, activity_time, activity_elevation
