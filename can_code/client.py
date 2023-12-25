import socket
import pyaudio


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5

HOST = '10.200.86.151'  # Put the server's IP or hostname
PORT = 65432  # Port

# Create a socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

audio = pyaudio.PyAudio()


stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK)

print("Recording...")

frames = []

# Record audio
for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)

print("Finished recording")

stream.stop_stream()
stream.close()
audio.terminate()

# Send audio to server
for frame in frames:
    client_socket.sendall(frame)

client_socket.close()
