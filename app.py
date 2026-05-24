import streamlit as st
import random

# =========================================================
# TBF BRİÇ CORE ENGINE v7.5 OPTIMIZED STABLE
# =========================================================

st.set_page_config(
    page_title="TBF Briç Core Engine v7.5",
    layout="centered"
)

st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}
div.stButton > button {
    width: 100%;
    font-weight: bold;
    border-radius: 7px;
}
.table-box {
    padding: 14px;
    border-radius: 10px;
    background-color: #0f172a;
    color: white;
    margin-bottom: 10px;
}
.card-box {
    padding: 10px;
    border-radius: 8px;
    background-color: #f8fafc;
    color: black;
    margin-bottom: 10px;
    font-family: monospace;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# CORE CONSTANTS
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
# DECK
# =========================================================

class BridgeDeck:
    SUITS = ["♠", "♥", "♦", "♣"]
    RANKS = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]

    @staticmethod
    def generate_and_deal():
        deck = [
            f"{s}{r}"
            for s in BridgeDeck.SUITS
            for r in BridgeDeck.RANKS
        ]
        random.shuffle(deck)

        hands = {
            p: {"♠":[],"♥":[],"♦":[],"♣":[]}
            for p in PLAYERS
        }

        for idx, card in enumerate(deck):
            suit = card[0]
            rank = card[1:]
            hands[PLAYERS[idx % 4]][suit].append(rank)

        rank_order = {v:i for i,v in enumerate(BridgeDeck.RANKS)}

        for p in PLAYERS:
            for s in BridgeDeck.SUITS:
                hands[p][s].sort(
                    key=lambda x: rank_order[x],
                    reverse=True
                )
        return hands

# =========================================================
# HAND EVALUATOR
# =========================================================

class HandEvaluator:
    @staticmethod
    def get_hcp(hand):
        values = {"A":4, "K":3, "Q":2, "J":1}
        hcp = 0
        for suit in hand:
            for card in hand[suit]:
                hcp += values.get(card, 0)
        return hcp

# =========================================================
# BIDDING LEGALITY ENGINE (FIXED)
# =========================================================

class BiddingLegalityEngine:
    @staticmethod
    def last_real_bid_meta(history):
        """Son yapılan geçerli kontrat teklifini ve kimin verdiğini döner"""
        for b in reversed(history):
            if b["bid"] not in ["PAS", "X", "XX"]:
                return b
        return None

    @staticmethod
    def is_legal(proposed_bid, history, current_player):
        if proposed_bid == "PAS":
            return True

        last_meta = BiddingLegalityEngine.last_real_bid_meta(history)

        # AÇILIŞ DEKLARESİ KONTROLLERİ
        if not last_meta:
            return proposed_bid not in ["X", "XX"]

        # KONTRA (X) - Sadece rakibin teklifine atılabilir
        if proposed_bid == "X":
            if history[-1]["bid"] in ["X", "XX"]:
                return False
            # Ortaklık kontrolü (Rakiplerimizden biri mi açtı?)
            opponents = ["Batı", "Doğu"] if current_player in ["Kuzey", "Güney"] else ["Kuzey", "Güney"]
            return last_meta["player"] in opponents

        # SÜRKONTRA (XX) - Sadece ortağımızın teklifine rakip kontra attıysa atılabilir
        if proposed_bid == "XX":
            if not history: return False
            return history[-1]["bid"] == "X"

        # NORMAL KONTRAT ARTIRIMI YASALLIK KONTROLÜ
        last_bid = last_meta["bid"]
        last_level = int(last_bid[0])
        last_suit = last_bid[1:]

        prop_level = int(proposed_bid[0])
        prop_suit = proposed_bid[1:]

        if prop_level > last_level:
            return True
        if prop_level < last_level:
            return False

        return SUIT_ORDER[prop_suit] > SUIT_ORDER[last_suit]

# =========================================================
# AUCTION RESOLVER
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

            decl_idx = PLAYERS.index(declarer)
            leader = PLAYERS[(decl_idx + 1) % 4]
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
# CARD TRACKER (SYNTAX FIXED)
# =========================================================

class CardTracker:
    def __init__(self):
        self.played_cards = []
        self.suit_counts = {"♠":0, "♥":0, "♦":0, "♣":0} # Virgül hatası düzeltildi
        self.void_inference = {
            p: {"♠":False, "♥":False, "♦":False, "♣":False}
            for p in PLAYERS
        }

    def log_card(self, player, card):
        self.played_cards.append(card)
        suit = card[0]
        self.suit_counts[suit] += 1

    def analyze_void(self, player, played_suit, led_suit):
        if led_suit and played_suit != led_suit:
            self.void_inference[player][led_suit] = True

    def get_remaining(self, suit):
        return 13 - self.suit_counts[suit]

