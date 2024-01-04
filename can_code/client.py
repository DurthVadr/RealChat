import socket
import pyaudio
import tkinter as tk
import threading

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

HOST = '192.168.1.101'
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

        self.play_selected_button = tk.Button(self.root, text="Play Selected Audio", command=self.play_selected_audio, state=tk.DISABLED)
        self.play_selected_button.pack()

        self.history_display = tk.Listbox(self.root, height=10, width=40)
        self.history_display.pack()

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.audio = pyaudio.PyAudio()

        self.stream = None
        self.play_stream = None
        self.sent_messages = []  # To store sent audio messages
        self.selected_message_index = None  # To store the index of the selected message

        self.history_display.bind('<<ListboxSelect>>', self.on_select)  # Bind event handler

    def on_select(self, event):
        selected_idx = self.history_display.curselection()
        if selected_idx:
            self.selected_message_index = int(selected_idx[0])  # Store the selected index
            self.play_selected_button.config(state=tk.NORMAL)  # Enable Play Selected button

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
        self.sent_messages.append(audio_data)  # Store sent audio for history
        self.update_history_display()  # Update the history display

    def receive_voice_message(self):
        def play_audio():
            try:
                self.play_stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                                                   rate=RATE, output=True,
                                                   frames_per_buffer=CHUNK)
                while True:
                    data = self.client_socket.recv(1024)
                    if not data:
                        print("No more data to play. Stopping...")
                        break

                    self.play_stream.write(data)
            except socket.error as e:
                print(f"Socket error: {e}")
            finally:
                self.play_stream.stop_stream()
                self.play_stream.close()

        receive_thread = threading.Thread(target=play_audio)
        receive_thread.start()

    def update_history_display(self):
        self.history_display.delete(0, tk.END)  # Clear the history display
        for idx, message in enumerate(self.sent_messages):
            self.history_display.insert(idx, f"Message {idx + 1}")  # Display message number

    def play_selected_audio(self):
        if self.selected_message_index is not None:
            try:
                selected_audio = self.sent_messages[self.selected_message_index]
                self.play_stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                                                   rate=RATE, output=True,
                                                   frames_per_buffer=CHUNK)
                self.play_stream.write(selected_audio)
                self.play_stream.stop_stream()
                self.play_stream.close()
            except IndexError:
                print("Invalid selection")
            finally:
                self.selected_message_index = None
                self.play_selected_button.config(state=tk.DISABLED)  # Disable the button after playing

def main():
    root = tk.Tk()
    app = VoiceChatClient(root)
    root.mainloop()

if __name__ == "__main__":
    main()
