import gpxpy
import pandas as pd
import requests
import urllib3
from datetime import datetime, timedelta

from shapely import Point
import geopandas as geo_pd

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

    data.to_csv(f'strava_activity{activity_num}', index=False)

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
    with open(f'strava_activity{activity_num}.gpx', 'w') as f:
        f.write(gpx.to_xml())


def create_timestamped_geojson(data, colour):
    # Convert df to geo df
    gdf = geo_pd.GeoDataFrame(data, geometry=[Point(xy) for xy in zip(data.long, data.lat)])

    # Initialize the GeoJSON structure
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    # Extract time and coordinates
    time_list = gdf['time'].tolist()
    geometry_list = gdf['geometry'].tolist()

    # Format timestamps and geometry lists
    time_formatted = [dt.isoformat() for dt in time_list]
    geometry_formatted = [[point.x, point.y] for point in geometry_list]

    # Populate the GeoJSON with features from the GeoDataFrame
    feature = {
        "type": "Feature",
        "properties": {
            "style": {"color": colour},
            "icon": "circle",
            "iconstyle": {
                "fillOpacity": 0.8,
                "stroke": "true",
                "radius": 4},
            "times": time_formatted
        },
        "geometry": {
            "type": "LineString",
            "coordinates": geometry_formatted
        }
    }
    geojson['features'].append(feature)

    return geojson
