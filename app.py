import streamlit as st
import random
import time

# =========================================================
# TBF BRİÇ AKADEMİ v20.0
# GELİŞMİŞ ALPHA AUCTION ENGINE
# =========================================================

st.set_page_config(
    page_title="TBF Briç Akademi v20.0",
    layout="centered"
)

# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.block-container{
    padding-top:1rem;
    padding-bottom:1rem;
}

.card-box{
    background:#f8fafc;
    padding:14px;
    border-radius:12px;
    border-left:5px solid #ef4444;
    margin-bottom:12px;
    font-family:monospace;
    font-size:19px;
    line-height:1.9;
}

.bid-history{
    background:#1e293b;
    color:white;
    padding:12px;
    border-radius:10px;
    overflow-x:auto;
    white-space:nowrap;
    margin-bottom:10px;
    font-size:18px;
}

.result-box{
    background:#dcfce7;
    color:#166534;
    padding:14px;
    border-radius:12px;
    margin-top:12px;
    font-weight:bold;
}

.error-box{
    background:#fee2e2;
    color:#991b1b;
    padding:14px;
    border-radius:12px;
    margin-top:12px;
    font-weight:bold;
}

div.stButton > button{
    width:100%;
    border-radius:10px;
    font-weight:bold;
    height:48px;
    font-size:17px;
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
    '2':2,
    '3':3,
    '4':4,
    '5':5,
    '6':6,
    '7':7,
    '8':8,
    '9':9,
    '10':10,
    'J':11,
    'Q':12,
    'K':13,
    'A':14
}

ALL_BIDS = [

    "PAS",

    "1♣","1♦","1♥","1♠","1NT",

    "2♣","2♦","2♥","2♠","2NT",

    "3♣","3♦","3♥","3♠","3NT",

    "4♣","4♦","4♥","4♠","4NT",

    "5♣","5♦","5♥","5♠","5NT",

    "6♣","6♦","6♥","6♠","6NT",

    "7♣","7♦","7♥","7♠","7NT",

    "X",
    "XX"
]

# =========================================================
# DECK ENGINE
# =========================================================

