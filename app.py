# TBF Briç Akademi v13.0 — Full Stabilized Engine


import streamlit as st
import random

# =========================================================
# TBF BRİÇ AKADEMİ v13.0
# FULL STABILIZED ENGINE
# =========================================================

st.set_page_config(
    page_title="TBF Briç Akademi v13.0",
    layout="centered"
)

# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.block-container {
    padding-top: 0.7rem;
    padding-bottom: 1rem;
    padding-left: 0.7rem;
    padding-right: 0.7rem;
}

.card-box {
    background:#f8fafc;
    padding:12px;
    border-radius:10px;
    border-left:5px solid #ef4444;
    margin-bottom:10px;
}

.bid-history {
    background:#1e293b;
    color:white;
    padding:10px;
    border-radius:10px;
    overflow-x:auto;
    white-space:nowrap;
    margin-bottom:10px;
}

.table-box {
    background:#0f172a;
    color:white;
    padding:12px;
    border-radius:10px;
    margin-bottom:10px;
}

.mobile-cards {
    font-size:21px;
    line-height:2.0;
    font-family:monospace;
}

div.stButton > button {
    width:100%;
    height:52px;
    border-radius:10px;
    font-weight:bold;
    font-size:17px !important;
}

@media (max-width: 768px) {

    .mobile-cards {
        font-size:22px;
    }

    div.stButton > button {
        height:56px;
        font-size:18px !important;
    }
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# CONSTANTS
# =========================================================

PLAYERS = ["Batı", "Kuzey", "Doğu", "Güney"]

SUIT_ORDER = {
    "♣":1,
    "♦":2,
    "♥":3,
    "♠":4,
    "NT":5
}

CARD_RANK = {
    '2':2,'3':3,'4':4,'5':5,'6':6,'7':7,
    '8':8,'9':9,'10':10,'J':11,'Q':12,'K':13,'A':14
}

# =========================================================
# HELPERS
# =========================================================


def next_player(player):

    return PLAYERS[
        (PLAYERS.index(player)+1)%4
    ]


def get_axis(player):

    if player in ["Kuzey", "Güney"]:
        return ["Kuzey", "Güney"]

    return ["Batı", "Doğu"]

# =========================================================
# DECK
# =========================================================

class BridgeDeck:

    SUITS = ["♠","♥","♦","♣"]

    RANKS = [
        "2","3","4","5","6","7",
        "8","9","10","J","Q","K","A"
    ]

    @staticmethod
    def sort_hand(hand):

        for s in BridgeDeck.SUITS:

            hand[s].sort(
                key=lambda x: CARD_RANK[x],
                reverse=True
            )

        return hand

    @staticmethod
    def generate_and_deal():

        deck = [
            f"{s}{r}"
            for s in BridgeDeck.SUITS
            for r in BridgeDeck.RANKS
        ]

        random.shuffle(deck)

        hands = {
            p:{
                "♠":[],
                "♥":[],
                "♦":[],
                "♣":[]
            }
            for p in PLAYERS
        }

        for idx, card in enumerate(deck):

            suit = card[0]
            rank = card[1:]

            hands[
                PLAYERS[idx % 4]
            ][suit].append(rank)

        for p in PLAYERS:
            hands[p] = BridgeDeck.sort_hand(hands[p])

        return hands

# =========================================================
# HAND EVALUATOR
# =========================================================

class HandEvaluator:

    @staticmethod
    def get_hcp(hand):

        vals = {
            "A":4,
            "K":3,
            "Q":2,
            "J":1
        }

        total = 0

        for s in hand:
            for c in hand[s]:
                total += vals.get(c, 0)

        return total

# =========================================================
# CARD TRACKER
# =========================================================

class CardTracker:

    def __init__(self):

        self.played = []

        self.void_memory = {
            p:{
                "♠":False,
                "♥":False,
                "♦":False,
                "♣":False
            }
            for p in PLAYERS
        }

    def analyze_void(
        self,
        player,
        played_suit,
        led_suit
    ):

        if led_suit and played_suit != led_suit:
            self.void_memory[player][led_suit] = True

# =========================================================
# BIDDING LEGALITY
# =========================================================

class BiddingLegalityEngine:

    @staticmethod
    def last_real_bid(history):

        bids = [
            b for b in history
            if b["bid"] not in ["PAS", "X", "XX"]
        ]

        return bids[-1] if bids else None

    @staticmethod
    def is_legal(
        proposed,
        history,
        current_player
    ):

        if proposed == "PAS":
            return True

        last_real = BiddingLegalityEngine.last_real_bid(history)

        if not last_real:
            return proposed not in ["X", "XX"]

        # DOUBLE

        if proposed == "X":

            if history[-1]["bid"] in ["X", "XX"]:
                return False

            bidder_axis = get_axis(last_real["player"])
            current_axis = get_axis(current_player)

            return bidder_axis != current_axis

        # REDOUBLE

        if proposed == "XX":

            if history[-1]["bid"] != "X":
                return False

            last_bidder_axis = get_axis(
                history[-2]["player"]
            )

            current_axis = get_axis(current_player)

            return last_bidder_axis == current_axis

        # NORMAL BID

        ll = int(last_real["bid"][0])
        ls = last_real["bid"][1:]

        pl = int(proposed[0])
        ps = proposed[1:]

        if pl > ll:
            return True

        if pl < ll:
            return False

        return SUIT_ORDER[ps] > SUIT_ORDER[ls]

# =========================================================
# AUCTION AI
# =========================================================

class AuctionAI:

    @staticmethod
    def generate_bid(player, hand, history):

        hcp = HandEvaluator.get_hcp(hand)

        sp = len(hand["♠"])
        he = len(hand["♥"])

        longest = max(
            len(hand[s])
            for s in hand
        )

        # OPENING

        if not history:

            if hcp < 9 and longest < 7:
                return "PAS"

            if 15 <= hcp <= 17:
                if sp < 5 and he < 5:
                    return "1NT"

            if sp >= 5 and hcp >= 12:
                return "1♠"

            if he >= 5 and hcp >= 12:
                return "1♥"

            if hcp >= 12:
                return "1♣"

            if longest >= 7:

                if sp >= 7:
                    return "2♠"

                if he >= 7:
                    return "2♥"

            return "PAS"

        # RESPONSES

        partner = (
            "Batı"
            if player == "Doğu"
            else "Kuzey"
        )

        partner_bids = [
            b for b in history
            if b["player"] == partner
        ]

        if partner_bids:

            pbid = partner_bids[-1]["bid"]

            # STAYMAN

            if pbid == "1NT":

                if hcp >= 8:

                    if sp == 4 or he == 4:
                        return "2♣"

            # FIT SUPPORT

            if pbid == "1♠":

                if sp >= 3 and hcp >= 6:
                    return "2♠"

            if pbid == "1♥":

                if he >= 3 and hcp >= 6:
                    return "2♥"

        return "PAS"

# =========================================================
# AUCTION RESOLVER
# =========================================================

class AuctionResolver:

    @staticmethod
    def resolve(history):

        if len(history) < 4:
            return None

        # PASS OUT

        if (
            len(history) >= 4
            and all(
                h["bid"] == "PAS"
                for h in history[-4:]
            )
        ):
            return "PASS_OUT"

        # NORMAL END

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

                if b["bid"] == "XX":
                    redoubled = True

                elif b["bid"] == "X":
                    doubled = True

                elif b["bid"] != "PAS":

                    final_bid = b["bid"]
                    final_player = b["player"]
                    break

            if not final_bid:
                return "PASS_OUT"

            trump = final_bid[1:]

            axis = get_axis(final_player)

            declarer = final_player

            for b in history:

                if (
                    b["player"] in axis
                    and b["bid"] not in ["PAS", "X", "XX"]
                    and b["bid"][1:] == trump
                ):

                    declarer = b["player"]
                    break

            leader = next_player(declarer)

            dummy = [
                p for p in axis
                if p != declarer
            ][0]

            return {
                "contract":final_bid,
                "declarer":declarer,
                "leader":leader,
                "dummy":dummy,
                "is_doubled":doubled,
                "is_redoubled":redoubled
            }

        return None

# =========================================================
# PLAY LOGIC
# =========================================================

class BridgeLogic:

    @staticmethod
    def determine_trick_winner(
        trick,
        trump
    ):

        winner = trick[0]

        for p in trick[1:]:

            ws = winner["card"][0]
            wr = winner["card"][1:]

            ps = p["card"][0]
            pr = p["card"][1:]

            # SAME SUIT

            if ps == ws:

                if CARD_RANK[pr] > CARD_RANK[wr]:
                    winner = p

            # RUFF

            elif (
                ps == trump
                and trump != "NT"
                and ws != trump
            ):
                winner = p

            # OVERRUFF

            elif (
                ps == trump
                and ws == trump
            ):

                if CARD_RANK[pr] > CARD_RANK[wr]:
                    winner = p

        return winner

# =========================================================
# DEAL FILTER
# =========================================================


def deal_filtered_hands():

    while True:

        hands = BridgeDeck.generate_and_deal()

        south_hcp = HandEvaluator.get_hcp(
            hands["Güney"]
        )

        longest = max(
            len(hands["Güney"][s])
            for s in hands["Güney"]
        )

        if south_hcp >= 9 or longest >= 7:
            return hands

# =========================================================
# STATE
# =========================================================

if "bridge_v13" not in st.session_state:

    st.session_state.bridge_v13 = {

        "step":"AUCTION",

        "hands":deal_filtered_hands(),

        "bidding_history":[],

        "trick_history":[],

        "tracker":CardTracker(),

        "current_turn":random.choice(PLAYERS),

        "mode":"Turnuva Sekansı",

        "contract_meta":None,

        "score_decl":0,

        "score_def":0,

        "trick_count":0
    }

state = st.session_state.bridge_v13

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("🎓 Eğitim Modları")

    mode = st.radio(
        "Mod:",
        [
            "Kendi Açılış Pratiğiniz",
            "Ortak Açışına Yanıtlar",
            "Turnuva Sekansı"
        ]
    )

    if mode != state["mode"]:

        state["mode"] = mode

        state["step"] = "AUCTION"

        state["hands"] = deal_filtered_hands()

        state["bidding_history"] = []

        state["trick_history"] = []

        state["tracker"] = CardTracker()

        state["score_decl"] = 0
        state["score_def"] = 0

        state["trick_count"] = 0

        if mode == "Kendi Açılış Pratiğiniz":
            state["current_turn"] = "Güney"

        elif mode == "Ortak Açışına Yanıtlar":

            state["bidding_history"] = [
                {
                    "player":"Kuzey",
                    "bid":"1NT"
                }
            ]

            state["current_turn"] = "Güney"

        else:
            state["current_turn"] = random.choice(PLAYERS)

        st.rerun()

    if st.button("🔄 Yeni El"):

        st.session_state.clear()
        st.rerun()

# =========================================================
# TITLE
# =========================================================

st.title("🃏 TBF Briç Akademi v13.0")

# =========================================================
# AUCTION
# =========================================================

if state["step"] == "AUCTION":

    st.subheader("💬 Müzayede")

    south = state["hands"]["Güney"]

    hcp = HandEvaluator.get_hcp(south)

    st.markdown("<div class='card-box'>", unsafe_allow_html=True)

    st.write(f"HCP: {hcp}")

    st.markdown(
        f"""
        <div class='mobile-cards'>
        ♠ {' '.join(south['♠'])}<br>
        ♥ {' '.join(south['♥'])}<br>
        ♦ {' '.join(south['♦'])}<br>
        ♣ {' '.join(south['♣'])}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("</div>", unsafe_allow_html=True)

    if state["bidding_history"]:

        st.markdown(
            f"""
            <div class='bid-history'>
            {' -> '.join([
                f"{b['player']}:{b['bid']}"
                for b in state['bidding_history']
            ])}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write(f"### Sıra: {state['current_turn']}")

    # RESOLUTION

    resolution = AuctionResolver.resolve(
        state["bidding_history"]
    )

    if resolution:

        if resolution == "PASS_OUT":

            st.warning("Board PAS geçti.")

        else:

            state["contract_meta"] = resolution

            st.success(
                f"Kontrat: {resolution['contract']} | "
                f"Deklaran: {resolution['declarer']}"
            )

            if st.button("Oyuna Başla"):

                state["step"] = "PLAY"

                state["current_turn"] = resolution["leader"]

                st.rerun()

    # HUMAN

    if (
        state["current_turn"] == "Güney"
        and not resolution
    ):

        bids = [
            "PAS","X","XX",
            "1♣","1♦","1♥",
            "1♠","1NT","2♣",
            "2♦","2♥","2♠",
            "2NT","3♣","3♦",
            "3♥","3♠","3NT"
        ]

        for i in range(0, len(bids), 3):

            cols = st.columns(3)

            for j in range(3):

                if i+j < len(bids):

                    bid = bids[i+j]

                    legal = BiddingLegalityEngine.is_legal(
                        bid,
                        state["bidding_history"],
                        "Güney"
                    )

                    if cols[j].button(
                        bid,
                        disabled=not legal,
                        key=f"{bid}_{i}_{j}"
                    ):

                        state["bidding_history"].append({
                            "player":"Güney",
                            "bid":bid
                        })

                        state["current_turn"] = next_player("Güney")

                        st.rerun()

    # ROBOTS

    elif not resolution:

        bot = state["current_turn"]

        bid = AuctionAI.generate_bid(
            bot,
            state["hands"][bot],
            state["bidding_history"]
        )

        state["bidding_history"].append({
            "player":bot,
            "bid":bid
        })

        state["current_turn"] = next_player(bot)

        st.rerun()

# =========================================================
# PLAY
# =========================================================

elif state["step"] == "PLAY":

    meta = state["contract_meta"]

    trump = meta["contract"][1:]

    decl_side = get_axis(meta["declarer"])

    st.subheader(
        f"🎴 Oyun | {meta['contract']}"
    )

    c1,c2 = st.columns(2)

    c1.metric(
        "Deklaran",
        state["score_decl"]
    )

    c2.metric(
        "Defans",
        state["score_def"]
    )

    # TABLE

    st.markdown(
        "<div class='table-box'>",
        unsafe_allow_html=True
    )

    if state["trick_history"]:

        cols = st.columns(4)

        for idx,p in enumerate(state["trick_history"]):

            cols[idx].write(
                f"{p['player']}\n{p['card']}"
            )

    else:
        st.write("Yeni löve")

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    # DUMMY

    with st.expander(
        f"Yer ({meta['dummy']})",
        expanded=True
    ):

        dhand = state["hands"][meta["dummy"]]

        st.markdown(
            f"""
            <div class='mobile-cards'>
            ♠ {' '.join(dhand['♠'])}<br>
            ♥ {' '.join(dhand['♥'])}<br>
            ♦ {' '.join(dhand['♦'])}<br>
            ♣ {' '.join(dhand['♣'])}
            </div>
            """,
            unsafe_allow_html=True
        )

    # HUMAN PLAY

    human_side = ["Güney", meta["dummy"]]

    if state["current_turn"] in human_side:

        active = state["current_turn"]

        hand = state["hands"][active]

        led = (
            state["trick_history"][0]["card"][0]
            if state["trick_history"]
            else None
        )

        has_led = led and any(hand[led])

        st.write(f"### Sıra: {active}")

        for s,cards in hand.items():

            if cards:

                st.write(
                    f"### {s} {' '.join(cards)}"
                )

                cols = st.columns(
                    min(4, len(cards))
                )

                for idx,val in enumerate(cards):

                    disabled = (
                        has_led
                        and s != led
                    )

                    if cols[idx % 4].button(
                        val,
                        disabled=disabled,
                        key=f"{active}_{s}_{val}"
                    ):

                        hand[s].remove(val)

                        state["tracker"].analyze_void(
                            active,
                            s,
                            led
                        )

                        state["trick_history"].append({
                            "player":active,
                            "card":f"{s}{val}"
                        })

                        state["current_turn"] = next_player(active)

                        st.rerun()

    # ROBOT PLAY

    else:

        active = state["current_turn"]

        hand = state["hands"][active]

        led = (
            state["trick_history"][0]["card"][0]
            if state["trick_history"]
            else None
        )

        selected = None

        # FOLLOW SUIT

        if led and hand[led]:
            selected = f"{led}{hand[led].pop(-1)}"

        # RUFF

        elif trump != "NT" and hand[trump]:
            selected = f"{trump}{hand[trump].pop(-1)}"

        # DISCARD

        else:

            for s in ["♣","♦","♥","♠"]:

                if hand[s]:

                    selected = f"{s}{hand[s].pop(-1)}"
                    break

        if selected:

            state["tracker"].analyze_void(
                active,
                selected[0],
                led
            )

            state["trick_history"].append({
                "player":active,
                "card":selected
            })

            state["current_turn"] = next_player(active)

            st.rerun()

    # TRICK END

    if len(state["trick_history"]) == 4:

        winner = BridgeLogic.determine_trick_winner(
            state["trick_history"],
            trump
        )

        st.success(
            f"Löveyi alan: {winner['player']}"
        )

        if st.button("Löveyi Topla"):

            if winner["player"] in decl_side:
                state["score_decl"] += 1
            else:
                state["score_def"] += 1

            state["trick_history"] = []

            state["current_turn"] = winner["player"]

            state["trick_count"] += 1

            if state["trick_count"] == 13:
                st.balloons()

            st.rerun()
```