# =========================================================
# AUCTION AI
# =========================================================

class AuctionAI:
    @staticmethod
    def generate_bid(player, hand, history):
        hcp = HandEvaluator.get_hcp(hand)
        spades = len(hand["♠"])
        hearts = len(hand["♥"])
        meaningful = [b for b in history if b["bid"] != "PAS"]

        def legal(bid):
            if BiddingLegalityEngine.is_legal(bid, history, player):
                return bid
            return "PAS"

        # OPENING
        if not meaningful:
            if 15 <= hcp <= 17:
                if spades < 5 and hearts < 5:
                    return legal("1NT")
            if hcp >= 12:
                if spades >= 5: return legal("1♠")
                if hearts >= 5: return legal("1♥")
                if len(hand["♦"]) >= len(hand["♣"]): return legal("1♦")
                return legal("1♣")
            return "PAS"

        # RESPONSES
        partner = "Batı" if player == "Doğu" else "Kuzey"
        partner_bids = [b for b in history if b["player"] == partner]

        if partner_bids:
            pbid = partner_bids[-1]["bid"]

            # STAYMAN / TRANSFER
            if pbid == "1NT":
                if hearts >= 5 and hcp >= 5: return legal("2♦")
                if spades >= 5 and hcp >= 5: return legal("2♥")
                if ((spades == 4 or hearts == 4) and hcp >= 8): return legal("2♣")

            # FIT DESTEKLERİ
            if pbid == "1♠" and spades >= 3 and hcp >= 6: return legal("2♠")
            if pbid == "1♥" and hearts >= 3 and hcp >= 6: return legal("2♥")

        return "PAS"

# =========================================================
# PLAY LOGIC
# =========================================================

class BridgeLogic:
    @staticmethod
    def determine_trick_winner(trick_cards, led_suit, trump_suit):
        winner = trick_cards[0]
        for played in trick_cards[1:]:
            w_suit = winner["card"][0]
            w_rank = winner["card"][1:]
            p_suit = played["card"][0]
            p_rank = played["card"][1:]

            if p_suit == w_suit:
                if CARD_RANK[p_rank] > CARD_RANK[w_rank]: winner = played
            elif (p_suit == trump_suit and trump_suit != "NT" and w_suit != trump_suit):
                winner = played
            elif (p_suit == trump_suit and w_suit == trump_suit):
                if CARD_RANK[p_rank] > CARD_RANK[w_rank]: winner = played
        return winner

# =========================================================
# STRATEGIC AI
# =========================================================

class StrategicAI:
    @staticmethod
    def play_card(bot_name, hand, trick_history, trump_suit, void_memory, declarer_side):
        # OPENING LEAD
        if not trick_history:
            safe_suits = ["♠","♥","♦","♣"]
            for opp in declarer_side:
                for s in ["♠","♥","♦","♣"]:
                    if void_memory[opp][s] and s in safe_suits:
                        safe_suits.remove(s)

            if not safe_suits:
                safe_suits = ["♠","♥","♦","♣"]

            # TOP OF SEQUENCE
            for s in safe_suits:
                if len(hand[s]) >= 3:
                    c1 = CARD_RANK[hand[s][0]]
                    c2 = CARD_RANK[hand[s][1]]
                    c3 = CARD_RANK[hand[s][2]]
                    if c1-c2 == 1 and c2-c3 == 1:
                        return f"{s}{hand[s].pop(0)}"

            # 4TH BEST
            for s in safe_suits:
                if (len(hand[s]) >= 4 and any(c in hand[s] for c in ["A","K","Q","J"])):
                    return f"{s}{hand[s].pop(3)}"

            # FALLBACK
            for s in safe_suits:
                if hand[s]: return f"{s}{hand[s].pop(-1)}"

        # FOLLOW SUIT
        led = trick_history[0]["card"][0]
        if hand[led]:
            partner_led = len(trick_history) == 2
            if (partner_led and any(c in hand[led] for c in ["A","K","Q"])):
                return f"{led}{hand[led].pop(0)}"
            return f"{led}{hand[led].pop(-1)}"

        # RUFF
        if trump_suit != "NT" and hand[trump_suit]:
            return f"{trump_suit}{hand[trump_suit].pop(-1)}"

        # DISCARD
        for s in ["♣","♦","♥","♠"]:
            if hand[s]: return f"{s}{hand[s].pop(-1)}"
        return None

