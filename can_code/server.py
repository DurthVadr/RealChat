import socket
import requests
import threading

HOST = socket.gethostbyname(socket.gethostname())
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

            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

            online_clients_thread = threading.Thread(target=self.get_online_clients, args=(client_socket,))
            online_clients_thread.start()

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

    def get_online_clients(self, requesting_client):
        online_clients = list(self.connected_clients - {requesting_client.getpeername()[0]})
        online_clients_str = ",".join(online_clients)
        try:
            requesting_client.sendall(online_clients_str.encode())
        except Exception as e:
            print(f"Error sending online clients list: {e}")


    def remove_client(self, client_socket):
        if client_socket in self.clients:
            self.clients.remove(client_socket)
            print(f"Client {client_socket.getpeername()} disconnected.")
            self.broadcast_disconnect_message(client_socket)

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
