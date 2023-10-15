#!/usr/bin/python3

# You will need to setup your API details in the file api_keys.py
# GPS data messages information can be found at https://aprs.gids.nl/nmea/

# Install libraries: pip3 install googlemaps openrouteservice tkintermapview pynmea2 pynput

from api_keys import GMAPS_API_KEY, ORS_API_KEY # Gets api keys required from local file api_keys.py
from pynput.mouse import Button, Controller # Used for controlling the mouse
import openrouteservice as ors # Used for directions between A and B
from gpiozero import Button as gpb # Setup GPIO's for the buttons
import tkintermapview # Used for creating the map
import tkinter as tk # Main GUI library
import googlemaps # Used for finding nearest argument in options list
import threading # Used for background
import datetime # Used only to correct the time received by GPS
import pynmea2 #Used to parse the GPS
import serial # Used to access the GPS module
import time # Used only to delay some loops


# Setup buttons to GPIO pins
btn_up = gpb(5)
btn_dwn = gpb(6)
btn_left = gpb(13)
btn_right = gpb(19)
btn_go = gpb(26)
btn_z_in = gpb(16)
btn_z_out = gpb(20)
btn_option = gpb(21)

# Variables
option = 0
options = ['stats', 'mcdonalds'] # Add additional search options as a string
satellites_found = 0 # Keeps track of satellites 
gps_time = '00:00:00'
gps_date = '00-00-0000'
tracking = False

# Setup GUI window and to size of screen
root = tk.Tk()
root.geometry('320x240')
root_frame = tk.Frame(root)
root_frame.pack()
title_label = tk.Label(root_frame, text='Nugget Finder')
title_label.pack(pady=70)


# Button functions
def map_up():
    mouse = Controller()
    mouse.press(Button.left)
    mouse.move(0, 1)
    mouse.release(Button.left)
    time.sleep(1)


def map_down():
    mouse = Controller()
    mouse.press(Button.left)
    mouse.move(0, -1)
    mouse.release(Button.left)
    time.sleep(1)


def map_left():
    mouse = Controller()
    mouse.press(Button.left)
    mouse.move(1, 0)
    mouse.release(Button.left)
    time.sleep(1)


def map_right():
    mouse = Controller()
    mouse.press(Button.left)
    mouse.move(-1, 0)
    mouse.release(Button.left)
    time.sleep(1)


def zoom_in():
    mouse = Controller()
    mouse.position = (35, 35)
    mouse.click(Button.left, count=1)
    time.sleep(1)


def zoom_out():
    mouse = Controller()
    mouse.position = (35, 75)
    mouse.click(Button.left, count=1)
    time.sleep(1)


def lets_go():
    if tracking == True:
        my_map.set_position(lat, lon)
        root.after(1000, lets_go)


# Used by a thread to monitor button pressing
def controls():
    global option, tracking
    while True:
        if btn_up.is_pressed:
            map_up()
        if btn_dwn.is_pressed:
            map_down()
        if btn_left.is_pressed:
            map_left()
        if btn_right.is_pressed:
            map_right()
        if btn_z_in.is_pressed:
            zoom_in()
        if btn_z_out.is_pressed:
            zoom_out()
        if btn_option.is_pressed:
            tracking = False # If already tracking it stops so you can see new option selected on screen
            if int(satellites_found) >= 1: # If enough satellites are found allow to find options
                option += 1
                if option == len(options): # If run out of options then return to stats screen
                    option = 0
                    show_stats()
                else: # Runs to function search_for for selected option
                    search_for(options[option])
            time.sleep(1)
        if btn_go.is_pressed and option !=0: # checks if option is not set to stats
            if tracking == True: # Stops tracking if was already
                tracking = False
            else: # Starts tracking, sets map zoom to close and runs lets_go function to keep updating screen to your position
                tracking = True
            time.sleep(1)
            my_map.set_zoom(17)
            lets_go()
        time.sleep(0.1)


