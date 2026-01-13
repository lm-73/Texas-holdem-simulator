# src/texas_holdem/strategy.py
from __future__ import annotations

from dataclasses import dataclass
import math


# ------------------------------------------------------------
# CALL: podatki, ki jih potrebujemo za izračun EV pri call-u
# ------------------------------------------------------------
@dataclass
class CallDecision:
    # Vhodni podatki za ocenjevanje EV "CALL" v primerjavi s "FOLD".
    #
    # Predpostavke:
    # - Odločitev je enkratna (npr. river ali situacija, kjer po call-u ni več stavljanja).
    # - Če hero calla, gremo direktno do showdown-a (brez nadaljnjih stav).
    #
    # Pojasnila atributov:
    # pot:
    #   Trenutni pot P pred našo odločitvijo (vključuje že villainovo stavo).
    # to_call:
    #   Koliko moramo doplačati za call (C).
    # win_prob:
    #   Verjetnost, da zmagamo, če callamo in pridemo do showdown-a.
    # tie_prob:
    #   Verjetnost, da je split (delitev pota).
    # risk_factor:
    #   0 = risk-nevtralen (linearen EV v žetonih),
    #   >0 = bolj previden (konkavna uporabnost),
    #   <0 = iskalec tveganja (konveksna uporabnost).
    pot: float
    to_call: float
    win_prob: float
    tie_prob: float = 0.0
    risk_factor: float = 0.0

    def lose_prob(self) -> float:
        # Izračunana verjetnost poraza (1 - win - tie), z varnostnim "clamp"
        lp = 1.0 - self.win_prob - self.tie_prob
        return max(0.0, min(1.0, lp))


# ------------------------------------------------------------
# RAISE/BET: podatki, ki jih potrebujemo za izračun EV pri stavi/raisu
# ------------------------------------------------------------
@dataclass
class RaiseDecision:
    # Vhodni podatki za ocenjevanje EV "BET/RAISE".
    #
    # Predpostavke:
    # - Trenutni pot je P (pred našo stavo).
    # - Mi stavimo/raisamo B (nova investicija z naše strani).
    # - Nasprotnik foldda s pf, sicer calla.
    # - Če nasprotnik calla, imamo win_prob_call / tie_prob_call proti njegovemu calling range-u.
    # - Po call-u ni nadaljnjih stav (showdown).
    #
    # pot:
    #   Trenutni pot P pred našim raise/bet.
    # bet_size:
    #   Naša stava/raise B.
    # fold_prob:
    #   Verjetnost, da villain foldda na naš bet/raise (pf).
    # win_prob_call / tie_prob_call:
    #   Verjetnosti izida pod pogojem, da villain calla.
    # risk_factor:
    #   Stil tveganja (enako kot pri call-u).
    pot: float
    to_call: float
    bet_size: float
    fold_prob: float
    win_prob_call: float
    tie_prob_call: float = 0.0
    risk_factor: float = 0.0

    expected_callers_when_called: float = 1.0

    def lose_prob_call(self) -> float:
        # Izračunana verjetnost poraza ob call-u (1 - win - tie), z "clamp"
        lp = 1.0 - self.win_prob_call - self.tie_prob_call
        return max(0.0, min(1.0, lp))


# ------------------------------------------------------------
# Utility funkcija: pretvorba "žetoni -> uporabnost" glede na stil tveganja
# ------------------------------------------------------------
def utility(
    delta_chips: float,
    risk_style: float,
    *,
    chip_scale: float = 100.0,   
    slider_scale: float = 0.1,  
) -> float:

    x = float(delta_chips)
    if x == 0.0:
        return 0.0

    r = float(risk_style) * slider_scale

    if abs(r) < 1e-12:
        return x

    k = abs(r)  

    if r > 0:  
        a_gain = 1.0 + k
        a_loss = 1.0 / (1.0 + k)
    else:      
        a_gain = 1.0 / (1.0 + k)
        a_loss = 1.0 + k

    a = a_gain if x > 0 else a_loss

    C = max(float(chip_scale), 1e-9)

    s = abs(x) / C
    s = min(s, 1e12) 

    u = C * ((s + 1.0) ** a - 1.0) / a

    return math.copysign(u, x)




# ------------------------------------------------------------
# EV za CALL (v žetonih)
# ------------------------------------------------------------
def ev_call_chips(decision: CallDecision) -> float:
    # EV (risk-nevtralen) relativno na FOLD = 0.
    #
    # Izidi (relativno na folding):
    # - win:  +P
    # - tie:  +0.5*P - 0.5*C
    # - lose: -C
    P = decision.pot
    C = decision.to_call
    p_win = decision.win_prob
    p_tie = decision.tie_prob
    p_lose = decision.lose_prob()

    return (
        p_win * P
        + p_tie * (0.5 * P - 0.5 * C)
        - p_lose * C
    )


# ------------------------------------------------------------
# EV za CALL (v uporabnosti - upošteva risk_factor)
# ------------------------------------------------------------
def ev_call_utility(decision: CallDecision) -> float:
    # Pričakovana uporabnost (EU) za CALL.
    # Enaki izidi kot pri ev_call_chips, samo da gredo skozi utility().
    P = decision.pot
    C = decision.to_call
    p_win = decision.win_prob
    p_tie = decision.tie_prob
    p_lose = decision.lose_prob()
    r = decision.risk_factor

    delta_win = P
    delta_tie = 0.5 * P - 0.5 * C
    delta_lose = -C

    cs = max(1.0, C)

    u_win = utility(delta_win, r, chip_scale=cs)
    u_tie = utility(delta_tie, r, chip_scale=cs)
    u_lose = utility(delta_lose, r, chip_scale=cs)

    return (
        p_win * u_win
        + p_tie * u_tie
        + p_lose * u_lose
    )


