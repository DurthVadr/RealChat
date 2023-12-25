import socket
import threading
import rsa
import pickle
import bcrypt
import threading

host = "192.168.1.196"
port = 9999

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = []
nicknames = []
passwords = {}
admins = ["admin"]  # Add usernames of admin(s) here

public_key, private_key = rsa.newkeys(1024)

server_stop_event = threading.Event()
#server_start_event = threading.Event()

print("Server is listening...")


def stop_server():
    server_stop_event.set() 

    server.close()

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password)

def broadcast(message):
    encrypted_message = rsa.encrypt(message.encode("utf-8"), public_key)
    for client in clients:
        client.send(encrypted_message)

def handle_voice_messages(client):
    while True:
        try:
            voice_message = client.recv(4096)

            if not voice_message:
                break

            decrypted_message = rsa.decrypt(voice_message, private_key)

            broadcast(f"Voice Message from {nicknames[clients.index(client)]:<10}: {decrypted_message.decode()}")

        except Exception as e:
            print(e)
            break

def handle_client(client):
    while True:
        try:
            message = client.recv(1024)
            if not message:
                index = clients.index(client)
                nickname = nicknames[index]
                broadcast(f"{nickname} has left the chat!")
                clients.remove(client)
                nicknames.remove(nickname)
                break
            elif message.startswith(b"/register "):
                _, username, password = message.split()
                if username not in nicknames:
                    hashed_password = hash_password(password.decode())
                    passwords[username] = hashed_password
                    nicknames.append(username)
                    client.send("Registration successful!".encode())
                else:
                    client.send("Username already in use. Please choose another one.".encode())
            elif message.startswith(b"/login "):
                _, username, password = message.split()
                if username in nicknames and check_password(password.decode(), passwords[username]):
                    client.send("Login successful!".encode())
                else:
                    client.send("Invalid username or password.".encode())
            elif message.startswith(b"/ban "):
                if nicknames[clients.index(client)] in admins:
                    _, username_to_ban = message.split()
                    if username_to_ban in nicknames:
                        banned_index = nicknames.index(username_to_ban)
                        banned_client = clients[banned_index]
                        banned_nickname = nicknames[banned_index]

                        broadcast(f"Admin {nicknames[clients.index(client)]} has banned {banned_nickname}!")
                        banned_client.send("You have been banned from the server!".encode())

                        clients.remove(banned_client)
                        nicknames.remove(banned_nickname)
                        banned_client.close()
                    else:
                        client.send("User not found.".encode())
                else:
                    client.send("Permission denied. You are not an admin.".encode())
            else:
                broadcast(f"{nicknames[clients.index(client)]:<10}: {message.decode()}")

        except Exception as e:
            print(e)
            break

def receive(server_stop_event):
    while not server_stop_event.is_set():
        try:
            client, address = server.accept()
            print(f"Connection established with {str(address)}")

            client.send(public_key.save_pkcs1())

            nickname = client.recv(1024).decode()
            password = client.recv(1024).decode()

            if nickname in nicknames:
                client.send("Nickname already in use. Please choose another one.".encode())
                client.close()
                continue

            if nickname.lower() == "admin":
                client.send("Permission denied. This username is reserved for admins.".encode())
                client.close()
                continue

            if not authenticate_user(nickname, password):
                client.send("Invalid username or password.".encode())
                client.close()
                continue

            nicknames.append(nickname)
            clients.append(client)

            print(f"Nickname of the client is {nickname}!")
            broadcast(f"{nickname} has joined the chat!")
            client.send("Connection established!".encode())

            # Start a thread for handling text messages
            thread = threading.Thread(target=handle_client, args=(client,))
            thread.start()

            # Start a thread for handling voice messages
            voice_thread = threading.Thread(target=handle_voice_messages, args=(client,))
            voice_thread.start()

        except Exception as e:
            print(f"Error in receive: {e}")
            break  # Break


def authenticate_user(username, password):
    # Check if the provided username exists and the password is correct
    return username in passwords and check_password(password, passwords[username])


if __name__ == "__main__":
    try:
        receive()
    finally:
        stop_server()
