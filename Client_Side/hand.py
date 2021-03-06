import random


class Hand:

    def __init__(self, bet, cards=[]):
        self.bet = bet
        self.cards = cards
        self.suit_cards = []
        self.set_suit_cards()
        if not cards:
            for i in range(2):
                self.add_card()

    def set_suit_cards(self):
        for card_num in self.cards:
            self.suit_cards.append((Hand.add_suit(card_num)))

    @staticmethod
    def add_suit(card_num):
        return str(card_num) + random.choice(random.choice(('C', 'H', 'S', 'D')))

    def sum_2_highest_if_ace(self):
        cards_sum = self.sum_cards()
        if cards_sum.__class__.__name__ == 'tuple':
            cards_sum = cards_sum[1]

        return cards_sum

    def sum_cards(self):
        ace_in_cards = False

        cards_sum = 0

        for card in self.cards:
            if card == 1:
                ace_in_cards = True

            if card > 10:
                cards_sum += 10
            else:
                cards_sum += card

        if ace_in_cards:
            ace_sum_cards = (cards_sum, cards_sum + 10)
            if ace_sum_cards[1] <= 21:
                return ace_sum_cards

        return cards_sum

    def add_card(self):
        card_num = random.randint(1, 13)
        self.cards.append(card_num)
        self.suit_cards.append((Hand.add_suit(card_num)))
