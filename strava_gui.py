"""
Title: Strava Gui Application
Purpose: Interactive Strava activity interaction GUI to allow direct comparison between Strava activities.
Author: Kieran Gash
Date: 21/03/2024
"""

import sys
import io
import strava_dataset
import folium
import numpy as np
import pyqtgraph as pg

from lib.helper_functions import create_timestamped_geojson, calc_elevation_plot
from pathlib import Path
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QMainWindow, QApplication, QDesktopWidget, QVBoxLayout, QPushButton, QComboBox, \
    QFormLayout, QWidget, QDialog, QLineEdit, QGridLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from folium.plugins import TimestampedGeoJson


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
        self.setMinimumSize(1000, 1000)
        frame_geometry = self.frameGeometry()
        screen_center = QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)

        # Create central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Layout Structure (vertical box)
        main_layout_v1 = QVBoxLayout(central_widget)
        main_layout_v1.setAlignment(Qt.AlignVCenter)

        # Activity 1 combo box
        self.activity1_combo = QComboBox(self)
        self.activity1_combo.setEditable(True)
        self.activity1_combo.addItem("Loading...")

        # Activity 2 combo box
        self.activity2_combo = QComboBox(self)
        self.activity2_combo.setEditable(True)
        self.activity2_combo.addItem("Loading...")

        # RUN button
        self.run_btn = QPushButton("RUN")
        self.run_btn.setFixedWidth(125)
        self.run_btn.setFixedHeight(25)

        # Add widgets to form layout and add form layout
        main_layout_form = QFormLayout()
        main_layout_form.addRow("", self.activity1_combo)
        main_layout_form.addRow("", self.activity2_combo)
        main_layout_form.addRow("", self.run_btn)

        # Create map with starting lat long and zoom
        strava_map = folium.Map(location=[51.381065, -2.359017], tiles='CartoDBPositron', zoom_start=14)

        # Save initial map in BytesIO
        data = io.BytesIO()
        strava_map.save(data, close_file=False)

        # Create QWebEngineView widget to display map
        self.webview = QWebEngineView(self)
        self.webview.setMinimumSize(600, 400)
        self.webview.setHtml(data.getvalue().decode())

        # Create PlotWidget to display elevation of activity 1
        self.elevation_plot_act1 = pg.PlotWidget()
        self.elevation_plot_act1.setLabel('left', "Elevation (m)")
        self.elevation_plot_act1.setLabel('bottom', "Distance (km)")
        self.elevation_plot_act1.setXRange(0, 5)
        self.elevation_plot_act1.setYRange(0, 100)
        self.elevation_plot_act1.setBackground("#1E1F22")
        self.pen1 = pg.mkPen(color="#3574F0", width=2)

        # Create PlotWidget to display elevation of activity 2
        self.elevation_plot_act2 = pg.PlotWidget()
        self.elevation_plot_act2.setLabel('left', "Elevation (m)")
        self.elevation_plot_act2.setLabel('bottom', "Distance (km)")
        self.elevation_plot_act2.setXRange(0, 5)
        self.elevation_plot_act2.setYRange(0, 100)
        self.elevation_plot_act2.setBackground("#1E1F22")
        self.pen2 = pg.mkPen(color="#7D1A3B", width=2)

        # Add widgets to main layout
        main_layout_v1.addLayout(main_layout_form)
        main_layout_v1.addWidget(self.elevation_plot_act1)
        main_layout_v1.addWidget(self.elevation_plot_act2)
        main_layout_v1.addWidget(self.webview)

        self.setLayout(main_layout_v1)

        # Button actions
        self.run_btn.clicked.connect(self.process_activities)

    def update_combobox(self):
        """
        Update the activities which are displayed within the combo boxes. Currently set to display the latest 200
        activities.
        """
        # Clear existing combo boxes
        self.activity1_combo.clear()
        self.activity2_combo.clear()

        # Get all activities
        self.activities = strava_dataset.get_activities()

        # Add latest 200 activities to list
        activity_list = []
        for i in range(0, 200):
            activity_list.append(self.activities[i]['name'])

        # Add list to combo boxes
        self.activity1_combo.addItems(activity_list)
        self.activity2_combo.addItems(activity_list)

    def process_activities(self):
        """
        Take the activities chosen and process into dataframes and gpx files in preparation of animation.
        """
        # Get the activity ID for the activity names
        activity1_id = strava_dataset.get_activity_id(self.activity1_combo.currentText(), self.activities)
        activity2_id = strava_dataset.get_activity_id(self.activity2_combo.currentText(), self.activities)

        # Create activity route dataframe
        activity1_df = strava_dataset.get_route_stream(activity1_id, 1)
        activity2_df = strava_dataset.get_route_stream(activity2_id, 2)

        # Convert dataframe to Timestamped Geojson
        activity_geojson = create_timestamped_geojson(activity1_df, activity2_df,
                                                      '#3574F0', '#7D1A3B')

        # Update map and prepare animation
        self.flyby_animation(activity1_df, activity2_df, activity_geojson)

    def flyby_animation(self, activity1_df, activity2_df, activity_geojson):
        """
        Generate the animation, reposition the map and create gpx, and dataframes for the two routes chosen. 
        """
        # Lists to store combined latitude and longitudes
        combined_lat = []
        combined_long = []

        # Add both latitudes to list
        combined_lat.extend(activity1_df['lat'])
        combined_lat.extend(activity2_df['lat'])

        # Add both longitudes to list
        combined_long.extend(activity1_df['long'])
        combined_long.extend(activity2_df['long'])

        # Update map to centre on the chosen routes
        centroid = [np.mean(combined_lat), np.mean(combined_long)]
        update_map = folium.Map(location=centroid, tiles='CartoDBPositron', zoom_start=13)

        # Add animation of Activities
        TimestampedGeoJson(activity_geojson,
                           period='PT1S',
                           auto_play=True,
                           loop=False).add_to(update_map)

        # Update and save map
        data = io.BytesIO()
        update_map.save(data, close_file=False)
        self.webview.setHtml(data.getvalue().decode())

        # Update the plot widget
        self.update_plot(activity1_df, activity2_df)

    def update_plot(self, activity1_route_stream, activity2_route_stream):
        """
        Update the plot widget with the elevation data from the activities selected.
        """
        # Calculate the cumulative elevation and distance data
        activity1_route_stream = calc_elevation_plot(activity1_route_stream)
        activity2_route_stream = calc_elevation_plot(activity2_route_stream)

        # Define x and y data
        x1 = activity1_route_stream['cum_distance']
        x2 = activity2_route_stream['cum_distance']
        y1 = activity1_route_stream['altitude']
        y2 = activity2_route_stream['altitude']

        self.elevation_plot_act1.setXRange(0.2, max(x1))
        self.elevation_plot_act1.setYRange(min(y1), max(y1))
        self.elevation_plot_act2.setXRange(0.2, max(x2))
        self.elevation_plot_act2.setYRange(min(y2), max(y2))

        self.elevation_plot_act1.clear()
        self.elevation_plot_act2.clear()
        self.elevation_plot_act1.plot(x1, y1, pen=self.pen1, fillLevel=10, brush=(26, 59, 125, 50))
        self.elevation_plot_act2.plot(x2, y2, pen=self.pen2, fillLevel=10, brush=(125, 26, 59, 50))

