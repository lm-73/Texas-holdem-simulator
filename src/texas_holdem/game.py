# src/texas_holdem/game.py
from __future__ import annotations

from typing import List, Tuple

from .cards import Card
from .hand_eval import HandValue, evaluate_best, describe_hand_value


def validate_unique_cards(hole_hands: List[List[Card]], board: List[Card]) -> None:
    # Preveri, da se nobena fizična karta ne pojavi več kot enkrat
    # (ne v igralčevih kartah in ne na boardu).
    #
    # Če najde duplikat, sproži ValueError in pove, kje se karta pojavi.
    labeled_cards = []

    # Najprej zberemo vse karte igralcev in jih označimo z izvorom
    for i, hole in enumerate(hole_hands):
        for c in hole:
            labeled_cards.append((f"player {i} hole", c))

    # Nato dodamo še board karte in jih označimo z indeksom na mizi
    for j, c in enumerate(board):
        labeled_cards.append((f"board[{j}]", c))

    # seen preslika "karta -> kje se je prvič pojavila"
    seen: dict[Card, str] = {}

    # Gremo čez vse karte in preverimo duplikate
    for origin, card in labeled_cards:
        if card in seen:
            prev_origin = seen[card]
            raise ValueError(
                f"Duplicate card detected: {card} appears in {origin} and {prev_origin}"
            )
        seen[card] = origin


def determine_winners(
    hole_hands: List[List[Card]],
    board: List[Card],
) -> Tuple[List[int], List[HandValue]]:
    # Določi zmagovalca(-e) glede na hole karte vseh igralcev in board.
    #
    # Postopek:
    # 1) validacija vhodov (vsaj 1 igralec, vsak ima >= 2 karti)
    # 2) preverimo, da ni duplikatov kart (fizično ista karta se ne sme ponoviti)
    # 3) za vsakega igralca ovrednotimo najboljšo 5-kartno kombinacijo iz (hole + board)
    # 4) najdemo maksimalno HandValue in vrnemo vse indekse igralcev, ki imajo enako najboljšo roko
    if not hole_hands:
        # Brez igralcev ni mogoče določiti zmagovalca
        raise ValueError("Need at least one player")

    # Preverimo, da se nobena karta ne ponovi med igralci in na mizi
    validate_unique_cards(hole_hands, board)

    # Preverimo, da ima vsak igralec vsaj 2 hole karti (Texas Hold'em standard)
    for i, hole in enumerate(hole_hands):
        if len(hole) < 2:
            raise ValueError(f"Player {i} has fewer than 2 hole cards")

    # Izračunamo HandValue za vsakega igralca
    # evaluate_best poskrbi, da izbere najboljšo 5-kartno kombinacijo iz 5–7 kart
    hand_values: List[HandValue] = []
    for hole in hole_hands:
        hv = evaluate_best(hole + board)
        hand_values.append(hv)

    # Najmočnejša roka je max po HandValue (category in tiebreaker)
    best_value = max(hand_values)

    # Vsi igralci, ki imajo enako najboljšo roko, so zmagovalci (možen split)
    winner_indices = [i for i, hv in enumerate(hand_values) if hv == best_value]

    return winner_indices, hand_values


if __name__ == "__main__":
    # Mini demonstracija: poganjaj z
    #   python -m texas_holdem.game
    # (če si v mapi src, da importi delujejo)
    from .cards import Rank, Suit

    # Primer boarda (5 kart na mizi)
    board = [
        Card(Rank.ACE, Suit.SPADES),
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.KING, Suit.DIAMONDS),
        Card(Rank.KING, Suit.CLUBS),
        Card(Rank.TWO, Suit.SPADES),
    ]

    # Primer treh igralcev, vsak ima 2 hole karti
    hole_hands = [
        [Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.THREE, Suit.CLUBS)],  # player 0
        [Card(Rank.KING, Suit.HEARTS),  Card(Rank.FOUR, Suit.CLUBS)],   # player 1
        [Card(Rank.QUEEN, Suit.SPADES), Card(Rank.QUEEN, Suit.HEARTS)], # player 2
    ]

    # Določimo zmagovalce in ovrednotene roke vseh igralcev
    winners, hand_values = determine_winners(hole_hands, board)

    # Izpis za pregled
    print("Board:", board)
    for i, (hole, hv) in enumerate(zip(hole_hands, hand_values)):
        print(f"Player {i}: {hole} -> {hv} -> {describe_hand_value(hv)}")

    print("Winner indices:", winners)
