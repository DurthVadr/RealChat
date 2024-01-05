import socket
import threading
import rsa
import pyaudio
import tkinter as tk
from tkinter import Entry, Label, Button, StringVar

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

HOST = '192.168.1.196' # The server's hostname or IP address aman dikkat
PORT = 65432

class VoiceChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Chat Client")

        self.connect_button = Button(self.root, text="Connect", command=self.connect_to_server)
        self.connect_button.pack()

        self.disconnect_button = Button(self.root, text="Disconnect", command=self.disconnect_from_server, state=tk.DISABLED)
        self.disconnect_button.pack()

        self.record_button = Button(self.root, text="Record/Send", command=self.send_voice_message, state=tk.DISABLED)
        self.record_button.pack()

        self.listen_button = Button(self.root, text="Listen/Receive", command=self.receive_voice_message, state=tk.DISABLED)
        self.listen_button.pack()

        self.play_selected_button = Button(self.root, text="Play Selected Audio", command=self.play_selected_audio, state=tk.DISABLED)
        self.play_selected_button.pack()

        self.history_display = tk.Listbox(self.root, height=10, width=40)
        self.history_display.pack()

        self.chatroom_name_entry = Entry(self.root)
        self.chatroom_name_entry.pack()

        self.chatroom_password_entry = Entry(self.root, show="*")
        self.chatroom_password_entry.pack()

        self.create_chatroom_button = Button(self.root, text="Create Chatroom", command=self.create_chatroom, state=tk.DISABLED)
        self.create_chatroom_button.pack()

        self.join_chatroom_button = Button(self.root, text="Join Chatroom", command=self.join_chatroom, state=tk.DISABLED)
        self.join_chatroom_button.pack()

        self.admin_var = StringVar()
        self.admin_checkbox = tk.Checkbutton(self.root, text="Admin", variable=self.admin_var)
        self.admin_checkbox.pack()

        self.username_entry = Entry(self.root)
        self.username_entry.pack()

        self.password_entry = Entry(self.root, show="*")
        self.password_entry.pack()

        self.register_button = Button(self.root, text="Register", command=self.register_user, state=tk.DISABLED)
        self.register_button.pack()

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_public_key = None  # Server's public key for encryption
        self.private_key = rsa.newkeys(1024).private_key()  # Client's private key

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
        self.create_chatroom_button.config(state=tk.NORMAL)
        self.join_chatroom_button.config(state=tk.NORMAL)
        self.register_button.config(state=tk.NORMAL)

        self.client_socket.connect((HOST, PORT))

        # Receive and store the server's public key
        self.server_public_key = rsa.PublicKey.load_pkcs1(self.client_socket.recv(1024))

        # Send additional info to identify if this client is the admin or a user
        is_admin = "admin" if self.admin_var.get() else "user"
        self.client_socket.sendall(is_admin.encode())

        if not self.admin_var.get():
            # Send username and password for user registration
            username = self.username_entry.get()
            password = self.password_entry.get()
            self.client_socket.sendall(username.encode())
            self.client_socket.sendall(password.encode())

    def disconnect_from_server(self):
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.record_button.config(state=tk.DISABLED)
        self.listen_button.config(state=tk.DISABLED)
        self.create_chatroom_button.config(state=tk.DISABLED)
        self.join_chatroom_button.config(state=tk.DISABLED)
        self.register_button.config(state=tk.DISABLED)

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

    def create_chatroom(self):
        chatroom_name = self.chatroom_name_entry.get()
        password = self.chatroom_password_entry.get()
        command = f"/create_chatroom {chatroom_name} {password}"
        self.send_command(command)

    def join_chatroom(self):
        chatroom_name = self.chatroom_name_entry.get()
        password = self.chatroom_password_entry.get()
        command = f"/join_chatroom {chatroom_name} {password}"
        self.send_command(command)

    def register_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        command = f"/register {username} {password}"
        self.send_command(command)

    def send_command(self, command):
        # Encrypt the command with the server's public key
        encrypted_command = rsa.encrypt(command.encode(), self.server_public_key)
        self.client_socket.sendall(encrypted_command)

def main():
    root = tk.Tk()
    app = VoiceChatClient(root)
    root.mainloop()

if __name__ == "__main__":
    main()
