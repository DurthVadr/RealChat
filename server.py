import socket
import threading
import rsa

public_key,private_key = rsa.newkeys(1024)

p_key = dict()

HOST = socket.gethostbyname(socket.gethostname())
PORT_VOICE = 65431
PORT_COMMAND = 65432

class VoiceChatServer:
    def __init__(self):
        self.voice_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.voice_clients = []  
        self.command_clients = []
        self.lock = threading.Lock()  
        self.whisper_mode = False
        self.whisper_receiver = None
        self.username_dict = {}  # Dictionary to store usernames associated with command clients
        

    def start_server(self):
        self.voice_socket.bind((HOST, PORT_VOICE))
        self.voice_socket.listen()

        self.command_socket.bind((HOST, PORT_COMMAND))
        self.command_socket.listen()

        print(f"Server started, waiting for connections... private:{HOST} voice port:{PORT_VOICE} command port:{PORT_COMMAND}")

        voice_thread = threading.Thread(target=self.accept_voice_clients)
        voice_thread.start()

        self.accept_command_clients()

    def accept_voice_clients(self):
        while True:
            client_socket, addr = self.voice_socket.accept()
            print(f"Connected voice client: {addr}")
            self.voice_clients.append(client_socket)   

            client_thread = threading.Thread(target=self.handle_voice_client, args=(client_socket,))
            client_thread.start()


    # encrypt edilcek
    def accept_command_clients(self):
        while True:
            client_socket, addr = self.command_socket.accept()
            
            command_id = addr[1]
            voice_id = command_id-1 
            self.username_dict[client_socket] = ("username", voice_id, command_id)         

            client_socket.send(public_key.save_pkcs1("PEM"))
            p_key[client_socket] = rsa.PublicKey.load_pkcs1(client_socket.recv(1024))
            print("pub_key: ", public_key)
            print("priv_key: ", private_key)

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


     # encrypt edilcek
    def handle_command_client(self, client_socket):
        while True:
            try:
                #print("Non decrypted: ", client_socket.recv(1024))
                print("0")
                data = client_socket.recv(1024)
         
                if not data:
                    print(f"Client {client_socket.getpeername()} disconnected.")
                    break  # Exit loop on client disconnect
                print(data)
                message = rsa.decrypt(data, private_key)
                print("2")
                command = message.decode()
                print("message: ", message)
                print(command)


                if not command:
                    break

                if command == "GET_ONLINE_CLIENTS":
                    self.get_online_clients(client_socket)

                if command.startswith("WHISPER:"):
                    receiver_username = command.split(":")[1]
                    self.whisper_mode = True
                    self.whisper_receiver = receiver_username
                    print(f"Whisper mode enabled. Receiver: {receiver_username}")

                if command.startswith("REGISTER_USERNAME:"):
                    username = command.split(":")[1]
                    self.register_username(client_socket, username)
           
            except ConnectionResetError:
                print(f"Client {client_socket.getpeername()} forcibly closed the connection.")
                break
            except rsa.pkcs1.DecryptionError:
                print(f"Decryption failed for client {client_socket.getpeername()}.")

        self.remove_command_client(client_socket)

    def register_username(self, client_socket, username):
        with self.lock:
            self.username_dict[client_socket] = (username, self.username_dict[client_socket][1], self.username_dict[client_socket][2])
            print(f"Registered username '{username}' for client socket info {client_socket}")
            self.broadcast_online_clients()

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
                del self.username_dict[client_socket]
                self.broadcast_online_clients()


    #encrypt
    def broadcast_online_clients(self):
        online_clients = ','.join([info[0] for info in self.username_dict.values() if info[0]])
        print(f"Online clients: {online_clients}")

        for c in self.command_clients:
            try:
                c.sendall(rsa.encrypt(f"ONLINE_CLIENTS:{online_clients}".encode(), p_key[c]))
                print(f"Broadcasted online clients list to {c.getpeername()[0]}")
            except Exception as e:
                print(f"Error broadcasting online clients list: {e}")

    def broadcast_voice_message(self, audio_data, sender_socket):
        if self.whisper_mode:
            receiver_socket = self.get_voice_socket_by_username(self.whisper_receiver)
            if receiver_socket:
                print(f"Sending whisper message to {receiver_socket}")
                receiver_socket.sendall(audio_data)
            self.whisper_mode = False  
        else:
            for client in self.voice_clients:
                if client != sender_socket:
                    try:
                        client.sendall(audio_data)
                    except Exception as e:
                        print(f"Error broadcasting voice message: {e}")

    def get_online_clients(self, requester_socket):
        command_client_usernames = [self.username_dict[client] for client in self.username_dict]
        online_clients = ','.join(command_client_usernames)

        try:
            requester_socket.sendall(rsa.encrypt(f"ONLINE_CLIENTS:{online_clients}".encode(), p_key[requester_socket]))
                        #client_.send(rsa.encrypt("REFUSED".encode(),p_key[client_]))
            print(f"Sent online clients list to {requester_socket.getpeername()[0]}")
        except Exception as e:
            print(f"Error sending online clients list: {e}")

    def find_client_by_id(self, client_id):
        for client_socket in self.voice_clients:
            if client_socket.getpeername()[0] == client_id:
                return client_socket
        return None

    
    def get_voice_socket_by_username(self, username): ##used in whisper
        for client_socket, info in self.username_dict.items():
            if info[0] == username:
                voice_id = info[1]
                return self.find_client_by_id(voice_id)
        return None



def main():
    server = VoiceChatServer()
    server.start_server()

if __name__ == "__main__":
    main()