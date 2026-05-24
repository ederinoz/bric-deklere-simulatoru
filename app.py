# =========================================================
# TBF BRİÇ AKADEMİ v43.0
# EDUCATION ENGINE + BID JUDGE SYSTEM
# =========================================================

import streamlit as st
import random

st.set_page_config(page_title="TBF Briç Akademi", layout="centered")

# =========================================================
# BASIC CONSTANTS
# =========================================================

PLAYERS = ["Kuzey", "Doğu", "Güney", "Batı"]

ALL_BIDS = [
    "PAS",
    "1♣","1♦","1♥","1♠","1NT",
    "2♣","2♦","2♥","2♠","2NT",
    "3♣","3♦","3♥","3♠","3NT",
    "4♥","4♠","4NT"
]

HCP_MAP = {
    "A":4,
    "K":3,
    "Q":2,
    "J":1
}

SUITS = ["♠","♥","♦","♣"]

RANKS = ["A","K","Q","J","10","9","8","7","6","5","4","3","2"]

# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>
.card-box{
    background:#f8fafc;
    padding:14px;
    border-radius:12px;
    border-left:5px solid #ef4444;
    font-family:monospace;
    font-size:20px;
    margin-bottom:10px;
}

.result-good{
    background:#dcfce7;
    color:#065f46;
    padding:15px;
    border-radius:12px;
    margin-bottom:10px;
}

.result-bad{
    background:#fee2e2;
    color:#991b1b;
    padding:15px;
    border-radius:12px;
    margin-bottom:10px;
}

.analysis-box{
    background:#f1f5f9;
    padding:12px;
    border-radius:10px;
    margin-top:10px;
}

