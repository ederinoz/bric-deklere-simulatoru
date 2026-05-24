import streamlit as st
import random

# TBF BRİÇ AKADEMİ v15.0 - EĞİTİM ASİSTANI (Final Foundation)

# --- ENGINE ---
# [BridgeDeck, HandEvaluator, BiddingLegalityEngine aynı]

class BiddingEvaluator:
    @staticmethod
    def get_feedback(mode, hand, bid, history):
        hcp = get_hcp(hand)
        sp, he = len(hand["♠"]), len(hand["♥"])
        
        if mode == "Kendi Açılış Pratiğiniz":
            if hcp >= 12 and sp >= 5 and bid != "1♠": return "❌ Yanlış", "5'li Majör(♠) ile 1♠ açılmalıydı.", "1♠"
            if hcp >= 15 and hcp <= 17 and bid != "1NT": return "❌ Yanlış", "Dengeli 15-17 HCP ile 1NT açılmalıydı.", "1NT"
            return "✅ Doğru", "Mükemmel tercih.", bid
            
        elif mode == "Ortak Açışına Yanıtlar":
            # Basit Stayman Kontrolü
            if history and history[-1]["bid"] == "1NT":
                if bid == "2♣": return "✅ Doğru", "Stayman kullanıldı.", "2♣"
                return "❌ Yanlış", "1NT açışına Stayman (2♣) yanıtı gelmeliydi.", "2♣"
        return "✅ Doğru", "Güzel teklif.", bid

# --- STATE (Selective Reset) ---
def init_state(mode):
    return {
        "step": "AUCTION", "mode": mode, "hands": BridgeDeck.generate_and_deal(),
        "bidding_history": [{"player":"Kuzey", "bid":"1NT"}] if mode == "Ortak Açışına Yanıtlar" else [],
        "current_turn": "Güney"
    }

if "state" not in st.session_state:
    st.session_state.state = init_state("Kendi Açılış Pratiğiniz")
state = st.session_state.state

# --- SIDEBAR (Kritik Düzeltme: KeyError önleyici Selective Reset) ---
with st.sidebar:
    mode = st.radio("Mod:", ["Kendi Açılış Pratiğiniz", "Ortak Açışına Yanıtlar", "Turnuva Sekansı"])
    if mode != state["mode"]:
        st.session_state.state = init_state(mode)
        st.rerun()

# --- AUCTION UI (Feedback Pipeline) ---
if state["step"] == "AUCTION":
    # 3'lü Responsive Grid...
    for j in range(3):
        if cols[j].button(b):
            status, msg, ideal = BiddingEvaluator.get_feedback(state["mode"], south, b, state["bidding_history"])
            
            # FEEDBACK PİPELINE
            if status == "❌ Yanlış":
                st.error(f"{status} | {msg}")
                st.info(f"💡 İdeal teklif: {ideal}")
                if st.button("Yeni Ele Geç"): st.session_state.state = init_state(state["mode"]); st.rerun()
            else:
                st.success(f"{status} | {msg}")
                state["bidding_history"].append({"player":"Güney", "bid":b})
                st.rerun()
