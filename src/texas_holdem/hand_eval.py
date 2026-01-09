# src/texas_holdem/hand_eval.py
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable, Tuple
from collections import Counter
from itertools import combinations

from .cards import Card


# ------------------------------------------------------------
# Kategorije poker kombinacij (urejene po moči)
# Večja vrednost = močnejša kombinacija
# ------------------------------------------------------------
class HandCategory(IntEnum):
    HIGH_CARD = 0
    ONE_PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8


# ------------------------------------------------------------
# Predstavitev ovrednotene roke, ki je primerljiva (order=True)
#
# Primerjava poteka leksikografsko po:
#   (category, tiebreaker)
# - Najprej odloča kategorija (moč kombinacije)
# - Če je kategorija enaka, odloča tiebreaker (od najpomembnejšega do najmanjšega)
# ------------------------------------------------------------
@dataclass(frozen=True, order=True)
class HandValue:
    category: HandCategory
    tiebreaker: Tuple[int, ...]


# ---------------------------------------------------------------------------
# Funkcije za človeku berljive opise rangov in kombinacij
# ---------------------------------------------------------------------------

def _rank_word(rank: int) -> str:
    # Enkratna oblika ranga (14 -> Ace, 13 -> King, ...)
    return {
        2: "Two",
        3: "Three",
        4: "Four",
        5: "Five",
        6: "Six",
        7: "Seven",
        8: "Eight",
        9: "Nine",
        10: "Ten",
        11: "Jack",
        12: "Queen",
        13: "King",
        14: "Ace",
    }[rank]


def _rank_word_plural(rank: int) -> str:
    # Množinska oblika ranga (14 -> Aces, 13 -> Kings, ...)
    return {
        2: "Twos",
        3: "Threes",
        4: "Fours",
        5: "Fives",
        6: "Sixes",
        7: "Sevens",
        8: "Eights",
        9: "Nines",
        10: "Tens",
        11: "Jacks",
        12: "Queens",
        13: "Kings",
        14: "Aces",
    }[rank]


def describe_hand_value(hv: HandValue) -> str:
    # Pretvori HandValue v človeku berljiv opis (npr. "Full house, Aces over Tens")
    cat = hv.category
    r = list(hv.tiebreaker)

    if cat == HandCategory.STRAIGHT_FLUSH:
        # tiebreaker: (high_card_of_straight,)
        high = r[0]
        if high == 14:
            return "Royal flush"
        if high == 5:
            return "Five-high straight flush"
        return f"{_rank_word(high)}-high straight flush"

    if cat == HandCategory.FOUR_OF_A_KIND:
        # tiebreaker: (rank_of_quads, kicker)
        four, kicker = r
        return f"Four of a kind, {_rank_word_plural(four)} with {_rank_word(kicker)} kicker"

    if cat == HandCategory.FULL_HOUSE:
        # tiebreaker: (rank_of_trips, rank_of_pair)
        trip, pair = r
        return f"Full house, {_rank_word_plural(trip)} over {_rank_word_plural(pair)}"

    if cat == HandCategory.FLUSH:
        # tiebreaker: (rangi v flushu od najvišjega do najnižjega)
        ranks_words = " ".join(_rank_word(x) for x in r)
        return f"Flush, {ranks_words}"

    if cat == HandCategory.STRAIGHT:
        # tiebreaker: (high_card_of_straight,), wheel A-2-3-4-5 ima high=5
        high = r[0]
        if high == 5:
            return "Five-high straight"
        return f"{_rank_word(high)}-high straight"

    if cat == HandCategory.THREE_OF_A_KIND:
        # tiebreaker: (rank_of_trips, kicker1, kicker2)
        trip = r[0]
        kickers = r[1:]
        if kickers:
            kickers_words = ", ".join(_rank_word(k) for k in kickers)
            return f"Three of a kind, {_rank_word_plural(trip)} with {kickers_words} kickers"
        return f"Three of a kind, {_rank_word_plural(trip)}"

    if cat == HandCategory.TWO_PAIR:
        # tiebreaker: (higher_pair, lower_pair, kicker)
        high_pair, low_pair, kicker = r
        return (
            f"Two pair, {_rank_word_plural(high_pair)} and "
            f"{_rank_word_plural(low_pair)} with {_rank_word(kicker)} kicker"
        )

    if cat == HandCategory.ONE_PAIR:
        # tiebreaker: (pair_rank, kicker1, kicker2, kicker3)
        pair_rank = r[0]
        kickers = r[1:]
        if kickers:
            kickers_words = ", ".join(_rank_word(k) for k in kickers)
            return f"Pair of {_rank_word_plural(pair_rank)} with {kickers_words} kickers"
        return f"Pair of {_rank_word_plural(pair_rank)}"

    if cat == HandCategory.HIGH_CARD:
        # tiebreaker: (najvišji, ..., najnižji)
        high = r[0]
        ranks_words = ", ".join(_rank_word(x) for x in r)
        return f"{_rank_word(high)}-high ({ranks_words})"

    # Fallback za debug (ne bi se smelo zgoditi)
    return f"{cat.name} {hv.tiebreaker}"


# ---------------------------------------------------------------------------
# Interno: ovrednoti NATANKO 5 kart
# ---------------------------------------------------------------------------

