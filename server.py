import socket
import requests
import threading

HOST = socket.gethostbyname(socket.gethostname())
PORT_VOICE = 65431
PORT_COMMAND = 65432

class VoiceChatServer:
    def __init__(self):
        self.voice_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.voice_clients = []  
        self.command_clients = []
        self.lock = threading.Lock()  # Add a lock for thread safety

    def start_server(self):
        self.voice_socket.bind((HOST, PORT_VOICE))
        self.voice_socket.listen()

        self.command_socket.bind((HOST, PORT_COMMAND))
        self.command_socket.listen()

       
        print(f"Server started, waiting for connections... private:{HOST} voice port:{PORT_VOICE} command port:{PORT_COMMAND}")

        # Start threads to accept connections for both types of sockets
        voice_thread = threading.Thread(target=self.accept_voice_clients)
        voice_thread.start()

        # No need for a separate thread for command clients
        self.accept_command_clients()

    def accept_voice_clients(self):
        while True:
            client_socket, addr = self.voice_socket.accept()
            print(f"Connected voice client: {addr}")
            self.voice_clients.append(client_socket)

            client_thread = threading.Thread(target=self.handle_voice_client, args=(client_socket,))
            client_thread.start()

    def accept_command_clients(self):
        while True:
            client_socket, addr = self.command_socket.accept()
            print(f"Connected command client: {addr}")
            self.command_clients.append(client_socket)

            client_thread = threading.Thread(target=self.handle_command_client, args=(client_socket,))
            client_thread.start()

    def handle_voice_client(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                with self.lock:
                    self.broadcast_voice_message(data, client_socket)
            except ConnectionResetError:
                break
        self.remove_voice_client(client_socket)
       

    def handle_command_client(self, client_socket):
        while True:
            try:
                command = client_socket.recv(1024).decode()

                if not command:
                    break

                if command == "GET_ONLINE_CLIENTS":
                    self.get_online_clients(client_socket)

            except (ConnectionResetError, BrokenPipeError):
                break
            
        self.remove_command_client(client_socket)

    def remove_voice_client(self, client_socket):
        if client_socket in self.voice_clients:
            self.voice_clients.remove(client_socket)
            addr = client_socket.getpeername()
            print(f"Voice client {addr} disconnected.")
            self.broadcast_online_clients()

    def remove_command_client(self, client_socket):
        with self.lock:
            if client_socket in self.command_clients:
                self.command_clients.remove(client_socket)
                addr = client_socket.getpeername()
                print(f"Command client {addr} disconnected.")
                self.broadcast_online_clients()

    def broadcast_online_clients(self):
        # for c in self.command_clients:
        #     try:
        #         c.sendall(f"{online_clients}".encode())
        #     except Exception as e:
        # print(f"Error broadcasting online clients list: {e}")
        pass

    def broadcast_voice_message(self, audio_data, sender_socket):
        for client in self.voice_clients:
            if client != sender_socket:
                try:
                    client.sendall(audio_data)
                except Exception as e:
                    print(f"Error broadcasting voice message: {e}")

    def get_online_clients(self, requester_socket):
        command_client_addresses = []
        for client in self.command_clients:
            addr = client.getpeername()[0]
            if client == requester_socket:
                addr += " (current)"
            command_client_addresses.append(addr)

        online_clients = ','.join(command_client_addresses)

        try:
            requester_socket.sendall(f"{online_clients}".encode())
        except Exception as e:
            print(f"Error sending online clients list: {e}")


def main():
    server = VoiceChatServer()
    server.start_server()

if __name__ == "__main__":
    main()
