# =========================================================
# TBF BRİÇ AKADEMİ v9.5 - OPTIMIZED STABLE
# Mobil + Eğitim + Saf Core Çekirdek (Tek Dosya)
# =========================================================

import streamlit as st
import random

st.set_page_config(
    page_title="TBF Briç Akademi v9.5",
    layout="centered"
)

# =========================================================
# CSS - MOBİL VE EKRAN TASARIMI
# =========================================================

st.markdown("""
<style>
.block-container {
    padding-top: 0.8rem;
    padding-bottom: 1rem;
    padding-left: 0.7rem;
    padding-right: 0.7rem;
}

div.stButton > button {
    width: 100%;
    border-radius: 10px;
    font-weight: bold;
    height: 50px;
    font-size: 17px !important;
}

.card-box {
    background-color: #f8fafc;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 10px;
    border-left: 5px solid #ef4444;
}

.table-box {
    background-color: #1e293b;
    color: white;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 10px;
}

.bid-history {
    background: #1e293b;
    color: white;
    padding: 10px;
    border-radius: 10px;
    overflow-x: auto;
    white-space: nowrap;
    font-size: 16px;
}

.mobile-cards {
    font-size: 21px;
    line-height: 2.0;
    font-family: monospace;
}

@media (max-width: 768px) {
    h1 { font-size: 2rem !important; }
    h2 { font-size: 1.3rem !important; }
    .mobile-cards { font-size: 22px; }
    div.stButton > button {
        height: 56px;
        font-size: 18px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# SABİTLER
# =========================================================

PLAYERS = ["Batı", "Kuzey", "Doğu", "Güney"]

SUIT_ORDER = {
    "♣": 1,
    "♦": 2,
    "♥": 3,
    "♠": 4,
    "NT": 5
}

CARD_RANK = {
    '2':2,'3':3,'4':4,'5':5,'6':6,'7':7,
    '8':8,'9':9,'10':10,'J':11,'Q':12,'K':13,'A':14
}

# =========================================================
# DECK (DESTE ÜRETİCİ)
# =========================================================

class BridgeDeck:
    SUITS = ["♠","♥","♦","♣"]
    RANKS = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]

    @staticmethod
    def generate_and_deal():
        deck = [f"{s}{r}" for s in BridgeDeck.SUITS for r in BridgeDeck.RANKS]
        random.shuffle(deck)

        hands = {p: {"♠":[],"♥":[],"♦":[],"♣":[]} for p in PLAYERS}

        for idx, card in enumerate(deck):
            suit = card[0]
            rank = card[1:]
            hands[PLAYERS[idx % 4]][suit].append(rank)

        for p in PLAYERS:
            for s in BridgeDeck.SUITS:
                hands[p][s].sort(key=lambda x: CARD_RANK[x], reverse=True)

        return hands

# =========================================================
# HAND EVALUATOR (HCP)
# =========================================================

class HandEvaluator:
    @staticmethod
    def get_hcp(hand):
        vals = {"A":4, "K":3, "Q":2, "J":1}
        total = 0
        for s in hand:
            for c in hand[s]:
                total += vals.get(c, 0)
        return total

# =========================================================
# BIDDING LEGALITY MOTORU
# =========================================================

class BiddingLegalityEngine:
    @staticmethod
    def last_real_bid(history):
        bids = [b["bid"] for b in history if b["bid"] not in ["PAS","X","XX"]]
        return bids[-1] if bids else None

    @staticmethod
    def is_legal(proposed, history):
        if proposed == "PAS":
            return True

        last_bid = BiddingLegalityEngine.last_real_bid(history)

        if not last_bid:
            return proposed not in ["X","XX"]

        # KONTRA
        if proposed == "X":
            if history[-1]["bid"] in ["X","XX"]:
                return False
            return True

        # SÜRKONTRA
        if proposed == "XX":
            return history[-1]["bid"] == "X"

        # NORMAL DEKLARE ARTIRIMI
        ll = int(last_bid[0])
        ls = last_bid[1:]
        pl = int(proposed[0])
        ps = proposed[1:]

        if pl > ll:
            return True
        if pl < ll:
            return False

        return SUIT_ORDER[ps] > SUIT_ORDER[ls]

# =========================================================
# AUCTION RESOLVER (YASAL DERLEYİCİ)
# =========================================================

class AuctionResolver:
    @staticmethod
    def resolve(history):
        if len(history) < 4:
            return None

        if (
            history[-1]["bid"] == "PAS"
            and history[-2]["bid"] == "PAS"
            and history[-3]["bid"] == "PAS"
        ):
            final_bid = None
            final_player = None
            doubled = False
            redoubled = False

            for b in reversed(history[:-3]):
                if b["bid"] == "XX": redoubled = True
                elif b["bid"] == "X": doubled = True
                elif b["bid"] != "PAS":
                    final_bid = b["bid"]
                    final_player = b["player"]
                    break

            if not final_bid:
                return "PASS_OUT"

            trump = final_bid[1:]
            axis = ["Batı","Doğu"] if final_player in ["Batı","Doğu"] else ["Kuzey","Güney"]
            declarer = final_player

            for b in history:
                if (
                    b["player"] in axis
                    and b["bid"] not in ["PAS","X","XX"]
                    and b["bid"][1:] == trump
                ):
                    declarer = b["player"]
                    break

            leader = PLAYERS[(PLAYERS.index(declarer)+1)%4]
            dummy = [p for p in axis if p != declarer][0]

            return {
                "contract": final_bid,
                "declarer": declarer,
                "leader": leader,
                "dummy": dummy,
                "is_doubled": doubled,
                "is_redoubled": redoubled
            }
        return None

# =========================================================
# CARD TRACKER
# =========================================================

class CardTracker:
    def __init__(self):
        self.suit_counts = {"♠":0, "♥":0, "♦":0, "♣":0}
        self.void_memory = {p: {"♠":False, "♥":False, "♦":False, "♣":False} for p in PLAYERS}

    def log_card(self, card):
        self.suit_counts[card[0]] += 1

    def analyze_void(self, player, played_suit, led_suit):
        if led_suit and played_suit != led_suit:
            self.void_memory[player][led_suit] = True

# =========================================================
# AUCTION AI (ROBOT DEKLARE STRATEJİSİ)
# =========================================================

class AuctionAI:
    @staticmethod
    def generate_bid(player, hand, history):
        hcp = HandEvaluator.get_hcp(hand)
        sp = len(hand["♠"])
        he = len(hand["♥"])
        longest = max(len(hand[s]) for s in hand)

        # 9 PUAN / 7 PARÇA KURALI ENTEGRASYONU
        if not history:
            if hcp < 9 and longest < 7:
                return "PAS"

            if 15 <= hcp <= 17:
                if sp < 5 and he < 5:
                    return "1NT"

            if hcp >= 12 or longest >= 7:
                if sp >= 5: return "1♠"
                if he >= 5: return "1♥"
                if len(hand["♦"]) >= len(hand["♣"]): return "1♦"
                return "1♣"

            return "PAS"

        # ORTAK CEVAP MODELLEMESİ
        partner = "Batı" if player == "Doğu" else "Kuzey"
        p_bids = [b for b in history if b["player"] == partner]

        if p_bids:
            pbid = p_bids[-1]["bid"]

            if pbid == "1NT" and hcp >= 8:
                if sp == 4 or he == 4: return "2♣"

            if pbid in ["1♠","1♥"]:
                suit = pbid[1:]
                if len(hand[suit]) >= 3 and hcp >= 6:
                    return f"2{suit}"

        return "PAS"

# =========================================================
# PLAY LOGIC
# =========================================================

class BridgeLogic:
    @staticmethod
    def determine_trick_winner(cards, led, trump):
        winner = cards[0]
        for p in cards[1:]:
            ws = winner["card"][0]
            wr = winner["card"][1:]
            ps = p["card"][0]
            pr = p["card"][1:]

            if ps == ws:
                if CARD_RANK[pr] > CARD_RANK[wr]: winner = p
            elif (ps == trump and trump != "NT" and ws != trump):
                winner = p
            elif (ps == trump and ws == trump):
                if CARD_RANK[pr] > CARD_RANK[wr]: winner = p
        return winner

# =========================================================
# STRATEGIC AI (ROBOT OYUN ZEKASI)
# =========================================================

class StrategicAI:
    @staticmethod
    def play_card(hand, trick, trump):
        # ATAK
        if not trick:
            # TOP OF SEQUENCE
            for s in ["♠","♥","♦","♣"]:
                if len(hand[s]) >= 3:
                    c1 = CARD_RANK[hand[s][0]]
                    c2 = CARD_RANK[hand[s][1]]
                    c3 = CARD_RANK[hand[s][2]]
                    if c1-c2 == 1 and c2-c3 == 1:
                        return f"{s}{hand[s].pop(0)}"

            # STANDART ATAK
            for s in ["♠","♥","♦","♣"]:
                if hand[s]: return f"{s}{hand[s].pop(-1)}"

        led = trick[0]["card"][0]

        # FOLLOW SUIT
        if hand[led]:
            return f"{led}{hand[led].pop(-1)}"

        # RUFF
        if trump != "NT" and hand[trump]:
            return f"{trump}{hand[trump].pop(-1)}"

        # DISCARD
        for s in ["♣","♦","♥","♠"]:
            if hand[s]: return f"{s}{hand[s].pop(-1)}"

        return None

# =========================================================
# STATE INITIALIZATION & SAF KART FİLTRESİ
# =========================================================

if "bridge_v9" not in st.session_state:
    # 9 Puan veya 7 Parça Filtresini while döngüsüyle arka planda çözüyoruz (Sonsuz Döngü Engeli)
    while True:
        generated_hands = BridgeDeck.generate_and_deal()
        hcp_check = HandEvaluator.get_hcp(generated_hands["Güney"])
        len_check = max(len(generated_hands["Güney"][s]) for s in generated_hands["Güney"])
        if hcp_check >= 9 or len_check >= 7:
            hands = generated_hands
            break

    st.session_state.bridge_v9 = {
        "step":"AUCTION",
        "hands":hands,
        "bidding_history":[],
        "trick_history":[],
        "tracker":CardTracker(),
        "contract_meta":None,
        "current_turn":"Batı",
        "score_decl":0,
        "score_def":0,
        "trick_count":0,
        "vulnerable":random.choice([True, False]),
        "mode":"Turnuva Sekansı"
    }

state = st.session_state.bridge_v9

# =========================================================
# SIDEBAR MOD CONTROLLER
# =========================================================

with st.sidebar:
    st.title("🎓 Eğitim Modları")

    mode = st.radio(
        "Çalışma Alanı:",
        [
            "Kendi Açılış Pratiğiniz",
            "Ortak Açışına Yanıtlar",
            "Turnuva Sekansı"
        ]
    )

    if mode != state["mode"]:
        state["mode"] = mode
        state["bidding_history"] = []
        state["trick_history"] = []
        state["step"] = "AUCTION"

        if mode == "Kendi Açılış Pratiğiniz":
            state["current_turn"] = "Güney"
        elif mode == "Ortak Açışına Yanıtlar":
            state["bidding_history"] = [{"player":"Kuzey", "bid":"1NT"}]
            state["current_turn"] = "Güney"
        else:
            state["current_turn"] = "Batı"
        st.rerun()

    if st.button("🔄 Yeni El"):
        st.session_state.clear()
        st.rerun()

    st.markdown("---")
    st.metric("Zon", "ZONDA" if state["vulnerable"] else "ZONSUZ")

# =========================================================
# MAIN RENDER
# =========================================================

st.title("🃏 TBF Briç Akademi v9.5")
south = state["hands"]["Güney"]
hcp_south = HandEvaluator.get_hcp(south)

# =========================================================
# AUCTION STAGE
# =========================================================

if state["step"] == "AUCTION":
    st.subheader("💬 Müzayede")

    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.write(f"**Güney Eliniz (HCP: {hcp_south})**")
    st.markdown(
        f"""
        <div class="mobile-cards">
        ♠ {' '.join(south['♠'])}<br>
        ♥ {' '.join(south['♥'])}<br>
        ♦ {' '.join(south['♦'])}<br>
        ♣ {' '.join(south['♣'])}
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.write(f"### Sıra: {state['current_turn']}")

    # BIDDING HISTORY DISPLAY
    if state["bidding_history"]:
        st.markdown(
            f"""
            <div class="bid-history">
            {" -> ".join([f"{b['player']}:{b['bid']}" for b in state["bidding_history"]]}
            </div>
            """,
            unsafe_allow_html=True
        )

    res = AuctionResolver.resolve(state["bidding_history"])

    if res:
        if res == "PASS_OUT":
            st.warning("Pas geçildi.")
            if st.button("Yeni Board"):
                st.session_state.clear()
                st.rerun()
        else:
            state["contract_meta"] = res
            st.success(f"Kontrat: {res['contract']} | Deklaran: {res['declarer']}")
            if st.button("Oyuna Başla"):
                state["step"] = "PLAY"
                state["current_turn"] = res["leader"]
                st.rerun()

    # HUMAN PLAYER INTERACTION
    if state["current_turn"] == "Güney" and not res:
        st.write("---")

        # SATIR 1: ANA AKSİYONLAR
        r1 = st.columns(3)
        
        if r1[0].button("PAS"):
            state["bidding_history"].append({"player":"Güney", "bid":"PAS"})
            state["current_turn"] = "Batı"
            st.rerun()

        # TYPE SQUASH: disabled durumunu tam Boolean olarak zorluyoruz
        is_x_legal = bool(BiddingLegalityEngine.is_legal("X", state["bidding_history"]))
        if r1[1].button("KONTRA", disabled=not is_x_legal):
            state["bidding_history"].append({"player":"Güney", "bid":"X"})
            state["current_turn"] = "Batı"
            st.rerun()

        is_xx_legal = bool(BiddingLegalityEngine.is_legal("XX", state["bidding_history"]))
        if r1[2].button("SUR", disabled=not is_xx_legal):
            state["bidding_history"].append({"player":"Güney", "bid":"XX"})
            state["current_turn"] = "Batı"
            st.rerun()

        st.write("### Deklare Ver")

        # SATIR 2 VE 3: GENİŞ KOMPAKT MOBİL DEKLARE BASAMAKLARI
        bids = ["1♠", "1NT", "2♣", "2♦", "2♥", "4♠"]
        row1 = st.columns(3)
        row2 = st.columns(3)

        first = bids[:3]
        second = bids[3:]

        for i, b in enumerate(first):
            ok = bool(BiddingLegalityEngine.is_legal(b, state["bidding_history"]))
            if row1[i].button(b, disabled=not ok, key=f"b1_{b}"):
                state["bidding_history"].append({"player":"Güney", "bid":b})
                state["current_turn"] = "Batı"
                st.rerun()

        for i, b in enumerate(second):
            ok = bool(BiddingLegalityEngine.is_legal(b, state["bidding_history"]))
            if row2[i].button(b, disabled=not ok, key=f"b2_{b}"):
                state["bidding_history"].append({"player":"Güney", "bid":b})
                state["current_turn"] = "Batı"
                st.rerun()

    # ROBOT TURNS
    elif not res:
        bot = state["current_turn"]
        bid = AuctionAI.generate_bid(bot, state["hands"][bot], state["bidding_history"])
        state["bidding_history"].append({"player":bot, "bid":bid})
        idx = PLAYERS.index(bot)
        state["current_turn"] = PLAYERS[(idx+1)%4]
        st.rerun()

# =========================================================
# PLAY STAGE
# =========================================================

elif state["step"] == "PLAY":
    meta = state["contract_meta"]
    trump = meta["contract"][1:] if meta["contract"][1:] in ["♠","♥","♦","♣"] else "NT"
    decl_side = ["Güney","Kuzey"] if meta["declarer"] in ["Güney","Kuzey"] else ["Batı","Doğu"]

    st.subheader(f"🎴 Oyun | {meta['contract']}")

    c1, c2 = st.columns(2)
    c1.metric("Biz", state["score_decl"])
    c2.metric("Onlar", state["score_def"])

    # MASADAKİ CANLI DURUM
    st.markdown("<div class='table-box'>", unsafe_allow_html=True)
    if state["trick_history"]:
        cols = st.columns(4)
        for i, p in enumerate(state["trick_history"]):
            cols[i].write(f"{p['player']}\n{p['card']}")
    else:
        st.write("Yeni löve")
    st.markdown("</div>", unsafe_allow_html=True)

    # DUMMY DISPLAY
    with st.expander(f"Yer Kartları ({meta['dummy']})", expanded=True):
        dhand = state["hands"][meta["dummy"]]
        st.markdown(
            f"""
            <div class="mobile-cards">
            ♠ {' '.join(dhand['♠'])}<br>
            ♥ {' '.join(dhand['♥'])}<br>
            ♦ {' '.join(dhand['♦'])}<br>
            ♣ {' '.join(dhand['♣'])}
            </div>
            """,
            unsafe_allow_html=True
        )

    # BOT PLAY ACTIONS
    is_bot = state["current_turn"] not in ["Güney", meta["dummy"]]

    if is_bot:
        card = StrategicAI.play_card(state["hands"][state["current_turn"]], state["trick_history"], trump)
        if card:
            led = state["trick_history"][0]["card"][0] if state["trick_history"] else None
            state["tracker"].analyze_void(state["current_turn"], card[0], led)
            state["tracker"].log_card(card)

            state["trick_history"].append({"player":state["current_turn"], "card":card})
            state["current_turn"] = PLAYERS[(PLAYERS.index(state["current_turn"])+1)%4]
            st.rerun()

    # HUMAN VEYA DUMMY KART OYNATMA ALANI
    else:
        active = state["current_turn"]
        hand = state["hands"][active]
        led = state["trick_history"][0]["card"][0] if state["trick_history"] else None
        
        # TYPE SQUASH: bool zorlaması ile Streamlit çökme riskini tamamen sıfırlıyoruz
        has_led = bool(led and any(hand.get(led, [])))

        st.write(f"### Sıra: {active}")

        for s, cards in hand.items():
            if cards:
                st.write(f"### {s} {' '.join(cards)}")
                cols = st.columns(min(len(cards), 4))

                for i, val in enumerate(cards):
                    disabled_status = bool(has_led and s != led)
                    if cols[i % 4].button(val, key=f"{active}_{s}_{val}", disabled=disabled_status):
                        hand[s].remove(val)
                        state["tracker"].analyze_void(active, s, led)
                        state["tracker"].log_card(f"{s}{val}")

                        state["trick_history"].append({"player":active, "card":f"{s}{val}"})
                        state["current_turn"] = PLAYERS[(PLAYERS.index(active)+1)%4]
                        st.rerun()

    # TRICK RESOLUTION
    if len(state["trick_history"]) == 4:
        winner = BridgeLogic.determine_trick_winner(
            state["trick_history"],
            state["trick_history"][0]["card"][0],
            trump
        )["player"]

        st.success(f"Löveyi alan: {winner}")

        if st.button("Löveyi Topla"):
            if winner in decl_side: state["score_decl"] += 1
            else: state["score_def"] += 1

            state["trick_history"] = []
            state["current_turn"] = winner
            state["trick_count"] += 1

            if state["trick_count"] == 13:
                state["step"] = "SCORING"
            st.rerun()

# =========================================================
# SCORING STAGE
# =========================================================

elif state["step"] == "SCORING":
    st.subheader("📊 Board Sonu")
    st.success(f"Biz: {state['score_decl']} | Onlar: {state['score_def']}")
    
    if st.button("🔄 Yeni Board"):
        st.session_state.clear()
        st.rerun()
