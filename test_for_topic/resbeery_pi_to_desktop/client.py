import socket

HOST = "100.79.64.120"
PORT = 5000
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

client.sendall(b"Hello Raspberry Pi")

print(client.recv(1024).decode())

client.close()