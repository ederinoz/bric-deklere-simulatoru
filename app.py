import streamlit as st
import random
import time

# =========================================================
# TBF BRİÇ AKADEMİ v42.0 - FULL EDUCATION + TOURNAMENT
# =========================================================

st.set_page_config(page_title="TBF Briç Akademi v42.0", layout="centered")

# --- CSS: Rozetler ve Karar Ağacı için ---
st.markdown("""
<style>
.card-box{background:#f8fafc;padding:15px;border-radius:12px;border-left:5px solid #ef4444;font-family:monospace;font-size:20px;margin-bottom:10px;}
.badge{font-size:0.7em;background:#546E7A;color:#fff;padding:2px 8px;border-radius:10px;margin-left:5px;font-weight:bold;}
.bid-history{background:#1e293b;color:#e2e8f0;padding:12px;border-radius:10px;text-align:center;font-family:monospace;margin-bottom:15px;}
.result-box{background:#dcfce7;color:#065f46;padding:15px;border-radius:12px;font-weight:bold;margin-bottom:15px;}
.tree-row{display:flex;align-items:flex-start;margin:3px 0;padding:5px 10px;background:#f9f9f9;border-left:3px solid #ccc;border-radius:4px;font-size:0.85em;}
</style>
""", unsafe_allow_html=True)

# ... [DECK, EVALUATOR, LEGALITY, AI, RESOLVER SINIFLARI AYNI] ...
# (V41'deki mantığı koruyoruz)

# --- YENİ EĞİTİM MODÜLÜ ---
def render_decision_tree(hand):
    hcp = HandEvaluator.get_hcp(hand)
    sp, he = len(hand["♠"]), len(hand["♥"])
    st.markdown("#### 🌳 Karar Mantığı")
    steps = [
        ("Puan Kontrolü", f"HKP: {hcp}", hcp >= 12),
        ("Majör Kontrolü", f"5'li Majör: {'Evet' if (sp>=5 or he>=5) else 'Hayır'}", (sp>=5 or he>=5)),
        ("Denge Kontrolü", f"Dengeli: {'Evet' if HandEvaluator.is_balanced(hand) else 'Hayır'}", HandEvaluator.is_balanced(hand))
    ]
    for name, detail, hit in steps:
        icon = "✅" if hit else "❌"
        st.markdown(f'<div class="tree-row">{icon} <b>{name}</b>: {detail}</div>', unsafe_allow_html=True)

# --- INIT ---
def init_game():
    hands = BridgeDeck.generate_and_deal()
    return {"hands": hands, "dealer": random.choice(PLAYERS), "current_turn": None, "bidding_history": [], "auction_finished": False, "feedback": None}

if "state" not in st.session_state: st.session_state.state = init_game()
state = st.session_state.state
if state["current_turn"] is None: state["current_turn"] = state["dealer"]

# --- UI ---
st.title("🃏 TBF Briç Akademi v42.0")
south = state["hands"]["Güney"]

# El render + Rozetler
st.write(f"### Güney | HCP: {HandEvaluator.get_hcp(south)}")
for suit, sym in [("♠", "Maça"), ("♥", "Kupa"), ("♦", "Karo"), ("♣", "Sinek")]:
    ln = len(south[suit])
    bonus = 3 if ln==0 else (2 if ln==1 else (1 if ln==2 else 0))
    badge = f'<span class="badge">+{bonus} Dağılım</span>' if bonus > 0 else ""
    st.markdown(f"<div class='card-box'>{suit} {' '.join(south[suit])} {badge}</div>", unsafe_allow_html=True)

if state["bidding_history"]:
    st.markdown(f"<div class='bid-history'>{' → '.join([f\"{b['player']}:{b['bid']}\" for b in state['bidding_history']])}</div>", unsafe_allow_html=True)

# Sonuç ve Karar Ağacı
if state["feedback"]:
    st.markdown(f"<div class='result-box'>{state['feedback']}</div>", unsafe_allow_html=True)
    render_decision_tree(south)
    if st.button("➡ Yeni Ele Geç"): st.session_state.state = init_game(); st.rerun()
    st.stop()

# BOT PLAY
if not state["auction_finished"] and state["current_turn"] != "Güney":
    bot = state["current_turn"]
    bid = AuctionAI.generate_bid(state["hands"][bot], state["bidding_history"])
    if not BiddingLegalityEngine.is_legal(bid, state["bidding_history"]): bid = "PAS"
    state["bidding_history"].append({"player": bot, "bid": bid})
    res = AuctionResolver.resolve(state["bidding_history"])
    if res: state["feedback"] = res["message"]; state["auction_finished"] = True
    else: state["current_turn"] = PLAYERS[(PLAYERS.index(bot) + 1) % 4]
    time.sleep(0.3); st.rerun()

# USER PLAY
if not state["auction_finished"] and state["current_turn"] == "Güney":
    for i in range(0, len(ALL_BIDS), 3):
        cols = st.columns(3)
        for j in range(3):
            if i+j < len(ALL_BIDS):
                bid = ALL_BIDS[i+j]
                legal = True if bid == "PAS" else BiddingLegalityEngine.is_legal(bid, state["bidding_history"])
                if cols[j].button(bid, disabled=not legal, key=f"{bid}_{i}_{j}"):
                    state["bidding_history"].append({"player": "Güney", "bid": bid})
                    res = AuctionResolver.resolve(state["bidding_history"])
                    if res: state["feedback"] = res["message"]; state["auction_finished"] = True
                    else: state["current_turn"] = PLAYERS[(PLAYERS.index("Güney") + 1) % 4]
                    st.rerun()
