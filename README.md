# Strava Activity Animation
*Author: Kieran Gash*

*v1.0.0*

[![Python: 37, 38, 39, 310](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10-blue)](https://python.org)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/)

This project enables users to access activities stored on Strava by utilising the Strava API.

The users can visually compare two selected activities irrespective of the time the activity was performed or the
location of the activities. When the application is executed, the map centralises around the activities, and they are 
simultaneously plotted on the map creating an animation of the activity. 

Supporting graphics include the elevation profile and activity details such as
distance, pace and total elevation.

The animation speed can be modified, restarted or the user may change which activities to compare. Authentication is
only required when initially opening the application or if wanting to access a different Strava profile (although this
functionality is not yet added)

This application is a work in progress and continued updates will be released resolving bugs and adding additional
functionality. Currently desired functionality to improve/add can be found at the bottom of this README document. 


## Features

## Dependencies
1. Users must have access to a Strava account
2. If using the 

## User Guide
***Sub Heading***

## Bugs and Improvements


1) Get Client ID and Client Secret from Strava application webpage:
https://www.strava.com/settings/api

2) Paste the URL below into a browser and replace "your_client_id" with the Client ID obtained from step 1:
https://www.strava.com/oauth/authorize?client_id=your_client_id&redirect_uri=http://localhost&response_type=code&scope=activity:read_all

3) Redirect webpage shall contain the following URL. Save the code which will be in place of the "somecode" in the URL provided:
http://localhost/?state=&code=somecode&scope=read,activity:read_all

4) Make a POST request to the following URL. Replace with the Client ID, Client Secret and Code:
https://www.strava.com/oauth/token?client_id=your_client_id&client_secret=your_client_secret&code=your_code_from_previous_step&grant_type=authorization_code

5) Save the refersh token and access token from the output. 

6) Use the refresh token to obtain an updated access token:
https://www.strava.com/oauth/token?client_id=your_client_id&client_secret=your_client_secret&refresh_token=your_refresh_token_from_previous_step&grant_type=refresh_token 