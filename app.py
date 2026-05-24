import streamlit as st
import random

# =========================================================
# TBF BRİÇ AKADEMİ v18.0
# FULL STABILIZED EDUCATION EDITION
# =========================================================

st.set_page_config(
    page_title="TBF Briç Akademi v18.0",
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
    padding:10px;
    border-radius:10px;
    overflow-x:auto;
    white-space:nowrap;
    margin-bottom:10px;
}

.feedback-good{
    background:#dcfce7;
    padding:12px;
    border-radius:10px;
    margin-bottom:10px;
    color:#166534;
    font-weight:bold;
}

.feedback-bad{
    background:#fee2e2;
    padding:12px;
    border-radius:10px;
    margin-bottom:10px;
    color:#991b1b;
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
    '2':2,'3':3,'4':4,'5':5,'6':6,'7':7,
    '8':8,'9':9,'10':10,'J':11,'Q':12,
    'K':13,'A':14
}

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

        lengths = sorted(
            [len(hand[s]) for s in hand]
        )

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
            if b["bid"] not in ["PAS","X","XX"]
        ]

        if not bids:
            return proposed not in ["X","XX"]

        if proposed == "X":
            return history[-1]["bid"] not in ["X","XX"]

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
# EDUCATION ENGINE
# =========================================================

class BiddingEvaluator:

    @staticmethod
    def evaluate_opening(hand, bid):

        hcp = HandEvaluator.get_hcp(hand)

        sp = len(hand["♠"])
        he = len(hand["♥"])

        balanced = HandEvaluator.is_balanced(hand)

        # 1NT

        if (
            15 <= hcp <= 17
            and balanced
        ):

            if bid == "1NT":

                return (
                    True,
                    "✅ Doğru",
                    "Dengeli 15-17 HCP ile doğru açılış 1NT."
                )

            return (
                False,
                "❌ Yanlış",
                "Dengeli 15-17 HCP elde 1NT açılmalıydı."
            )

        # 1♠

        if hcp >= 12 and sp >= 5:

            if bid == "1♠":

                return (
                    True,
                    "✅ Doğru",
                    "5'li majör ♠ ile doğru açılış."
                )

            return (
                False,
                "❌ Yanlış",
                "5'li majör ♠ ile 1♠ açılmalıydı."
            )

        # 1♥

        if hcp >= 12 and he >= 5:

            if bid == "1♥":

                return (
                    True,
                    "✅ Doğru",
                    "5'li majör ♥ ile doğru açılış."
                )

            return (
                False,
                "❌ Yanlış",
                "5'li majör ♥ ile 1♥ açılmalıydı."
            )

        # PASS

        if hcp < 12:

            if bid == "PAS":

                return (
                    True,
                    "✅ Doğru",
                    "Açılış için yetersiz puan."
                )

            return (
                False,
                "❌ Yanlış",
                "Bu elde PAS geçilmeliydi."
            )

        return (
            True,
            "✅ Kabul Edilebilir",
            "Makul bir teklif."
        )

    @staticmethod
    def evaluate_response(
        hand,
        bid,
        history
    ):

        hcp = HandEvaluator.get_hcp(hand)

        sp = len(hand["♠"])
        he = len(hand["♥"])

        partner_bid = history[-1]["bid"]

        # STAYMAN

        if partner_bid == "1NT":

            if (
                hcp >= 8
                and
                (sp >= 4 or he >= 4)
            ):

                if bid == "2♣":

                    return (
                        True,
                        "✅ Doğru",
                        "Stayman doğru kullanıldı."
                    )

                return (
                    False,
                    "❌ Yanlış",
                    "4'lü majör aramak için Stayman (2♣) denmeliydi."
                )

            # PASS

            if hcp < 8:

                if bid == "PAS":

                    return (
                        True,
                        "✅ Doğru",
                        "Yetersiz puan ile PAS doğru."
                    )

                return (
                    False,
                    "❌ Yanlış",
                    "Bu elde PAS geçilmeliydi."
                )

        return (
            True,
            "✅ Kabul Edilebilir",
            "Makul cevap."
        )

# =========================================================
# STATE
# =========================================================

def init_game(mode):

    while True:

        hands = BridgeDeck.generate_and_deal()

        hcp = HandEvaluator.get_hcp(
            hands["Güney"]
        )

        longest = max(
            len(hands["Güney"][s])
            for s in hands["Güney"]
        )

        if hcp >= 9 or longest >= 7:
            break

    return {

        "mode":mode,

        "hands":hands,

        "bidding_history":[
            {
                "player":"Kuzey",
                "bid":"1NT"
            }
        ] if mode == "Ortak Açışına Yanıtlar"
        else [],

        "feedback":None,

        "last_result":None
    }

if "bridge_v18" not in st.session_state:

    st.session_state.bridge_v18 = init_game(
        "Kendi Açılış Pratiğiniz"
    )

state = st.session_state.bridge_v18

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

        st.session_state.bridge_v18 = init_game(mode)

        st.rerun()

    if st.button("🔄 Yeni El"):

        st.session_state.bridge_v18 = init_game(
            state["mode"]
        )

        st.rerun()

# =========================================================
# TITLE
# =========================================================

st.title("🃏 TBF Briç Akademi v18.0")

# =========================================================
# HAND
# =========================================================

south = state["hands"]["Güney"]

hcp = HandEvaluator.get_hcp(south)

st.write(f"### {state['mode']}")
st.write(f"**HCP:** {hcp}")

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

    good, title, msg = state["feedback"]

    css = (
        "feedback-good"
        if good
        else "feedback-bad"
    )

    st.markdown(
        f"""
        <div class='{css}'>
        {title}<br><br>
        {msg}
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("➡ Yeni Ele Geç"):

        st.session_state.bridge_v18 = init_game(
            state["mode"]
        )

        st.rerun()

# =========================================================
# BIDDING GRID
# =========================================================

if not state["feedback"]:

    bids = [
        "PAS","1♣","1♦",
        "1♥","1♠","1NT",
        "2♣","2♦","2♥",
        "2♠","2NT","3NT"
    ]

    for i in range(0, len(bids), 3):

        cols = st.columns(3)

        for j in range(3):

            if i+j < len(bids):

                bid = bids[i+j]

                legal = BiddingLegalityEngine.is_legal(
                    bid,
                    state["bidding_history"]
                )

                if cols[j].button(
                    bid,
                    disabled=not legal,
                    key=f"{bid}_{i}_{j}"
                ):

                    # MODE 1

                    if (
                        state["mode"]
                        ==
                        "Kendi Açılış Pratiğiniz"
                    ):

                        result = (
                            BiddingEvaluator
                            .evaluate_opening(
                                south,
                                bid
                            )
                        )

                    # MODE 2

                    elif (
                        state["mode"]
                        ==
                        "Ortak Açışına Yanıtlar"
                    ):

                        result = (
                            BiddingEvaluator
                            .evaluate_response(
                                south,
                                bid,
                                state["bidding_history"]
                            )
                        )

                    # MODE 3

                    else:

                        result = (
                            True,
                            "✅ Teklif Kaydedildi",
                            f"{bid} deklarasyonu işlendi."
                        )

                    state["feedback"] = result

                    state["bidding_history"].append({
                        "player":"Güney",
                        "bid":bid
                    })

                    st.rerun()
