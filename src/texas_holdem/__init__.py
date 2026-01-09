# src/texas_holdem/__init__.py

# ------------------------------------------------------------
# Ta datoteka naredi paket "texas_holdem" prijaznejši za uvoz.
# Ideja:
# - uporabnik lahko piše: from texas_holdem import Card, Deck, simulate_equity, ...
# - mi pa tukaj izvozimo (re-export) najpomembnejše razrede in funkcije
# ------------------------------------------------------------

# Osnovni gradniki kart
from .cards import Card, Rank, Suit, Deck

# Ovrednotenje kombinacij (hand evaluation)
from .hand_eval import (
    HandCategory,
    HandValue,
    evaluate_best,
    compare_hands,
    describe_hand_value,
    describe_best_hand,
)

# Igra: določanje zmagovalcev glede na hole + board
from .game import determine_winners

# Equity simulacije (Monte Carlo)
from .equity import simulate_equity

# Strategija: EV in expected utility za call/raise
from .strategy import (
    CallDecision,
    ev_call_chips,
    ev_call_utility,
    recommend_action,
    RaiseDecision,
    ev_raise_chips,
    ev_raise_utility,
    recommend_raise_action,
)

# Ponoven uvoz iz equity:
# - simulate_equity (že zgoraj) in
# - simulate_hero_vs_random_opponents (hero proti naključnim nasprotnikom)
#
# Opomba: simulate_equity je tukaj importan dvakrat (ni kritično, ampak je redundantno).
from .equity import simulate_equity, simulate_hero_vs_random_opponents


# ------------------------------------------------------------
# __all__ določa, kaj se iz izvozi ob:
#   from texas_holdem import *
# in tudi jasno dokumentira "javni API" paketa.
# ------------------------------------------------------------
__all__ = [
    "Card",
    "Rank",
    "Suit",
    "Deck",
    "HandCategory",
    "HandValue",
    "evaluate_best",
    "compare_hands",
    "describe_hand_value",
    "describe_best_hand",
    "determine_winners",
    "simulate_equity",
    "simulate_hero_vs_random_opponents",
    "CallDecision",
    "ev_call_chips",
    "ev_call_utility",
    "recommend_action",
    "RaiseDecision",
    "ev_raise_chips",
    "ev_raise_utility",
    "recommend_raise_action",
]


