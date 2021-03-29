import time
from random import randint
from Server_Side.sql import SQLConnection
from Server_Side.hand import Hand


class GameRoom:
    MAX_PLAYERS = DECKS_NUMBER = 6
    SLEEP_TIME = 0.5

    def __init__(self):
        self.sql = SQLConnection()
        self.clients_connected = []  # The first on the list is the admin
        self.clients_ready = []
        self.start = self.round_over = False
        self.burned_cards = {}  # {card: number of appearances}
        self.clients_bets = {}  # {client: bet}
        self.current_client = None

    def join(self, client):
        if self.start or len(self.clients_connected) >= GameRoom.MAX_PLAYERS:
            return False

        self.take_bet_from_player(client)

        # welcome!
        self.send_broadcast(
            f"{client.username} joined the game!\nThere are {len({*self.clients_connected}) + 1}/{GameRoom.MAX_PLAYERS} players in room!")
        self.clients_connected.append(client)
        client.send_message(
            f"""Welcome to {self.clients_connected[0].username}'s game room!
Currently, there are {len({*self.clients_connected})}/{GameRoom.MAX_PLAYERS} players in room.
There are {len(self.clients_ready) + 1} players ready!
Waiting for other players...""")

        return self.waiting_room(client)

    def take_bet_from_player(self, client):

        # get bet
        bet = client.get_answer(
            f"""You have {self.sql.get_staff_on_user(client.username, "score")} points!\nHow much do you wanna bet for the room?""")
        if not bet.isdigit():
            return self.take_bet_from_player(client)
        bet = int(bet)
        if bet <= 0:
            return self.take_bet_from_player(client)

        self.clients_bets[client] = bet
        self.actual_bet_taking(client)

    def actual_bet_taking(self, client):
        # take bet from client
        self.sql.add_staff_2_user(client.username, 'score', -self.clients_bets[client])

    def get_ready_or_back(self, client):
        client.send_message("Hit 'r' for READY and 'b' for BACK!")
        answer = ""
        while not (answer in ("b", "r") or self.start or client is self.clients_connected[0]):
            answer = client.recv_message()

        if answer == "b":
            self.logout(client)
        elif answer == "r":
            self.clients_ready.append(client)
            self.send_broadcast(f"{client} is ready!\nThere are {len(self.clients_ready) + 1} players ready!")
        elif self.start:
            client.send_message("Game already started :(\nWait until next round...")

    def logout(self, client):
        self.sql.add_staff_2_user(client.username, 'score', self.clients_bets[client])
        self.clients_connected.remove(client)
        self.clients_bets.pop(client)
        self.send_broadcast(f"{client} has left the room!")

    def waiting_room(self, client):

        if client is self.clients_connected[0]:  # The admin client
            client.send_message("Hit 's' to START or 'b' for BACK!")
            client_message = ""
            while client_message not in ("s", "b"):
                client_message = client.recv_message()

            # check if exited
            if client_message == "b":
                self.logout(client)
                client.game_room = None
                return

            self.clients_ready.insert(0, client)
            self.start_round()

        else:
            self.get_ready_or_back(client)

            if client not in self.clients_connected:  # exited
                return

            while not (client is self.clients_connected[0] or self.start):  # waiting for the game to start...
                time.sleep(GameRoom.SLEEP_TIME)

            if client is self.clients_connected[0]:  # he is admin now!
                client.game_room = self
                self.clients_connected[0].send_message("You are admin now!")
                self.clients_ready.remove(client)
                return self.waiting_room(client)

            while self.start:  # game started
                time.sleep(GameRoom.SLEEP_TIME)

        # game over
        client.send_message("Get ready for the next round!")
        self.take_bet_from_player(client)
        return self.waiting_room(client)

    def start_round(self):

        self.start = True
        self.send_broadcast(f"""\n---------------------------\nNew round started!
The players are: {self.clients_ready}
It's {self.clients_connected[0]}'s turn!""")

        dealers_hand = Hand(0, self.deal_card, cards=[0])
        dealers_hand.add_card()
        hands = {}  # {client: hand}

        # the actual game
        for client in self.clients_ready:
            client_hand = Hand(self.clients_bets[client], self.deal_card)
            hands[client] = client_hand

            client.send_message(f"The dealer's hand is: {dealers_hand}\nHere is your hand: {client_hand}")

        hands = self.pass_turn(self.clients_ready.copy(), hands)

        while not self.round_over:
            time.sleep(GameRoom.SLEEP_TIME)

        # dealer's card revel
        dealers_hand.cards.pop(0)
        dealer_cards_sum = 0

        while dealer_cards_sum < 17:
            dealers_hand.add_card()
            dealer_cards_sum = dealers_hand.sum_2_highest_if_ace()

        self.send_broadcast(f"The dealer's full cards are: {dealers_hand}")

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

    def pass_turn(self, clients_in_game, hands, split=False):
        if clients_in_game:
            self.current_client = clients_in_game[0]
            current_clients_hand = hands[self.current_client]

            if current_clients_hand.sum_2_highest_if_ace() <= 21:

                # prepare message
                message = ""
                if split:
                    message += f"You currently playing with this hand: {current_clients_hand}!\n"
                message += "What do you wanna do? (stand, hit"
                if len(current_clients_hand.cards) == 2:
                    message += ", double"
                    if current_clients_hand.cards[0] == current_clients_hand.cards[1] or (
                            current_clients_hand.cards[0] >= 10 and current_clients_hand.cards[1] >= 10):
                        message += ", split"

                message += "): "

                move = self.current_client.get_answer(message)  # send message

                if move == "hit":
                    self.hit(current_clients_hand)

                elif move == "double" and "double" in message:

                    self.actual_bet_taking(self.current_client)

                    current_clients_hand.bet *= 2

                    self.hit(current_clients_hand)
                    if current_clients_hand.sum_2_highest_if_ace() > 21:
                        self.current_client.send_message("You are an idiot!")
                    self.send_pass_turn_message(clients_in_game)

                elif move == "split" and "split" in message:

                    self.actual_bet_taking(self.current_client)

                    # actual split
                    splited_hands = current_clients_hand.split()
                    copy_client = self.current_client.__copy__()

                    hands[copy_client] = splited_hands[0]
                    hands[self.current_client] = splited_hands[1]

                    clients_in_game.insert(0, copy_client)

                    # send staff to player
                    self.current_client.send_message(f"""Your hands are: {splited_hands[0]},
{splited_hands[1]}""")
                    self.pass_turn(clients_in_game, hands, split=True)
                    return self.pass_turn(clients_in_game, hands, split=True)

                elif move == "stand":
                    self.send_pass_turn_message(clients_in_game)
                    if split:
                        return
            else:
                self.current_client.send_message("You are Burned!\nWait until next round...")

                self.send_pass_turn_message(clients_in_game)
                if split:
                    return

            return self.pass_turn(clients_in_game, hands)

        self.current_client = None
        self.round_over = True
        return hands

    def hit(self, hand):
        hand.add_card()
        self.current_client.send_message(f"Your hand is: {hand}")

    def send_pass_turn_message(self, clients_in_game):
        clients_in_game.pop(0)

        if clients_in_game:
            self.send_broadcast(f"It's {clients_in_game[0]}'s turn!")
        else:
            self.send_broadcast("Round's OVER!\n")

    def deal_card(self):
        if sum(self.burned_cards.values()) >= GameRoom.DECKS_NUMBER * 3.5:
            self.send_broadcast("Deck shuffled!")
            self.burned_cards = {}

        card = randint(1, 13)

        if card in self.burned_cards.keys():
            self.burned_cards[card] += 1
        else:
            self.burned_cards[card] = 1

        if self.burned_cards[card] > GameRoom.DECKS_NUMBER * 4:
            return self.deal_card()

        return card

    def send_broadcast(self, message):
        for client in self.clients_connected:
            client.send_message(message)