def _evaluate_5cards(cards: Iterable[Card]) -> HandValue:
    # Ovrednoti moč natanko 5 kart in vrne HandValue (primerljivo z <, >, ==)
    cards = list(cards)
    if len(cards) != 5:
        raise ValueError("Exactly 5 cards are required for _evaluate_5cards")

    # Rangi kot int (Ace=14, King=13, ...)
    ranks = [int(c.rank) for c in cards]
    suits = [c.suit for c in cards]

    # Štejemo pojavitve rangov (pare, trisi, full house, ...)
    rank_counts = Counter(ranks)

    # Podpis številčnosti rangov (npr. (3,2) = full house, (2,2,1)=two pair)
    counts_signature = tuple(sorted(rank_counts.values(), reverse=True))

    # Flush: vseh 5 kart iste barve
    is_flush = len(set(suits)) == 1

    # Straight: 5 različnih rangov, zaporedje; upoštevamo tudi wheel A-2-3-4-5
    unique_ranks = sorted(set(ranks), reverse=True)
    is_straight = False
    straight_high = None

    if len(unique_ranks) == 5:
        # Poseben primer: A-2-3-4-5 (wheel) -> obravnavamo kot 5-high straight
        if unique_ranks == [14, 5, 4, 3, 2]:
            is_straight = True
            straight_high = 5
        # Normalen straight: max - min == 4 (ker so vsi različni)
        elif unique_ranks[0] - unique_ranks[4] == 4:
            is_straight = True
            straight_high = unique_ranks[0]

    # Straight flush
    if is_flush and is_straight:
        return HandValue(HandCategory.STRAIGHT_FLUSH, (straight_high,))

    # Four of a kind
    if counts_signature == (4, 1):
        four_rank = max(rank for rank, cnt in rank_counts.items() if cnt == 4)
        kicker = max(rank for rank, cnt in rank_counts.items() if cnt == 1)
        return HandValue(HandCategory.FOUR_OF_A_KIND, (four_rank, kicker))

    # Full house
    if counts_signature == (3, 2):
        trip_rank = max(rank for rank, cnt in rank_counts.items() if cnt == 3)
        pair_rank = max(rank for rank, cnt in rank_counts.items() if cnt == 2)
        return HandValue(HandCategory.FULL_HOUSE, (trip_rank, pair_rank))

    # Flush
    if is_flush:
        ordered = tuple(sorted(ranks, reverse=True))
        return HandValue(HandCategory.FLUSH, ordered)

    # Straight
    if is_straight:
        return HandValue(HandCategory.STRAIGHT, (straight_high,))

    # Three of a kind
    if counts_signature == (3, 1, 1):
        trip_rank = max(rank for rank, cnt in rank_counts.items() if cnt == 3)
        kickers = sorted((rank for rank, cnt in rank_counts.items() if cnt == 1), reverse=True)
        return HandValue(HandCategory.THREE_OF_A_KIND, (trip_rank, *kickers))

    # Two pair
    if counts_signature == (2, 2, 1):
        pair_ranks = sorted((rank for rank, cnt in rank_counts.items() if cnt == 2), reverse=True)
        kicker = max(rank for rank, cnt in rank_counts.items() if cnt == 1)
        return HandValue(HandCategory.TWO_PAIR, (*pair_ranks, kicker))

    # One pair
    if counts_signature == (2, 1, 1, 1):
        pair_rank = max(rank for rank, cnt in rank_counts.items() if cnt == 2)
        kickers = sorted((rank for rank, cnt in rank_counts.items() if cnt == 1), reverse=True)
        return HandValue(HandCategory.ONE_PAIR, (pair_rank, *kickers))

    # High card
    ordered = tuple(sorted(ranks, reverse=True))
    return HandValue(HandCategory.HIGH_CARD, ordered)


# ---------------------------------------------------------------------------
# Javni API: najboljša 5-kartna roka iz 5–7 (ali več) kart
# ---------------------------------------------------------------------------

def evaluate_best(cards: Iterable[Card]) -> HandValue:
    # Ovrednoti najboljšo možno 5-kartno roko iz podanih kart.
    # Tipično za Texas Hold'em:
    # - flop:  2 + 3 = 5 kart
    # - turn:  2 + 4 = 6 kart
    # - river: 2 + 5 = 7 kart
    cards = list(cards)
    n = len(cards)

    if n < 5:
        raise ValueError("Need at least 5 cards to evaluate a poker hand")

    # Hitri primer: natanko 5 kart, ni kombiniranja
    if n == 5:
        return _evaluate_5cards(cards)

    # Splošni primer: preverimo vse kombinacije 5 kart in izberemo najboljšo
    best: HandValue | None = None
    for combo in combinations(cards, 5):
        hv = _evaluate_5cards(combo)
        if best is None or hv > best:
            best = hv

    return best  # type: ignore[return-value]


def describe_best_hand(cards: Iterable[Card]) -> str:
    # Ovrednoti najboljšo roko in jo opiše z besedami
    hv = evaluate_best(cards)
    return describe_hand_value(hv)


def compare_hands(cards1: Iterable[Card], cards2: Iterable[Card]) -> int:
    # Primerja dve roki (vsaka 5–7 kart):
    # -1 če je prva slabša
    #  0 če sta enaki
    #  1 če je prva boljša
    h1 = evaluate_best(cards1)
    h2 = evaluate_best(cards2)

    if h1 < h2:
        return -1
    if h1 > h2:
        return 1
    return 0
