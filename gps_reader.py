## I got this code from https://maker.pro/raspberry-pi/tutorial/how-to-read-gps-data-with-python-on-a-raspberry-pi

from gps import *
from time import sleep

url = "https://gps-coordinates.org/my-location.php?lat=latitude&lng=longitude"
running = True

def getPositionData(gps):
    nx = gpsd.next()
    if nx['class'] == 'TPV':       
        current_time = getattr(nx, 'time', "Unknown")
        latitude = getattr(nx,'lat', "Unknown")
        longitude = getattr(nx,'lon', "Unknown")
        url = "https://gps-coordinates.org/my-location.php?lat="+str(latitude)+"&lng="+str(longitude)
        # print("Dog position: Time = " + str(current_time) + ", Latitude = " + str(latitude) + ", Longitude = " + str(longitude))
        print("View on map: " + url)
        write_location_data(current_time, latitude, longitude, url)

gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

# Helper function to write and save location data
def write_location_data(current_time, latitude, longitude, url):
    # Adjust the file path as necessary
    file_path = "gps_data_parsed.txt"
    with open(file_path, "a") as file:
        location_info = f"{current_time}, {latitude}, {longitude}, \"{url}\"\n"
        file.write(location_info)

# New function to read the latest GPS data from the file
def get_latest_gps_position():
    try:
        # Adjust the file path as necessary
        with open("gps_data_parsed.txt", "r") as file:
            lines = file.readlines()
            last_line = lines[-1]
            _, latitude, longitude, url = last_line.split(', ')
            return latitude.strip(), longitude.strip(), url
    except Exception as e:
        print(f"Error reading GPS data: {e}")
        return "Unknown", "Unknown"

try:
    print("Application started!")
    while running:
        getPositionData(gpsd)
        sleep(1.0)

except (KeyboardInterrupt):
    running = False
    print("Applications closed!")