# TODO: Improve the css "how to edit the default leaflet.timedimension_css when used in a python script"
# TODO: Create thread for application and buttons etc.
# TODO: Review activity choice matrix.
# TODO: Make the flyby animation smoother.
# TODO: Compare activities between multiple atheletes
# TODO: Add the update combo box to its own thread to ensure it does not delay the loading of the application.


class AthleteSelectorDialog(QDialog):
    """
    Pop up dialog at the start of the application to select the athlete(s) to analyse
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(240, 120)
        self.setWindowTitle("Athlete Selection")

        # Create custom buttons
        yes_button = QPushButton("Yes")
        yes_button.setFixedSize(100, 25)

        no_button = QPushButton("No")
        no_button.setFixedSize(100, 25)

        athlete_entry = QLineEdit()
        athlete_entry.setText("Enter Athlete ID...")

        # Connect button signals
        yes_button.clicked.connect(self.yes_clicked)
        no_button.clicked.connect(self.no_clicked)

        # Layout
        layout = QVBoxLayout()
        sublayout = QGridLayout()
        sublayout.addWidget(athlete_entry, 0, 0, 1, 2)
        sublayout.addWidget(yes_button, 1, 0)
        sublayout.addWidget(no_button, 1, 1)
        layout.addLayout(sublayout)
        self.setLayout(layout)

    def yes_clicked(self):
        self.accept()

    def no_clicked(self):
        self.reject()


class ActivitiesThread(QThread):
    """
    Setup of thread class to handle the getting of activities from Strava
    """
    activitiesFetched = pyqtSignal(list)

    def __init__(self):
        super().__init__()

    def run(self):
        activities = strava_dataset.get_activities()
        self.activitiesFetched.emit(activities)


class ApplicationSetup:
    """
    Contains all the required setup procedure for the application including both the initial dialog pop-up, main
    application window, stylesheet and thread setup.
    """
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(Path('strava_stylesheet.qss').read_text())

        self.athlete_selector = AthleteSelectorDialog()
        self.athlete_selector.accepted.connect(self.on_dialog_accepted)
        self.main_window = MainWindow()

    def on_dialog_accepted(self):
        thread = ActivitiesThread()
        thread.activitiesFetched.connect(self.main_window.update_combobox)
        thread.start()
        self.main_window.show()

    def run(self):
        self.athlete_selector.show()
        return self.app.exec_()


if __name__ == "__main__":
    app_setup = ApplicationSetup()
    sys.exit(app_setup.run())
