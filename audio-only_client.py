import pymumble.pymumble_py3 as pymumble_py3
from pymumble.pymumble_py3.callbacks import PYMUMBLE_CLBK_SOUNDRECEIVED as PCS
import pyaudio

# Connection details for mumble server. Hardcoded for now, will have to be
# command line arguments eventually
pwd = "pimylifeup"  # password
server = "192.168.137.51"  # server address
nick = "WXL317"
port = 64738  # port number


# pyaudio set up
CHUNK = 1024
FORMAT = pyaudio.paInt16  # pymumble soundchunk.pcm is 16 bits
CHANNELS = 1
RATE = 48000  # pymumble soundchunk.pcm is 48000Hz

p = pyaudio.PyAudio()

stream_listen = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                #input=True,  # enable both talk
                output=True,  # and listen
                frames_per_buffer=CHUNK)

stream_talk = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,  # enable both talk
                #output=True,  # and listen
                frames_per_buffer=CHUNK)



# mumble client set up
def sound_received_handler(user, soundchunk):
    """ play sound received from mumble server upon its arrival """
    stream_listen.write(soundchunk.pcm)


# Spin up a client and connect to mumble server
mumble = pymumble_py3.Mumble(server, nick, password=pwd, port=port)

# set up callback called when PCS event occurs
mumble.callbacks.set_callback(PCS, sound_received_handler)
mumble.set_receive_sound(1)  # Enable receiving sound from mumble server
mumble.start()
mumble.is_ready()  # Wait for client is ready


# constant capturing sound and sending it to mumble server
while True:
    data = stream_talk.read(CHUNK)
    mumble.sound_output.add_sound(data)

# close the stream and pyaudio instance
stream_talk.stop_stream()
stream_talk.close()
stream_listen.stop_stream()
stream_listen.close()
p.terminate()

