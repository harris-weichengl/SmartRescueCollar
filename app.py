from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import os
import logging
import threading
from threading import Condition, Thread
import socketserver

from gps_reader import get_latest_gps_position

import subprocess

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

GPS_PAGE = """\
<html>
<head>
<title>GPS Location</title>
<link rel="stylesheet" href="/css/template.css"/>
</head>
<body>
<h1>Dog Coordinates</h1>
<p>Latitude: {latitude}</p>
<p>Longitude: {longitude}</p>
<a href={url}>View on map</a>
<a href="/">Back to home</a>
</body>
</html>
"""

AUDIO_PAGE = """\
<html>
<head>
<title>Audio Streaming</title>
<link rel="stylesheet" href="/css/template.css"/>
</head>
<body>
<h1>Audio Streaming</h1>
<img src="https://www.kindpng.com/picc/m/403-4036753_voice-call-icon-formation4you-hd-png-download.png" width="580" height="480" />
<a href="/">Back to home</a>
</body>
</html>
"""

VIDEO_PAGE = """\
<html>
<head>
<title>Smart Rescue Collar's View</title>
<link rel="stylesheet" href="/css/template.css"/>
</head>
<body>
<h1>Smart Collar's View</h1>
<img src="stream.mjpg" width="640" height="480" />
<a href="/">Back to home</a>  </body>
</html>
"""

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class PetCollarHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
        if self.path.endswith(".html"):
            self.serve_static_file('templates/index.html')
        elif self.path.endswith(".css"):
            self.serve_css_file('css/template.css')
            
        elif self.path == '/gps':
            latitude, longitude, url = get_latest_gps_position()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(GPS_PAGE.format(latitude=latitude, longitude=longitude, url=url), "utf-8"))
            
        elif self.path == '/audio':
            content = AUDIO_PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)            
            try:
                # Adjust the path to audio-only_client.py as necessary
                subprocess.run(["python3", "audio-only_client.py"], check=True)
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(b'Running audio-only_client.py')
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to run audio-only_client.py: {e}")
                self.send_error(500, "Internal Server Error", "Failed to run audio client.")

                
        elif self.path == '/video':
            content = VIDEO_PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

    def serve_css_file(self, filename):
        try:
            self.path.endswith(".css")
            file_path = os.path.join(os.getcwd(), filename)
            with open(file_path, 'rb') as file:
                self.send_response(200)
                self.send_header('Content-type', 'text/css')
                self.end_headers()
                self.wfile.write(file.read())
            file.close()
            self.flush_headers()
        except IOError:
            self.send_error(404, "File Not Found", f"The file {filename} does not exist.")
            
    def serve_static_file(self, filename):
        try:
            file_path = os.path.join(os.getcwd(), filename)
            with open(file_path, 'rb') as file:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(file.read())
            file.close()
            self.flush_headers()
        except IOError:
            self.send_error(404, "File Not Found", f"The file {filename} does not exist.")

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
output = StreamingOutput()
picam2.start_recording(JpegEncoder(), FileOutput(output))

def run(server_class=HTTPServer, handler_class=PetCollarHTTPRequestHandler, port=8080):
  server_address = ('', port)
  httpd = server_class(server_address, handler_class)
  print(f'Starting server on port {port}...')
  httpd.serve_forever()

if __name__ == '__main__':
  run()
