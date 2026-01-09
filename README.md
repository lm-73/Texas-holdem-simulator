# Texas hold'em simulator

Interaktivni simulator igre **Texas hold'em**, napisan v Pythonu.  
Aplikacija omogoča naključno deljenje kart, izračun verjetnosti zmage (equity) proti naključnim nasprotnikom ter analizo odločitev **fold / call / raise** na podlagi pričakovane vrednosti (EV) in izbranega stila tveganja.

---

## Glavne funkcionalnosti

- 🎴 **Model kart in kupčka**
  - Standardni 52-kartni kupček (brez jokerjev).
  - Naključno deljenje kart brez ponavljanja.
  - Podpora za Texas hold'em: 2 karti igralca + 5 skupnih kart (flop, turn, river).

- 🧠 **Ovrednotenje pokerskih kombinacij**
  - Prepozna vseh 9 kombinacij: high card, pair, two pair, three of a kind, straight, flush, full house, four of a kind, straight flush.
  - Pravilno obravnava **A–2–3–4–5** kot najslabšo (5-high) lestvico.
  - Iz 5–7 kart vedno izbere najboljšo možno 5-kartno kombinacijo.

- 🎲 **Monte Carlo simulacija (equity)**
  - Simulacija iger proti **naključnim nasprotnikom**.
  - Ocena:
    - verjetnosti zmage (`Win`),
    - verjetnosti neodločenega izida (`Tie`),
    - verjetnosti poraza (`Lose`),
  glede na:
    - igralčeve karte,
    - odprte skupne karte (flop/turn/river),
    - število nasprotnikov (1–9).

- 💰 **Izračun EV za FOLD / CALL / RAISE**
  - Izračun ev v žetonih glede na:
    - trenutni pot (pred odločitvijo),
    - znesek za `call`,
    - velikost vaše stave / raisa,
    - verjetnosti `Win` in `Tie` iz simulacije,
    - verjetnost, da nasprotniki folddajo na vaš raise.
  - Prikazana je tabela:
    - EV (v žetonih) za **FOLD / CALL / RAISE**,
    - pričakovana uporabnost (EU), ki upošteva stil tveganja.

- ⚖️ **Stil tveganja (risk style)**
  - Drsnik od **-5 do +5**:
    - negativne vrednosti → riziko-ljubeč igralec (risk-seeking),
    - 0 → nevtralen igralec (čista EV),
    - pozitivne vrednosti → previden igralec (risk-averse).
  - Spremeni **utility funkcijo**, ne pa matematične verjetnosti zmage – tako lahko analiziramo, kako bi igral igralec z različnim odnosom do tveganja.

- 🖼️ **Grafični prikaz kart**
  - Karte so prikazane s PNG slikami (npr. `ace_of_spades.png`, `7_of_hearts.png`).
  - Posebej se prikaže:
    - igralčeva roka,
    - skupne karte na mizi,
    - opis najboljše trenutne kombinacije (npr. *“Two pair, Fours and Threes with King kicker”*).

