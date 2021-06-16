import socket
import pickle
from hand import Hand

class Client:
    HEADER_SIZE = 10
    BUFFER_SIZE = 16

    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gui = None

    def connect(self, ip, port):
        self.client_socket.connect((ip, port))

    def recv_message(self):
        full_msg = b''
        new_msg = True
        msg_len = 0
        while len(full_msg) - Client.HEADER_SIZE != msg_len:
            msg = self.client_socket.recv(Client.BUFFER_SIZE)
            if new_msg:
                msg_len = int(msg[:Client.HEADER_SIZE])
                new_msg = False

            full_msg += msg

        # full msg recvd
        print("recved: " + str(pickle.loads(full_msg[Client.HEADER_SIZE:])))
        return pickle.loads(full_msg[Client.HEADER_SIZE:])

    def send_message(self, message):
        print("send:" + str(message))
        bytes_message = pickle.dumps(message)
        self.client_socket.send(bytes(f'{len(bytes_message):<{Client.HEADER_SIZE}}', 'utf-8') + bytes_message)

    def get_answer(self, message):  # makes life easier
        self.send_message(message)
        return self.recv_message()
