# app.py
import streamlit as st
import os
import sys

# ------------------------------------------------------------
# Nastavitve poti (da lahko uvozimo naš paket iz mape "src")
# ------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(CURRENT_DIR, "src")

# Če "src" še ni v sys.path, ga dodamo, da "import texas_holdem" deluje
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# ------------------------------------------------------------
# Uvoz funkcionalnosti iz našega modula texas_holdem
# ------------------------------------------------------------
from texas_holdem import (
    Card, Rank, Suit, Deck,
    simulate_hero_vs_random_opponents,
    CallDecision, ev_call_chips, ev_call_utility,
    RaiseDecision, ev_raise_chips, ev_raise_utility,
    describe_best_hand,
)

# ------------------------------------------------------------
# Nastavitve poti do slik kart
# ------------------------------------------------------------
IMAGE_DIR = os.path.join(CURRENT_DIR, "images", "cards")  # prilagodi, če imaš drugo strukturo map

# Pretvorba enum Rank -> ime datoteke (npr. Rank.FIVE -> "5")
RANK_TO_NAME = {
    Rank.TWO: "2",
    Rank.THREE: "3",
    Rank.FOUR: "4",
    Rank.FIVE: "5",
    Rank.SIX: "6",
    Rank.SEVEN: "7",
    Rank.EIGHT: "8",
    Rank.NINE: "9",
    Rank.TEN: "10",
    Rank.JACK: "jack",
    Rank.QUEEN: "queen",
    Rank.KING: "king",
    Rank.ACE: "ace",
}

# Pretvorba enum Suit -> ime datoteke (npr. Suit.HEARTS -> "hearts")
SUIT_TO_NAME = {
    Suit.CLUBS: "clubs",
    Suit.DIAMONDS: "diamonds",
    Suit.HEARTS: "hearts",
    Suit.SPADES: "spades",
}

# ------------------------------------------------------------
# Funkcije za prikaz kart v UI
# ------------------------------------------------------------
def card_image_path(card: Card) -> str:
    # Vrne pot do PNG slike za dano karto (glede na rank + suit)
    r = RANK_TO_NAME[card.rank]
    s = SUIT_TO_NAME[card.suit]
    filename = f"{r}_of_{s}.png"  # npr. "5_of_hearts.png"
    return os.path.join(IMAGE_DIR, filename)


def show_cards(cards: list[Card]):
    # Prikaže slike kart v eni vrstici (kolone v Streamlit-u)
    cols = st.columns(len(cards))
    for card, col in zip(cards, cols):
        col.image(card_image_path(card), width=80)


# ------------------------------------------------------------
# Pomožne funkcije za deljenje kart
# ------------------------------------------------------------
def new_deck():
    # Ustvari nov premešan komplet
    deck = Deck()
    deck.shuffle()
    return deck


def deal_new_hand(num_opponents: int):
    # Deli novo roko:
    # - hero dobi 2 karti
    # - board je na začetku prazen
    # Opomba: nasprotniki imajo "naključne" karte v simulaciji,
    # zato jih za UI ne shranjujemo kot fiksne.
    deck = new_deck()
    hero = deck.draw_many(2)
    board: list[Card] = []
    return deck, hero, board


# ------------------------------------------------------------
# Streamlit nastavitve strani
# ------------------------------------------------------------
st.set_page_config(page_title="Texas hold'em EV", layout="wide")

# ------------------------------------------------------------
# Inicializacija session_state (da stanje ostane med kliki)
# ------------------------------------------------------------
if "deck" not in st.session_state:
    st.session_state.deck = None
if "hero" not in st.session_state:
    st.session_state.hero = None
if "board" not in st.session_state:
    st.session_state.board = []


# ------------------------------------------------------------
# Sidebar: kontrolniki za simulacijo in parametre EV
# ------------------------------------------------------------
st.sidebar.title("Texas hold 'em EV")

# Število nasprotnikov (za simulacijo proti random handom)
num_opponents = st.sidebar.slider("Število nasprotnikov", 1, 9, 1)

# Pot in znesek za call (v žetonih)
pot = st.sidebar.number_input(
    "Trenutni pot (vključno z nasprotnikovo stavo)",
    min_value=0.0,
    value=100.0,
    step=10.0
)
to_call = st.sidebar.number_input(
    "Znesek za call",
    min_value=0.0,
    value=50.0,
    step=5.0
)

# Parametri za raise:
# - bet_size: koliko stavimo/raisamo
# - fold_prob: verjetnost, da vsi folddajo na naš raise (poenostavljen model)
bet_size = st.sidebar.number_input(
    "Velikost vaše stave / raisa",
    min_value=0.0,
    value=50.0,
    step=5.0
)
fold_prob = st.sidebar.slider(
    "Verjetnost, da nasprotnik folda na vašo stavo",
    0.0, 1.0, 0.3, 0.05
)

# Faktor tveganja (risk preference) za expected utility (EU)
risk_style = st.sidebar.slider(
    "Stil tveganja (-5 = iskalec tveganja, 0 = nevtralen, 5 = zelo previden)",
    min_value=-5.0,
    max_value=5.0,
    value=0.0,
    step=0.5,
)

# ------------------------------------------------------------
# Gumbi za preflop/flop/turn/river
# ------------------------------------------------------------
if st.sidebar.button("Nova roka / Preflop"):
    # Ustvarimo novo roko in resetiramo board
    deck, hero, board = deal_new_hand(num_opponents)
    st.session_state.deck = deck
    st.session_state.hero = hero
    st.session_state.board = board