# ------------------------------------------------------------
# EV za RAISE/BET (v žetonih)
# ------------------------------------------------------------
def ev_raise_chips(decision: RaiseDecision) -> float:
    # EV (risk-nevtralen) relativno na check/fold baseline = 0.
    #
    # Izidi (relativno na check/fold):
    # - villain folds:           +P
    # - villain calls & win:     +P + B
    # - villain calls & tie:     +0.5*P
    # - villain calls & lose:    -B
    P = decision.pot
    C = decision.to_call
    B = decision.bet_size
    pf_all = decision.fold_prob
    k = max(1.0, decision.expected_callers_when_called)

    p_win = decision.win_prob_call
    p_tie = decision.tie_prob_call
    p_lose = decision.lose_prob_call()

    delta_win = P + k * B
    delta_tie = 0.5 * P + 0.5 * (k - 1.0) * B - 0.5 * C
    delta_lose = -B -C

    ev_if_called = (
        p_win * delta_win
        + p_tie * delta_tie
        + p_lose * delta_lose
    )

    return pf_all * P + (1.0 - pf_all) * ev_if_called


# ------------------------------------------------------------
# EV za RAISE/BET (v uporabnosti - upošteva risk_factor)
# ------------------------------------------------------------
def ev_raise_utility(decision: RaiseDecision) -> float:
    # Pričakovana uporabnost (EU) za bet/raise.
    P = decision.pot
    C = decision.to_call
    B = decision.bet_size
    pf_all = decision.fold_prob
    r = decision.risk_factor
    k = max(1.0, decision.expected_callers_when_called)

    p_win = decision.win_prob_call
    p_tie = decision.tie_prob_call
    p_lose = decision.lose_prob_call()

    cs = max(1.0, C + B)

    # Če villain foldda: dobimo +P
    u_fold = utility(P, r, chip_scale=cs)

    # Če villain calla:
    delta_win = P + k * B
    delta_tie = 0.5 * P + 0.5 * (k - 1.0) * B - 0.5 * C
    delta_lose = -B - C

    u_win_call = utility(delta_win, r, chip_scale=cs)
    u_tie_call = utility(delta_tie, r, chip_scale=cs)
    u_lose_call = utility(delta_lose, r, chip_scale=cs)

    eu_if_called = (
        p_win * u_win_call
        + p_tie * u_tie_call
        + p_lose * u_lose_call
    )

    return pf_all * u_fold + (1.0 - pf_all) * eu_if_called


# ------------------------------------------------------------
# Priporočilo: CALL vs FOLD (na podlagi EU_call)
# ------------------------------------------------------------
def recommend_action(decision: CallDecision) -> str:
    # Če je EU(call) > 0: call je (v tem modelu) boljši od fold
    # Če je EU(call) < 0: fold je boljši
    eu_call = ev_call_utility(decision)
    eps = 1e-6

    if eu_call > eps:
        return f"CALL (EU = {eu_call:.3f})"
    elif eu_call < -eps:
        return f"FOLD (EU = {eu_call:.3f})"
    else:
        return f"CLOSE DECISION (EU ≈ {eu_call:.3f})"


# ------------------------------------------------------------
# Priporočilo: RAISE/BET vs NO RAISE (na podlagi EU_raise)
# ------------------------------------------------------------
def recommend_raise_action(decision: RaiseDecision) -> str:
    # Če je EU(raise) > 0: raise je boljši kot check/fold baseline
    # Če je EU(raise) < 0: raje ne raisamo (check/fold baseline boljši)
    eu_rais = ev_raise_utility(decision)
    eps = 1e-6

    if eu_rais > eps:
        return f"RAISE/BET (EU = {eu_rais:.3f})"
    elif eu_rais < -eps:
        return f"NO RAISE (EU = {eu_rais:.3f})"
    else:
        return f"CLOSE DECISION (EU ≈ {eu_rais:.3f})"


# ------------------------------------------------------------
# Hiter test (če poganjamo datoteko direktno)
# ------------------------------------------------------------
if __name__ == "__main__":
    # Mini sanity check za CALL (risk-nevtralen)
    d = CallDecision(pot=100.0, to_call=50.0, win_prob=0.40, tie_prob=0.05, risk_factor=0.0)
    print("Risk-neutral EV(call):", ev_call_chips(d))
    print("Risk-neutral EU(call):", ev_call_utility(d), "->", recommend_action(d))

    # Mini sanity check za CALL (previden igralec)
    d_risk_averse = CallDecision(pot=100.0, to_call=50.0, win_prob=0.40, tie_prob=0.05, risk_factor=2.0)
    print("Risk-averse EU(call):", ev_call_utility(d_risk_averse), "->", recommend_action(d_risk_averse))

    # Mini sanity check za RAISE (risk-nevtralen)
    rd = RaiseDecision(
    pot=100.0,
    to_call=20.0,      
    bet_size=50.0,
    fold_prob=0.3,
    win_prob_call=0.45,
    tie_prob_call=0.05,
    risk_factor=0.0,
    )
    print("Risk-neutral EV(raise):", ev_raise_chips(rd))
    print("Risk-neutral EU(raise):", ev_raise_utility(rd), "->", recommend_raise_action(rd))
