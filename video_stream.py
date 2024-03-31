import io
import time
import socket
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

# Initialize Picamera2
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))

# Output setup - using an in-memory stream
output = io.BytesIO()

# Initialize socket client
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = 'localhost'  # Host IP where app.py is running
port = 8001  # Port on which app.py is listening
client_socket.connect((host_ip, port))

# Start recording to the in-memory stream
picam2.start_recording(JpegEncoder(), FileOutput(output))

# Capture for a certain period or until a condition is met
try:
    # Example: capture for 10 seconds
    start_time = time.time()
    while time.time() - start_time < 10000:
        # Reset stream position to the beginning
        output.seek(0)
        # Send 'output.read()' to app.py via the socket
        data = output.read()
        client_socket.sendall(data)
        # Wait for a bit before the next capture
        time.sleep(0.1)
finally:
    picam2.stop_recording()
    client_socket.close()
