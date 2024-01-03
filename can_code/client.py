import socket
import pyaudio
import tkinter as tk
import threading

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

HOST = '10.200.111.191'
PORT = 65432

class VoiceChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Chat Client")

        self.connect_button = tk.Button(self.root, text="Connect", command=self.connect_to_server)
        self.connect_button.pack()

        self.disconnect_button = tk.Button(self.root, text="Disconnect", command=self.disconnect_from_server, state=tk.DISABLED)
        self.disconnect_button.pack()

        self.record_button = tk.Button(self.root, text="Record/Send", command=self.send_voice_message, state=tk.DISABLED)
        self.record_button.pack()

        self.listen_button = tk.Button(self.root, text="Listen/Receive", command=self.receive_voice_message, state=tk.DISABLED)
        self.listen_button.pack()

        self.voice_display = tk.Text(self.root, height=10, width=40)
        self.voice_display.pack()

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio = pyaudio.PyAudio()

        self.stream = None
        self.play_stream = None

    def connect_to_server(self):
        self.connect_button.config(state=tk.DISABLED)
        self.disconnect_button.config(state=tk.NORMAL)
        self.record_button.config(state=tk.NORMAL)
        self.listen_button.config(state=tk.NORMAL)

        self.client_socket.connect((HOST, PORT))

    def disconnect_from_server(self):
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.record_button.config(state=tk.DISABLED)
        self.listen_button.config(state=tk.DISABLED)

        self.client_socket.close()

    def send_voice_message(self):
        self.stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                                      rate=RATE, input=True,
                                      frames_per_buffer=CHUNK)

        frames = []
        for i in range(0, int(RATE / CHUNK * 6)):  # Record for 6 seconds
            data = self.stream.read(CHUNK)
            frames.append(data)

        audio_data = b''.join(frames)
        self.client_socket.sendall(audio_data)

    def receive_voice_message(self):
        def play_audio():
            while True:
                try:
                    data = self.client_socket.recv(1024)
                    if not data:
                        break

                    self.play_stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                                                       rate=RATE, output=True,
                                                       frames_per_buffer=CHUNK)
                    self.play_stream.write(data)
                    self.play_stream.stop_stream()
                    self.play_stream.close()
                except socket.error as e:
                    print(f"Socket error: {e}")
                    break

        receive_thread = threading.Thread(target=play_audio)
        receive_thread.start()

def main():
    root = tk.Tk()
    app = VoiceChatClient(root)
    root.mainloop()

if __name__ == "__main__":
    main()
