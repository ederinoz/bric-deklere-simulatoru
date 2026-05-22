import streamlit as st
from cards import Card, Suit, Rank, SUIT_SYMBOLS, SUIT_NAMES_TR, RANK_SYMBOLS

# Kartların gerçek TBF puan değerlerini buraya sabitleyerek dışarıdaki hataları engelliyoruz
TRUE_HCP_VALUES = {
    Rank.ACE: 4,
    Rank.KING: 3,
    Rank.QUEEN: 2,
    Rank.JACK: 1
}

class HandEvaluator:
    def __init__(self, cards: list[Card]):
        self.cards = cards
        self._by_suit: dict[Suit, list[Card]] = {s: [] for s in Suit}
        for card in cards:
            self._by_suit[card.suit].append(card)

    def hcp(self) -> int:
        # Dışarıdaki c.hcp() yerine doğrudan buradaki garantili tablodan okuyoruz
        # Böylece 10'lu gibi kartlar asla haksız puan alamaz
        return sum(TRUE_HCP_VALUES.get(c.rank, 0) for c in self.cards)

    def length(self, suit: Suit) -> int:
        return len(self._by_suit[suit])

    def distribution_points(self) -> int:
        dp = 0
        for suit in Suit:
            ln = self.length(suit)
            if ln == 0:
                dp += 3  # Şanzman
            elif ln == 1:
                dp += 2  # Teketon
            elif ln == 2:
                dp += 1  # Dubleton
        return dp

    def total_points(self) -> int:
        return self.hcp() + self.distribution_points()

    def suit_cards(self, suit: Suit) -> list[Card]:
        return self._by_suit[suit]

    def longest_suit(self) -> Suit:
        return max(Suit, key=lambda s: (self.length(s), s))

    def longest_major(self) -> Suit | None:
        majors = [Suit.SPADES, Suit.HEARTS]
        best = max(majors, key=lambda s: self.length(s))
        if self.length(best) >= 4:
            return best
        return None

    def is_balanced(self) -> bool:
        lengths = sorted(self.length(s) for s in Suit)
        if lengths[0] == 0:
            return False
        if lengths[0] == 1:
            return False
        if lengths[3] > 5:
            return False
        return True

    def has_stoppers(self, suits: list[Suit]) -> bool:
        for suit in suits:
            cards = self._by_suit[suit]
            ranks = [c.rank for c in cards]
            if Rank.ACE in ranks:
                continue
            if Rank.KING in ranks and len(ranks) >= 2:
                continue
            if Rank.QUEEN in ranks and len(ranks) >= 3:
                continue
            return False
        return True

    def controls(self, trump_suit: Suit) -> int:
        aces = sum(1 for c in self.cards if c.rank == Rank.ACE)
        trump_king = any(c.rank == Rank.KING and c.suit == trump_suit for c in self.cards)
        return aces + (1 if trump_king else 0)

    def has_trump_queen(self, trump_suit: Suit) -> bool:
        return any(c.rank == Rank.QUEEN and c.suit == trump_suit for c in self.cards)

    def key_cards(self, trump_suit: Suit) -> int:
        aces = sum(1 for c in self.cards if c.rank == Rank.ACE)
        trump_king = any(c.rank == Rank.KING and c.suit == trump_suit for c in self.cards)
        return aces + (1 if trump_king else 0)

    def format_hand(self) -> str:
        lines = []
        for suit in reversed(list(Suit)):
            cards = sorted(self._by_suit[suit], key=lambda c: c.rank, reverse=True)
            card_str = ' '.join(RANK_SYMBOLS[c.rank] for c in cards) if cards else '-'
            lines.append(f"  {SUIT_SYMBOLS[suit]}  {card_str}")
        lines.append(f"  HKP: {self.hcp()}  |  Toplam: {self.total_points()}")
        return '\n'.join(lines)