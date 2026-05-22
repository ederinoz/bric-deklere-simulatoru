import streamlit as st
import sys
import os
import random
sys.path.insert(0, os.path.dirname(__file__))
from cards import deal_hands, Suit, SUIT_SYMBOLS, SUIT_NAMES_TR, RANK_SYMBOLS
from evaluator import HandEvaluator
from bidding_system import (
    opening_bid, opening_bid_trace, suggest_response, rkcb_response,
    response_to_1nt, response_to_major, BID_PASS, BID_DBL, suit_symbol,
    overcall_or_double, respond_to_double, _bid_rank
)

st.set_page_config(page_title="Briç Deklere Simülatörü", page_icon="🃏", layout="wide")

MODE_TITLES = {
    "opening":        "Açılış Pratiği — TBF 5'li Majör",
    "response_major": "Yanıt Pratiği — 1♥ / 1♠ Sonrası",
    "response_1nt":   "Yanıt Pratiği — 1NT Sonrası",
    "rkcb":           "RKCB 0314 Pratiği",
    "full":           "Tam Deklere Sekansı",
    "live":           "Canlı Masa Sekansı",
}

DEFAULTS = {
    "mode": "opening", "hands": None, "step": 0, "feedback": None, "feedback_ok": None,
    "correct_bid": None, "north_bid": None, "north_suit": None, "trump": None,
    "score": {"total": 0, "correct": 0}, "rkcb_trump_chosen": False, "full_step": 0, "seat": 1,
    "karar_agaci_acik": False,
    "live_dealer": 0, "live_zone": "Kimse", "live_bids": [], "live_turn": 0, "live_done": False,
    "live_feedback": None, "live_feedback_ok": None, "live_feedback_correct": None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state: st.session_state[k] = v

POS_NAMES  = ["Kuzey", "Doğu", "Güney", "Batı"]
POS_EMOJI  = ["🔵", "🟠", "🔴", "🟢"]
POS_COLORS = ["#1565C0", "#E65100", "#B71C1C", "#2E7D32"]
ALL_BIDS_ORDER: list[str] = []
for _lvl in range(1, 8):
    for _sym in ["♣", "♦", "♥", "♠", "NT"]: ALL_BIDS_ORDER.append(f"{_lvl}{_sym}")

def suit_color(suit: Suit) -> str:
    return "#e03030" if suit in (Suit.HEARTS, Suit.DIAMONDS) else "#1a1a1a"

_DP_BADGE: dict[int, str] = {
    1: '<span style="margin-left:10px;font-size:0.73em;background:#546E7A;color:#fff;padding:1px 7px;border-radius:10px;font-weight:bold;vertical-align:middle" title="2 kartlı renk: +1 dağılım puanı">+1 Dubleton</span>',
    2: '<span style="margin-left:10px;font-size:0.73em;background:#E65100;color:#fff;padding:1px 7px;border-radius:10px;font-weight:bold;vertical-align:middle" title="Tek kartlı renk: +2 dağılım puanı">+2 Teketon</span>',
    3: '<span style="margin-left:10px;font-size:0.73em;background:#B71C1C;color:#fff;padding:1px 7px;border-radius:10px;font-weight:bold;vertical-align:middle" title="Boş renk (şanzman): +3 dağılım puanı">+3 Şanzman</span>',
}

def render_hand(ev: HandEvaluator, title: str, show_hcp: bool = True):
    st.markdown(f"**{title}**")
    for suit in reversed(list(Suit)):
        cards = ev.suit_cards(suit)
        color = suit_color(suit)
        sym   = SUIT_SYMBOLS[suit]
        ln    = len(cards)
        ranks = " ".join(RANK_SYMBOLS[c.rank] for c in sorted(cards, key=lambda c: c.rank, reverse=True)) if cards else "—"
        dp_bonus = 3 if ln == 0 else (2 if ln == 1 else (1 if ln == 2 else 0))
        badge    = _DP_BADGE.get(dp_bonus, "")
        st.markdown(f'<span style="font-size:1.25em; color:{color}; font-weight:600">{sym}</span><span style="font-size:1.1em; font-family:monospace; margin-left:8px">{ranks}</span>{badge}', unsafe_allow_html=True)
    if show_hcp:
        hcp, dp_total, tp = ev.hcp(), ev.distribution_points(), ev.total_points()
        st.markdown(f'<div style="margin-top:6px;padding:5px 10px;background:#f0f4f8;border-radius:6px;font-size:0.88em;color:#37474F;line-height:1.6">HKP: <b>{hcp}</b>&nbsp; + &nbsp;Dağılım: <b>+{dp_total}</b>&nbsp; = &nbsp;Toplam: <b style="color:#1565C0;font-size:1.05em">{tp} TP</b></div>', unsafe_allow_html=True)

def extract_suit(bid: str) -> Suit | None:
    mapping = {"♠": Suit.SPADES, "♥": Suit.HEARTS, "♦": Suit.DIAMONDS, "♣": Suit.CLUBS}
    for sym, s in mapping.items():
        if sym in bid: return s
    return None

def bid_color(bid: str) -> str:
    return "#c62828" if "♥" in bid or "♦" in bid else "#1a1a1a"

def valid_bids_above(last_bid: str | None) -> list[str]:
    if last_bid is None or last_bid == BID_PASS: return [BID_PASS] + ALL_BIDS_ORDER[:]
    try:
        idx = ALL_BIDS_ORDER.index(last_bid)
        return [BID_PASS] + ALL_BIDS_ORDER[idx + 1 :]
    except ValueError: return [BID_PASS] + ALL_BIDS_ORDER[:]

def is_auction_over(bids: list) -> bool:
    if len(bids) < 3: return False

    # --- GAME FORCING (GF) KONTROLÜ ---
    bids_strings = [b for _, b, _ in bids]
    is_gf = "2NT" in bids_strings and any(b.startswith("1♠") or b.startswith("1♥") for b in bids_strings)

    if is_gf:
        last_real, _ = last_real_bid_and_pos(bids)
        if last_real:
            if last_real.startswith("4") or ("NT" in last_real and int(last_real[0]) >= 3):
                pass 
            else:
                return False  # Zona ulaşılmadıysa pas döngüsüyle ihale BİTEMEZ!

    last_three = [b for _, b, _ in bids[-3:]]
    if all(b == BID_PASS for b in last_three):
        if any(b != BID_PASS for _, b, _ in bids): return True
    if len(bids) >= 4 and all(b == BID_PASS for _, b, _ in bids[-4:]): return True
    return False

def last_real_bid_and_pos(bids: list) -> tuple[str | None, int | None]:
    for b_pos, bid, _ in reversed(bids):
        if bid not in (BID_PASS, BID_DBL, "RKON"): return bid, b_pos
    return None, None

def robot_bid_for_pos(pos: int, hands: list, bids: list) -> tuple[str, str]:
    ev, partner, seat = HandEvaluator(hands[pos]), (pos + 2) % 4, len(bids) + 1
    last_real, last_real_pos = last_real_bid_and_pos(bids)

    if last_real is None: 
        return opening_bid(ev, seat=min(seat, 4))

    our_last     = next((b for p, b, _ in reversed(bids) if p == pos     and b != BID_PASS), None)
    partner_last = next((b for p, b, _ in reversed(bids) if p == partner and b != BID_PASS), None)

    # --- MINÖR AÇILIŞI SONRASI 2NT ZON GARANTİSİ KORUMASI ---
    bids_strings = [b for _, b, _ in bids]
    if len(bids_strings) >= 2:
        # Eğer ortak (Kuzey/Robot) 2NT demişse ve siz (Güney) üstüne 3 Sinek veya 3 Karo kaçtıysanız
        if "2NT" in bids_strings and (bids_strings[-1] == "3♣" or bids_strings[-1] == "3♦"):
            if pos == 0:  # Sıra Kuzey'e geldiğinde Pas demesin, 3NT ile zona tamamlasın!
                return "3NT", "Ortak minör rengini tekrarladı, 15+ dengeli puanla 3NT'ye tamamlıyorum."

    # 1. DURUM: En son konuşan bizim ortağımızsa (YANIT MODU)
    if last_real_pos == partner:
        if last_real == BID_DBL:
            doubled = _find_doubled_suit_bid(bids, partner)
            return respond_to_double(doubled, ev)
        s = extract_suit(last_real)
        bid, expl = suggest_response(last_real, s, ev, 12)
        if "tekrifi" in expl or "tıkacı" in expl or "1NT" in last_real:
            expl = f"{last_real} konuşmasına natürel sistem yanıtı"
        return bid, expl

    # 2. DURUM: En son rakip konuştuysa (ARAYA GİRİŞ/DEFANS MODU)
    if our_last is None and partner_last is None: 
        return overcall_or_double(ev, last_real)

    # 3. DURUM: Ortağımızın araya girişine rekabetçi destek
    if our_last is None and partner_last is not None:
        p_suit = extract_suit(partner_last)
        if p_suit and ev.length(p_suit) >= 3 and ev.hcp() >= 6:
            sym = suit_symbol(p_suit)
            return f"2{sym}", f"Ortağın araya giriş rengine destek – 3+ {sym}"

    return BID_PASS, "Pas"

def correct_south_live(bids: list, hands: list) -> tuple[str, str]:
    s_ev, n_ev, seat = HandEvaluator(hands[2]), HandEvaluator(hands[0]), len(bids) + 1
    last_real, last_real_pos = last_real_bid_and_pos(bids)
    if last_real is None: return opening_bid(s_ev, seat=min(seat, 4))

    south_last = next((b for p, b, _ in reversed(bids) if p == 2 and b != BID_PASS), None)

    # En son konuşan ortağımız Kuzey (0) ise natürel sistem kuralları
    if last_real_pos == 0:
        if last_real == BID_DBL: return respond_to_double(last_real, s_ev)
        return suggest_response(last_real, extract_suit(last_real), s_ev, n_ev.hcp())

    # En son rakipler konuştuysa araya giriş kuralları
    if last_real_pos in (1, 3) and south_last is None:
        north_last = next((b for p, b, _ in reversed(bids) if p == 0 and b != BID_PASS), None)
        if north_last is None: return overcall_or_double(s_ev, last_real)
        n_suit = extract_suit(north_last)
        if n_suit and s_ev.length(n_suit) >= 3 and s_ev.hcp() >= 6:
            return f"2{suit_symbol(n_suit)}", f"Partner açılışına destek – 3+ {suit_symbol(n_suit)}"

    # GÜNEY İÇİN GF AKTİFKEN PAS ÖNERME KORUMASI
    bids_strings = [b for _, b, _ in bids]
    if "2NT" in bids_strings and not (last_real and (last_real.startswith("4") or "NT" in last_real)):
        if north_suit:
            return f"4{suit_symbol(north_suit)}", "Game Forcing (GF) aktif – Zona tamamlanmalı!"

    return BID_PASS, "Pas önerilir"

def advance_live_robots():
    """Robotların sıra Güney'e (2) gelene kadar oynamasını sağlayan ana döngü"""
    hands, bids = st.session_state["hands"], st.session_state["live_bids"]
    for _ in range(20):
        if is_auction_over(bids):
            st.session_state["live_done"] = True
            return
        turn = st.session_state["live_turn"]
        if turn == 2:  # Sıra Güney'de (Sizde) ise dur, kullanıcının tıklamasını bekle
            return
        bid, expl = robot_bid_for_pos(turn, hands, bids)
        bids.append((turn, bid, expl))
        st.session_state["live_turn"] = (turn + 1) % 4
    if is_auction_over(bids):
        st.session_state["live_done"] = True

def submit_live_bid(user_bid: str):
    hands, bids = st.session_state["hands"], st.session_state["live_bids"]
    correct, expl = correct_south_live(bids, hands)
    ok = user_bid.strip() == correct.strip()
    bids.append((2, user_bid, "Oyuncunun hamlesi"))
    st.session_state["live_feedback"], st.session_state["live_feedback_ok"], st.session_state["live_feedback_correct"] = expl, ok, (correct if not ok else None)
    st.session_state["score"]["total"] += 1
    if ok: st.session_state["score"]["correct"] += 1

    st.session_state["live_turn"] = 3
    advance_live_robots()

def _south_hand_ok(hands: list) -> bool:
    s_ev, hcp = HandEvaluator(hands[2]), HandEvaluator(hands[2]).hcp()
    for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
        if s_ev.length(suit) >= 7 and hcp >= 6: return True
    return hcp >= 9

def new_hand_for_mode(mode: str):
    for _ in range(500):
        hands = deal_hands()
        if not _south_hand_ok(hands): continue
        n_ev = HandEvaluator(hands[0])
        nb, _ = opening_bid(n_ev, seat=1)
        ns = extract_suit(nb)
        if mode in ("opening", "rkcb", "full", "live"): return hands
        if mode == "response_major" and ns in (Suit.HEARTS, Suit.SPADES) and nb.startswith("1"): return hands
        if mode == "response_1nt" and 15 <= n_ev.hcp() <= 17 and n_ev.is_balanced(): return hands
    return deal_hands()

def deal_new_hand():
    mode = st.session_state["mode"]
    hands = new_hand_for_mode(mode)
    st.session_state["hands"] = hands
    st.session_state["feedback"], st.session_state["feedback_ok"], st.session_state["correct_bid"], st.session_state["step"], st.session_state["full_step"], st.session_state["rkcb_trump_chosen"], st.session_state["trump"], st.session_state["live_feedback"], st.session_state["live_feedback_ok"], st.session_state["live_feedback_correct"] = None, None, None, 0, 0, False, None, None, None, None
    st.session_state["seat"] = random.randint(1, 3) if mode == "opening" else 1
    n_ev = HandEvaluator(hands[0])
    nb, _ = opening_bid(n_ev, seat=1)
    st.session_state["north_bid"], st.session_state["north_suit"] = nb, extract_suit(nb)

    if mode == "live":
        # Dağıtıcıyı 0-3 arası (Kuzey, Doğu, Güney, Batı) tamamen özgürce seçiyoruz
        dealer = random.randint(0, 3)
        zone = random.choice(["Kimse", "K-G", "D-B", "Herkes"])
        st.session_state["live_dealer"] = dealer
        st.session_state["live_zone"] = zone
        st.session_state["live_bids"] = []
        st.session_state["live_turn"] = dealer
        st.session_state["live_done"] = False

        # SIRA SİZDE (GÜNEY = 2) DEĞİLSE, ROBOTLAR KENDİ ARALARINDA SIRA SİZE GELENE KADAR AKITSIN
        if dealer != 2:
            advance_live_robots()

def submit_bid(user_bid: str):
    mode, hands = st.session_state["mode"], st.session_state["hands"]
    s_ev, n_ev = HandEvaluator(hands[2]), HandEvaluator(hands[0])
    if mode == "opening": correct, explanation = opening_bid(s_ev, seat=st.session_state["seat"])
    elif mode == "response_major": correct, explanation = suggest_response(st.session_state["north_bid"], st.session_state["north_suit"], s_ev, n_ev.hcp())
    elif mode == "response_1nt": correct, explanation = response_to_1nt(s_ev)
    elif mode == "rkcb": correct, explanation = rkcb_response(s_ev, st.session_state["trump"])
    elif mode == "full":
        if st.session_state["full_step"] == 0:
            correct, explanation = suggest_response(st.session_state["north_bid"], st.session_state["north_suit"], s_ev, n_ev.hcp())
            st.session_state["full_step"] = 1
        else:
            trump = st.session_state["trump"] or st.session_state["north_suit"]
            correct, explanation = rkcb_response(s_ev, trump or Suit.SPADES)
    else: return
    ok = user_bid.strip() == correct.strip()
    st.session_state["feedback"], st.session_state["feedback_ok"], st.session_state["correct_bid"] = explanation, ok, correct
    st.session_state["score"]["total"] += 1
    if ok: st.session_state["score"]["correct"] += 1

RULE_CARD_OPENING = "\n| Deklere | Kural |\n|---------|-------|\n| **1♣** | 3+ Sinek, 12-21 HKP |\n| **1♦** | 4+ Karo, 12-21 HKP |\n| **1♥** | **5+ Kupa**, 12-21 HKP |\n| **1♠** | **5+ Maça**, 12-21 HKP |\n| **1NT** | Dengeli, 15-17 HKP |\n| **2♣** | Yapay güçlü, 22+ HKP |\n| **2♦/2♥/2♠** | Zayıf iki, 6 koz, 6-10 HKP ¹ |\n| **2NT** | Dengeli, 20-21 HKP |\n| **3x** | Preemptif, 7+ koz, 5-10 HKP |\n| **PAS** | Toplam Puan < 12 (HKP + Dağılım) |\n\n¹ **Zayıf 2 koltuk kuralı:**\n- 1. ve 2. koltuk → 6 kart **+ en az 2 büyük onör** (A/K/Q/J) renkte\n- 3. koltuk → sadece 6 kart yeterli (ortak pas geçti, kalite aranmaz)\n"
RULE_CARD_RESPONSE = "\n| Deklere | Kural |\n|---------|-------|\n| **PAS** | < 6 HKP |\n| **1NT** | 6-9 HKP, desteksiz |\n| **2♥/2♠** | 3+ destek, 6-9 HKP |\n| **3♥/3♠** | 3+ destek, 10-12 HKP (sınır) |\n| **4♥/4♠** | 5+ destek, < 10 HKP (kapatma) |\n| **2NT** | Jacoby: 4+ destek, 13+ HKP |\n| Yeni renk | 10+ HKP, zorlayıcı |\n"
RULE_CARD_1NT = "\n| Deklere | Kural |\n|---------|-------|\n| **PAS** | 0-7 HKP |\n| **2♣** | Stayman (4'lü majör sorusu) |\n| **2♦** | Jacoby transfer → 5+ Kupa |\n| **2♥** | Jacoby transfer → 5+ Maça |\n| **2NT** | Davet, 8-9 HKP |\n| **3NT** | Oyun, 10+ HKP |\n"
RULE_CARD_RKCB = "\n| Yanıt | Anahtar Koz Sayısı |\n|-------|-------------------|\n| **5♣** | 0 veya 3 |\n| **5♦** | 1 veya 4 |\n| **5♥** | 2 veya 5 — **koz kızı YOK** |\n| **5♠** | 2 veya 5 — **koz kızı VAR** |\n\n*Anahtar kozlar: 4 as + koz rengi K = toplam 5*\n"
RULE_CARD_LIVE = "\n**Canlı Masa:** Tüm masa TBF 5'li Majör kurallarıyla deklere yapar.\n\n- 🔵 Kuzey / 🟠 Doğu / 🟢 Batı → Robot\n- 🔴 Güney → **Siz**\n\nHer hamleniz TBF'ye göre kontrol edilir; hatalıysa uyarı gösterilir\nama sekans durmadan devam eder.\n\n**Bitiş:** 3 ardışık PAS (açılış varsa) veya 4 PAS (herkese).\n"
RULE_CARDS = {"opening": RULE_CARD_OPENING, "response_major": RULE_CARD_RESPONSE, "response_1nt": RULE_CARD_1NT, "rkcb": RULE_CARD_RKCB, "full": RULE_CARD_RESPONSE, "live": RULE_CARD_LIVE}

with st.sidebar:
    st.title("🃏 Briç Simülatörü")
    st.caption("TBF 5'li Majör  ·  RKCB 0314")
    st.divider()
    mode_labels = {"opening": "1  Açılış Pratiği", "response_major": "2  Yanıt (1♥ / 1♠)", "response_1nt": "3  Yanıt (1NT)", "rkcb": "4  RKCB 0314", "full": "5  Tam Sekans", "live": "6  Canlı Masa Sekansı"}
    chosen = st.radio("Antrenman Modu", options=list(mode_labels.keys()), format_func=lambda x: mode_labels[x], key="mode_radio")
    if chosen != st.session_state["mode"]:
        st.session_state["mode"], st.session_state["hands"], st.session_state["feedback"], st.session_state["feedback_ok"], st.session_state["live_bids"], st.session_state["live_done"], st.session_state["live_feedback"], st.session_state["live_feedback_ok"] = chosen, None, None, None, [], False, None, None
    st.divider()
    if st.button("🔀  Yeni El", use_container_width=True, type="primary"):
        deal_new_hand()
        st.rerun()
    st.divider()
    sc, total, correct = st.session_state["score"], st.session_state["score"]["total"], st.session_state["score"]["correct"]
    pct = int(correct / total * 100) if total else 0
    st.metric("Doğru / Toplam", f"{correct} / {total}", f"{pct}%")
    if total >= 5:
        if pct >= 80: st.success("Mükemmel gidiyor! 🏆")
        elif pct >= 60: st.info("İyi ilerliyorsunuz!")
        else: st.warning("Pratik yapmaya devam edin.")
    if st.button("Sıfırla", use_container_width=True):
        st.session_state["score"] = {"total": 0, "correct": 0}
        st.rerun()
    st.divider()
    with st.expander("📋 Kural Kartı"): st.markdown(RULE_CARDS.get(st.session_state["mode"], RULE_CARD_OPENING))

mode = st.session_state["mode"]
st.header(MODE_TITLES[mode])
if st.session_state["hands"] is None:
    st.info("Sol menüden **Yeni El** butonuna tıklayarak canlı masayı başlatın." if mode == "live" else "Sol menüden **Yeni El** butonuna tıklayarak başlayın.")
    st.stop()

if mode == "live":
    dealer, zone, bids, live_done, turn = st.session_state["live_dealer"], st.session_state["live_zone"], st.session_state["live_bids"], st.session_state["live_done"], st.session_state["live_turn"]
    zone_icon = {"Kimse": "🟢", "K-G": "🔴", "D-B": "🟡", "Herkes": "🔴"}.get(zone, "")
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Dağıtıcı", f"{POS_EMOJI[dealer]} {POS_NAMES[dealer]}")
    mc2.metric("Zon", f"{zone_icon} {zone}")
    mc3.metric("Durum" if live_done else "Sıra", "✅ Sekans bitti" if live_done else f"{POS_EMOJI[turn]} {POS_NAMES[turn]}")
    st.divider()
    h = st.session_state["hands"]
    col_north_info, col_s = st.columns([1, 2])
    with col_north_info:
        with st.container(border=True):
            st.markdown("****🔵 Kuzey (Ortağınız)**")
            if live_done:
                render_hand(HandEvaluator(h[0]), "Kuzey'in Gerçek Kartları", show_hcp=True)
            else:
                st.caption("Briç antrenmanında ortağın eli görünemez.")
                st.markdown("<div style='text-align:center;font-size:2.5em;padding:12px'>🂠🂠🂠🂠</div>", unsafe_allow_html=True)
    with col_s:
        with st.container(border=True): render_hand(HandEvaluator(h[2]), "🔴 Güney'in Eli (Sizin)")
    st.divider()
    st.subheader("Deklere Tablosu")
    hcols = st.columns(4)
    for hc, name, color in zip(hcols, POS_NAMES, POS_COLORS):
        hc.markdown(f"<div style='text-align:center;font-weight:bold;color:{color};border-bottom:2px solid {color};padding-bottom:4px'>{name}</div>", unsafe_allow_html=True)
    all_cells = list(bids)
    if not live_done and turn == 2: all_cells.append((2, "👉", ""))
    def build_grid(cells, d):
        rows = []
        for i, (pos, bid, _) in enumerate(cells):
            abs_pos = d + i
            row_idx, col_idx = abs_pos // 4, abs_pos % 4
            while len(rows) <= row_idx: rows.append([""] * 4)
            rows[row_idx][col_idx] = (pos, bid)
        return rows
    grid = build_grid(all_cells, dealer)
    for row in grid:
        rcols = st.columns(4)
        for j, (rc, cell) in enumerate(zip(rcols, row)):
            if cell == "": rc.write(" "); continue
            pos_idx, bid = cell
            if bid == "👉": rc.markdown("<div style='text-align:center;background:#dbeafe;border:2px dashed #1565C0;border-radius:6px;padding:6px;font-weight:bold;color:#1565C0'>👉 Sıranız</div>", unsafe_allow_html=True)
            elif bid == BID_PASS: rc.markdown("<div style='text-align:center;color:#888;font-style:italic;padding:4px'>PAS</div>", unsafe_allow_html=True)
            else:
                bc, bg = bid_color(bid), ("#fff9e6" if pos_idx == 2 else "#ffffff")
                rc.markdown(f"<div style='text-align:center;background:{bg};border-radius:5px;padding:4px;font-weight:bold;font-size:1.15em;color:{bc}'>{bid}</div>", unsafe_allow_html=True)
    st.divider()
    if bids:
        with st.expander("🤖 Robot açıklamaları", expanded=False):
            for pos_idx, bid, expl in bids[-8:]:
                if pos_idx != 2 and expl: st.caption(f"{POS_EMOJI[pos_idx]} **{POS_NAMES[pos_idx]}** → {bid}:  {expl}")
    if st.session_state["live_feedback"] is not None:
        if st.session_state["live_feedback_ok"]: st.success("✅ **Doğru hamle!**")
        else: st.warning(f"⚠️ **Önerilen deklere: {st.session_state['live_feedback_correct'] or '?'}** — Sekans devam ediyor.")
        st.markdown(f"> {st.session_state['live_feedback']}")
        st.divider()
    if live_done:
        last_real, last_real_pos = last_real_bid_and_pos(bids)
        if last_real and last_real_pos is not None: st.success(f"🏁 **Sekans tamamlandı!** Son kontrat: **{last_real}** —  {POS_EMOJI[last_real_pos]} {POS_NAMES[last_real_pos]} oynar.")
        else: st.info("🏁 **Herkes pas geçti.** El oynanmıyor.")
        st.caption(f"Toplam {len(bids)} deklere yapıldı.  Güney {len([b for p, b, e in bids if p == 2])} kez deklere etti.")
        if st.button("🔀 Yeni El", type="primary", key="live_new"): deal_new_hand(); st.rerun()
        st.stop()
    if turn == 2:
        last_real, _ = last_real_bid_and_pos(bids)
        available    = valid_bids_above(last_real)
        st.markdown("#### ✋ Sıra Sizde — Deklerenizi Seçin")
        pas_col, _ = st.columns([1, 5])
        with pas_col:
            if st.button("PAS", use_container_width=True, key="live_btn_PAS"): submit_live_bid(BID_PASS); st.rerun()
        real_bids = [b for b in available if b != BID_PASS and b[0] <= "5"]
        if real_bids:
            st.markdown("**Seviyeli Deklereler:**")
            for lvl in range(1, 6):
                level_bids = [b for b in real_bids if b.startswith(str(lvl))]
                if not level_bids: continue
                lcols = st.columns(len(level_bids))
                for col_w, bid in zip(lcols, level_bids):
                    with col_w:
                        if st.button(bid, use_container_width=True, key=f"live_btn_{bid}"): submit_live_bid(bid); st.rerun()
    st.stop()

hands, s_ev, n_ev, north_bid, north_suit = st.session_state["hands"], HandEvaluator(st.session_state["hands"][2]), HandEvaluator(st.session_state["hands"][0]), st.session_state["north_bid"], st.session_state["north_suit"]
if mode == "full":
    col_n, col_s = st.columns(2)
    with col_n:
        with st.container(border=True): render_hand(n_ev, "🔵 Kuzey'in Eli")
    with col_s:
        with st.container(border=True): render_hand(s_ev, "🔴 Güney'in Eli (Sizin)")
else:
    col_hand, col_ctx = st.columns([1, 1])
    with col_hand:
        with st.container(border=True): render_hand(s_ev, "🔴 Sizin Eliniz (Güney)")
    with col_ctx:
        with st.container(border=True):
            if mode == "response_major":
                st.markdown(f"**Kuzey Açılışı:** &nbsp; <span style='font-size:1.4em'>{north_bid}</span>", unsafe_allow_html=True)
                st.caption("Kuzey'in açılışına Güney olarak yanıt verin.")
            elif mode == "response_1nt":
                st.markdown("<span style='font-size:1.4em'>**Kuzey: 1NT** (15-17 HKP, dengeli)</span>", unsafe_allow_html=True)
                st.caption("1NT açılışına yanıt verin.")
            elif mode == "opening":
                seat = st.session_state["seat"]
                seat_labels = {1: "1. Koltuk — satıcı", 2: "2. Koltuk", 3: "3. Koltuk — ortak pas geçti"}
                st.markdown(f"**Koltuk:** {seat_labels[seat]}")
                st.caption("3. koltukta zayıf 2 için yalnızca 6 kart yeterli (kalite aranmaz)." if seat == 3 else f"{seat}. koltukta zayıf 2 için 6 kart + renkte 2 büyük onör (A/K/Q/J) gerekir.")
            elif mode == "rkcb": st.markdown("**Görev:** RKCB 0314 — Partner 4NT sordu, yanıt verin.")

if mode == "rkcb" and not st.session_state["rkcb_trump_chosen"]:
    st.subheader("Koz rengi seçin")
    trump_cols = st.columns(4)
    trump_map  = {"♠ Maça": Suit.SPADES, "♥ Kupa": Suit.HEARTS, "♦ Karo": Suit.DIAMONDS, "♣ Sinek": Suit.CLUBS}
    for i, (label, suit) in enumerate(trump_map.items()):
        with trump_cols[i]:
            if st.button(label, use_container_width=True):
                st.session_state["trump"], st.session_state["rkcb_trump_chosen"] = suit, True
                st.rerun()
    st.stop()

if mode == "rkcb" and st.session_state["rkcb_trump_chosen"]:
    trump = st.session_state["trump"]
    st.info(f"**Koz:** {SUIT_SYMBOLS[trump]} {SUIT_NAMES_TR[trump]}  |  Anahtar koz sayınız: **{s_ev.key_cards(trump)}** |  {SUIT_SYMBOLS[trump]} Koz kızı: **{'VAR ✓' if s_ev.has_trump_queen(trump) else 'YOK ✗'}**")

if mode == "full":
    fstep = st.session_state["full_step"]
    if fstep == 0: st.info(f"**Kuzey açılışı: {north_bid}** — Güney olarak yanıt verin.")
    else:
        trump = st.session_state.get("trump") or north_suit
        if trump: f"Koz anlaşması: {SUIT_SYMBOLS[trump]} {SUIT_NAMES_TR[trump]}  — Partner 4NT sordu. **RKCB 0314** yanıtı verin."

st.divider()
if st.session_state["feedback"] is not None:
    if st.session_state["feedback_ok"]: st.success(f"✅ **Doğru!** Deklere: **{st.session_state['correct_bid']}**")
    else: st.error(f"❌ **Yanlış.** Önerilen deklere: **{st.session_state['correct_bid']}**")
    st.markdown(f"> {st.session_state['feedback']}")
    st.divider()

def render_opening_trace(steps: list[dict]) -> None:
    rows_html = []
    for st_item in steps:
        n, name, detail, hit, is_stop = st_item["step"], st_item["name"], st_item["detail"], st_item["hit"], st_item.get("is_stop", False)
        if hit and is_stop: icon, bg, border, color, weight, opacity = "⛔", "#FFEBEE", "#C62828", "#B71C1C", "bold", "1"
        elif hit: icon, bg, border, color, weight, opacity = "✅", "#E8F5E9", "#2E7D32", "#1B5E20", "bold", "1"
        else: icon, bg, border, color, weight, opacity = "↷", "transparent", "transparent", "#78909C", "normal", "0.75"
        rows_html.append(f'<div style="display:flex;align-items:flex-start;margin:3px 0;padding:4px 10px;background:{bg};border-left:3px solid {border};border-radius:4px;opacity:{opacity}"><span style="min-width:22px;font-size:1em;flex-shrink:0">{icon}</span><span style="font-size:0.83em;color:{color};font-weight:{weight};line-height:1.45"><b>Adım {n}: {name}</b><span style="font-weight:normal;margin-left:6px">— {detail}</span></span></div>')
    st.markdown('<div style="background:#FAFAFA;border:1px solid #E0E0E0;border-radius:8px;padding:8px 6px;margin-bottom:10px">' + "".join(rows_html) + '</div>', unsafe_allow_html=True)

def bid_buttons(bids_list: list[str], cols_per_row: int = 5):
    if st.session_state["feedback"] is not None: return
    rows = [bids_list[i : i + cols_per_row] for i in range(0, len(bids_list), cols_per_row)]
    for row in rows:
        cols = st.columns(len(row))
        for col, bid in zip(cols, row):
            with col:
                if st.button(bid, use_container_width=True): submit_bid(bid); st.rerun()

if mode == "opening":
    st.markdown("#### Açılış Deklereniz")
    _, _trace_steps = opening_bid_trace(s_ev, seat=st.session_state["seat"])
    with st.expander("🌳 Açılış Karar Ağacı", expanded=st.session_state.get("karar_agaci_acik", False)): render_opening_trace(_trace_steps)
    bid_buttons([BID_PASS, "1♣", "1♦", "1♥", "1♠", "1NT", "2♣", "2♦", "2♥", "2♠", "2NT", "3♣", "3♦", "3♥", "3♠"])
elif mode == "response_major":
    st.markdown(f"#### {north_bid} Açılışına Yanıtınız")
    bid_buttons([BID_PASS, "1♠", "1NT", "2♣", "2♦", "2♥", "3♥", "4♥", "2NT"] if north_suit == Suit.HEARTS else [BID_PASS, "1NT", "2♣", "2♦", "2♥", "2♠", "3♠", "4♠", "2NT"])
elif mode == "response_1nt":
    st.markdown("#### 1NT Açılışına Yanıtınız")
    bid_buttons([BID_PASS, "2♣", "2♦", "2♥", "2NT", "3NT"], cols_per_row=6)
elif mode == "rkcb" and st.session_state["rkcb_trump_chosen"]:
    st.markdown("#### RKCB 0314 Yanıtınız")
    bid_buttons(["5♣", "5♦", "5♥", "5♠"], cols_per_row=4)
elif mode == "full" and st.session_state["feedback"] is None:
    if fstep == 0:
        st.markdown(f"#### {north_bid} Açılışına Yanıtınız")
        if north_suit == Suit.HEARTS: bid_buttons([BID_PASS, "1♠", "1NT", "2♣", "2♦", "2♥", "3♥", "4♥", "2NT"])
        elif north_suit == Suit.SPADES: bid_buttons([BID_PASS, "1NT", "2♣", "2♦", "2♥", "2♠", "3♠", "4♠", "2NT"])
        elif north_bid == "1NT": bid_buttons([BID_PASS, "2♣", "2♦", "2♥", "2NT", "3NT"])
        else: bid_buttons([BID_PASS, "1♦", "1♥", "1♠", "1NT", "2♣", "2♦", "2♥", "2♠", "2NT"])
    elif fstep == 1:
        if s_ev.hcp() >= 13 and n_ev.hcp() >= 14 and north_suit:
            st.session_state["trump"] = north_suit
            st.markdown("#### RKCB 0314 Yanıtı (Partner 4NT sordu)")
            bid_buttons(["5♣", "5♦", "5♥", "5♠"], cols_per_row=4)
        else: st.info("Sekans tamamlandı. Yeni el için **Yeni El** butonuna tıklayın.")

if st.session_state["feedback"] is not None:
    if st.button("➡️  Sonraki El", type="primary"): deal_new_hand(); st.rerun()