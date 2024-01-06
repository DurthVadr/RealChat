import socket
import pyaudio
import tkinter as tk
import threading

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# HOST = '13.49.67.178'
HOST = '51.20.31.123'
#10.200.111.191
#13.49.243.37
PORT = 65432 


class VoiceChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Chat Client")
        self.connection_frame = tk.Frame(self.root)
        self.main_frame = tk.Frame(self.root)
        self.room_frame = tk.Frame(self.root)

        self.connect_button = tk.Button(self.connection_frame, text="Connect", command=self.connect_to_server)
        self.connect_button.pack()

        '''self.create_room_button = None
        self.join_room_button = None
        self.room_listbox = None
        self.room_name_entry = None
        self.room_selected_index = None '''

        self.client_socket = None
        self.disconnect_button = None
        self.record_button = None
        self.listen_button = None
        self.play_selected_button = None
        self.history_display = None
        self.password = None

        self.connection_frame.pack()

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

        self.connection_frame.pack_forget()
        self.main_frame.pack()

        self.disconnect_button = tk.Button(self.main_frame, text="Disconnect", command=self.disconnect_from_server, state=tk.NORMAL)
        self.disconnect_button.pack()

        self.record_button = tk.Button(self.main_frame, text="Record/Send", command=self.send_voice_message, state=tk.NORMAL)
        self.record_button.pack()

        self.listen_button = tk.Button(self.main_frame, text="Listen/Receive", command=self.receive_voice_message, state=tk.NORMAL)
        self.listen_button.pack()

        self.play_selected_button = tk.Button(self.main_frame, text="Play Selected Audio", command=self.play_selected_audio, state=tk.NORMAL)
        self.play_selected_button.pack()

        self.history_display = tk.Listbox(self.main_frame, height=10, width=40)
        self.history_display.pack()

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.client_socket.connect((HOST, PORT))
            self.show_room_selection()
        except Exception as e:
            print(f"Error connecting to server: {e}")
            self.disconnect_from_server()

        self.audio = pyaudio.PyAudio()

        self.stream = None
        self.play_stream = None
        self.sent_messages = []
        self.selected_message_index = None

        self.history_display.bind('<<ListboxSelect>>', self.on_select)

    def show_room_selection(self):
        self.main_frame.pack_forget()
        self.room_frame.pack()

        self.create_room_button = tk.Button(self.room_frame, text="Create Room", command=self.create_room_with_password)
        self.create_room_button.pack()

        self.join_room_button = tk.Button(self.room_frame, text="Join Room", command=self.join_room)
        self.join_room_button.pack()

        self.refresh_button = tk.Button(self.room_frame, text="Refresh", command=self.refresh_rooms)
        self.refresh_button.pack()

        '''self.room_listbox = tk.Listbox(self.room_frame, height=10, width=40)
        self.room_listbox.pack()'''

        self.rooms_display = tk.Listbox(self.room_frame, height=10, width=40)
        self.rooms_display.pack()  # Make sure it's packed within the main_frame

        # Room name entry
        self.room_name_label = tk.Label(self.room_frame, text="Room Name:")
        self.room_name_label.pack()
        self.room_name_entry = tk.Entry(self.room_frame)
        self.room_name_entry.pack()

        # Password entry
        self.password_label = tk.Label(self.room_frame, text="Password:")
        self.password_label.pack()
        self.password_entry = tk.Entry(self.room_frame, show="*")  # Password entry with hidden characters
        self.password_entry.pack()

    def ask_for_password(self, room_name):
        self.password_page = tk.Toplevel()
        self.password_page.title(f"Password for {room_name}")
        
        self.room_name_label = tk.Label(self.password_page, text=f"Room: {room_name}")
        self.room_name_label.pack()

        self.password_label = tk.Label(self.password_page, text="Enter password:")
        self.password_label.pack()

        self.password_entry = tk.Entry(self.password_page, show="*")
        self.password_entry.pack()

        self.submit_password_button = tk.Button(self.password_page, text="Submit", command=lambda: self.submit_password(room_name))
        self.submit_password_button.pack()

    def submit_password(self, room_name):
        password = self.password_entry.get()
        if password:
            self.password = password
            self.client_socket.send(f"JOIN_ROOM:{room_name}:{self.password}".encode())
            self.show_voice_messaging_page()  # Show the voice messaging page after successful password submission
            self.password_page.destroy()
        else:
            # Handle no password provided
            pass

    def create_room_with_password(self):
        room_name = self.room_name_entry.get()
        password = self.password_entry.get()

        if room_name and password:
            self.client_socket.sendall(f"CREATE_ROOM:{room_name}:{password}".encode())
        else:
            print("Please enter both room name and password.")

    def join_room(self):
        selected_index = self.rooms_display.curselection()
        if selected_index:
            room_name = self.rooms_display.get(selected_index)
            password = self.ask_for_password(room_name)
            if password:
                message = f"JOIN_ROOM:{room_name}:{password}"
                self.client_socket.sendall(message.encode())
                self.show_voice_messaging_page()

    def show_voice_messaging_page(self):
        self.room_frame.pack_forget()  # Hide the room selection page
        self.main_frame.pack()  # Show the voice messaging page

    def refresh_rooms(self):
        try:
            self.client_socket.sendall("GET_ROOMS".encode())
            rooms_list = self.client_socket.recv(1024).decode()
            self.display_rooms(rooms_list)
        except Exception as e:
            print(f"Error refreshing rooms: {e}")

    def display_rooms(self, rooms_list):
        self.rooms_display.delete(0, tk.END)
        rooms = rooms_list.strip("[]").split(", ")  # Remove square brackets and split
        for room in rooms:
            # Remove single quotes from the room name and insert into the listbox
            self.rooms_display.insert(tk.END, room.strip("'"))

    def on_select(self, event):
        selected_idx = self.history_display.curselection()
        if selected_idx:
            self.selected_message_index = int(selected_idx[0])
            self.play_selected_button.config(state=tk.NORMAL)

    def disconnect_from_server(self):
        if self.client_socket:
            try:
                self.client_socket.shutdown(socket.SHUT_RDWR)
                self.client_socket.close()
            except OSError as e:
                print(f"Error while disconnecting: {e}")
            finally:
                self.client_socket = None

        self.room_frame.pack_forget()
        self.connection_frame.pack()

    def send_voice_message(self):
        if self.client_socket:
            try:
                self.stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)

                frames = []
                for _ in range(0, int(44100 / 1024 * 6)):
                    data = self.stream.read(1024)
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
                self.play_stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=44100, output=True, frames_per_buffer=1024)
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
        for idx, _ in enumerate(self.sent_messages):
            self.history_display.insert(idx, f"Message {idx + 1}")

    def play_selected_audio(self):
        selected_index = self.history_display.curselection()
        if selected_index:
            try:
                selected_audio = self.sent_messages[selected_index[0]]
                self.play_stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=44100, output=True, frames_per_buffer=1024)
                self.play_stream.write(selected_audio)
                self.play_stream.stop_stream()
                self.play_stream.close()
            except IndexError:
                print("Invalid selection")
            finally:
                self.selected_message_index = None


def main():
    root = tk.Tk()
    app = VoiceChatClient(root)
    root.mainloop()

if __name__ == "__main__":
    main()
