import socket
import requests
import threading

HOST = socket.gethostbyname(socket.gethostname())
# HOST = '192.168.1.101'
PORT = 65432


def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org')
        return response.text
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None
                            
class VoiceChatServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []
        self.shared_history = []
        self.connected_clients = set()

    def start_server(self):
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen()
        public_ip = get_public_ip()
        print(f"Server started, waiting for connections... public:{public_ip} private:{HOST} port:{PORT} this is branch")

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connected by {addr}")
            self.clients.append(client_socket)
            self.connected_clients.add(addr[0])
            
            for client in self.clients:
                self.get_online_clients(client_socket)
                print(client_socket.getpeername())

            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

            #online_clients_thread = threading.Thread(target=self.get_online_clients, args=(client_socket,))
            #online_clients_thread.start()

    def handle_client(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break

                self.broadcast_voice_message(data, client_socket)

            except ConnectionResetError:
                # Handle disconnection or errors
                break

        self.remove_client(client_socket)
        client_socket.close()

    def get_online_clients(self, requester_socket):
        online_clients = ','.join(self.connected_clients)  # Prepare a comma-separated list of connected client IPs
        try:
            requester_socket.sendall(online_clients.encode())  # Send the list to the requester
        except Exception as e:
            print(f"Error sending online clients list: {e}")


    def remove_client(self, client_socket):
        if client_socket in self.clients:
            self.clients.remove(client_socket)
            addr = client_socket.getpeername()
            print(f"Client {addr} disconnected.")
            self.broadcast_disconnect_message(client_socket)
            
            for client in self.clients:
                if client != client_socket:
                    client.sendall(f"User {addr} has disconnected".encode())
                    self.get_online_clients(client)

            # Remove the disconnected client from connected_clients set
            disconnected_ip = addr[0]
            if disconnected_ip in self.connected_clients:
                self.connected_clients.remove(disconnected_ip)

            print(f"Current connected clients: {self.connected_clients}")
                


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

    def broadcast_voice_message(self, audio_data, sender_socket):
        for client in self.clients:
            if client != sender_socket:
                try:
                    client.sendall(audio_data)
                except Exception as e:
                    print(f"Error broadcasting message: {e}")

def main():
    server = VoiceChatServer()
    server.start_server()

if __name__ == "__main__":
    main()