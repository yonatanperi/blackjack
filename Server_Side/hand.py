class Hand:
    NUMBER_TO_CARD = {
        0: "?",
        1: "A",
        11: "J",
        12: "Q",
        13: "K"
    }

    def __init__(self, bet, deal_card, cards=None):
        self.bet = bet
        self._deal_card = deal_card
        self.cards = cards
        if not self.cards:
            self.cards = [deal_card(), deal_card()]

    def __str__(self):
        return f"{self.cards_2_letters()} > {self.sum_cards()}"

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

    def cards_2_letters(self):
        letter_cards = []

        for card in self.cards:
            if card in Hand.NUMBER_TO_CARD.keys():
                letter_cards.append(Hand.NUMBER_TO_CARD[card])
            else:
                letter_cards.append(card)

        return letter_cards

    def split(self):
        # assuming the cards are (#1, #1)
        hands = []
        for i in range(2):
            hands.append(Hand(self.bet, self._deal_card, cards=[self.cards[i]]))
            hands[i].add_card()

        return hands

    def add_card(self):
        self.cards.append(self._deal_card())
