from game_room import GameRoom


class Client:
    HEADER_SIZE = 10

    def __init__(self, client_socket, username):
        self.socket = client_socket
        self.username = username
        self.game_room = None

    def recv_message(self):
        try:
            message_length = int(self.socket.recv(Client.HEADER_SIZE))
            message = self.socket.recv(message_length)
            return message.decode('utf-8')
        except ConnectionResetError:
            print(f"{self} loged out!")
            return

    def send_message(self, message):
        self.socket.send(bytes(f'{len(message):<{Client.HEADER_SIZE}}{message}', 'utf-8'))

    def get_answer(self, message):
        self.send_message(message)
        return self.recv_message()

    def open_game_room(self):
        self.game_room = GameRoom()

    def __eq__(self, other):
        return self.username == other.username

    def __str__(self):
        return self.username

    def __hash__(self):
        return self.username.__hash__()

    def __copy__(self):
        return Client(self.socket, self.username)

    __repr__ = __str__