class BridgeDeck:

    @staticmethod
    def generate_and_deal():

        deck = [

            f"{s}{r}"

            for s in ["♠","♥","♦","♣"]

            for r in [
                "2","3","4","5","6","7",
                "8","9","10","J","Q","K","A"
            ]
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

            for s in ["♠","♥","♦","♣"]:

                hands[p][s].sort(
                    key=lambda x: CARD_RANK[x],
                    reverse=True
                )

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

    @staticmethod
    def is_balanced(hand):

        lengths = sorted([
            len(hand[s])
            for s in hand
        ])

        return lengths in [
            [2,3,4,4],
            [2,3,3,5],
            [3,3,3,4]
        ]

# =========================================================
# LEGALITY ENGINE
# =========================================================

class BiddingLegalityEngine:

    @staticmethod
    def is_legal(
        proposed,
        history
    ):

        if proposed == "PAS":
            return True

        bids = [

            b["bid"]

            for b in history

            if b["bid"] not in [
                "PAS",
                "X",
                "XX"
            ]
        ]

        if not bids:

            return proposed not in [
                "X",
                "XX"
            ]

        if proposed == "X":

            return history[-1]["bid"] not in [
                "X",
                "XX"
            ]

        if proposed == "XX":

            return history[-1]["bid"] == "X"

        ll = int(bids[-1][0])
        ls = bids[-1][1:]

        pl = int(proposed[0])
        ps = proposed[1:]

        return (
            pl > ll
            or
            (
                pl == ll
                and
                SUIT_ORDER[ps] > SUIT_ORDER[ls]
            )
        )

# =========================================================
# SIMPLE AI
# =========================================================

class AuctionAI:

    @staticmethod
    def generate_bid(
        player,
        hand,
        history
    ):

        hcp = HandEvaluator.get_hcp(hand)

        sp = len(hand["♠"])
        he = len(hand["♥"])
        di = len(hand["♦"])
        cl = len(hand["♣"])

        balanced = HandEvaluator.is_balanced(hand)

        candidates = []

        # 1NT
        if (
            15 <= hcp <= 17
            and balanced
        ):
            candidates.append("1NT")

        # 5li major

        if hcp >= 12 and sp >= 5:
            candidates.append("1♠")

        if hcp >= 12 and he >= 5:
            candidates.append("1♥")

        # minör açış

        if hcp >= 12:

            if di >= cl:
                candidates.append("1♦")
            else:
                candidates.append("1♣")

        # zayıf el

        if hcp < 12:
            candidates.append("PAS")

        # legality filtre

        for bid in candidates:

            if BiddingLegalityEngine.is_legal(
                bid,
                history
            ):
                return bid

        return "PAS"

# =========================================================
# AUCTION RESOLVER
# =========================================================

class AuctionResolver:

    @staticmethod
    def resolve(history):

        if len(history) < 4:
            return None

        last_three = history[-3:]

        if all(
            x["bid"] == "PAS"
            for x in last_three
        ):

            real_bids = [

                h for h in history

                if h["bid"] not in [
                    "PAS",
                    "X",
                    "XX"
                ]
            ]

            if not real_bids:

                return {
                    "type":"PASS_OUT",
                    "message":"El pas geçti."
                }

            final_bid = real_bids[-1]

            return {
                "type":"CONTRACT",
                "contract":final_bid["bid"],
                "declarer":final_bid["player"],
                "message":
                    f"Final Kontrat: "
                    f"{final_bid['bid']} - "
                    f"Deklaran: "
                    f"{final_bid['player']}"
            }

        return None

# =========================================================
# GAME INIT
# =========================================================

def init_game(mode):

    hands = BridgeDeck.generate_and_deal()

    history = []

    if mode == "Ortak Açışına Yanıtlar":

        north_bid = AuctionAI.generate_bid(
            "Kuzey",
            hands["Kuzey"],
            []
        )

        history.append({
            "player":"Kuzey",
            "bid":north_bid
        })

    return {

        "mode":mode,

        "hands":hands,

        "bidding_history":history,

        "current_turn":"Güney",

        "feedback":None,

        "auction_finished":False
    }

# =========================================================
# SESSION
# =========================================================

if "bridge_v20" not in st.session_state:

    st.session_state.bridge_v20 = init_game(
        "Kendi Açılış Pratiğiniz"
    )

state = st.session_state.bridge_v20

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("🎓 Briç Eğitim")

    mode = st.radio(
        "Mod:",
        [
            "Kendi Açılış Pratiğiniz",
            "Ortak Açışına Yanıtlar",
            "Turnuva Sekansı"
        ]
    )

    if mode != state["mode"]:

        st.session_state.bridge_v20 = init_game(mode)

        st.rerun()

    if st.button("🔄 Yeni El"):

        st.session_state.bridge_v20 = init_game(
            state["mode"]
        )

        st.rerun()

# =========================================================
# TITLE
# =========================================================

st.title("🃏 TBF Briç Akademi v20.0")

# =========================================================
# HAND
# =========================================================

south = state["hands"]["Güney"]

hcp = HandEvaluator.get_hcp(south)

st.write(f"### {state['mode']}")
st.write(f"### HCP: {hcp}")

st.markdown(
    f"""
    <div class='card-box'>
    ♠ {' '.join(south['♠'])}<br>
    ♥ {' '.join(south['♥'])}<br>
    ♦ {' '.join(south['♦'])}<br>
    ♣ {' '.join(south['♣'])}
    </div>
    """,
    unsafe_allow_html=True
)

# =========================================================
# HISTORY
# =========================================================

if state["bidding_history"]:

    st.markdown(
        f"""
        <div class='bid-history'>
        {' → '.join([
            f"{b['player']}:{b['bid']}"
            for b in state["bidding_history"]
        ])}
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================================================
# FEEDBACK
# =========================================================

if state["feedback"]:

    if isinstance(state["feedback"], dict):

        msg = state["feedback"]["message"]

    else:

        msg = str(state["feedback"])

    st.markdown(
        f"""
        <div class='result-box'>
        {msg}
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("➡ Yeni Ele Geç"):

        st.session_state.bridge_v20 = init_game(
            state["mode"]
        )

        st.rerun()

# =========================================================
# BOT ENGINE
# =========================================================

if (
    state["mode"] == "Turnuva Sekansı"
    and
    not state["feedback"]
):

    while (
        state["current_turn"] != "Güney"
        and
        not state["auction_finished"]
    ):

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

        result = AuctionResolver.resolve(
            state["bidding_history"]
        )

        if result:

            state["feedback"] = result

            state["auction_finished"] = True

            break

        next_player = PLAYERS[
            (PLAYERS.index(bot)+1)%4
        ]

        state["current_turn"] = next_player

# =========================================================
# USER BIDDING
# =========================================================

if (
    not state["feedback"]
    and
    state["current_turn"] == "Güney"
):

    for i in range(0, len(ALL_BIDS), 3):

        cols = st.columns(3)

        for j in range(3):

            if i+j < len(ALL_BIDS):

                bid = ALL_BIDS[i+j]

                legal = (
                    BiddingLegalityEngine
                    .is_legal(
                        bid,
                        state["bidding_history"]
                    )
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

                    result = AuctionResolver.resolve(
                        state["bidding_history"]
                    )

                    if result:

                        state["feedback"] = result

                        state["auction_finished"] = True

                    else:

                        next_player = PLAYERS[
                            (
                                PLAYERS.index("Güney")
                                + 1
                            ) % 4
                        ]

                        state["current_turn"] = next_player

                    st.rerun()
