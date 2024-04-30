"""
Title: Helper Functions
Purpose: Data manipulation functions to enable visualisation on the Strava GUI app.
Author: Kieran Gash
Date: 21/03/2024
"""

import gpxpy
import numpy as np
import haversine as hs
import geopandas as geo_pd

from shapely import Point


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
                lat1=data.iloc[i - 1]['lat'],
                long1=data.iloc[i - 1]['long'],
                lat2=data.iloc[i]['lat'],
                long2=data.iloc[i]['long'],
            ))

    data['distance'] = distances

    data['cum_elevation'] = data['elevation_diff'].cumsum()
    data['cum_distance'] = (data['distance'].cumsum())/1000

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


def calc_pace(distance, time):
    pace = round((time/60)/(distance/1000), 2)

    return pace
