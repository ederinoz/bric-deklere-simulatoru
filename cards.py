from enum import IntEnum
import random

class Suit(IntEnum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3

class Rank(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

SUIT_SYMBOLS = {
    Suit.CLUBS: '♣',
    Suit.DIAMONDS: '♦',
    Suit.HEARTS: '♥',
    Suit.SPADES: '♠',
}
SUIT_NAMES_TR = {
    Suit.CLUBS: 'Sinek',
    Suit.DIAMONDS: 'Karo',
    Suit.HEARTS: 'Kupa',
    Suit.SPADES: 'Maça',
}
SUIT_LETTERS = {
    Suit.CLUBS: 'S',
    Suit.DIAMONDS: 'K',
    Suit.HEARTS: 'Ku',
    Suit.SPADES: 'M',
}
RANK_SYMBOLS = {
    Rank.TWO: '2', Rank.THREE: '3', Rank.FOUR: '4', Rank.FIVE: '5',
    Rank.SIX: '6', Rank.SEVEN: '7', Rank.EIGHT: '8', Rank.NINE: '9',
    Rank.TEN: '10', Rank.JACK: 'J', Rank.QUEEN: 'Q',
    Rank.KING: 'K', Rank.ACE: 'A',
}
HCP_TABLE = {Rank.ACE: 4, Rank.KING: 3, Rank.QUEEN: 2, Rank.JACK: 1}


class Card:
    def __init__(self, suit: Suit, rank: Rank):
        self.suit = suit
        self.rank = rank

    def hcp(self) -> int:
        return HCP_TABLE.get(self.rank, 0)

    def __str__(self) -> str:
        return f"{RANK_SYMBOLS[self.rank]}{SUIT_SYMBOLS[self.suit]}"

    def __repr__(self) -> str:
        return str(self)

    def __lt__(self, other) -> bool:
        if self.suit != other.suit:
            return self.suit < other.suit
        return self.rank < other.rank


def deal_hands() -> list[list[Card]]:
    deck = [Card(Suit(s), Rank(r)) for s in range(4) for r in range(2, 15)]
    random.shuffle(deck)
    hands: list[list[Card]] = [[], [], [], []]
    for i, card in enumerate(deck):
        hands[i % 4].append(card)
    for hand in hands:
        hand.sort(key=lambda c: (c.suit, c.rank), reverse=True)
    return hands
