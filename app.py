import streamlit as st
import random

# =========================================================
# TBF BRİÇ AKADEMİ v15.1 - FULL STABILIZED MASTER
# =========================================================

st.set_page_config(page_title="TBF Briç Akademi v15.1", layout="centered")

# --- CORE ENGINE SINIFLARI ---
PLAYERS = ["Batı", "Kuzey", "Doğu", "Güney"]
SUIT_ORDER = {"♣": 1, "♦": 2, "♥": 3, "♠": 4, "NT": 5}
CARD_RANK = {'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':11,'Q':12,'K':13,'A':14}

class BridgeDeck:
    @staticmethod
    def generate_and_deal():
        deck = [f"{s}{r}" for s in ["♠","♥","♦","♣"] for r in ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]]
        random.shuffle(deck)
        hands = {p: {"♠":[],"♥":[],"♦":[],"♣":[]} for p in PLAYERS}
        for idx, card in enumerate(deck): hands[PLAYERS[idx % 4]][card[0]].append(card[1:])
        for p in PLAYERS:
            for s in ["♠","♥","♦","♣"]: hands[p][s].sort(key=lambda x: CARD_RANK[x], reverse=True)
        return hands

class HandEvaluator:
    @staticmethod
    def get_hcp(hand): return sum({"A":4,"K":3,"Q":2,"J":1}.get(c,0) for s in hand for c in hand[s])

class BiddingLegalityEngine:
    @staticmethod
    def is_legal(proposed, history, player):
        if proposed == "PAS": return True
        bids = [b["bid"] for b in history if b["bid"] not in ["PAS","X","XX"]]
        if not bids: return proposed not in ["X","XX"]
        if proposed == "X": return history[-1]["bid"] not in ["X","XX"]
        if proposed == "XX": return history[-1]["bid"] == "X"
        ll, ls = int(bids[-1][0]), bids[-1][1:]
        pl, ps = int(proposed[0]), proposed[1:]
        return pl > ll or (pl == ll and SUIT_ORDER[ps] > SUIT_ORDER[ls])

class BiddingEvaluator:
    @staticmethod
    def get_feedback(mode, hand, bid, history):
        hcp = HandEvaluator.get_hcp(hand)
        sp = len(hand["♠"])
        if mode == "Kendi Açılış Pratiğiniz":
            if hcp >= 12 and sp >= 5 and bid != "1♠": return "❌ Yanlış", "5'li Majör (♠) ile 1♠ açılmalı.", "1♠"
            if hcp >= 15 and hcp <= 17 and bid != "1NT": return "❌ Yanlış", "Dengeli 15-17 HCP ile 1NT açılmalı.", "1NT"
        return None, None, None

# --- STATE MANAGEMENT ---
def init_game(mode):
    hands = BridgeDeck.generate_and_deal()
    # 9 HCP Filtresi (While döngüsü)
    while HandEvaluator.get_hcp(hands["Güney"]) < 9 and max(len(hands["Güney"][s]) for s in hands["Güney"]) < 7:
        hands = BridgeDeck.generate_and_deal()
        
    return {
        "step": "AUCTION", "mode": mode, "hands": hands,
        "bidding_history": [{"player":"Kuzey", "bid":"1NT"}] if mode == "Ortak Açışına Yanıtlar" else [],
        "current_turn": "Güney", "trick_history": [], "score_decl": 0, "score_def": 0
    }

if "state" not in st.session_state:
    st.session_state.state = init_game("Kendi Açılış Pratiğiniz")
state = st.session_state.state

# --- SIDEBAR ---
with st.sidebar:
    mode = st.radio("Mod:", ["Kendi Açılış Pratiğiniz", "Ortak Açışına Yanıtlar", "Turnuva Sekansı"])
    if mode != state["mode"]:
        st.session_state.state = init_game(mode)
        st.rerun()

# --- AUCTION UI ---
st.write(f"### {state['mode']}")
south = state["hands"]["Güney"]
st.write(f"**HCP:** {HandEvaluator.get_hcp(south)}")
# (Buraya kartları gösteren mobile-cards render bloğunu ekle)

if state["step"] == "AUCTION":
    bids = ["PAS","X","XX","1♣","1♦","1♥","1♠","1NT","2♣","2♦","2♥","2♠","2NT","3♣","3♦","3♥","3♠","3NT"]
    for i in range(0, len(bids), 3):
        cols = st.columns(3)
        for j in range(3):
            if i+j < len(bids):
                b = bids[i+j]
                if cols[j].button(b, disabled=not BiddingLegalityEngine.is_legal(b, state["bidding_history"], "Güney")):
                    # Feedback Sistemi
                    status, msg, ideal = BiddingEvaluator.get_feedback(state["mode"], south, b, state["bidding_history"])
                    if status:
                        st.error(f"{status}: {msg}")
                        st.info(f"💡 İdeal: {ideal}")
                    else:
                        state["bidding_history"].append({"player":"Güney", "bid":b})
                        st.rerun()

    if st.button("Yeni El"): st.session_state.state = init_game(state["mode"]); st.rerun()
