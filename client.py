import tkinter as tk
from tkinter import scrolledtext, Entry, Button, messagebox, simpledialog
import socket
import threading
import rsa
import pickle
import sounddevice as sd
import numpy as np

host = "192.168.1.196"
port = 9999

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, port))

# Function to send text messages
def send_text_message():
    message = message_entry.get()
    encrypted_message = rsa.encrypt(message.encode("utf-8"), server_public_key)
    client.send(encrypted_message)
    message_entry.delete(0, tk.END)

# Function to send voice messages
def send_voice_message():
    voice_message = np.array([])

    def callback(indata, frames, time, status):
        if status:
            print(status)
        voice_message.extend(indata.flatten())

    with sd.InputStream(callback=callback):
        sd.sleep(5000)  # Record for 5 seconds

    encrypted_voice_message = rsa.encrypt(pickle.dumps(voice_message), server_public_key)
    client.send(encrypted_voice_message)

# Function to receive messages
def receive_messages():
    while True:
        try:
            message = client.recv(4096)

            if not message:
                break

            if message.startswith(b"-----BEGIN RSA PUBLIC KEY-----"):
                # Update the server's public key
                server_public_key = rsa.PublicKey.load_pkcs1(message)
            else:
                # Decrypt and display the message
                decrypted_message = rsa.decrypt(message, client_private_key)
                chat_text.insert(tk.END, decrypted_message.decode() + "\n")
                chat_text.yview(tk.END)

        except Exception as e:
            print(e)
            break

# GUI setup
root = tk.Tk()
root.title("Chat Application")

# Prompt for username and password
username = simpledialog.askstring("Username", "Enter your username")
password = simpledialog.askstring("Password", "Enter your password", show='*')

# Send username and password to the server
client.send(username.encode())
client.send(password.encode())

# Receive the server's public key
server_public_key = rsa.PublicKey.load_pkcs1(client.recv(1024))

# Generate a random private key for the client
client_public_key, client_private_key = rsa.newkeys(1024)

# Send the client's public key to the server
client.send(client_public_key.save_pkcs1())

# Text area for chat messages
chat_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=40, height=15)
chat_text.grid(row=0, column=0, columnspan=2)

# Entry for typing messages
message_entry = Entry(root, width=30)
message_entry.grid(row=1, column=0, padx=5, pady=5)

# Send text message button
send_text_button = Button(root, text="Send Text", command=send_text_message)
send_text_button.grid(row=1, column=1, padx=5, pady=5)

# Send voice message button
send_voice_button = Button(root, text="Send Voice", command=send_voice_message)
send_voice_button.grid(row=2, column=0, columnspan=2, pady=5)

# Start a thread to receive messages
receive_thread = threading.Thread(target=receive_messages)
receive_thread.start()

# Start the Tkinter main loop
root.mainloop()
