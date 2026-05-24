import streamlit as st
import random

# =========================================================
# TBF BRİÇ AKADEMİ v17.0 - TAM BİRLEŞİK FİNAL
# =========================================================

st.set_page_config(page_title="TBF Briç Akademi v17.0", layout="centered")

# --- CSS ---
st.markdown("""<style>.card-box{background:#f8fafc;padding:12px;border-radius:10px;border-left:5px solid #ef4444;margin-bottom:10px;font-family:monospace;}.bid-history{background:#1e293b;color:white;padding:10px;border-radius:10px;overflow-x:auto;white-space:nowrap;margin-bottom:10px;}div.stButton>button{width:100%;border-radius:8px;font-weight:bold;height:45px;}</style>""", unsafe_allow_html=True)

# --- CORE ENGINE ---
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
            if hcp >= 12 and sp >= 5 and bid != "1♠": return "❌ Yanlış", "5'li Majör(♠) ile 1♠ açılmalıydı.", "1♠"
            if hcp >= 15 and hcp <= 17 and bid != "1NT": return "❌ Yanlış", "Dengeli 15-17 HCP ile 1NT açılmalıydı.", "1NT"
        return None, None, None

class AuctionResolver:
    @staticmethod
    def resolve(history):
        if len(history) >= 4 and all(h["bid"] == "PAS" for h in history[-4:]): return "PASS_OUT"
        if len(history) > 3 and history[-1]["bid"]=="PAS" and history[-2]["bid"]=="PAS" and history[-3]["bid"]=="PAS":
            final = next((h for h in reversed(history) if h["bid"] not in ["PAS","X","XX"]), None)
            if not final: return "PASS_OUT"
            return {"contract": final["bid"], "declarer": final["player"], "leader": PLAYERS[(PLAYERS.index(final["player"])+1)%4], "dummy": "Kuzey" if final["player"] in ["Güney", "Kuzey"] else "Batı"}
        return None

# --- STATE MANAGEMENT ---
def init_game(mode):
    while True:
        hands = BridgeDeck.generate_and_deal()
        if HandEvaluator.get_hcp(hands["Güney"]) >= 9 or max(len(hands["Güney"][s]) for s in hands["Güney"]) >= 7:
            break
    return {
        "step": "AUCTION", "mode": mode, "hands": hands,
        "bidding_history": [{"player":"Kuzey", "bid":"1NT"}] if mode == "Ortak Açışına Yanıtlar" else [],
        "current_turn": "Güney", "contract_meta": None
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

st.markdown("<div class='card-box'>♠ " + " ".join(south['♠']) + "<br>♥ " + " ".join(south['♥']) + "<br>♦ " + " ".join(south['♦']) + "<br>♣ " + " ".join(south['♣']) + "</div>", unsafe_allow_html=True)

if state["step"] == "AUCTION":
    bids = ["PAS","1♣","1♦","1♥","1♠","1NT","2♣","2♦","2♥","2♠","2NT","3NT"]
    for i in range(0, len(bids), 3):
        cols = st.columns(3)
        for j in range(3):
            if i+j < len(bids):
                b = bids[i+j]
                if cols[j].button(b, disabled=not BiddingLegalityEngine.is_legal(b, state["bidding_history"], "Güney")):
                    status, msg, ideal = BiddingEvaluator.get_feedback(state["mode"], south, b, state["bidding_history"])
                    if status:
                        st.error(f"{status}: {msg} | İdeal: {ideal}")
                    else:
                        state["bidding_history"].append({"player":"Güney", "bid":b})
                        st.rerun()
    
    res = AuctionResolver.resolve(state["bidding_history"])
    if res == "PASS_OUT":
        st.warning("⚠️ Board PAS geçti.")
        if st.button("Yeni El Dağıt"): st.session_state.state = init_game(state["mode"]); st.rerun()
    elif res:
        state["step"] = "PLAY"; state["contract_meta"] = res; st.rerun()

elif state["step"] == "PLAY":
    st.success(f"Kontrat: {state['contract_meta']['contract']}")
    if state["mode"] == "Turnuva Sekansı":
        st.info(f"Yer: {state['contract_meta']['dummy']}")
    else:
        st.info("Eğitim Modu: Yer (Dummy) gizli.")
    if st.button("Yeni El Dağıt"): st.session_state.state = init_game(state["mode"]); st.rerun()