.tree-row{
    background:#f8fafc;
    padding:8px;
    border-left:4px solid #cbd5e1;
    border-radius:6px;
    margin-bottom:5px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# CARD ENGINE
# =========================================================

def generate_deck():
    deck = []

    for suit in SUITS:
        for rank in RANKS:
            deck.append(f"{rank}{suit}")

    random.shuffle(deck)
    return deck

def deal_hands():

    deck = generate_deck()

    hands = {
        "Kuzey":{},
        "Doğu":{},
        "Güney":{},
        "Batı":{}
    }

    for p in PLAYERS:
        for s in SUITS:
            hands[p][s] = []

    for i in range(52):

        player = PLAYERS[i % 4]
        card = deck[i]

        rank = card[:-1]
        suit = card[-1]

        hands[player][suit].append(rank)

    return hands

# =========================================================
# HAND EVALUATOR
# =========================================================

class HandEvaluator:

    @staticmethod
    def get_hcp(hand):

        total = 0

        for suit in SUITS:
            for card in hand[suit]:
                total += HCP_MAP.get(card, 0)

        return total

    @staticmethod
    def suit_length(hand, suit):
        return len(hand[suit])

    @staticmethod
    def is_balanced(hand):

        lengths = sorted([
            len(hand["♠"]),
            len(hand["♥"]),
            len(hand["♦"]),
            len(hand["♣"])
        ])

        return lengths in [
            [2,3,4,4],
            [2,3,3,5],
            [3,3,3,4]
        ]

# =========================================================
# BID ENGINE
# =========================================================

class BidEngine:

    @staticmethod
    def opening_bid(hand):

        hcp = HandEvaluator.get_hcp(hand)

        sp = len(hand["♠"])
        he = len(hand["♥"])
        di = len(hand["♦"])
        cl = len(hand["♣"])

        balanced = HandEvaluator.is_balanced(hand)

        # 1NT
        if 15 <= hcp <= 17 and balanced:
            return "1NT"

        # 5'li majör
        if sp >= 5 and hcp >= 12:
            return "1♠"

        if he >= 5 and hcp >= 12:
            return "1♥"

        # Minör
        if di >= 4 and hcp >= 12:
            return "1♦"

        if cl >= 3 and hcp >= 12:
            return "1♣"

        return "PAS"

    @staticmethod
    def response_to_major(opening_bid, hand):

        hcp = HandEvaluator.get_hcp(hand)

        trump = opening_bid[-1]

        fit = len(hand[trump])

        # 4+ destek ve 13+
        if fit >= 4 and hcp >= 13:
            return {
                "best":"2NT",
                "category":"Jacoby 2NT"
            }

        # limit raise
        if fit >= 3 and 10 <= hcp <= 12:
            return {
                "best":f"3{trump}",
                "category":"Limit Raise"
            }

        # simple raise
        if fit >= 3 and 6 <= hcp <= 9:
            return {
                "best":f"2{trump}",
                "category":"Simple Raise"
            }

        # game
        if fit >= 5 and hcp <= 9:
            return {
                "best":f"4{trump}",
                "category":"Preemptive Raise"
            }

        # NT
        if 6 <= hcp <= 9:
            return {
                "best":"1NT",
                "category":"1NT Response"
            }

        return {
            "best":"PAS",
            "category":"Pass"
        }

# =========================================================
# EDUCATION ENGINE
# =========================================================

class BidJudge:

    @staticmethod
    def judge(user_bid, correct_data, hand, opening):

        best = correct_data["best"]
        category = correct_data["category"]

        hcp = HandEvaluator.get_hcp(hand)

        fit = len(hand[opening[-1]])

        if user_bid == best:

            return {
                "correct":True,
                "title":"✅ Doğru Deklere",
                "message":f"{best} doğru seçim.",
                "category":category,
                "severity":"good"
            }

        # yakın hata
        near = False

        if best.startswith("2") and user_bid.startswith("3"):
            near = True

        if best.startswith("3") and user_bid.startswith("2"):
            near = True

        if near:

            return {
                "correct":False,
                "title":"⚠ Yakın Hata",
                "message":f"{user_bid} oynanabilir ama sistem tercihi {best}.",
                "category":"Near Miss",
                "severity":"medium"
            }

        # büyük hata

        mistake = "Overbid"

        if user_bid == "2NT" and best != "2NT":
            mistake = "False Jacoby"

        return {
            "correct":False,
            "title":"❌ Yanlış Deklere",
            "message":f"Önerilen teklif: {best}",
            "category":mistake,
            "severity":"bad"
        }

# =========================================================
# DECISION TREE
# =========================================================

def render_tree(hand, opening):

    hcp = HandEvaluator.get_hcp(hand)

    trump = opening[-1]

    fit = len(hand[trump])

    balanced = HandEvaluator.is_balanced(hand)

    st.markdown("### 🌳 Karar Ağacı")

    rows = [
        ("HKP Kontrolü", f"{hcp} HKP", hcp >= 6),
        ("Fit Kontrolü", f"{fit} kart destek", fit >= 3),
        ("Denge Kontrolü", "Dengeli" if balanced else "Dengesiz", balanced),
    ]

    for name, detail, ok in rows:

        icon = "✅" if ok else "❌"

        st.markdown(
            f'<div class="tree-row">{icon} <b>{name}</b> → {detail}</div>',
            unsafe_allow_html=True
        )

# =========================================================
# INIT
# =========================================================

def new_game():

    hands = deal_hands()

    opening = BidEngine.opening_bid(hands["Kuzey"])

    return {
        "hands":hands,
        "opening":opening,
        "feedback":None
    }

if "game" not in st.session_state:
    st.session_state.game = new_game()

game = st.session_state.game

# =========================================================
# UI
# =========================================================

st.title("🃏 TBF Briç Akademi v43.0")

south = game["hands"]["Güney"]

opening = game["opening"]

st.markdown(f"## Kuzey Açılışı: {opening}")

st.write(f"### Güney Eli | HKP: {HandEvaluator.get_hcp(south)}")

for suit in SUITS:

    cards = " ".join(south[suit])

    st.markdown(
        f"<div class='card-box'>{suit} {cards}</div>",
        unsafe_allow_html=True
    )

# =========================================================
# FEEDBACK
# =========================================================

if game["feedback"]:

    fb = game["feedback"]

    if fb["severity"] == "good":
        css = "result-good"
    else:
        css = "result-bad"

    st.markdown(
        f"""
        <div class="{css}">
        <h3>{fb["title"]}</h3>
        <p>{fb["message"]}</p>
        <b>Kategori:</b> {fb["category"]}
        </div>
        """,
        unsafe_allow_html=True
    )

    render_tree(south, opening)

    if st.button("➡ Yeni El"):

        st.session_state.game = new_game()
        st.rerun()

    st.stop()

# =========================================================
# USER ACTION
# =========================================================

correct_data = BidEngine.response_to_major(opening, south)

st.markdown("## Deklerenizi Seçin")

for i in range(0, len(ALL_BIDS), 4):

    cols = st.columns(4)

    for j in range(4):

        if i + j < len(ALL_BIDS):

            bid = ALL_BIDS[i+j]

            if cols[j].button(bid):

                result = BidJudge.judge(
                    bid,
                    correct_data,
                    south,
                    opening
                )

                game["feedback"] = result

                st.rerun()
