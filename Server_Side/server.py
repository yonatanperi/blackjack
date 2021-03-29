from threading import Thread
from Server_Side.client_room import ClientRoom
from Server_Side.client_object import Client
import socket


class Server:

    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []

    def start(self, ip, port):
        self.server_socket.bind((ip, port))
        self.server_socket.listen(5)
        print(f"Server is listening on {ip} on port {port}")

        while True:
            client_socket = self.server_socket.accept()[0]
            print("Client connected!")
            Thread(target=ClientRoom(Client(client_socket, None), self).authenticate_client).start()

    def login(self, client):
        if client in self.clients:
            return False

        self.clients.append(client)
        print(f"{client} loged in!")
        return True

    def get_game_room(self, username):
        for client in self.clients:
            if client.username == username:
                return client.game_room

        return None


def main():
    server = Server()
    server.start("localhost", 1234)


if __name__ == '__main__':
    main()