if st.sidebar.button("Flop"):
    # Flop lahko odpremo samo, če imamo deck in je board prazen (preflop)
    if st.session_state.deck is not None and len(st.session_state.board) == 0:
        d = st.session_state.deck
        d.draw()  # burn karta
        flop = d.draw_many(3)
        st.session_state.board.extend(flop)

if st.sidebar.button("Turn"):
    # Turn lahko odpremo samo, če je board dolg 3 (po flopu)
    if st.session_state.deck is not None and len(st.session_state.board) == 3:
        d = st.session_state.deck
        d.draw()  # burn karta
        turn = d.draw_many(1)
        st.session_state.board.extend(turn)

if st.sidebar.button("River"):
    # River lahko odpremo samo, če je board dolg 4 (po turnu)
    if st.session_state.deck is not None and len(st.session_state.board) == 4:
        d = st.session_state.deck
        d.draw()  # burn karta
        river = d.draw_many(1)
        st.session_state.board.extend(river)


# ------------------------------------------------------------
# Glavni UI
# ------------------------------------------------------------
st.title("Texas hold'em – verjetnost zmage in EV")

hero = st.session_state.hero
board = st.session_state.board

# Če roka še ni inicializirana, uporabniku pokažemo navodilo
if hero is None:
    st.write("Klikni **'Nova roka / Preflop'** za začetek.")
else:
    # Prikažemo hero roko
    st.subheader("Vaša roka")
    show_cards(hero)

    # Prikažemo board
    st.subheader("Miza")
    if not board:
        st.write("Ni odprtih kart na mizi (preflop).")
    else:
        show_cards(board)

    # --------------------------------------------------------
    # Izračun verjetnosti zmage proti naključnim nasprotnikom
    # --------------------------------------------------------
    st.markdown("---")
    st.subheader("Verjetnost zmage proti naključnim nasprotnikom")

    # Simulacija Monte Carlo (num_samples lahko prilagodiš za hitrost/natančnost)
    win_prob, tie_prob = simulate_hero_vs_random_opponents(
        hero_hole=hero,
        board=board,
        num_opponents=num_opponents,
        num_samples=20_000,
    )

    # Poraz je preostanek
    lose_prob = max(0.0, 1.0 - win_prob - tie_prob)

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"Win: {win_prob:.3f}")
        st.write(f"Tie: {tie_prob:.3f}")
        st.write(f"Lose: {lose_prob:.3f}")

    # --------------------------------------------------------
    # Opis najboljše trenutne kombinacije (ko imamo vsaj 5 kart)
    # --------------------------------------------------------
    st.write("Vaša najboljša trenutna kombinacija:")
    if len(hero) + len(board) >= 5:
        st.write(describe_best_hand(hero + board))
    else:
        st.write("Premalo kart za 5-člansko kombinacijo (potrebujemo vsaj flop).")

    # --------------------------------------------------------
    # EV primerjava: FOLD vs CALL vs RAISE
    # --------------------------------------------------------
    st.markdown("---")
    st.subheader("EV odločitve: FOLD vs CALL vs RAISE")

    # CALL odločitev (vključuje pot, znesek za call, win/tie verjetnosti in risk faktor)
    decision = CallDecision(
        pot=pot,
        to_call=to_call,
        win_prob=win_prob,
        tie_prob=tie_prob,
        risk_factor=risk_style,
    )

    # RAISE odločitev:
    # fold_prob = verjetnost, da vsi folddajo (takoj dobimo pot)
    # win_prob_call/tie_prob_call = poenostavitev: ob call-u predpostavimo enako equity kot prej
    raise_decision = RaiseDecision(
        pot=pot,
        bet_size=bet_size,
        fold_prob=fold_prob,
        win_prob_call=win_prob,
        tie_prob_call=tie_prob,
        risk_factor=risk_style,
    )

    # 1) FOLD (osnovna referenca: nič ne dobimo, nič ne izgubimo v tem modelu)
    ev_fold_chips = 0.0
    ev_fold_utility = 0.0

    # 2) CALL EV (v žetonih in v uporabnosti)
    ev_call_ch = ev_call_chips(decision)
    ev_call_ut = ev_call_utility(decision)

    # 3) RAISE EV (v žetonih in v uporabnosti)
    ev_raise_ch = ev_raise_chips(raise_decision)
    ev_raise_ut = ev_raise_utility(raise_decision)

    # Prikažemo tabelo primerjave
    st.write("Primerjava EV (v žetonih) in uporabnosti (EU):")
    st.table({
        "Akcija": ["FOLD", "CALL", "RAISE"],
        "EV (žetoni)": [ev_fold_chips, ev_call_ch, ev_raise_ch],
        "EU (tveganje upoštevano)": [ev_fold_utility, ev_call_ut, ev_raise_ut],
    })

    # Izberemo najboljšo akcijo glede na expected utility (EU)
    actions = ["FOLD", "CALL", "RAISE"]
    eu_values = [ev_fold_utility, ev_call_ut, ev_raise_ut]
    best_idx = max(range(3), key=lambda i: eu_values[i])
    best_action = actions[best_idx]
    best_eu = eu_values[best_idx]

    st.write(
        f"Predlagana akcija (glede na pričakovano uporabnost): "
        f"**{best_action}** (EU = {best_eu:.3f})"
    )
