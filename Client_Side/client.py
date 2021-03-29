import socket
from threading import Thread


class Client:
    HEADER_SIZE = 10

    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, ip, port):
        self.client_socket.connect((ip, port))

        Thread(target=self.recv_message).start()
        self.send_message()
        print("Socket closed!")

    def recv_message(self):
        try:
            message_length = int(self.client_socket.recv(Client.HEADER_SIZE))
            message = self.client_socket.recv(message_length)
            print(message.decode('utf-8'))
            self.recv_message()
        except ValueError:
            pass

    def send_message(self):
        try:
            message = input()
            self.client_socket.send(bytes(f'{len(message):<{Client.HEADER_SIZE}}{message}', 'utf-8'))
            self.send_message()
        except ConnectionAbortedError:
            pass


def main():
    client = Client()
    client.connect("localhost", 1234)


if __name__ == '__main__':
    main()