# =========================================================
# SCORING
# =========================================================

class AdvancedScoring:
    @staticmethod
    def calculate_score(contract, tricks_won, vulnerable=False, doubled=False, redoubled=False):
        level = int(contract[0])
        trump = contract[1:]
        target = level + 6

        # DOWN (BATIK HESAPLAYICI)
        if tricks_won < target:
            down = target - tricks_won
            if doubled: penalty = 200 if vulnerable else 100
            elif redoubled: penalty = 400 if vulnerable else 200
            else: penalty = 100 if vulnerable else 50
            total = penalty * down
            return {"status":"DOWN", "score":-total, "msg":f"{down} battı | Skor: -{total}"}

        # MADE (BAŞARILI KONTRAT HESAPLAYICI)
        multiplier = 30 if trump in ["♠","♥","NT"] else 20
        trick_score = level * multiplier
        if trump == "NT": trick_score += 10

        if doubled: trick_score *= 2
        if redoubled: trick_score *= 4

        bonus = 500 if vulnerable else 300 if trick_score >= 100 else 50
        if level == 6: bonus += 750 if vulnerable else 500
        if level == 7: bonus += 1500 if vulnerable else 1000

        over = tricks_won - target
        if doubled: over_score = over * (200 if vulnerable else 100)
        elif redoubled: over_score = over * (400 if vulnerable else 200)
        else: over_score = over * (30 if trump in ["♠","♥","NT"] else 20)

        total = trick_score + bonus + over_score
        return {"status":"MADE", "score":total, "msg":f"Kontrat yapıldı | Skor: +{total}"}

# =========================================================
# STATE INIT
# =========================================================

if "bridge_v7" not in st.session_state:
    st.session_state.bridge_v7 = {
        "step":"AUCTION",
        "hands":BridgeDeck.generate_and_deal(),
        "bidding_history":[],
        "trick_history":[],
        "tracker":CardTracker(),
        "contract_meta":None,
        "current_turn":"Batı",
        "trick_count":0,
        "score_decl":0,
        "score_def":0,
        "vulnerable":random.choice([True, False])
    }

state = st.session_state.bridge_v7

# =========================================================
# UI MAIN RENDER
# =========================================================

st.title("🃏 TBF Briç Core Engine v7.5")

st.sidebar.metric(
    "Zon Durumu",
    "ZONDA" if state["vulnerable"] else "ZONSUZ"
)

