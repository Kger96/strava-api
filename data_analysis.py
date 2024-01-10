import pandas as pd
import polyline
from pandas import json_normalize
from Scripts.data_get import *
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import numpy as np
from datetime import datetime
import folium
import webbrowser
import stravalib
from stravalib.client import Client
from tqdm import tqdm


client = Client(access_token=access_token)

# Assign full dataset to variable
activities = json_normalize(my_dataset)


# Create new dataframe with only columns needed
cols = ['name', 'upload_id', 'type', 'distance', 'moving_time', 'elapsed_time', 'average_speed', 'max_speed',
        'total_elevation_gain', 'start_date_local', 'map.summary_polyline']
activities = activities[cols]

# Format date and time
activities['start_date_local'] = pd.to_datetime(activities['start_date_local'])
activities['start_time'] = activities['start_date_local'].dt.time
activities['start_date'] = activities['start_date_local'].dt.date

# Add Day of the week and month of the year columns
activities['day_of_week'] = activities['start_date_local'].dt.day_name()
activities['month_of_year'] = activities['start_date_local'].dt.month

# Convert times to timedeltas
activities['moving_time'] = pd.to_timedelta(activities['moving_time'])
activities['elapsed_time'] = pd.to_timedelta(activities['elapsed_time'])

# Convert timings to hours for plotting
activities['elapsed_time_hr'] = activities['elapsed_time'].dt.total_seconds() / 3600
activities['moving_time_hr'] = activities['moving_time'].dt.total_seconds() / 3600

# Create a distance in km column
activities['distance_km'] = activities['distance']/1e3

# Show latest 5 activities
# print(activities.head(5))

# Filter dataframe for activities which are of type 'Run'
runs = activities.loc[activities['type'] == 'Run']

########################################################################################################################
# Average Speed vs Distance plot
########################################################################################################################
# sns.set(style="ticks", context="talk")
# sns.regplot(x='distance', y='average_speed', data=runs).set_title("Average Speed vs Distance")
# plt.show()

########################################################################################################################
# Average Speed vs Date of Run & filtered by distance
########################################################################################################################
# Filter for runs between 4k and 6k
# runs_5k = runs[(runs['distance'] >= 4000) & (runs['distance'] <= 6000)]

# Format date and time
# runs_5k['start_date_local'] = pd.to_datetime(activities['start_date_local'])

# Filter for only 2023 dates
# runs_5k_2023 = runs_5k[runs_5k['start_date_local'].dt.year == 2023]

# Create figure and subplot
# fig = plt.figure()
# ax1 = fig.add_subplot(111)

# Convert data to numpy array
# x = np.asarray(runs_5k_2023.start_date_local)
# y = np.asarray(runs_5k_2023.average_speed)

# Add data points to graph
# ax1.plot_date(x, y)
# ax1.set_title('Average Speed over Time')

# Add trend line
# x2 = dates.date2num(x)
# z = np.polyfit(x2, y, 1)
# p = np.poly1d(z)
# plt.plot(x, p(x2), 'r--')

# Format the figure and display
# fig.autofmt_xdate(rotation=45)
# fig.tight_layout()
# plt.show()

########################################################################################################################
# Distance of Run vs Day of the week of the activity
########################################################################################################################
# day_of_week_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
# g = sns.catplot(x='day_of_week', y='distance_km', kind='strip', data=runs, order=day_of_week_order, col='type',
#                height=4, aspect=0.9, palette='pastel')
# g.set_axis_labels("Week day", "Distance (km)")
# g.set_titles("Activity type: {col_name}")
# g.set_xticklabels(rotation=30)
#
# plt.show()

########################################################################################################################
# Elevation plot for most recent activity
########################################################################################################################
# activities['map_polyline'] = activities['map.summary_polyline'].apply(polyline.decode)
#
#
# # define function to get elevation data using the open-elevation API
# def get_elevation(latitude, longitude):
#     base_url = "https://api.open-elevation.com/api/v1/lookup"
#     pload = {'locations': f'{latitude},{longitude}'}
#     r = requests.get(base_url, params=pload).json()['results'][0]
#     return r['elevation']
#
#
# # select recent activity
# my_run = activities.iloc[0, :]
#
# # get elevation data
# elevation_data = list()
# for idx in tqdm(activities.index):
#     if idx == 0:
#         activity = activities.loc[idx, :]
#         elevation = [get_elevation(coord[0], coord[1]) for coord in activity['map_polyline']]
#         elevation_data.append(elevation)
#     else:
#         elevation_data.append([])
#
# # add elevation data to dataframe
# my_run['map_elevation'] = elevation_data
#
# # plot elevation profile
# fig, ax2 = plt.subplots(figsize=(10, 4))
# ax2 = pd.Series(my_run['map_elevation'][0]).rolling(10).mean().plot(
#     ax=ax2,
#     color='steelblue',
#     legend=False
# )
# ax2.set_ylabel('Elevation')
# ax2.axes.xaxis.set_visible(False)
# ax2.spines['top'].set_visible(False)
# ax2.spines['right'].set_visible(False)
# plt.show()


########################################################################################################################
# Map plot for most recent activity
########################################################################################################################
activities['map_polyline'] = activities['map.summary_polyline'].apply(polyline.decode)

# select recent activity
my_run = activities.iloc[0, :]

# Determine number of lat-lng points and label start and finish
run_poly_length = len(my_run['map_polyline'])
finish_run = my_run['map_polyline'][run_poly_length-1]
start_run = my_run['map_polyline'][0]

# plot ride on map
centroid = [
    np.mean([coord[0] for coord in my_run['map_polyline']]),
    np.mean([coord[1] for coord in my_run['map_polyline']])]

# Create map and centre around run
m = folium.Map(location=centroid, zoom_start=15)

# Add route line and start and finish points to map
folium.PolyLine(my_run['map_polyline'], color='red', tooltip=my_run['distance']).add_to(m)
folium.Marker(start_run, popup='<i>Start</i>', icon=folium.Icon(icon='flag', color='green')).add_to(m)
folium.Marker(finish_run, popup='<i>Finish</i>', icon=folium.Icon(icon='flag', color='red')).add_to(m)
m.save('strava_run.html')
