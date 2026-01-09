# src/texas_holdem/equity.py
from __future__ import annotations

from typing import List, Tuple

from .cards import Card, Deck
from .game import determine_winners


# ------------------------------------------------------------
# Pomožna funkcija: naredi "zmanjšan" deck brez že uporabljenih kart
# ------------------------------------------------------------
def _build_reduced_deck(used_cards: List[Card]) -> Deck:
    # Ustvari komplet kart, ki NE vsebuje nobene karte iz used_cards
    # (tj. hole karte + že znane board karte).
    #
    # Ideja:
    # - ustvarimo poln Deck
    # - izločimo vse karte, ki so že uporabljene
    # - vrnemo nov Deck samo s preostalimi kartami
    full_deck = Deck()
    used_set = set(used_cards)
    remaining_cards = [c for c in full_deck.remaining() if c not in used_set]
    return Deck(remaining_cards)


# ------------------------------------------------------------
# Simulacija equity za več igralcev z znanimi hole kartami
# ------------------------------------------------------------
def simulate_equity(
    hole_hands: List[List[Card]],
    board: List[Card],
    num_samples: int = 50_000,
) -> Tuple[List[float], List[float]]:
    # Monte Carlo simulacija verjetnosti zmage / izenačenja za vsakega igralca.
    #
    # hole_hands:
    #   seznam seznamov; hole_hands[i] so hole karte igralca i (tipično 2)
    #   V tej funkciji predpostavimo, da so hole karte vseh igralcev znane.
    #
    # board:
    #   trenutno znane skupne karte na mizi (0 do 5).
    #   Če jih je manj kot 5, manjkajoče karte naključno do-delimo.
    #
    # num_samples:
    #   koliko simulacij izvedemo (več = bolj natančno, počasneje).
    if not hole_hands:
        raise ValueError("Need at least one player")

    num_players = len(hole_hands)

    if not (0 <= len(board) <= 5):
        raise ValueError("Board must have between 0 and 5 cards")

    # Preverimo, da ima vsak igralec vsaj 2 karti (Texas Hold'em standard)
    for i, hole in enumerate(hole_hands):
        if len(hole) < 2:
            raise ValueError(f"Player {i} has fewer than 2 hole cards")

    # Če je board že poln (5 kart), ni več naključnosti:
    # izračunamo zmagovalce enkrat in to je to.
    if len(board) == 5:
        winners, _ = determine_winners(hole_hands, board)
        win_counts = [0] * num_players
        tie_counts = [0] * num_players

        if len(winners) == 1:
            win_counts[winners[0]] = 1
        else:
            # Če je split, štejemo tie za vsakega zmagovalca
            for w in winners:
                tie_counts[w] = 1

        # Delimo z 1.0, da dobimo float verjetnosti
        return (
            [w / 1.0 for w in win_counts],
            [t / 1.0 for t in tie_counts],
        )

    # Splošni Monte Carlo primer: board je delno znan, manjkajoče karte do-delimo.
    win_counts = [0] * num_players
    tie_counts = [0] * num_players

    # Vse znane karte (hole vseh igralcev + trenutno znane board karte)
    known_cards: List[Card] = [c for hand in hole_hands for c in hand] + list(board)

    # Koliko board kart še manjka do 5
    cards_to_draw = 5 - len(board)
    if cards_to_draw < 0:
        raise ValueError("Board has more than 5 cards")

    for _ in range(num_samples):
        # Vsako simulacijo:
        # - sestavimo deck brez znanih kart
        # - premešamo
        # - potegnemo manjkajoče board karte
        # - določimo zmagovalca
        deck = _build_reduced_deck(known_cards)
        deck.shuffle()

        drawn = deck.draw_many(cards_to_draw)
        full_board = board + drawn

        winners, _ = determine_winners(hole_hands, full_board)

        if len(winners) == 1:
            win_counts[winners[0]] += 1
        else:
            # Split: vsak zmagovalec dobi tie-štetje
            for w in winners:
                tie_counts[w] += 1

    # Pretvorimo števce v verjetnosti
    win_probs = [w / num_samples for w in win_counts]
    tie_probs = [t / num_samples for t in tie_counts]

    return win_probs, tie_probs