# --- AUCTION STAGE ---
if state["step"] == "AUCTION":
    st.subheader("💬 Müzayede")
    south = state["hands"]["Güney"]

    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.write(f"Güney HCP: {HandEvaluator.get_hcp(south)}")
    for s,c in south.items():
        st.write(f"{s}: {' '.join(c)}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.write(f"Sıra: {state['current_turn']}")

    if state["bidding_history"]:
        st.code(" -> ".join([f"{b['player']}:{b['bid']}" for b in state["bidding_history"]]))

    resolution = AuctionResolver.resolve(state["bidding_history"])

    if resolution:
        if resolution == "PASS_OUT":
            st.warning("Pas geçildi.")
            if st.button("Yeni El"):
                st.session_state.clear()
                st.rerun()
        else:
            state["contract_meta"] = resolution
            st.success(f"Kontrat: {resolution['contract']} | Deklaran: {resolution['declarer']}")
            if st.button("Oyuna Geç"):
                state["step"] = "PLAY"
                state["current_turn"] = resolution["leader"]
                st.rerun()

    # HUMAN ACTIONS
    if state["current_turn"] == "Güney" and not resolution:
        bids = ["PAS", "1♠", "1NT", "2♣", "2♦", "2♥", "4♠"]
        cols = st.columns(len(bids))

        for idx,bid in enumerate(bids):
            legal = BiddingLegalityEngine.is_legal(bid, state["bidding_history"], "Güney")
            if cols[idx].button(bid, disabled=not legal, key=f"bid_{bid}"):
                state["bidding_history"].append({"player":"Güney", "bid":bid})
                state["current_turn"] = "Batı"
                st.rerun()

    # BOT ACTIONS
    elif not resolution:
        bot = state["current_turn"]
        bid = AuctionAI.generate_bid(bot, state["hands"][bot], state["bidding_history"])
        state["bidding_history"].append({"player":bot, "bid":bid})
        idx = PLAYERS.index(bot)
        state["current_turn"] = PLAYERS[(idx+1)%4]
        st.rerun()

# --- PLAY STAGE ---
elif state["step"] == "PLAY":
    meta = state["contract_meta"]
    trump = meta["contract"][1:] if meta["contract"][1:] in ["♠","♥","♦","♣"] else "NT"
    declarer_side = ["Güney","Kuzey"] if meta["declarer"] in ["Güney","Kuzey"] else ["Batı","Doğu"]

    st.subheader(f"🎴 Oyun | Kontrat: {meta['contract']}")

    c1,c2 = st.columns(2)
    c1.metric("Deklaran Lövesi", state["score_decl"])
    c2.metric("Defans Lövesi", state["score_def"])

    with st.sidebar.expander("🧠 Inference Memory", expanded=True):
        for s in ["♠","♥","♦","♣"]:
            st.write(f"{s} kalan: {state['tracker'].get_remaining(s)}")
        st.markdown("---")
        for p in PLAYERS:
            voids = [s for s,v in state["tracker"].void_inference[p].items() if v]
            if voids: st.error(f"{p}: {' '.join(voids)} VOID")

    st.write(f"Sıra: {state['current_turn']}")
    st.markdown("<div class='table-box'>", unsafe_allow_html=True)

    if state["trick_history"]:
        cols = st.columns(len(state["trick_history"]))
        for idx,p in enumerate(state["trick_history"]):
            cols[idx].markdown(f"**{p['player']}**\n\n`{p['card']}`")
    else:
        st.write("Yeni löve.")
    st.markdown("</div>", unsafe_allow_html=True)

    # DUMMY CARDS DISPLAY
    st.success(f"Yer ({meta['dummy']})")
    for s,cards in state["hands"][meta["dummy"]].items():
        st.write(f"{s}: {' '.join(cards)}")

    # ROBOT TURNS
    is_bot = state["current_turn"] not in ["Güney", meta["dummy"]]
    if is_bot:
        bot = state["current_turn"]
        card = StrategicAI.play_card(bot, state["hands"][bot], state["trick_history"], trump, state["tracker"].void_inference, declarer_side)
        if card:
            led = state["trick_history"][0]["card"][0] if state["trick_history"] else None
            state["tracker"].analyze_void(bot, card[0], led)
            state["tracker"].log_card(bot, card)
            state["trick_history"].append({"player":bot, "card":card})
            
            idx = PLAYERS.index(bot)
            state["current_turn"] = PLAYERS[(idx+1)%4]
            st.rerun()

    # HUMAN / DUMMY TURNS
    else:
        active = state["current_turn"]
        hand = state["hands"][active]
        led = state["trick_history"][0]["card"][0] if state["trick_history"] else None
        has_led = led and any(hand[led])

        for suit,cards in hand.items():
            if cards:
                cols = st.columns([1]+[1]*len(cards))
                cols[0].write(suit)
                for idx,val in enumerate(cards):
                    disabled = has_led and suit != led
                    if cols[idx+1].button(val, key=f"{active}_{suit}_{val}", disabled=disabled):
                        hand[suit].remove(val)
                        state["tracker"].analyze_void(active, suit, led)
                        state["tracker"].log_card(active, f"{suit}{val}")
                        state["trick_history"].append({"player":active, "card": f"{suit}{val}"})
                        
                        idxp = PLAYERS.index(active)
                        state["current_turn"] = PLAYERS[(idxp+1)%4]
                        st.rerun()

    # TRICK RESOLUTION WINDOW
    if len(state["trick_history"]) == 4:
        led_suit = state["trick_history"][0]["card"][0]
        winner_play = BridgeLogic.determine_trick_winner(state["trick_history"], led_suit, trump)
        winner = winner_play["player"]

        st.success(f"Löveyi alan: {winner} ({winner_play['card']})")
        if st.button("Löveyi Topla"):
            if winner in declarer_side: state["score_decl"] += 1
            else: state["score_def"] += 1

            state["trick_history"] = []
            state["current_turn"] = winner
            state["trick_count"] += 1

            if state["trick_count"] == 13:
                state["step"] = "SCORING"
            st.rerun()

# --- SCORING STAGE ---
elif state["step"] == "SCORING":
    st.subheader("📊 Skor")
    meta = state["contract_meta"]
    score = AdvancedScoring.calculate_score(meta["contract"], state["score_decl"], vulnerable=state["vulnerable"], doubled=meta["is_doubled"], redoubled=meta["is_redoubled"])

    if score["status"] == "MADE":
        st.success(score["msg"])
        st.balloons()
    else:
        st.error(score["msg"])

    if st.button("Yeni Board"):
        st.session_state.clear()
        st.rerun()
