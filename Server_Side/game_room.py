import time
from sql import SQLConnection
from hand import Hand


class GameRoom:
    MAX_PLAYERS = DECKS_NUMBER = 6
    SLEEP_TIME = 0.5

    def __init__(self):
        self.sql = SQLConnection()
        self.clients_connected = []  # The first on the list is the admin
        self.clients_ready = []
        self.start = self.round_over = False
        self.clients_bets = {}  # {client: bet}
        self.current_client = None

    def join(self, client):
        if self.start or len(self.clients_connected) >= GameRoom.MAX_PLAYERS:
            return False

        # welcome!
        self.clients_connected.append(client)
        client.send_message(f"""
        Welcome to {self.clients_connected[0].username}'s game room!
        Currently, there are {len({*self.clients_connected})}/{GameRoom.MAX_PLAYERS} players in room.
        There are {len(self.clients_ready)} players ready!
        You have {self.sql.get_staff_on_user(client.username, "score")} points!
        Waiting for other players...""")

        self.take_bet_from_player(client)

        return self.waiting_room(client)

    def take_bet_from_player(self, client):

        # get bet
        bet = client.recv_message()
        if not bet.isdigit():
            client.send_message(False)
            return self.take_bet_from_player(client)
        bet = int(bet)
        if bet <= 0:
            client.send_message(False)
            return self.take_bet_from_player(client)

        client.send_message(True)
        self.clients_bets[client] = bet
        self.actual_bet_taking(client)

    def actual_bet_taking(self, client):
        # take bet from client
        self.sql.add_staff_2_user(client.username, 'score', -self.clients_bets[client])

    def logout(self, client):
        self.sql.add_staff_2_user(client.username, 'score', self.clients_bets[client])
        self.clients_connected.remove(client)
        self.clients_bets.pop(client)
        self.send_broadcast(f"{client} has left the room!")

    def waiting_room(self, client):

        if client is self.clients_connected[0]:  # The admin client
            ready = client.get_answer(True)  # is admin
            client.send_message("Connected successfully!")
            if ready:
                self.send_broadcast(True)  # send the game just started
                self.clients_ready.insert(0, client)
                self.start_round()
            else:
                self.logout(client)
                client.game_room = None
                return

        else:
            ready = client.get_answer(False)  # is admin

            if ready:
                self.clients_ready.append(client)
                while not self.start:  # waiting for the game to start...
                    time.sleep(GameRoom.SLEEP_TIME)
                    if client is self.clients_connected[0]:  # admin loged out
                        self.logout(client)
                        return

                client.send_message("Connected successfully!")

                while self.start:  # game started
                    time.sleep(GameRoom.SLEEP_TIME)
            else:
                self.logout(client)
                return

        # game over
        self.take_bet_from_player(client)
        return self.waiting_room(client)

    def start_round(self):

        self.start = True

        dealers_hand = Hand(0, cards=[0])
        dealers_hand.add_card()
        hands = {}  # {client: hand}

        # the actual game
        for client in self.clients_ready:
            client.send_message(client.username)

            clients_hand = Hand(self.clients_bets[client])
            hands[client] = clients_hand

            client.send_message((dealers_hand, clients_hand))

        self.send_broadcast(f"""\n---------------------------\nNew round started!
The players are: {self.clients_ready}
It's {self.clients_ready[0]}'s turn!""")
        hands = self.pass_turn(self.clients_ready.copy(), hands)

        while not self.round_over:
            time.sleep(GameRoom.SLEEP_TIME)

        # dealer's card revel
        dealers_hand.cards.pop(0)
        dealers_hand.suit_cards.pop(0)
        dealer_cards_sum = 0

        # add cards to dealer
        while dealer_cards_sum < 17:
            dealers_hand.add_card()
            dealer_cards_sum = dealers_hand.sum_2_highest_if_ace()

        self.send_broadcast(dealers_hand)

        # winners & losers
        winners = []
        losers = []
        for client, client_hand in hands.items():
            client_cards_sum = client_hand.sum_2_highest_if_ace()

            if client_cards_sum < dealer_cards_sum <= 21 or client_cards_sum > 21:
                losers.append(client)
                self.sql.add_staff_2_user(client.username, 'lose', 1)
                client.send_message(f"You LOST!")

            elif client_cards_sum == dealer_cards_sum:
                self.sql.add_staff_2_user(client.username, 'score', client_hand.bet)
                client.send_message(f"PUSH!")

            else:
                winners.append(client)
                self.sql.add_staff_2_user(client.username, 'win', 1)
                if client_cards_sum == 21 and len(client_hand.cards) == 2:
                    self.sql.add_staff_2_user(client.username, 'score', client_hand.bet * 2.5)
                    client.send_message(f"Winner winner chicken dinner!")
                else:
                    self.sql.add_staff_2_user(client.username, 'score', client_hand.bet * 2)
                    client.send_message(f"You WON!")

            client.send_message(f"You have {self.sql.get_staff_on_user(client.username, 'score')} points!\n")

        self.send_broadcast(f"The WINNERS are: {winners}!\n The LOSERS are: {losers}\n------------------------------\n")

        # reset some staff
        self.start = False
        self.clients_ready = []
        self.clients_bets = {}
        self.current_client = None

    def pass_turn(self, clients_in_game, hands):
        if clients_in_game:
            self.current_client = clients_in_game[0]
            current_clients_hand = hands[self.current_client]

            if current_clients_hand.sum_2_highest_if_ace() <= 21:

                # prepare message
                game_options_num = 2  # hit, stand
                if len(current_clients_hand.cards) == 2:
                    game_options_num = 3  # hit, stand, double

                move = self.current_client.get_answer(game_options_num)  # send message

                if move == "hit":
                    self.hit(current_clients_hand)

                elif move == "double" and game_options_num == 3:

                    self.actual_bet_taking(self.current_client)

                    current_clients_hand.bet *= 2

                    self.hit(current_clients_hand)
                    if current_clients_hand.sum_2_highest_if_ace() > 21:
                        self.current_client.send_message("You are an idiot!")
                    self.send_pass_turn_message(clients_in_game)

                elif move == "stand":
                    self.send_pass_turn_message(clients_in_game)
            else:
                self.current_client.send_message("You are Burned!\nWait until next round...")

                self.send_pass_turn_message(clients_in_game)

            return self.pass_turn(clients_in_game, hands)

        self.current_client = None
        self.round_over = True
        return hands

    def hit(self, hand):
        hand.add_card()
        self.current_client.send_message(hand)

    def send_pass_turn_message(self, clients_in_game):
        clients_in_game.pop(0)

        if clients_in_game:
            self.send_broadcast(f"It's {clients_in_game[0]}'s turn!")
        else:
            self.send_broadcast("Round's OVER!\n")

    def send_broadcast(self, message):
        for client in self.clients_ready:
            client.send_message(message)
