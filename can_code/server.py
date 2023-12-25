import socket


HOST = '10.200.86.151'  # Put your IP or 'localhost'
PORT = 65432  # Port

# Create a socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    print("Server started, waiting for connections...")
    server_socket.listen()
    
    
    conn, addr = server_socket.accept()
    print(f"Connected by {addr}")
    
    
    audio_frames = []
    
    # Receive audio from client
    while True:
        data = conn.recv(1024)
        if not data:
            break
        audio_frames.append(data)
    
    
    import pyaudio
    
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, output=True,
                        frames_per_buffer=CHUNK)
    
    for frame in audio_frames:
        stream.write(frame)
    
    stream.stop_stream()
    stream.close()
    audio.terminate()
