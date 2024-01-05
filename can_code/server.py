import socket
import threading
import rsa
import pyaudio

import bcrypt

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

HOST = '192.168.1.196' # The server's hostname or IP address aman dikkat
PORT = 65432

class VoiceChatServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}
        self.shared_history = {}
        self.public_keys = {}
        self.chatrooms = {}
        self.admin_password = bcrypt.hashpw("admin_password".encode("utf-8"), bcrypt.gensalt())

    def start_server(self):
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen()
        print("Server started, waiting for connections...")

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connected by {addr}")

            # Receive and store public key from the client
            public_key = rsa.PublicKey.load_pkcs1(client_socket.recv(1024))
            self.public_keys[client_socket] = public_key

            # Receive additional info to identify if this client is the admin
            is_admin = client_socket.recv(1024).decode() == "admin"

            if is_admin:
                self.clients["admin"] = client_socket
            else:
                username = client_socket.recv(1024).decode()
                password = client_socket.recv(1024).decode()
                if self.authenticate_user(username, password):
                    self.clients[client_socket] = {"username": username}
                else:
                    client_socket.send("Invalid username or password. Connection closed.".encode())
                    client_socket.close()
                    continue

            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def handle_client(self, client_socket):
        while True:
            try:
                encrypted_data = client_socket.recv(1024)
                if not encrypted_data:
                    break

                decrypted_data = self.decrypt_message(encrypted_data, client_socket)

                if client_socket == self.clients["admin"]:
                    self.handle_admin_command(decrypted_data)
                else:
                    self.handle_user_command(decrypted_data, client_socket)

            except ConnectionResetError:
                # Handle disconnection or errors
                break

        del self.public_keys[client_socket]

        if client_socket == self.clients["admin"]:
            del self.clients["admin"]
        else:
            del self.clients[client_socket]

        client_socket.close()

    def decrypt_message(self, encrypted_data, receiver_socket):
        public_key = self.public_keys[receiver_socket]
        decrypted_data = rsa.decrypt(encrypted_data, public_key)
        return decrypted_data

    def handle_admin_command(self, command):
        command = command.decode()
        if command.startswith("/ban "):
            _, username_to_ban = command.split()
            self.ban_user(username_to_ban)
        elif command.startswith("/view_chatrooms"):
            self.view_chatrooms()

    def handle_user_command(self, command, client_socket):
        command = command.decode()
        if command.startswith("/create_chatroom "):
            _, chatroom_name, password = command.split()
            self.create_chatroom(chatroom_name, password, client_socket)
        elif command.startswith("/join_chatroom "):
            _, chatroom_name, password = command.split()
            self.join_chatroom(chatroom_name, password, client_socket)
        else:
            self.broadcast_voice_message(command.encode(), client_socket)

    def ban_user(self, username):
        for client in list(self.clients.keys()):
            if self.clients[client]["username"] == username:
                client.send("You have been banned from the server!".encode())
                client.close()

    def view_chatrooms(self):
        chatrooms_list = "\n".join(self.chatrooms.keys())
        self.clients["admin"].sendall(chatrooms_list.encode())

    def create_chatroom(self, chatroom_name, password, creator_socket):
        if chatroom_name not in self.chatrooms:
            self.chatrooms[chatroom_name] = {"password": bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()), "clients": [creator_socket]}
            creator_socket.sendall(f"Chatroom {chatroom_name} created successfully!".encode())
        else:
            creator_socket.sendall(f"Chatroom {chatroom_name} already exists. Choose another name.".encode())

    def join_chatroom(self, chatroom_name, password, client_socket):
        if chatroom_name in self.chatrooms:
            if bcrypt.checkpw(password.encode("utf-8"), self.chatrooms[chatroom_name]["password"]):
                self.chatrooms[chatroom_name]["clients"].append(client_socket)
                client_socket.sendall(f"Joined chatroom {chatroom_name} successfully!".encode())
            else:
                client_socket.sendall("Invalid password for the chatroom.".encode())
        else:
            client_socket.sendall(f"Chatroom {chatroom_name} does not exist.".encode())

    def broadcast_shared_history(self, sender_socket):
        if sender_socket in self.clients:
            username = self.clients[sender_socket]["username"]
            for client in self.clients:
                if client != sender_socket:
                    try:
                        client.sendall(f"{username}: {str(self.shared_history)}".encode())  # Send shared history to all clients
                    except Exception as e:
                        print(f"Error broadcasting shared history: {e}")

    def update_shared_history(self, new_message):
        self.shared_history.append(new_message)  # Add new message to shared history list
        for client in self.clients:
            self.broadcast_shared_history(client)  # Broadcast updated shared history to all clients

    def broadcast_voice_message(self, audio_data, sender_socket):
        username = self.clients[sender_socket]["username"]
        for client in self.clients:
            if client != sender_socket:
                try:
                    # Encrypt audio_data with the recipient's public key
                    encrypted_data = rsa.encrypt(audio_data, self.public_keys[client])
                    client.sendall(f"{username}: ".encode() + encrypted_data)
                except Exception as e:
                    print(f"Error broadcasting message: {e}")

    def authenticate_user(self, username, password):
        return username in self.clients and bcrypt.checkpw(password.encode("utf-8"), self.admin_password)

def main():
    server = VoiceChatServer()
    server.start_server()

if __name__ == "__main__":
    main()
