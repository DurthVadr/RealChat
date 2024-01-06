import socket
import pyaudio
import tkinter as tk
from tkinter import ttk
import threading

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

HOST = '192.168.1.196'
PORT = 65432


class VoiceChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Chat Client")

        style = ttk.Style()
        style.theme_use("clam")  # You can choose a different theme here

        self.connection_frame = ttk.Frame(self.root)
        self.connection_frame.pack()

        self.main_frame = ttk.Frame(self.root)

        self.connect_button = ttk.Button(self.connection_frame, text="Connect", command=self.connect_to_server)
        self.connect_button.pack()

        self.disconnect_button = ttk.Button(self.main_frame, text="Disconnect", command=self.disconnect_from_server, state=tk.NORMAL)
        self.disconnect_button.pack()

        self.record_button = ttk.Button(self.main_frame, text="Record/Send", command=self.send_voice_message, state=tk.NORMAL)
        self.record_button.pack()

        self.listen_button = ttk.Button(self.main_frame, text="Listen/Receive", command=self.receive_voice_message, state=tk.NORMAL)
        self.listen_button.pack()

        self.play_selected_button = ttk.Button(self.main_frame, text="Play Selected Audio", command=self.play_selected_audio, state=tk.NORMAL)
        self.play_selected_button.pack()

        self.history_display = tk.Listbox(self.main_frame, height=10, width=40)
        self.history_display.pack()

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.audio = pyaudio.PyAudio()

        self.stream = None
        self.play_stream = None
        self.sent_messages = []
        self.selected_message_index = None

        self.history_display.bind('<<ListboxSelect>>', self.on_select)

    def on_select(self, event):
        selected_idx = self.history_display.curselection()
        if selected_idx:
            self.selected_message_index = int(selected_idx[0])
            self.play_selected_button.config(state=tk.NORMAL)

    def connect_to_server(self):
        if self.disconnect_button:
            self.disconnect_button.destroy()
        if self.record_button:
            self.record_button.destroy()
        if self.listen_button:
            self.listen_button.destroy()
        if self.play_selected_button:
            self.play_selected_button.destroy()
        if self.history_display:
            self.history_display.destroy()

        self.connection_frame.pack_forget()  # Hide the connection frame
        self.main_frame.pack()  # Show the main frame

        self.disconnect_button = ttk.Button(self.main_frame, text="Disconnect", command=self.disconnect_from_server, state=tk.NORMAL)
        self.disconnect_button.pack()

        self.record_button = ttk.Button(self.main_frame, text="Record/Send", command=self.send_voice_message, state=tk.NORMAL)
        self.record_button.pack()

        self.listen_button = ttk.Button(self.main_frame, text="Listen/Receive", command=self.receive_voice_message, state=tk.NORMAL)
        self.listen_button.pack()

        self.play_selected_button = ttk.Button(self.main_frame, text="Play Selected Audio", command=self.play_selected_audio, state=tk.NORMAL)
        self.play_selected_button.pack()

        self.history_display = tk.Listbox(self.main_frame, height=10, width=40)
        self.history_display.pack()

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.client_socket.connect((HOST, PORT))
        except Exception as e:
            print(f"Error connecting to server: {e}")
            self.disconnect_from_server()  # Ensure proper cleanup if connection fails

        self.audio = pyaudio.PyAudio()

        self.stream = None
        self.play_stream = None
        self.sent_messages = []
        self.selected_message_index = None

        self.history_display.bind('<<ListboxSelect>>', self.on_select)

    def disconnect_from_server(self):
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.record_button.config(state=tk.DISABLED)
        self.listen_button.config(state=tk.DISABLED)
        self.play_selected_button.config(state=tk.DISABLED)

        if self.client_socket:
            try:
                self.client_socket.shutdown(socket.SHUT_RDWR)
                self.client_socket.close()
            except OSError as e:
                print(f"Error while disconnecting: {e}")
            finally:
                self.client_socket = None

        self.main_frame.pack_forget()  # Hide the main frame
        self.connection_frame.pack()  # Show the connection frame

    def send_voice_message(self):
        if self.client_socket:
            try:
                self.stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                                              rate=RATE, input=True,
                                              frames_per_buffer=CHUNK)

                frames = []
                for i in range(0, int(RATE / CHUNK * 6)):
                    data = self.stream.read(CHUNK)
                    frames.append(data)

                audio_data = b''.join(frames)
                self.client_socket.sendall(audio_data)
                self.sent_messages.append(audio_data)
                self.update_history_display()
            except socket.error as e:
                print(f"Socket error: {e}")
            finally:
                if self.stream:
                    self.stream.stop_stream()
                    self.stream.close()

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
                if self.play_stream:
                    self.play_stream.stop_stream()
                    self.play_stream.close()

        receive_thread = threading.Thread(target=play_audio)
        receive_thread.start()

    def update_history_display(self):
        self.history_display.delete(0, tk.END)
        for idx, message in enumerate(self.sent_messages):
            self.history_display.insert(idx, f"Message {idx + 1}")

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
                self.play_selected_button.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = VoiceChatClient(root)
    root.mainloop()

if __name__ == "__main__":
    main()
