import socket
import pyaudio
import tkinter as tk
from tkinter import ttk
import threading
import sys
import rsa

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

#HOST = '192.168.1.196' #Mertcan
# HOST = '192.168.1.118'   #Onur
HOST = '13.53.131.88'
PORT_VOICE = 65431
PORT_COMMAND = 65432

public_key,private_key = rsa.newkeys(1024)


class VoiceChatClient:
    def __init__(self, root):

        self.root = root
        self.root.title("Voice Chat Client")

        self.client_socket_voice = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket_command = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Use ttk style for a more modern look
        self.style = ttk.Style()
        self.style.theme_use("clam")  # You can experiment with other themes

        self.connection_frame = ttk.Frame(self.root)
        self.connection_frame.pack()
     
      

        # Add entry widget for entering username
        self.username_label = ttk.Label(self.connection_frame, text="Username:")
        self.username_label.pack()
        self.username_entry = ttk.Entry(self.connection_frame)
        self.username_entry.pack()

        self.connect_button = ttk.Button(self.connection_frame, text="Connect", command=self.connect_to_server)
        self.connect_button.pack()

        self.main_frame = ttk.Frame(self.root)

        

         # Label to display welcome message
        self.welcome_label = ttk.Label(self.main_frame, text="", font=("Helvetica", 18, "bold"))
        self.welcome_label.pack(anchor=tk.NW, padx=10, pady=10)  # Adjust padx and pady as needed

        self.client_socket = None
        self.disconnect_button = None
        self.record_button = None
        self.listen_button = None
        self.play_selected_button = None
        self.history_display = None
        
        self.isListening = True #stopping listen thread 

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

        self.username = self.username_entry.get()

        # Set the welcome message
        welcome_message = f"Welcome {self.username}"
        self.welcome_label.config(text=welcome_message)


        self.buttons_frame = ttk.Frame(self.main_frame)
        self.buttons_frame.pack(side=tk.TOP, pady=10)  # Adjust pady as needed

        # Use ttk.Button for a themed button
        self.whisper_button = ttk.Button(self.buttons_frame, text="Whisper 🗨️", command=self.send_whisper, state=tk.NORMAL)
        self.whisper_button.pack(side=tk.LEFT, padx=5)

        self.disconnect_button = ttk.Button(self.buttons_frame, text="Disconnect 🚫", command=self.disconnect_from_server, state=tk.NORMAL)
        self.disconnect_button.pack(side=tk.LEFT, padx=5)

        self.record_button = ttk.Button(self.buttons_frame, text="Record/Send 🎤", command=self.send_voice_message, state=tk.NORMAL)
        self.record_button.pack(side=tk.LEFT, padx=5)

        self.listen_button = ttk.Button(self.buttons_frame, text="Listen/Receive 🔊", command=self.receive_voice_message, state=tk.NORMAL)
        self.listen_button.pack(side=tk.LEFT, padx=5)

        self.play_selected_button = ttk.Button(self.buttons_frame, text="Play Selected Audio 🎵", command=self.play_selected_audio, state=tk.NORMAL)
        self.play_selected_button.pack(side=tk.LEFT, padx=5)

        # Use ttk.Treeview for a more organized display
        self.history_display = ttk.Treeview(self.main_frame, columns=("Message"))
        self.history_display.heading("#0", text="History")
        self.history_display.pack()


        self.online_clients_display = ttk.Treeview(self.main_frame, columns=("Online Clients"))
        self.online_clients_display.heading("#1", text="Online Clients")
        self.online_clients_display.heading("#0", text="")
        self.online_clients_display.heading("#2", text="")
        self.online_clients_display.pack()

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        

        try:
            self.client_socket_voice.connect((HOST, PORT_VOICE))
            self.client_socket_command.connect((HOST, PORT_COMMAND))
            self.server_key = rsa.PublicKey.load_pkcs1(self.client_socket_command.recv(1024))
            self.client_socket_command.send(public_key.save_pkcs1("PEM"))
            print("pub_key: ", public_key)
            print("priv_key: ", private_key)
        except Exception as e:
            print(f"Error connecting to server: {e}")
            self.disconnect_from_server()

        self.audio = pyaudio.PyAudio()

        self.stream = None
        self.play_stream = None
        self.sent_messages = []
        self.selected_message_index = None

        self.history_display.bind('<ButtonRelease-1>', self.on_select)

        register_username_command = f"REGISTER_USERNAME:{self.username}".encode()
        self.client_socket_command.sendall(rsa.encrypt(register_username_command, self.server_key))

        # Start listening for server messages
        threading.Thread(target=self.listen_for_server_messages, daemon=True).start()


    def on_select(self, event):
        selected_item = self.history_display.focus()

        if selected_item:
        # Split the string identifier to get the numerical part
         _, idx_str = selected_item.split('I')
        try:
            # Convert the numerical part to an integer
            self.selected_message_index = int(idx_str) - 1
            self.play_selected_button.config(state=tk.NORMAL)
        except ValueError:
            print(f"Invalid selection: {selected_item}")

    def disconnect_from_server(self):
        self.connect_button.state(['!disabled'])
        self.disconnect_button.state(['disabled'])
        self.record_button.state(['disabled'])
        self.listen_button.state(['disabled'])
        self.play_selected_button.state(['disabled'])
        self.isListening = False 
        print("sa")

        if self.client_socket_voice:
            try:
                self.client_socket_voice.shutdown(socket.SHUT_RDWR)
            except OSError as e:
                print(f"Error while shutting down voice socket: {e}")
            finally:
                self.client_socket_voice.close()

        if self.client_socket_command:
            try:
                self.client_socket_command.shutdown(socket.SHUT_RDWR)
            except OSError as e:
                print(f"Error while shutting down command socket: {e}")
            finally:
                self.client_socket_command.close()

        self.main_frame.pack_forget()
        self.root.destroy()
        self.root.quit()
        


    def listen_for_server_messages(self):
     while True:
        try:
            message = rsa.decrypt(self.client_socket_command.recv(1024), private_key).decode()
            if message.startswith("ONLINE_CLIENTS:"):
                online_clients = message.split(":", 1)[1].split(',')
                self.root.after(0, self.update_online_clients_display, online_clients)
            # Handle other types of messages here
        except Exception as e:
            print(f"Error receiving message from server: {e}")
            break

    
    def send_voice_message(self):
        if self.client_socket_voice:
            try:
                self.stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                                              rate=RATE, input=True,
                                              frames_per_buffer=CHUNK)

                frames = []
                for i in range(0, int(RATE / CHUNK * 6)):
                    data = self.stream.read(CHUNK)
                    frames.append(data)

                audio_data = b''.join(frames)
                self.client_socket_voice.sendall(audio_data)
                self.sent_messages.append(audio_data)
                self.update_history_display()
                # ... (other processing)
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
                while self.isListening:
                    data = self.client_socket_voice.recv(1024)
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
        self.history_display.delete(*self.history_display.get_children())
        for idx, message in enumerate(self.sent_messages, start=1):
            self.history_display.insert("", idx, text=f"Message {idx}")

    def update_online_clients_display(self, online_clients):
        self.online_clients_display.delete(*self.online_clients_display.get_children())
        for idx, username in enumerate(online_clients, start=1):
            display_text = username
            if username == self.username:
                display_text += " (Current)"
                print("sa")
            self.online_clients_display.insert("", idx, text=display_text)
            
    
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

    def on_window_close(self): #exts listen even the red exit button on top right is pressed
        self.disconnect_from_server()

    def send_whisper(self):
        selected_item = self.online_clients_display.focus()
        if not selected_item:
            print("No client selected")
            return
        
        receiver_ip = self.online_clients_display.item(selected_item, "text")
        if receiver_ip:
            try:
                self.stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                                              rate=RATE, input=True,
                                              frames_per_buffer=CHUNK)
                frames = []
                for i in range(0, int(RATE / CHUNK * 6)):
                    data = self.stream.read(CHUNK)
                    frames.append(data)
                    
                audio_data = b''.join(frames)
                whisper_command = f"WHISPER:{receiver_ip}".encode()  # Command format
                self.client_socket_command.sendall(rsa.encrypt(whisper_command, self.server_key))
                self.client_socket_voice.sendall(audio_data)

            except socket.error as e:
                print(f"Socket error: {e}")
            finally:
                if self.stream:
                    self.stream.stop_stream()
                    self.stream.close()

def main():
    root = tk.Tk()
    app = VoiceChatClient(root)
    #threading.Thread(target=app.listen_for_server_messages, daemon=True).start()
    root.mainloop()


if __name__ == "__main__":
    main()