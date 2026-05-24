import streamlit as st
import sys
import os
import random

sys.path.insert(0, os.path.dirname(__file__))

from cards import deal_hands, Suit, SUIT_SYMBOLS, SUIT_NAMES_TR, RANK_SYMBOLS
from evaluator import HandEvaluator
import bidding_system as bs

# INLINE VE UNIFIED CSS: Dark/Light fark etmeksizin kartların görünmesini ve üst üste binmesini sağlar
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { font-size: 15px !important; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; font-weight: bold; color: #1565C0; }
    .table-title { color: #2e7d32 !important; font-size: 1.35rem !important; font-weight: 800; margin-bottom: 6px; }
    
    /* Koltukların dikey eksende kaymasını engellemek için Flexbox Üst Sabitleme */
    [data-testid="stHorizontalBlock"] {
        align-items: flex-start !important;
        gap: 0.5rem !important;
    }
    
    .stButton>button { 
        width: 100%; border-radius: 6px; height: 3.2rem; 
        font-size: 1.2rem !important; font-weight: 700;
        margin-bottom: 1px !important; padding: 2px 4px;
    }
    
    /* Dark modda görünürlük için kart yazı zeminini garantiye alıyoruz */
    .suit-symbol { font-size: 1.7rem !important; font-weight: 700; vertical-align: middle; display: inline-block; width: 25px; }
    .suit-ranks { font-family: monospace; font-size: 1.45rem !important; margin-left: 12px; font-weight: bold; vertical-align: middle; color: inherit; }
    .hand-info-text { font-size: 1.15rem !important; font-weight: 600; margin-top: 6px; }
    
    @media screen and (min-width: 601px) and (max-width: 1024px) {
        html, body, [data-testid="stAppViewContainer"] { font-size: 16px !important; }
        [data-testid="stHorizontalBlock"] { gap: 0.4rem !important; padding: 0px !important; }
        .stButton>button { height: 3.3rem; font-size: 1.15rem !important; }
        .suit-symbol { font-size: 1.8rem !important; }
        .suit-ranks { font-size: 1.55rem !important; }
    }
    @media screen and (max-width: 600px) {
        html, body, [data-testid="stAppViewContainer"] { font-size: 13px !important; }
        .stButton>button { height: 2.9rem; font-size: 1.0rem !important; }
        [data-testid="stHorizontalBlock"] { gap: 0.2rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

DEFAULTS = {
    "mode": "opening", "hands": None, "feedback": None, "feedback_ok": None,
    "correct_bid": None, "north_bid": None, "north_suit": None, "trump": None,
    "score": {"total": 0, "correct": 0}, "rkcb_active": False, "seat": 1,
    "live_dealer": 0, "live_bids": [], "live_turn": 0, "live_done": False,
    "live_feedback": None, "live_feedback_ok": None, "live_feedback_correct": None,
    "live_opener_pos": None, "live_partner_pass_count": 0
}
for k, v in DEFAULTS.items():
    if k not in st.session_state: st.session_state[k] = v

POS_NAMES  = ["Kuzey", "Doğu", "Güney", "Batı"]
POS_EMOJI  = ["🔵", "🟠", "🔴", "🟢"]

def render_responsive_hand(ev, title, is_north=False):
    color_title = "#### 🔵 " if is_north else "#### "
    st.markdown(f"{color_title}{title}")
    for suit in reversed(list(Suit)):
        cards = ev.suit_cards(suit)
        # INLINE HARD-CODED COLOR: Dark modun renkleri yutmasını tamamen engeller
        color = "#e53935" if suit in (Suit.HEARTS, Suit.DIAMONDS) else "#212121"
        ranks = " ".join(RANK_SYMBOLS[c.rank] for c in sorted(cards, key=lambda c: c.rank, reverse=True)) if cards else "—"
        st.markdown(f"<span class='suit-symbol' style='color:{color} !important;'>{SUIT_SYMBOLS[suit]}</span><span class='suit-ranks'>{ranks}</span>", unsafe_allow_html=True)
    st.markdown(f"<div class='hand-info-text'>HKP: <b>{ev.hcp()}</b> | Dağılım: <b>+{ev.distribution_points()}</b> | Toplam: <b>{ev.total_points()} TP</b></div>", unsafe_allow_html=True)

def extract_suit(bid: str) -> Suit | None:
    mapping = {"♠": Suit.SPADES, "♥": Suit.HEARTS, "♦": Suit.DIAMONDS, "♣": Suit.CLUBS}
    for sym, s in mapping.items():
        if sym in bid: return s
    return None

def get_bid_style_inline(bid: str) -> str:
    """Streamlit markdown katmanını ezip deklere tablosundaki renkleri Dark modda da sabitler"""
    if "♥" in bid or "♦" in bid: return "color: #e53935 !important; font-weight: bold; font-size: 1.15rem;"
    return "color: #212121 !important; font-weight: bold; font-size: 1.15rem;"

def valid_bids_above(last_bid: str | None) -> list[str]:
    order = []
    for lvl in range(1, 7):
        for sym in ["♣", "♦", "♥", "♠", "NT"]: order.append(f"{lvl}{sym}")
    if last_bid is None or last_bid == bs.BID_PASS: return [bs.BID_PASS, bs.BID_DBL] + order[:]
    try:
        idx = order.index(last_bid)
        return [bs.BID_PASS, bs.BID_DBL] + order[idx + 1:]
    except ValueError: return [bs.BID_PASS, bs.BID_DBL] + order[:]

def is_auction_over_strict(bids: list) -> bool:
    if len(bids) < 3: return False
    if len(bids) == 4 and all(b == bs.BID_PASS for _, b, _ in bids): return True
    pass_streak = 0
    for _, b, _ in reversed(bids):
        if b == bs.BID_PASS:
            pass_streak += 1
            if pass_streak >= 3: return True
        else:
            break
    return False

def last_real_bid_and_pos(bids: list) -> tuple[str | None, int | None]:
    for b_pos, bid, _ in reversed(bids):
        if bid not in (bs.BID_PASS, bs.BID_DBL, bs.BID_RDBL, ''): return bid, b_pos
    return None, None

def calculate_correct_live_bid(bids: list, user_hand_ev: HandEvaluator) -> tuple[str, str]:
    last_real, last_real_pos = last_real_bid_and_pos(bids)
    
    if last_real is None:
        return bs.opening_bid(user_hand_ev, seat=3)
        
    if last_real_pos == 0:
        n_ev = HandEvaluator(st.session_state["hands"][0])
        return bs.suggest_response(last_real, extract_suit(last_real), user_hand_ev, partner_hcp=n_ev.hcp())
        
    if bids and bids[-1][1] == bs.BID_DBL and bids[-1][0] == 0:
        return bs.respond_to_double(last_real, user_hand_ev)
        
    p_passed_twice = st.session_state["live_partner_pass_count"] >= 2
    my_prev = next((b for p, b, _ in reversed(bids) if p == 2 and b != bs.BID_PASS), None)
    
    if my_prev:
        return bs.competitive_fallback(user_hand_ev, last_real, my_prev, p_passed_twice)
        
    partner_passed = any(b == bs.BID_PASS for p, b, _ in bids if p == 0)
    return bs.overcall_or_double(user_hand_ev, last_real, partner_passed=partner_passed)

def robot_bid_for_pos(pos: int, hands: list, bids: list) -> tuple[str, str]:
    ev = HandEvaluator(hands[pos])
    partner = (pos + 2) % 4
    seat = len(bids) + 1
    last_real, last_real_pos = last_real_bid_and_pos(bids)
    
    # KİMLİK KİLİDİ: Eğer 1NT açan düşmansa asla Stayman/Transfer tetikleme!
    if last_real == "1NT" and last_real_pos != partner:
        partner_passed = any(b == bs.BID_PASS for p, b, _ in bids if p == partner)
        return bs.overcall_or_double(ev, last_real, partner_passed=partner_passed)

    if partner == 2 and last_real is not None:
        s_ev = HandEvaluator(hands[2])
        bid, expl = bs.suggest_response(last_real, extract_suit(last_real), ev, partner_hcp=s_ev.hcp())
        if bid != bs.BID_PASS: return bid, expl

    if last_real is None:
        bid, expl = bs.opening_bid(ev, seat=min(seat, 4))
        if bid != bs.BID_PASS: st.session_state["live_opener_pos"] = pos
        return bid, expl
        
    if last_real_pos == partner:
        if last_real == bs.BID_DBL: return bs.respond_to_double(last_real, ev)
        p_ev = HandEvaluator(hands[partner])
        return bs.suggest_response(last_real, extract_suit(last_real), ev, partner_hcp=p_ev.hcp())
        
    partner_passed = any(b == bs.BID_PASS for p, b, _ in bids if p == partner)
    return bs.overcall_or_double(ev, last_real, partner_passed=partner_passed)

def advance_live_robots():
    hands, bids = st.session_state["hands"], st.session_state["live_bids"]
    for _ in range(12):
        if is_auction_over_strict(bids):
            st.session_state["live_done"] = True
            return
        turn = st.session_state["live_turn"]
        if turn == 2: return
        
        bid, expl = robot_bid_for_pos(turn, hands, bids)
        
        if turn == 0 and bid == bs.BID_PASS:
            st.session_state["live_partner_pass_count"] += 1
            
        bids.append((turn, bid, expl))
        st.session_state["live_turn"] = (turn + 1) % 4
        
    if is_auction_over_strict(bids): st.session_state["live_done"] = True

def submit_live_bid(user_bid: str):
    hands, bids = st.session_state["hands"], st.session_state["live_bids"]
    correct, expl = calculate_correct_live_bid(bids, HandEvaluator(hands[2]))
    
    if user_bid == bs.BID_PASS and "PAS" in expl: correct = bs.BID_PASS
    if user_bid == bs.BID_DBL and "Kontru" in expl: correct = bs.BID_DBL
        
    ok = user_bid.strip() == correct.strip()
    bids.append((2, user_bid, "Sizin Hamleniz"))
    st.session_state["live_feedback"], st.session_state["live_feedback_ok"], st.session_state["live_feedback_correct"] = expl, ok, correct
    
    st.session_state["score"]["total"] += 1
    if ok: st.session_state["score"]["correct"] += 1
    st.session_state["live_turn"] = 3
    advance_live_robots()

def new_hand_for_mode(mode: str):
    """MİNİMMUM 10 HKP FİLTRESİ: Zaman kaybettiren elleri eler, 7'li kart baraj açışını korur"""
    for _ in range(2000):
        hands = deal_hands()
        s_ev = HandEvaluator(hands[2])
        n_ev = HandEvaluator(hands[0])
        
        has_7_card_suit = any(s_ev.length(suit) >= 7 for suit in Suit)
        
        if mode in ("opening", "response"):
            if not has_7_card_suit and s_ev.hcp() < 10:
                continue
                
        nb, _ = bs.opening_bid(n_ev, seat=1)
        if mode == "opening": return hands
        if mode == "response" and nb != bs.BID_PASS: return hands
        if mode == "live": return hands
    return deal_hands()

def deal_new_hand():
    mode = st.session_state["mode"]
    hands = new_hand_for_mode(mode)
    st.session_state["hands"] = hands
    st.session_state["feedback"], st.session_state["feedback_ok"], st.session_state["correct_bid"], st.session_state["rkcb_active"], st.session_state["trump"], st.session_state["live_feedback"] = None, None, None, False, None, None
    st.session_state["seat"] = random.randint(1, 3)
    st.session_state["live_partner_pass_count"] = 0
    st.session_state["live_opener_pos"] = None
    
    n_ev = HandEvaluator(hands[0])
    st.session_state["north_bid"], st.session_state["north_suit"] = bs.opening_bid(n_ev, seat=1)
    
    if mode == "live":
        st.session_state["live_dealer"] = (st.session_state["live_dealer"] + 1) % 4
        st.session_state["live_bids"] = []
        st.session_state["live_turn"] = st.session_state["live_dealer"]
        st.session_state["live_done"] = False
        advance_live_robots()

def submit_bid(user_bid: str):
    mode, hands = st.session_state["mode"], st.session_state["hands"]
    s_ev, n_ev = HandEvaluator(hands[2]), HandEvaluator(hands[0])
    
    if mode == "opening": 
        correct, explanation = bs.opening_bid(s_ev, seat=st.session_state["seat"])
    elif mode == "response":
        if st.session_state["rkcb_active"]:
            correct, explanation = bs.rkcb_response(s_ev, st.session_state["trump"] or Suit.SPADES)
        else:
            correct, explanation = bs.suggest_response(st.session_state["north_bid"], extract_suit(st.session_state["north_bid"]), s_ev, partner_hcp=n_ev.hcp())
            if user_bid == "4NT" and correct == "4NT":
                st.session_state["rkcb_active"] = True
                st.session_state["trump"] = extract_suit(st.session_state["north_bid"]) or Suit.SPADES
    else: return
    
    if user_bid == bs.BID_DBL and "Kontru" in explanation: correct = bs.BID_DBL
        
    ok = user_bid.strip() == correct.strip()
    st.session_state["feedback"], st.session_state["feedback_ok"], st.session_state["correct_bid"] = explanation, ok, correct
    st.session_state["score"]["total"] += 1
    if ok: st.session_state["score"]["correct"] += 1

with st.sidebar:
    st.title("🃏 TBF Briç Akademi")
    st.caption("Resmi 5'li Majör & Standart Sistem")
    st.divider()
    
    mode_map = {
        "opening": "1 ── Kendi Açılış Pratiğiniz",
        "response": "2 ── Ortak Açışına Yanıtlar",
        "live": "3 ── Canlı Masa Turnuva Sekansı"
    }
    chosen = st.radio("Çalışma Alanı Seçin", options=list(mode_map.keys()), format_func=lambda x: mode_map[x])
    if chosen != st.session_state["mode"]:
        st.session_state["mode"] = chosen
        deal_new_hand()
        
    if st.button("🔀 Yeni Dağıtım Yap", type="primary", use_container_width=True):
        deal_new_hand()
        st.rerun()
        
    corrects, totals = st.session_state["score"]["correct"], st.session_state["score"]["total"]
    pct = int(corrects / totals * 100) if totals else 0
    st.metric("Performans (Doğru/Toplam)", f"{corrects} / {totals}", f"Başarı: {pct}%")

mode = st.session_state["mode"]
if st.session_state["hands"] is None:
    deal_new_hand()
    st.rerun()

hands = st.session_state["hands"]
s_ev, n_ev = HandEvaluator(hands[2]), HandEvaluator(hands[0])

# ───────────────────────────────────────────────
# MOD 3: CANLI MASA SEKANSI
# ───────────────────────────────────────────────
if mode == "live":
    st.subheader("Canlı Masa Turnuva Simülasyonu")
    bids, live_done = st.session_state["live_bids"], st.session_state["live_done"]
    
    lc1, lc2 = st.columns([1, 1])
    with lc1: 
        render_responsive_hand(s_ev, "🔴 Sizin Kartlarınız (Güney)")
        if is_auction_over_strict(bids) or live_done:
            st.divider()
            render_responsive_hand(n_ev, "Kuzey (Ortağınızın Kartları)", is_north=True)
            
    with lc2:
        st.markdown(f"**Dağıtıcı:** {POS_NAMES[st.session_state['live_dealer']]} | **Masa Akışı**")
        for p, b, e in bids:
            style_inline = get_bid_style_inline(b)
            st.markdown(f"{POS_EMOJI[p]} **{POS_NAMES[p]}**: <span style='{style_inline}'>`{b}`</span> — {e}", unsafe_allow_html=True)
            
    if st.session_state["live_feedback"]:
        if st.session_state["live_feedback_ok"]: 
            st.success(f"✅ Kusursuz Hamle! Şunu demeniz önerilirdi: {st.session_state['live_feedback']}")
        else: 
            st.error(f"❌ TBF Önerisi: {st.session_state['live_feedback_correct']} | {st.session_state['live_feedback']}")
        
    if not is_auction_over_strict(bids) and not live_done:
        st.markdown("---")
        st.markdown("<div class='table-title'>Deklerenizi Masaya Atın:</div>", unsafe_allow_html=True)
        
        last_real, _ = last_real_bid_and_pos(bids)
        allowed_bids = valid_bids_above(last_real)
        
        live_buttons = [bs.BID_PASS, bs.BID_DBL]
        for lvl in range(1, 7):
            for sym in ["♣", "♦", "♥", "♠", "NT"]:
                live_buttons.append(f"{lvl}{sym}")
        
        visible_buttons = [b for b in live_buttons if b in (bs.BID_PASS, bs.BID_DBL) or b in allowed_bids]
        
        btn_cols = st.columns(4)
        for index, b in enumerate(visible_buttons):
            if btn_cols[index % 4].button(b, key=f"lbtn_{b}"):
                submit_live_bid(b)
                st.rerun()
    else:
        st.success("🏁 Sekans Kurallara Uygun Olarak Tamamlandı. Kuzey'in Eli Sol Panelde Açıldı.")
        if st.button("Sonraki Masaya Geç ➡️", type="primary", use_container_width=True): deal_new_hand(); st.rerun()
    st.stop()

# ───────────────────────────────────────────────
# MOD 1 & 2: STANDART ANTRENMAN EKRANI
# ───────────────────────────────────────────────
sc1, sc2 = st.columns([1, 1])
with sc1:
    render_responsive_hand(s_ev, "🔴 Sizin Kartlarınız (Güney)")

with sc2:
    st.subheader("Masa Bilgisi")
    if mode == "opening":
        seat_text = {1: "1. Koltuk (Dağıtıcı Sizin)", 2: "2. Koltuk", 3: "3. Koltuk (Ortak Pas Geçti)"}
        st.info(f"Oturduğunuz Konum: **{seat_text[st.session_state['seat']]}**")
    elif mode == "response":
        st.warning(f"🔵 Kuzey (Ortak) Gerçek Sistem Açışı Yaptı: **{st.session_state['north_bid']}**")
        st.info(f"💡 Arka Plan Bilgisi: Kuzey'in gerçek gücü **{n_ev.hcp()} HKP**")

st.divider()

if st.session_state["feedback"] is not None:
    if st.session_state["feedback_ok"]: 
        st.success(f"✅ Doğru Deklere: {st.session_state['correct_bid']} | {st.session_state['feedback']}")
    else: 
        st.error(f"❌ Yanlış Tercih. TBF Kuralı Sistem Önerisi: {st.session_state['correct_bid']} | {st.session_state['feedback']}")
    if st.button("Sonraki El için Tıklayın ➡️", type="primary", use_container_width=True):
        deal_new_hand()
        st.rerun()
else:
    st.markdown("<div class='table-title'>Sisteme Göre Deklerenizi Seçin:</div>", unsafe_allow_html=True)
    if st.session_state["rkcb_active"]:
        buttons = ["5♣", "5♦", "5♥", "5♠"]
    else:
        buttons = [bs.BID_PASS, bs.BID_DBL]
        last_real_or_north = st.session_state["north_bid"] if mode == "response" else None
        allowed_bids = valid_bids_above(last_real_or_north)
        
        base_buttons = [bs.BID_PASS, bs.BID_DBL]
        for lvl in range(1, 6):
            for sym in ["♣", "♦", "♥", "♠", "NT"]: base_buttons.append(f"{lvl}{sym}")
            
        buttons = [b for b in base_buttons if b in (bs.BID_PASS, bs.BID_DBL) or b in allowed_bids]
        
    cols = st.columns(4)
    for idx, b in enumerate(buttons):
        if cols[idx % 4].button(b, key=f"sbtn_{b}"):
            submit_bid(b)
            st.rerun()
