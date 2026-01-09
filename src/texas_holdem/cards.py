# src/texas_holdem/cards.py
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import List, Iterable
import random


# ------------------------------------------------------------
# Suit (barve): klub, karo, srce, pik
# Uporabimo IntEnum, ker je priročno za indeksiranje in primerjave.
# ------------------------------------------------------------
class Suit(IntEnum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3

    def symbol(self) -> str:
        # Vrne Unicode simbol za barvo (npr. ♣)
        return "♣♦♥♠"[self.value]

    @classmethod
    def from_char(cls, ch: str) -> "Suit":
        # Pretvori znak (C/D/H/S) v ustrezno Suit vrednost
        ch = ch.upper()
        mapping = {
            "C": cls.CLUBS,
            "D": cls.DIAMONDS,
            "H": cls.HEARTS,
            "S": cls.SPADES,
        }
        try:
            return mapping[ch]
        except KeyError:
            raise ValueError(f"Invalid suit character: {ch!r}")


# ------------------------------------------------------------
# Rank (rangi): 2..10, J, Q, K, A
# Vrednosti so tipične poker vrednosti (Ace=14).
# ------------------------------------------------------------
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

    def label(self) -> str:
        # Kratka oznaka ranga za prikaz (2..9, T, J, Q, K, A)
        lookup = {
            self.TWO: "2",
            self.THREE: "3",
            self.FOUR: "4",
            self.FIVE: "5",
            self.SIX: "6",
            self.SEVEN: "7",
            self.EIGHT: "8",
            self.NINE: "9",
            self.TEN: "T",
            self.JACK: "J",
            self.QUEEN: "Q",
            self.KING: "K",
            self.ACE: "A",
        }
        return lookup[self]

    @classmethod
    def from_char(cls, ch: str) -> "Rank":
        # Pretvori znak (2-9, T, J, Q, K, A) v Rank
        ch = ch.upper()
        mapping = {
            "2": cls.TWO,
            "3": cls.THREE,
            "4": cls.FOUR,
            "5": cls.FIVE,
            "6": cls.SIX,
            "7": cls.SEVEN,
            "8": cls.EIGHT,
            "9": cls.NINE,
            "T": cls.TEN,
            "J": cls.JACK,
            "Q": cls.QUEEN,
            "K": cls.KING,
            "A": cls.ACE,
        }
        try:
            return mapping[ch]
        except KeyError:
            raise ValueError(f"Invalid rank character: {ch!r}")


# ------------------------------------------------------------
# Card: nespremenljiva (immutable) predstavitev karte
# frozen=True -> ne moremo spreminjati rank/suit po ustvaritvi
# order=True  -> omogoča primerjave in sortiranje (po rank, nato suit)
# ------------------------------------------------------------
@dataclass(frozen=True, order=True)
class Card:
    # Nespremenljiva reprezentacija ene karte.
    #
    # Primeri uporabe:
    #   Card(Rank.ACE, Suit.SPADES)
    #   Card.from_str("AS")
    #
    # Opomba:
    #   Card("T", "H") ni dovoljeno, ker pričakujemo Rank in Suit.
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        # Lep izpis: npr. "T♥" ali "A♠"
        return f"{self.rank.label()}{self.suit.symbol()}"

    def __repr__(self) -> str:
        # Razhroščevalni izpis: Card(ACE, SPADES)
        return f"Card({self.rank.name}, {self.suit.name})"

    @classmethod
    def from_str(cls, text: str) -> "Card":
        # Parsanje iz 2-znakovnega zapisa:
        # - prvi znak: rang (2-9, T, J, Q, K, A)
        # - drugi znak: barva (C, D, H, S)
        #
        # Dovolimo tudi male črke (npr. "td", "9h").
        text = text.strip()
        if len(text) != 2:
            raise ValueError(f"Card string must have length 2, got {text!r}")

        r_ch, s_ch = text[0], text[1]
        return cls(rank=Rank.from_char(r_ch), suit=Suit.from_char(s_ch))


# ------------------------------------------------------------
# Deck: standardni komplet 52 kart
# - shuffle() premeša
# - draw() potegne 1 karto (iz vrha/konca seznama)
# - draw_many(n) potegne n kart
# ------------------------------------------------------------
class Deck:
    # Standardni 52-kartni deck.
    #
    # Če v konstruktorju ne podamo kart:
    # - ustvarimo vse kombinacije (Suit x Rank).
    #
    # Če podamo "cards":
    # - ustvarimo deck iz podanega seznama (uporabno za reduced deck).
    def __init__(self, cards: Iterable[Card] | None = None) -> None:
        if cards is None:
            # Poln deck: 4 barve x 13 rangov = 52 kart
            self._cards: List[Card] = [
                Card(rank, suit)
                for suit in Suit
                for rank in Rank
            ]
        else:
            # Deck po meri (npr. že filtriran brez uporabljenih kart)
            self._cards = list(cards)

    def __len__(self) -> int:
        # Omogoča len(deck)
        return len(self._cards)

    def __repr__(self) -> str:
        # Kratek izpis za debug
        return f"Deck({len(self._cards)} cards)"

    def shuffle(self) -> None:
        # Naključno premešamo vrstni red kart v decku (in-place)
        random.shuffle(self._cards)

    def draw(self) -> Card:
        # Potegnemo eno karto (pop z konca seznama).
        # Če je deck prazen, sprožimo napako.
        if not self._cards:
            raise IndexError("Cannot draw from an empty deck")
        return self._cards.pop()

    def draw_many(self, n: int) -> List[Card]:
        # Potegnemo n kart; n mora biti >= 0 in ne več kot preostanek decka
        if n < 0:
            raise ValueError("n must be non-negative")
        if n > len(self._cards):
            raise IndexError(
                f"Cannot draw {n} cards, deck only has {len(self._cards)} left"
            )
        # draw() že odstranjuje iz decka, zato je vrstni red konsistenten
        return [self.draw() for _ in range(n)]

    def peek(self, n: int = 1) -> List[Card]:
        # Pogledamo zadnjih n kart brez odstranjevanja (kopija)
        # Opomba: če je n > len(deck), Python slicing vrne vse karte brez napake,
        # zato je to "mehko" obnašanje (kar je pogosto ok za peek).
        if n < 0:
            raise ValueError("n must be non-negative")
        return self._cards[-n:].copy()

    def remaining(self) -> List[Card]:
        # Vrne kopijo preostalih kart (da od zunaj ne spreminjamo self._cards)
        return self._cards.copy()