# Clears the screen, googlemaps API request to find nearest, ORS API request for route and creates map
def search_for(find):
    global root_frame, my_map
    root_frame.destroy()
    root_frame = tk.Frame(root)
    root_frame.pack()
    gmaps = googlemaps.Client(key=GMAPS_API_KEY)
    nearby = gmaps.places_nearby(location=f'{lat}, {lon}',
                                 keyword=find,
                                 rank_by='distance')
    nearest = nearby['results'][0]
    destination = nearest['geometry']['location']['lat'], nearest['geometry']['location']['lng']
    coords = [[lon, lat], list(reversed(destination))]
    # Setup ORS for getting the directions
    client = ors.Client(key=ORS_API_KEY)
    routes = client.directions(coords, format='geojson')
    dirs = routes['features'][0]['geometry']['coordinates']
    directions = []
    for i in dirs: 
        directions.append((i[1], i[0]))
    # Find midway-ish point to route
    halfway = int(len(directions) / 2)
    # Setup new route on the map
    my_map = tkintermapview.TkinterMapView(root_frame, width=320, height=240)
    # The following lines uses a google maps tile, others are available with a search online
    my_map.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
    my_map.set_position(directions[halfway][0], directions[halfway][1])
    my_map.set_zoom(11)
    my_map.set_path(directions, width=3)
    my_map.pack()


# Clears the screen and displays the stats
def show_stats():
    global root_frame, satellites_qty, time_var, date_var
    root_frame.destroy()
    root_frame = tk.Frame(root)
    root_frame.pack()
    satellites_label = tk.Label(root_frame, text='Satellites:')
    satellites_label.grid(row=0, column=0, padx=10, sticky='e')
    satellites_qty = tk.StringVar()
    satellites_qty_label = tk.Label(root_frame, textvariable=satellites_qty)
    satellites_qty_label.grid(row=0, column=1, sticky='w')
    time_label = tk.Label(root_frame, text='Time:')
    time_label.grid(row=1, column=0, padx=10, sticky='e')
    time_var = tk.StringVar()
    time_var_label = tk.Label(root_frame, textvariable=time_var)
    time_var_label.grid(row=1, column=1, sticky='w')
    date_label = tk.Label(root_frame, text='Date:')
    date_label.grid(row=2, column=0, padx=10, sticky='e')
    date_var = tk.StringVar()
    date_var_label = tk.Label(root_frame, textvariable=date_var)
    date_var_label.grid(row=2, column=1, sticky='w')
    update_stats() # After window is setup then calls update_stats function


# Updates the stats window while the option is still 0 and runs itself to keep updating
def update_stats():
    global gps_time, gps_date, option
    if option == 0:
        satellites_qty.set(str(satellites_found))
        gps_time = str(gps_time)
        time_hour = str(datetime.datetime.now().hour) # Gets the hour of local time
        gps_time = gps_time.replace(gps_time[:2], time_hour) # Corrects the hour
        time_var.set(str(gps_time[:8]))
        date_sort = str(gps_date).split('-') # Splits to sort the date format
        gps_date = date_sort[2] + '-' + date_sort[1] + '-' + date_sort[0]
        date_var.set(str(gps_date)) # Sets the date in UK format
        root.after(1000, update_stats) # Calls the function again to update


# Used by a thread to constantly get the GPS data
def get_gps_data():
    global satellites_found, gps_time, gps_date, lat, lon
    port = '/dev/serial0' # Serial connection via GPIO pins
    ser = serial.Serial(port, baudrate=9600, timeout=0.5)
    while True:
        raw_data = pynmea2.NMEAStreamReader()
        new_data = ser.readline().decode('utf-8') # Decoded so its a string of data
        if new_data[:6] == '$GPRMC': # Checks type of message data received
            gps_parsed = pynmea2.parse(new_data)
            lat = gps_parsed.latitude
            lon = gps_parsed.longitude
            if gps_parsed.timestamp != None:
                gps_time = gps_parsed.timestamp
            if gps_parsed.datestamp != None:
                gps_date = gps_parsed.datestamp
        if new_data[:6] == '$GPGGA': # Checks type of message data received
            gps_gga = pynmea2.parse(new_data)
            gps_gga = str(gps_gga).split(',')
            satellites_found = gps_gga[7]


# Thread for GPS data
gps_thread = threading.Thread(target=get_gps_data)
gps_thread.start()
# Thread for buttons
control_thread = threading.Thread(target=controls)
control_thread.start()

# This is only used at startup so it shows the GUI name then starts stats function
root.after(5000, show_stats)
root.attributes('-fullscreen', True) # This makes it full screen
root.config(cursor='none') # Makes the mouse cursor invisible as when used for zooming

root.mainloop() # Keeps the GUI running