# ------------------------------------------------------------
# Simulacija: hero proti naključnim nasprotnikom
# ------------------------------------------------------------
from .game import determine_winners, validate_unique_cards


def simulate_hero_vs_random_opponents(
    hero_hole: List[Card],
    board: List[Card],
    num_opponents: int,
    num_samples: int = 50_000,
) -> Tuple[float, float]:
    # Monte Carlo ocena win/tie verjetnosti za hero proti num_opponents naključnim nasprotnikom.
    #
    # Kaj je naključno v vsaki simulaciji:
    # - hole karte vseh nasprotnikov (2 karti na vsakega)
    # - manjkajoče board karte (do 5)
    #
    # Kaj je fiksno:
    # - hero_hole (2 karti)
    # - trenutno znane board karte (0–5)
    if len(hero_hole) < 2:
        raise ValueError("Hero must have at least 2 hole cards")
    if not (0 <= len(board) <= 5):
        raise ValueError("Board must have between 0 and 5 cards")
    if num_opponents < 1:
        raise ValueError("Need at least one opponent")

    # Koliko board kart še manjka
    cards_to_draw_board = 5 - len(board)
    if cards_to_draw_board < 0:
        raise ValueError("Board has more than 5 cards")

    hero_win = 0
    hero_tie = 0

    for _ in range(num_samples):
        # Sestavimo deck brez (hero + znani board)
        used = hero_hole + board
        full_deck = Deck()
        used_set = set(used)
        remaining_cards = [c for c in full_deck.remaining() if c not in used_set]
        deck = Deck(remaining_cards)
        deck.shuffle()

        # Pripravimo seznam hole handov: hero je vedno index 0
        hole_hands: List[List[Card]] = [hero_hole]

        # Naključno razdelimo hole karte nasprotnikom (2 na vsakega)
        for _opp in range(num_opponents):
            hole_hands.append(deck.draw_many(2))

        # Dokončamo board (če manjka)
        drawn_board = deck.draw_many(cards_to_draw_board)
        full_board = board + drawn_board

        # Varnostni check: ne bi smelo pasti, če je deck prav zgrajen
        validate_unique_cards(hole_hands, full_board)

        winners, _ = determine_winners(hole_hands, full_board)

        if len(winners) == 1:
            # Če je en zmagovalec in je to hero (index 0), štejemo zmago
            if winners[0] == 0:
                hero_win += 1
        else:
            # Split: če je hero med zmagovalci, štejemo tie
            if 0 in winners:
                hero_tie += 1

    win_prob = hero_win / num_samples
    tie_prob = hero_tie / num_samples
    return win_prob, tie_prob


# ------------------------------------------------------------
# Mini demo (če poganjamo datoteko direktno)
# ------------------------------------------------------------
if __name__ == "__main__":
    # Majhen demo: 2 igralca all-in preflop, brez boarda
    from .cards import Rank, Suit

    # Primer: hero As Kd, villain Qh Qc
    hero = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.DIAMONDS)]
    villain = [Card(Rank.QUEEN, Suit.HEARTS), Card(Rank.QUEEN, Suit.CLUBS)]
    board: List[Card] = []

    hole_hands = [hero, villain]

    print("Hero:", hero)
    print("Villain:", villain)
    print("Board:", board)

    win_probs, tie_probs = simulate_equity(hole_hands, board, num_samples=20_000)

    print("\nEstimated equity:")
    for i, (w, t) in enumerate(zip(win_probs, tie_probs)):
        print(f"Player {i}: win={w:.3f}, tie={t:.3f}, lose={1 - w - t:.3f}")
