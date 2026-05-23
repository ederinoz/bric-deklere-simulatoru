import streamlit as st
import sys
import os
import random

sys.path.insert(0, os.path.dirname(__file__))

from cards import deal_hands, Suit, SUIT_SYMBOLS, SUIT_NAMES_TR, RANK_SYMBOLS
from evaluator import HandEvaluator
import bidding_system as bs

# FOLD 7 GENİŞ/SIKI DÜZEN VE TÜM TELEFONLAR İÇİN OPTİMİZE ENJEKSİYON CSS
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { font-size: 15px !important; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; font-weight: bold; color: #1565C0; }
    
    /* ÇOHA YEŞİLİ BAŞLIK VE KOMPAKT BLOK DÜZENİ */
    .table-title { color: #2e7d32 !important; font-size: 1.4rem !important; font-weight: 800; margin-bottom: 8px; }
    
    .stButton>button { 
        width: 100%; border-radius: 6px; height: 3.3rem; 
        font-size: 1.2rem !important; font-weight: 700;
        margin-bottom: 2px !important; padding: 2px 4px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .suit-symbol { font-size: 1.7rem !important; font-weight: 700; vertical-align: middle; }
    .suit-ranks { font-family: monospace; font-size: 1.45rem !important; margin-left: 10px; font-weight: bold; vertical-align: middle; }
    .hand-info-text { font-size: 1.15rem !important; font-weight: 600; color: #37474F; margin-top: 4px; }

    /* RENK KODLAMASI: AKIŞ PANELİNDEKİ DEKLERELER */
    .bid-red { color: #c62828 !important; font-weight: bold; font-size: 1.15rem; }
    .bid-black { color: #1a1a1a !important; font-weight: bold; font-size: 1.15rem; }

    /* FOLD 7 AÇIK (GENİŞ KARE) SIKIŞTIRMA VE KENETLEME */
    @media screen and (min-width: 601px) and (max-width: 1024px) {
        html, body, [data-testid="stAppViewContainer"] { font-size: 16px !important; }
        [data-testid="stHorizontalBlock"] { gap: 0.4rem !important; padding: 0px !important; }
        .stButton>button { height: 3.4rem; font-size: 1.2rem !important; margin-bottom: 3px !important; }
        .suit-symbol { font-size: 1.8rem !important; }
        .suit-ranks { font-size: 1.55rem !important; }
        .table-title { font-size: 1.5rem !important; }
    }

    /* STANDART CEP TELEFONLARI */
    @media screen and (max-width: 600px) {
        html, body, [data-testid="stAppViewContainer"] { font-size: 13px !important; }
        .stButton>button { height: 3.0rem; font-size: 1.05rem !important; }
        [data-testid="stHorizontalBlock"] { gap: 0.2rem !important; }
        .suit-symbol { font-size: 1.4rem !important; }
        .suit-ranks { font-size: 1.25rem !important; }
        .table-title { font-size: 1.2rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

DEFAULTS = {
    "mode": "opening", "hands": None, "feedback": None, "feedback_ok": None,
    "correct_bid": None, "north_bid": None, "north_suit": None, "trump": None,
    "score": {"total": 0, "correct": 0}, "rkcb_active": False, "seat": 1,
    "live_dealer": 0, "live_bids": [], "live_turn": 0, "live_done": False,
    "live_feedback": None, "live_feedback_ok": None, "live_feedback_correct": None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state: st.session_state[k] = v

POS_NAMES  = ["Kuzey", "Doğu", "Güney", "Batı"]
POS_EMOJI  = ["🔵", "🟠", "🔴", "🟢"]
POS_COLORS = ["#1565C0", "#E65100", "#B71C1C", "#2E7D32"]

def render_responsive_hand(ev, title):
    st.markdown(f"#### {title}")
    for suit in reversed(list(Suit)):
        cards = ev.suit_cards(suit)
        color = "#c62828" if suit in (Suit.HEARTS, Suit.DIAMONDS) else "#1a1a1a"
        ranks = " ".join(RANK_SYMBOLS[c.rank] for c in sorted(cards, key=lambda c: c.rank, reverse=True)) if cards else "—"
        st.markdown(f"<span class='suit-symbol' style='color:{color};'>{SUIT_SYMBOLS[suit]}</span><span class='suit-ranks'>{ranks}</span>", unsafe_allow_html=True)
    st.markdown(f"<div class='hand-info-text'>HKP: <b>{ev.hcp()}</b> | Dağılım: <b>+{ev.distribution_points()}</b> | Toplam: <b>{ev.total_points()} TP</b></div>", unsafe_allow_html=True)

def extract_suit(bid: str) -> Suit | None:
    mapping = {"♠": Suit.SPADES, "♥": Suit.HEARTS, "♦": Suit.DIAMONDS, "♣": Suit.CLUBS}
    for sym, s in mapping.items():
        if sym in bid: return s
    return None

def get_bid_html_class(bid: str) -> str:
    """Deklere akış panelinde renk kodlaması yapar (Kupa-Karo kırmızı, Sinek-Maça siyah)"""
    if "♥" in bid or "♦" in bid: return "bid-red"
    return "bid-black"

def valid_bids_above(last_bid: str | None) -> list[str]:
    """Masadaki en son deklereye göre alt seviyedeki geçersiz butonları ayıklar"""
    order = []
    for lvl in range(1, 6):
        for sym in ["♣", "♦", "♥", "♠", "NT"]: order.append(f"{lvl}{sym}")
    if last_bid is None or last_bid == bs.BID_PASS: return [bs.BID_PASS] + order[:]
    try:
        idx = order.index(last_bid)
        return [bs.BID_PASS] + order[idx + 1:]
    except ValueError: return [bs.BID_PASS] + order[:]

def is_auction_over(bids: list) -> bool:
    if len(bids) < 3: return False
    last_three = [b for _, b, _ in bids[-3:]]
    if all(b == bs.BID_PASS for b in last_three):
        if any(b != bs.BID_PASS for _, b, _ in bids): return True
    if len(bids) >= 4 and all(b == bs.BID_PASS for _, b, _ in bids[-4:]): return True
    return False

def last_real_bid_and_pos(bids: list) -> tuple[str | None, int | None]:
    for b_pos, bid, _ in reversed(bids):
        if bid not in (bs.BID_PASS, bs.BID_DBL, "RKON"): return bid, b_pos
    return None, None

def robot_bid_for_pos(pos: int, hands: list, bids: list) -> tuple[str, str]:
    ev, partner, seat = HandEvaluator(hands[pos]), (pos + 2) % 4, len(bids) + 1
    last_real, last_real_pos = last_real_bid_and_pos(bids)
    if last_real is None: return bs.opening_bid(ev, seat=min(seat, 4))
    if last_real_pos == partner:
        if last_real == bs.BID_DBL: return bs.respond_to_double(last_real, ev)
        return bs.suggest_response(last_real, extract_suit(last_real), ev, 12)
    return bs.overcall_or_double(ev, last_real)

def advance_live_robots():
    hands, bids = st.session_state["hands"], st.session_state["live_bids"]
    for _ in range(12):
        if is_auction_over(bids):
            st.session_state["live_done"] = True
            return
        turn = st.session_state["live_turn"]
        if turn == 2: return
        bid, expl = robot_bid_for_pos(turn, hands, bids)
        bids.append((turn, bid, expl))
        st.session_state["live_turn"] = (turn + 1) % 4
    if is_auction_over(bids): st.session_state["live_done"] = True

def submit_live_bid(user_bid: str):
    hands, bids = st.session_state["hands"], st.session_state["live_bids"]
    last_real, _ = last_real_bid_and_pos(bids)
    if not bids or last_real is None:
        correct, expl = bs.opening_bid(HandEvaluator(hands[2]))
    else:
        correct, expl = bs.suggest_response(last_real, extract_suit(last_real), HandEvaluator(hands[2]), 12)
        
    ok = user_bid.strip() == correct.strip()
    bids.append((2, user_bid, "Sizin Hamleniz"))
    st.session_state["live_feedback"], st.session_state["live_feedback_ok"], st.session_state["live_feedback_correct"] = expl, ok, correct
    st.session_state["score"]["total"] += 1
    if ok: st.session_state["score"]["correct"] += 1
    st.session_state["live_turn"] = 3
    advance_live_robots()

def new_hand_for_mode(mode: str):
    for _ in range(1000):
        hands = deal_hands()
        n_ev = HandEvaluator(hands[0])
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
    n_ev = HandEvaluator(hands[0])
    st.session_state["north_bid"], st.session_state["north_suit"] = bs.opening_bid(n_ev, seat=1)
    if mode == "live":
        st.session_state["live_dealer"], st.session_state["live_bids"], st.session_state["live_turn"], st.session_state["live_done"] = 0, [], 0, False
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
            correct, explanation = bs.suggest_response(st.session_state["north_bid"], extract_suit(st.session_state["north_bid"]), s_ev, n_ev.hcp())
            if user_bid == "4NT" and correct == "4NT":
                st.session_state["rkcb_active"] = True
                st.session_state["trump"] = extract_suit(st.session_state["north_bid"]) or Suit.SPADES
    else: return
    
    ok = user_bid.strip() == correct.strip()
    st.session_state["feedback"], st.session_state["feedback_ok"], st.session_state["correct_bid"] = explanation, ok, correct
    st.session_state["score"]["total"] += 1
    if ok: st.session_state["score"]["correct"] += 1

with st.sidebar:
    st.title("🃏 TBF Briç Akademi")
    st.caption("Resmi 5'li Majör & Standart Sistem")
    st.divider()
    
    mode_map = {
        "opening": "1 ── Açılış Pratiği (Kendi Eliniz)",
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
# MOD 3: CANLI MASA SEKANSI (AKIŞ VE BUTON FİLTRELERİ GÜNCELLENDİ)
# ───────────────────────────────────────────────
if mode == "live":
    st.subheader("Canlı Masa Turnuva Simülasyonu")
    bids, live_done = st.session_state["live_bids"], st.session_state["live_done"]
    
    lc1, lc2 = st.columns([1, 1])
    with lc1: render_responsive_hand(s_ev, "🔴 Sizin Kartlarınız (Güney)")
    with lc2:
        st.markdown("**Masa Deklere Akışı**")
        for p, b, e in bids[-4:]:
            cls = get_bid_html_class(b)
            st.markdown(f"{POS_EMOJI[p]} **{POS_NAMES[p]}**: <span class='{cls}'>`{b}`</span> — <span style='font-size:0.85rem;color:#555'>{e}</span>", unsafe_allow_html=True)
            
    if st.session_state["live_feedback"]:
        if st.session_state["live_feedback_ok"]: 
            st.success(f"✅ Kusursuz Hamle! Şunu demeniz önerilirdi: {st.session_state['live_feedback']}")
        else: 
            st.error(f"❌ TBF Önerisi: {st.session_state['live_feedback_correct']} | Şunu demeniz önerilirdi: {st.session_state['live_feedback']}")
        
    if not live_done:
        st.markdown("---")
        st.markdown("<div class='table-title'>Deklerenizi Masaya Atın:</div>", unsafe_allow_html=True)
        
        # SEVİYE ALTI BUTON KİLİTLEME FİLTRESİ ENJEKSİYONU
        last_real, _ = last_real_bid_and_pos(bids)
        allowed_bids = valid_bids_above(last_real)
        
        live_buttons = [bs.BID_PASS, "1♣", "1♦", "1♥", "1♠", "1NT", "2♣", "2♦", "2♥", "2♠", "2NT", "3♣", "3♦", "3♥", "3♠", "3NT"]
        btn_cols = st.columns(4)
        
        for index, b in enumerate(live_buttons):
            # Eğer buton masadaki mevcut seviyenin altında kalıyorsa render etme / kilitle
            if b != bs.BID_PASS and b not in allowed_bids:
                btn_cols[index % 4].button(b, key=f"lbtn_{b}", disabled=True)
            else:
                if btn_cols[index % 4].button(b, key=f"lbtn_{b}"):
                    submit_live_bid(b)
                    st.rerun()
    else:
        st.success("🏁 Sekans Kurallara Uygun Olarak Tamamlandı.")
        if st.button("Sonraki Masaya Geç", type="primary", use_container_width=True): deal_new_hand(); st.rerun()
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
        if st.session_state["rkcb_active"]:
            st.warning(f"Koz Anlaşması: **{SUIT_NAMES_TR[st.session_state['trump']]}** | Ortak **4NT** Sordu. RKCB 0314 Yanıtı Verin.")
        else:
            st.warning(f"🔵 Kuzey (Ortak) Sistem Açışı Yaptı: **{st.session_state['north_bid']}**")

st.divider()

if st.session_state["feedback"] is not None:
    if st.session_state["feedback_ok"]: 
        st.success(f"✅ Doğru Deklere: {st.session_state['correct_bid']} | Şunu demeniz önerilirdi: {st.session_state['feedback']}")
    else: 
        st.error(f"❌ Yanlış Tercih. TBF Kuralı Sistem Önerisi: {st.session_state['correct_bid']} | Şunu demeniz önerilirdi: {st.session_state['feedback']}")
    if st.button("Sonraki El için Tıklayın ➡️", type="primary", use_container_width=True):
        deal_new_hand()
        st.rerun()
else:
    st.markdown("<div class='table-title'>Sisteme Göre Deklerenizi Seçin:</div>", unsafe_allow_html=True)
    if st.session_state["rkcb_active"]:
        buttons = ["5♣", "5♦", "5♥", "5♠"]
    else:
        buttons = [bs.BID_PASS, "1♣", "1♦", "1♥", "1♠", "1NT", "2♣", "2♦", "2♥", "2♠", "2NT", "3♣", "3♦", "3♥", "3♠", "3NT", "4♣", "4♦", "4♥", "4♠", "4NT"]
        
    cols = st.columns(4)
    for idx, b in enumerate(buttons):
        if cols[idx % 4].button(b, key=f"sbtn_{b}"):
            submit_bid(b)
            st.rerun()
