import sys
import io
from pathlib import Path

import numpy as np
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QMainWindow, QApplication, QDesktopWidget, QVBoxLayout, QPushButton, QComboBox, \
    QProgressBar, QFormLayout, QWidget
from PyQt5.QtCore import Qt
from folium.plugins import TimestampedGeoJson

import strava_dataset
import folium

html_path = "C:\\workspace\\Strava\\strava-api\\strava_map.html"


# Create main window
class MainWindow(QMainWindow):
    """
    Main GUI window application for the Strava App
    """

    def __init__(self):
        super().__init__()

        self.activities = None

        # Window Setup (Title, Size, Position ...)
        self.setWindowTitle("Strava GUI - v0.1")
        self.setMinimumSize(800, 400)
        frame_geometry = self.frameGeometry()
        screen_center = QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)

        # Create central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Layout Structure (vertical box)
        main_layout_v1 = QVBoxLayout(central_widget)
        main_layout_v1.setAlignment(Qt.AlignVCenter)

        # Get data button
        self.getData_btn = QPushButton("Get Data")
        self.getData_btn.setFixedWidth(125)
        self.getData_btn.setFixedHeight(25)

        # Activity 1 combo box
        self.activity1_combo = QComboBox(self)
        self.activity1_combo.setEditable(True)
        self.activity1_combo.addItem("GET DATA")

        # Activity 2 combo box
        self.activity2_combo = QComboBox(self)
        self.activity2_combo.setEditable(True)
        self.activity2_combo.addItem("GET DATA")

        # Generate GPX button
        self.genGPX_btn = QPushButton("Generate")
        self.genGPX_btn.setFixedWidth(125)
        self.genGPX_btn.setFixedHeight(25)

        # Data collection progress bar
        self.data_progress = QProgressBar(self)
        self.data_progress.setAlignment(Qt.AlignCenter)
        self.data_progress.setMinimum(0)
        self.data_progress.setMaximum(100)
        self.data_progress.setValue(0)

        # GPX collection progress bar
        self.gpx_progress = QProgressBar(self)
        self.gpx_progress.setAlignment(Qt.AlignCenter)
        self.gpx_progress.setMinimum(0)
        self.gpx_progress.setMaximum(100)
        self.gpx_progress.setValue(0)

        # Add widgets to form layout and add form layout
        main_layout_form = QFormLayout()
        main_layout_form.addRow(self.getData_btn, self.data_progress)
        main_layout_form.addRow("Activity 1:", self.activity1_combo)
        main_layout_form.addRow("Activity 2: ", self.activity2_combo)
        main_layout_form.addRow(self.genGPX_btn, self.gpx_progress)

        # Add form layout to the main layout
        main_layout_v1.addLayout(main_layout_form)

        # Create map with starting lat long and zoom
        strava_map = folium.Map(location=[51.381065, -2.359017], tiles='CartoDBDark_Matter', zoom_start=14)

        # Save initial map in BytesIO
        data = io.BytesIO()
        strava_map.save(data, close_file=False)

        # Create QWebEngineView widget to display map
        self.webview = QWebEngineView(self)
        self.webview.setMinimumSize(600, 400)
        self.webview.setHtml(data.getvalue().decode())
        main_layout_v1.addWidget(self.webview)

        self.setLayout(main_layout_v1)

        # Button actions
        self.getData_btn.clicked.connect(self.update_combobox)
        self.genGPX_btn.clicked.connect(self.generate_gpx)

    def update_combobox(self):
        """
        Update the options within the combo boxes following collection of the dataset
        """
        # Clear existing combo boxes
        self.activity1_combo.clear()
        self.activity2_combo.clear()

        # Get all activities
        self.activities = strava_dataset.get_activities()

        # Add latest 10 activities to list
        activity_name = []
        for i in range(0, 30):
            activity_name.append(self.activities[i]['name'])

        # Add list to combo boxes
        self.activity1_combo.addItems(activity_name)
        self.activity2_combo.addItems(activity_name)

    def generate_gpx(self):
        """
        Generates 2 gpx files for each of the activities selected
        """
        # Assign text from combo boxes to variables
        activity1_name = self.activity1_combo.currentText()
        activity2_name = self.activity2_combo.currentText()

        # Get the activity ID for the activity names
        activity1_id = self.activity_id_search(activity1_name)
        activity2_id = self.activity_id_search(activity2_name)

        # Get the activity route data as a dataframe
        activity1_route_stream = strava_dataset.get_route_stream(activity1_id, 1)
        activity2_route_stream = strava_dataset.get_route_stream(activity2_id, 2)

        # Convert dataframe into a gpx file
        strava_dataset.generate_gpx_file(activity1_route_stream, 1)
        strava_dataset.generate_gpx_file(activity2_route_stream, 2)

        # Convert dataframe to Timestamped Geojson
        activity1_geojson = strava_dataset.create_timestamped_geojson(activity1_route_stream, '#1A3B7D')
        activity2_geojson = strava_dataset.create_timestamped_geojson(activity2_route_stream, '#7D1A3B')

        # Lists to store combined latitude and longitudes
        combined_lat = []
        combined_long = []

        # Add both latitudes to list
        combined_lat.extend(activity1_route_stream['lat'])
        combined_lat.extend(activity2_route_stream['lat'])

        # Add both longitudes to list
        combined_long.extend(activity1_route_stream['long'])
        combined_long.extend(activity2_route_stream['long'])

        # Update map to centre on the chosen routes
        centroid = [np.mean(combined_lat), np.mean(combined_long)]
        update_map = folium.Map(location=centroid, tiles='CartoDBDark_Matter', zoom_start=13)

        # Add animation of Activity 1
        TimestampedGeoJson(activity1_geojson,
                           period='PT10S',
                           auto_play=True,
                           loop=False).add_to(update_map)

        # Add animation of Activity 2
        TimestampedGeoJson(activity2_geojson,
                           period='PT10S',
                           auto_play=True,
                           loop=False).add_to(update_map)

        # Update and save map
        data = io.BytesIO()
        update_map.save(data, close_file=False)
        self.webview.setHtml(data.getvalue().decode())

    def activity_id_search(self, activity_name):
        """
        Search the activity dataset for the names required and return the associated id
        """
        activity_id = 0

        # Search through the full activities list and find the ID associated with the name
        for index, entry in enumerate(self.activities):
            if activity_name == self.activities[index]['name']:
                activity_id = self.activities[index]['id']
                break

        return activity_id

    def ideas_function(self):
        """
        Function to store ideas and plan for the project temporarily
        """
        # Complete the flyby functionality
        # Add 2 widgets which display the elevation profile of the activities
            # https://betterdatascience.com/data-science-for-cycling-how-to-calculate-elevation-difference-and-distance-from-strava-gpx-route/


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(Path('strava_stylesheet.qss').read_text())
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())