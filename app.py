import streamlit as st
import random
import time

# =========================================================
# TBF BRİÇ AKADEMİ v43.0 - FULL FINAL
# =========================================================

st.set_page_config(page_title="TBF Briç Akademi v43.0", layout="centered")

st.markdown("""
<style>
.card-box{background:#f8fafc;padding:15px;border-radius:12px;border-left:5px solid #ef4444;font-family:monospace;font-size:20px;margin-bottom:15px;}
.bid-history{background:#1e293b;color:#e2e8f0;padding:15px;border-radius:10px;text-align:center;font-family:monospace;margin-bottom:15px;}
.result-box{background:#dcfce7;color:#065f46;padding:15px;border-radius:12px;font-weight:bold;margin-bottom:15px;}
.tree-row{background:#f8fafc;padding:8px;border-left:4px solid #cbd5e1;border-radius:6px;margin-bottom:5px;font-size:0.9em;}
</style>
""", unsafe_allow_html=True)

# --- ENGINE ---
PLAYERS = ["Kuzey", "Doğu", "Güney", "Batı"]
ALL_BIDS = ["PAS", "1♣","1♦","1♥","1♠","1NT", "2♣","2♦","2♥","2♠","2NT", "3♣","3♦","3♥","3♠","3NT", "4♥","4♠","4NT", "X", "XX"]
SUITS = ["♠","♥","♦","♣"]
RANKS = ["A","K","Q","J","10","9","8","7","6","5","4","3","2"]
HCP_MAP = {"A":4, "K":3, "Q":2, "J":1}

class BridgeDeck:
    @staticmethod
    def generate_and_deal():
        deck = [f"{r}{s}" for s in SUITS for r in RANKS]
        random.shuffle(deck)
        hands = {p: {s: [] for s in SUITS} for p in PLAYERS}
        for i, card in enumerate(deck): hands[PLAYERS[i % 4]][card[-1]].append(card[:-1])
        return hands

class HandEvaluator:
    @staticmethod
    def get_hcp(hand): return sum(HCP_MAP.get(r, 0) for s in SUITS for r in hand[s])
    @staticmethod
    def is_balanced(hand): return sorted([len(hand[s]) for s in SUITS]) in [[2,3,4,4], [2,3,3,5], [3,3,3,4]]

class BidEngine:
    @staticmethod
    def opening_bid(hand):
        hcp = HandEvaluator.get_hcp(hand); sp = len(hand["♠"]); he = len(hand["♥"]); balanced = HandEvaluator.is_balanced(hand)
        if hcp <= 10 and sp >= 7: return "3♠" # Baraj
        if 15 <= hcp <= 17 and balanced: return "1NT"
        if hcp >= 12 and sp >= 5: return "1♠"
        if hcp >= 12 and he >= 5: return "1♥"
        if hcp >= 12: return "1♦" if len(hand["♦"]) >= len(hand["♣"]) else "1♣"
        return "PAS"

    @staticmethod
    def get_correct_response(opening, hand):
        hcp = HandEvaluator.get_hcp(hand); trump = opening[-1]; fit = len(hand[trump])
        if opening.startswith("1"):
            if fit >= 4 and hcp >= 13: return {"best": "2NT", "category": "Jacoby 2NT"}
            if fit >= 3 and 10 <= hcp <= 12: return {"best": f"3{trump}", "category": "Limit Raise"}
            if fit >= 3 and 6 <= hcp <= 9: return {"best": f"2{trump}", "category": "Simple Raise"}
            if 6 <= hcp <= 9: return {"best": "1NT", "category": "1NT Response"}
        return {"best": "PAS", "category": "Pass"}

class BidJudge:
    @staticmethod
    def judge(user_bid, correct_data, hand, opening):
        if user_bid == correct_data["best"]:
            return {"correct": True, "title": "✅ Doğru Deklere", "message": f"{user_bid} doğru seçim.", "category": correct_data["category"], "severity": "good"}
        return {"correct": False, "title": "❌ Yanlış Deklere", "message": f"Sistem {correct_data['best']} öneriyor ({correct_data['category']}).", "category": "Eğitim", "severity": "bad"}

# --- INIT ---
def init_game():
    return {"hands": BridgeDeck.generate_and_deal(), "dealer": random.choice(PLAYERS), "current_turn": None, "bidding_history": [], "auction_finished": False, "feedback": None}

if "state" not in st.session_state: st.session_state.state = init_game()
state = st.session_state.state
if state["current_turn"] is None: state["current_turn"] = state["dealer"]

# --- UI ---
st.title("🃏 TBF Briç Akademi v43.0")
south = state["hands"]["Güney"]
st.write(f"### Güney | HCP: {HandEvaluator.get_hcp(south)}")

for suit in SUITS:
    st.markdown(f"<div class='card-box'>{suit} {' '.join(south[suit])}</div>", unsafe_allow_html=True)

if state["bidding_history"]:
    st.markdown(f"<div class='bid-history'>{' → '.join([f\"{b['player']}:{b['bid']}\" for b in state['bidding_history']])}</div>", unsafe_allow_html=True)

if state["feedback"]:
    fb = state["feedback"]
    css = "result-good" if fb["severity"] == "good" else "result-bad"
    st.markdown(f"<div class='{css}'><h3>{fb['title']}</h3><p>{fb['message']}</p></div>", unsafe_allow_html=True)
    
    # Karar Ağacı Görselleştirme
    hcp = HandEvaluator.get_hcp(south)
    fit = len(south[state["bidding_history"][0]["bid"][-1]]) if state["bidding_history"] else 0
    for name, detail, ok in [("HKP", f"{hcp} Puan", hcp >= 6), ("Fit", f"{fit} Kart", fit >= 3)]:
        st.markdown(f'<div class="tree-row">{"✅" if ok else "❌"} <b>{name}</b>: {detail}</div>', unsafe_allow_html=True)

    if st.button("➡ Yeni El"): st.session_state.state = init_game(); st.rerun()
    st.stop()

# --- USER PLAY ---
st.markdown("### Deklerenizi Seçin")
for i in range(0, len(ALL_BIDS), 4):
    cols = st.columns(4)
    for j in range(4):
        if i+j < len(ALL_BIDS):
            bid = ALL_BIDS[i+j]
            if cols[j].button(bid):
                # 1. Eğitim Kontrolü
                opening = state["bidding_history"][0]["bid"] if state["bidding_history"] else ""
                corr = BidEngine.get_correct_response(opening, south)
                state["feedback"] = BidJudge.judge(bid, corr, south, opening)
                state["bidding_history"].append({"player": "Güney", "bid": bid})
                state["auction_finished"] = True
                st.rerun()
