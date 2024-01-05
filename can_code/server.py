import socket

import threading

HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432

class VoiceChatServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []
        self.shared_history = []
        self.rooms = {}
        #self.rooms = []

    def start_server(self):
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen()
        print("Server started, waiting for connections...")

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connected by {addr}")
            self.clients.append(client_socket)

            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def handle_client(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break

                # Handle room-related commands from clients
                if data.startswith(b"CREATE_ROOM"):
                    room_name = data.split(b":")[1].decode()
                    self.create_room(room_name, client_socket)
                elif data == b"GET_ROOMS":
                    client_socket.sendall(str(list(self.rooms.keys())).encode())
                elif data.startswith(b"JOIN_ROOM"):
                    room_name = data.split(b":")[1].decode()
                    self.join_room(room_name, client_socket)
                else:
                    self.broadcast_voice_message(data, client_socket)

            except ConnectionResetError:
                # Handle disconnection or errors
                break

        self.remove_client(client_socket)
        client_socket.close()

    def create_room(self, room_name, client_socket):
        # Logic to create a room with the given name
        if room_name not in self.rooms:
            self.rooms[room_name] = [client_socket]
        else:
            self.rooms[room_name].append(client_socket)
        
        #print(f"Room '{room_name}' created. Clients: {self.rooms[room_name]}")
        print(f"Room '{room_name}' created.")

    def join_room(self, room_name, client_socket):
        # Logic to join a client to a specified room
        if room_name in self.rooms:
            self.rooms[room_name].append(client_socket)
            print(f"Client joined room '{room_name}'. Clients: {self.rooms[room_name]}")
        else:
            print(f"Room '{room_name}' does not exist.")

    def get_room_of_client(self, client_socket):
        for room, clients in self.rooms.items():
            if client_socket in clients:
                return room
        return None

    def remove_client(self, client_socket):
        # Logic to remove a client from rooms upon disconnection
        for room, clients in self.rooms.items():
            if client_socket in clients:
                clients.remove(client_socket)
                print(f"Client disconnected from room. Room '{room}' clients: {self.rooms[room]}")
        if client_socket in self.clients:
            self.clients.remove(client_socket)

    def broadcast_disconnect_message(self, disconnected_socket):
        disconnect_msg = "User has disconnected"
        for client in self.clients:
            if client != disconnected_socket:
                try:
                    client.sendall(disconnect_msg.encode())
                except Exception as e:
                    print(f"Error broadcasting disconnect message: {e}")

    def broadcast_shared_history(self):
        for client in self.clients:
            try:
                client.sendall(str(self.shared_history).encode())  # Send shared history to all clients
            except Exception as e:
                print(f"Error broadcasting shared history: {e}")

    def update_shared_history(self, new_message):
        self.shared_history.append(new_message)  # Add new message to shared history list
        self.broadcast_shared_history()  # Broadcast updated shared history to all clients

    def broadcast_voice_message(self, data, client_socket):
        current_room = self.get_room_of_client(client_socket)

        if current_room:
            for client in self.rooms[current_room]:
                if client != client_socket:
                    try:
                        client.sendall(data)
                    except Exception as e:
                        print(f"Error broadcasting message: {e}")

def main():
    server = VoiceChatServer()
    server.start_server()

if __name__ == "__main__":
    main()
