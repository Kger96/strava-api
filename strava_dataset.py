"""
Title: Strava Dataset API
Purpose: To extract the relevant data from Strava using API calls.
Author: Kieran Gash
Date: 21/03/2024
"""

import gpxpy
import numpy as np
import pandas as pd
import requests
import urllib3
import haversine as hs
import geopandas as geo_pd

from shapely import Point
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


def generate_gpx_file(data, activity_num):
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
    with open(f'dist\\strava_activity{activity_num}.gpx', 'w') as f:
        f.write(gpx.to_xml())


def create_timestamped_geojson(route1, route2, colour1, colour2):
    # Convert df to geo df
    gdf1 = geo_pd.GeoDataFrame(route1, geometry=[Point(xy) for xy in zip(route1.long, route1.lat)])
    gdf2 = geo_pd.GeoDataFrame(route2, geometry=[Point(xy) for xy in zip(route2.long, route2.lat)])

    # Initialize the GeoJSON structure
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    # Extract time and coordinates
    time_list1 = gdf1['time'].tolist()
    time_list2 = gdf2['time'].tolist()
    geometry_list1 = gdf1['geometry'].tolist()
    geometry_list2 = gdf2['geometry'].tolist()

    # Format timestamps and geometry lists
    time_formatted1 = [dt.isoformat() for dt in time_list1]
    time_formatted2 = [dt.isoformat() for dt in time_list2]
    geometry_formatted1 = [[point.x, point.y] for point in geometry_list1]
    geometry_formatted2 = [[point.x, point.y] for point in geometry_list2]

    feature1 = {
        "type": "Feature",
        "properties": {
            "style": {"color": colour1},
            "icon": "circle",
            "iconstyle": {
                "fillOpacity": 0.8,
                "stroke": "true",
                "radius": 4},
            "times": time_formatted1
        },
        "geometry": {
            "type": "LineString",
            "coordinates": geometry_formatted1
        }
    }

    feature2 = {
        "type": "Feature",
        "properties": {
            "style": {"color": colour2},
            "icon": "circle",
            "iconstyle": {
                "fillOpacity": 0.8,
                "stroke": "true",
                "radius": 4},
            "times": time_formatted2
        },
        "geometry": {
            "type": "LineString",
            "coordinates": geometry_formatted2
        }
    }

    geojson['features'].append(feature1)
    geojson['features'].append(feature2)

    return geojson


def calc_elevation_plot(data):
    data['elevation_diff'] = data['altitude'].diff()

    distances = [np.nan]

    for i in range(len(data)):
        if i == 0:
            continue
        else:
            distances.append(haversine_distance(
                lat1=data.iloc[i-1]['lat'],
                long1=data.iloc[i-1]['long'],
                lat2=data.iloc[i]['lat'],
                long2=data.iloc[i]['long'],
            ))

    data['distance'] = distances

    data['cum_elevation'] = data['elevation_diff'].cumsum()
    data['cum_distance'] = data['distance'].cumsum()

    data = data.fillna(0)

    return data


def haversine_distance(lat1, long1, lat2, long2):
    distance = hs.haversine(
        point1=(lat1, long1),
        point2=(lat2, long2),
        unit=hs.Unit.METERS
    )

    return np.round(distance, 2)


def total_elevation(data):
    data[data['elevation_diff'] >= 0]['elevation_diff'].sum()
