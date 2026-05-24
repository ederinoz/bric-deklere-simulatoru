import streamlit as st
import random

# =========================================================
# TBF BRİÇ AKADEMİ v40.0
# SINGLE TOURNAMENT MODE
# =========================================================

st.set_page_config(
    page_title="TBF Briç Akademi v40.0",
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
    margin-bottom:12px;
    font-size:17px;
}

.result-box{
    background:#dcfce7;
    color:#166534;
    padding:14px;
    border-radius:12px;
    margin-top:12px;
    font-weight:bold;
    font-size:18px;
}

.north-box{
    background:#eff6ff;
    color:#1e3a8a;
    padding:14px;
    border-radius:12px;
    margin-top:12px;
    font-family:monospace;
    font-size:17px;
    line-height:1.8;
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
# DECK
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
    def is_legal(proposed, history):

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
# AI
# =========================================================

class AuctionAI:

    @staticmethod
    def generate_bid(hand, history):

        hcp = HandEvaluator.get_hcp(hand)

        sp = len(hand["♠"])
        he = len(hand["♥"])
        di = len(hand["♦"])
        cl = len(hand["♣"])

        balanced = HandEvaluator.is_balanced(hand)

        candidates = []

        # =====================================================
        # RESPONSE LOGIC
        # =====================================================

        if history:

            partner_bid = history[-1]["bid"]

            # Stayman

            if partner_bid == "1NT":

                if (
                    hcp >= 8
                    and
                    (sp >= 4 or he >= 4)
                ):

                    candidates.append("2♣")

            # support raises

            if partner_bid == "1♠":

                if sp >= 3 and hcp >= 6:

                    if hcp <= 9:
                        candidates.append("2♠")
                    elif hcp <= 12:
                        candidates.append("3♠")
                    else:
                        candidates.append("4♠")

            if partner_bid == "1♥":

                if he >= 3 and hcp >= 6:

                    if hcp <= 9:
                        candidates.append("2♥")
                    elif hcp <= 12:
                        candidates.append("3♥")
                    else:
                        candidates.append("4♥")

            # simple overcalls

            if hcp >= 9:

                if sp >= 5:
                    candidates.append("2♠")

                if he >= 5:
                    candidates.append("2♥")

        # =====================================================
        # OPENING LOGIC
        # =====================================================

        if (
            15 <= hcp <= 17
            and balanced
        ):
            candidates.append("1NT")

        if hcp >= 12 and sp >= 5:
            candidates.append("1♠")

        if hcp >= 12 and he >= 5:
            candidates.append("1♥")

        if hcp >= 12:

            if di >= cl:
                candidates.append("1♦")
            else:
                candidates.append("1♣")

        candidates.append("PAS")

        # =====================================================
        # LEGAL FILTER
        # =====================================================

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

        # pass out

        if all(
            h["bid"] == "PAS"
            for h in history[-4:]
        ):

            return {
                "message":
                    "Tüm oyuncular PAS dedi. El pas geçti."
            }

        # contract

        last_three = history[-3:]

        if all(
            h["bid"] == "PAS"
            for h in last_three
        ):

            real_bids = [

                h for h in history

                if h["bid"] not in [
                    "PAS",
                    "X",
                    "XX"
                ]
            ]

            if real_bids:

                final_bid = real_bids[-1]

                return {
                    "message":
                        f"Final Kontrat: "
                        f"{final_bid['bid']} | "
                        f"Deklaran: "
                        f"{final_bid['player']}"
                }

        return None

# =========================================================
# INIT GAME
# =========================================================

def init_game():

    hands = BridgeDeck.generate_and_deal()

    dealer = random.choice(PLAYERS)

    return {

        "hands":hands,

        "dealer":dealer,

        "current_turn":dealer,

        "bidding_history":[],

        "auction_finished":False,

        "feedback":None
    }

# =========================================================
# SESSION
# =========================================================

if "bridge_v40" not in st.session_state:

    st.session_state.bridge_v40 = init_game()

state = st.session_state.bridge_v40

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("🃏 Turnuva Sekansı")

    st.write(f"Dealer: {state['dealer']}")

    if st.button("🔄 Yeni El"):

        st.session_state.bridge_v40 = init_game()

        st.rerun()

# =========================================================
# TITLE
# =========================================================

st.title("🃏 TBF Briç Akademi v40.0")

# =========================================================
# SOUTH HAND
# =========================================================

south = state["hands"]["Güney"]

hcp = HandEvaluator.get_hcp(south)

st.write(f"### Güney")
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
# RESULT
# =========================================================

if state["feedback"] is not None:

    st.markdown(
        f"""
        <div class='result-box'>
        {state["feedback"]}
        </div>
        """,
        unsafe_allow_html=True
    )

    north = state["hands"]["Kuzey"]

    st.markdown(
        f"""
        <div class='north-box'>

        <b>Kuzey Eli</b><br><br>

        ♠ {' '.join(north['♠'])}<br>
        ♥ {' '.join(north['♥'])}<br>
        ♦ {' '.join(north['♦'])}<br>
        ♣ {' '.join(north['♣'])}

        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("➡ Yeni Ele Geç"):

        st.session_state.bridge_v40 = init_game()

        st.rerun()

    st.stop()

# =========================================================
# BOT PLAY
# =========================================================

if (
    not state["auction_finished"]
    and
    state["current_turn"] != "Güney"
):

    loop_guard = 0
    changed = False

    while (
        state["current_turn"] != "Güney"
        and
        not state["auction_finished"]
    ):

        loop_guard += 1

        if loop_guard > 20:
            break

        bot = state["current_turn"]

        bid = AuctionAI.generate_bid(
            state["hands"][bot],
            state["bidding_history"]
        )

        if not BiddingLegalityEngine.is_legal(
            bid,
            state["bidding_history"]
        ):
            bid = "PAS"

        state["bidding_history"].append({
            "player":bot,
            "bid":bid
        })

        changed = True

        result = AuctionResolver.resolve(
            state["bidding_history"]
        )

        if result:

            state["feedback"] = result["message"]

            state["auction_finished"] = True

            break

        current_index = PLAYERS.index(
            state["current_turn"]
        )

        state["current_turn"] = PLAYERS[
            (current_index + 1) % 4
        ]

    if changed:
        st.rerun()

# =========================================================
# USER PLAY
# =========================================================

if (
    not state["auction_finished"]
    and
    state["current_turn"] == "Güney"
):

    for i in range(0, len(ALL_BIDS), 3):

        cols = st.columns(3)

        for j in range(3):

            if i+j < len(ALL_BIDS):

                bid = ALL_BIDS[i+j]

                # PAS always legal

                if bid == "PAS":
                    legal = True
                else:
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

                        state["feedback"] = (
                            result["message"]
                        )

                        state["auction_finished"] = True

                    else:

                        current_index = PLAYERS.index(
                            state["current_turn"]
                        )

                        state["current_turn"] = PLAYERS[
                            (current_index + 1) % 4
                        ]

                    st.rerun()
