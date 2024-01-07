import socket
import requests
import threading

HOST = socket.gethostbyname(socket.gethostname())
PORT_VOICE = 65431  # Port for voice data
PORT_COMMAND = 65432  # Port for command data


def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org')
        return response.text
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None
                            
class VoiceChatServer:
    def __init__(self):
        self.voice_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.voice_clients = []  # Store voice clients separately
        self.command_clients = {}  # Store command clients separately
        self.connected_clients = set()

    def start_server(self):
        self.voice_socket.bind((HOST, PORT_VOICE))
        self.voice_socket.listen()

        self.command_socket.bind((HOST, PORT_COMMAND))
        self.command_socket.listen()

        public_ip = get_public_ip()
        print(f"Server started, waiting for connections... public:{public_ip} private:{HOST} voice port:{PORT_VOICE} command port:{PORT_COMMAND}")

        # Start threads to accept connections for both types of sockets
        voice_thread = threading.Thread(target=self.accept_voice_clients)
        voice_thread.start()

        command_thread = threading.Thread(target=self.accept_command_clients)
        command_thread.start()

    def accept_voice_clients(self):
        while True:
            client_socket, addr = self.voice_socket.accept()
            print(f"Connected voice client: {addr}")
            self.voice_clients.append(client_socket)
            self.connected_clients.add(addr[0])

            client_thread = threading.Thread(target=self.handle_voice_client, args=(client_socket,))
            client_thread.start()

    def accept_command_clients(self):
        while True:
            client_socket, addr = self.command_socket.accept()
            print(f"Connected command client: {addr}")
            self.command_clients[addr] = client_socket

            client_thread = threading.Thread(target=self.handle_command_client, args=(client_socket,))
            client_thread.start()
    
    # Handle voice client messages
    def handle_voice_client(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break

                self.broadcast_voice_message(data, client_socket)

            except ConnectionResetError:
                # Handle disconnection or errors
                break

        self.remove_voice_client(client_socket)
                
    def handle_command_client(self, client_socket):
        while True:
            try:
                command = client_socket.recv(1024).decode()
                if command == "GET_ONLINE_CLIENTS":
                    self.get_online_clients(client_socket)
                # Add more command handling if necessary
            except ConnectionResetError:
                # Handle disconnection or errors
                break

    # Remove voice client
    def remove_voice_client(self, client_socket):
        if client_socket in self.voice_clients:
            self.voice_clients.remove(client_socket)
            addr = client_socket.getpeername()
            print(f"Voice client {addr} disconnected.")
            self.connected_clients.remove(addr[0])  # Remove the disconnected client from connected_clients set
            self.broadcast_online_clients()  # Update clients with the new online client list

    def remove_command_client(self, client_socket):
        try:
            addr = next(key for key, value in self.command_clients.items() if value == client_socket)
            del self.command_clients[addr]
            print(f"Command client {addr} disconnected.")
            self.broadcast_online_clients()
        except StopIteration:
            pass

    # Broadcast voice messages to all clients
# Broadcast voice messages to all clients
    def broadcast_voice_message(self, audio_data, sender_socket):
        for client in self.voice_clients:
            if client != sender_socket:
                try:
                    client.sendall(audio_data)
                except Exception as e:
                    print(f"Error broadcasting voice message: {e}")

    def get_online_clients(self, requester_socket):
        online_clients = ','.join(client[0] for client in self.command_clients.keys())
        try:
            requester_socket.sendall(f"ONLINE_CLIENTS:{online_clients}".encode())
        except Exception as e:
            print(f"Error sending online clients list: {e}")

    def broadcast_online_clients(self):
        online_clients = ','.join(client[0] for client in self.command_clients.keys())
        for client_socket in self.command_clients.values():
            try:
                client_socket.sendall(f"ONLINE_CLIENTS:{online_clients}".encode())
            except Exception as e:
                print(f"Error broadcasting online clients list: {e}")

    def update_shared_history(self, new_message):
        self.shared_history.append(new_message)  # Add new message to shared history list
        self.broadcast_shared_history()  # Broadcast updated shared history to all clients

    def broadcast_online_clients(self):
        online_clients = ','.join(self.connected_clients)  # Prepare a comma-separated list of connected client IPs
        for client in self.clients:
            try:
                client.sendall(("ONLINE_CLIENTS:" + online_clients).encode())  # Send the list to all clients
            except Exception as e:
                print(f"Error broadcasting online clients list: {e}")

def main():
    server = VoiceChatServer()
    server.start_server()

if __name__ == "__main__":
    main()