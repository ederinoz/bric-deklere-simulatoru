"""
TBF 5'li Majör Deklere Sistemi + RKCB 0314 kuralları.
Kuzey-Güney çifti için açılış ve yanıtlar.
Rekabetçi filtreler ve seviye koruması geliştirildi.
"""

from evaluator import HandEvaluator
from cards import Card, Suit, Rank

BID_PASS = "PAS"
BID_DBL  = "KON"
BID_RDBL = "RKON"

def suit_symbol(s: Suit) -> str:
    return {Suit.CLUBS: '♣', Suit.DIAMONDS: '♦', Suit.HEARTS: '♥', Suit.SPADES: '♠'}[s]

def has_two_honors(ev: HandEvaluator, suit: Suit) -> bool:
    """Renk içinde en az 2 büyük onör (A, K, Q, J) var mı?"""
    honors = {Rank.ACE, Rank.KING, Rank.QUEEN, Rank.JACK}
    return sum(1 for c in ev.suit_cards(suit) if c.rank in honors) >= 2

# ───────────────────────────────────────────────
# AÇILIŞ MOTORU
# ───────────────────────────────────────────────
def opening_bid(ev: HandEvaluator, seat: int = 1) -> tuple[str, str]:
    hcp = ev.hcp()
    tp  = ev.total_points()
    dp  = ev.distribution_points()

    if hcp >= 22 or tp >= 25:
        return "2♣", "Yapay güçlü açılış (22+ HKP)"

    for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
        if ev.length(suit) >= 7 and 5 <= hcp <= 10:
            sym = suit_symbol(suit)
            return f"3{sym}", f"Preemptif açılış (7+ {sym}, 5-10 HKP)"

    for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS]:
        if ev.length(suit) >= 6 and 6 <= hcp <= 10:
            sym = suit_symbol(suit)
            if seat == 3:
                return f"2{sym}", f"Zayıf iki açılışı – 3. koltuk (6+ {sym}, kalite aranmaz)"
            elif has_two_honors(ev, suit):
                return f"2{sym}", f"Zayıf iki açılışı – {seat}. koltuk (6+ {sym}, 2+ büyük onör var)"

    if tp < 12:
        return BID_PASS, f"Toplam puan yetersiz – pas (HKP={hcp} + Dağılım=+{dp} = {tp} TP)"

    if 20 <= hcp <= 21 and ev.is_balanced():
        return "2NT", "Dengeli el (20-21 HKP)"

    if 15 <= hcp <= 17 and ev.is_balanced():
        return "1NT", "Dengeli el (15-17 HKP)"

    for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
        if ev.length(suit) >= 6:
            sym = suit_symbol(suit)
            return f"1{sym}", f"6+ {sym} – uzun renk önce açılır"

    if ev.length(Suit.SPADES) >= 5 and ev.length(Suit.HEARTS) >= 5:
        return "1♠", "5-5 Majör – yüksek majör 1♠ önce açılır (TBF kuralı)"

    if ev.length(Suit.SPADES) >= 5 and ev.length(Suit.SPADES) >= ev.length(Suit.HEARTS):
        return "1♠", "5+ Maça (TBF 5'li Majör)"
    if ev.length(Suit.HEARTS) >= 5:
        return "1♥", "5+ Kupa (TBF 5'li Majör)"

    if ev.length(Suit.DIAMONDS) >= 4 and ev.length(Suit.DIAMONDS) >= ev.length(Suit.CLUBS):
        return "1♦", "4+ Karo"
    return "1♣", "3+ Sinek"

# ───────────────────────────────────────────────
# YANITLAR (MAJÖR AÇILIŞLARI)
# ───────────────────────────────────────────────
def response_to_major(opener_suit: Suit, ev: HandEvaluator, partner_hcp: int) -> tuple[str, str]:
    hcp  = ev.hcp()
    supp = ev.length(opener_suit)
    sym  = suit_symbol(opener_suit)

    if hcp < 6: return BID_PASS, "6 HKP altı – pas"
    if supp >= 4 and hcp >= 13: return "2NT", "Jacoby 2NT – 4+ destek, 13+ HKP (GF)"
    if supp >= 3 and 10 <= hcp <= 12: return f"3{sym}", f"Sınır artışı – 3+ destek, 10-12 HKP"
    if supp >= 3 and 6 <= hcp <= 9: return f"2{sym}", f"Basit artış – 3+ destek, 6-9 HKP"
    if supp >= 5 and hcp < 10: return f"4{sym}", f"Kapatma artışı – 5+ destek, <10 HKP"

    # Yeni renk okuma önceliği (1 seviyesinde majör varsa önce o)
    if opener_suit == Suit.HEARTS and ev.length(Suit.SPADES) >= 4 and hcp >= 6:
        return "1♠", "1♥ açışına 4+ Maça yanıtı (6+ HKP)"

    if hcp >= 10:
        for s in [Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES]:
            if s != opener_suit and ev.length(s) >= 4:
                # 2 seviyesinde yeni renk okuma zorlaması
                if _bid_rank(f"2{suit_symbol(s)}") > _bid_rank(f"1{sym}"):
                    return f"2{suit_symbol(s)}", f"Yeni renk 2 seviyesinde zorlayıcı ({suit_symbol(s)}, 10+ HKP)"

    if 6 <= hcp <= 9: return "1NT", "6-9 HKP, desteksiz dengesiz/uygunsuz el"
    return BID_PASS, "Pas"

# ───────────────────────────────────────────────
# YANITLAR (MINÖR AÇILIŞLARI - YENİ VE DETAYLI)
# ───────────────────────────────────────────────
def response_to_minor(opener_suit: Suit, ev: HandEvaluator) -> tuple[str, str]:
    hcp = ev.hcp()
    sym = suit_symbol(opener_suit)
    
    if hcp < 6: return BID_PASS, "6 HKP altı – pas"

    # KURAL 1: 4'+lü Majör önceliği (TBF Standardı)
    # Eğer hem Maça hem Kupa 4'lü ise ucuz olan (1 Kupa) önce söylenir.
    if ev.length(Suit.HEARTS) >= 4 and ev.length(Suit.HEARTS) >= ev.length(Suit.SPADES):
        return "1♥", f"Minör açılışına karşı 4+ Kupa majör yanıtı (6+ HKP)"
    if ev.length(Suit.SPADES) >= 4:
        return "1♠", f"Minör açılışına karşı 4+ Maça majör yanıtı (6+ HKP)"

    # KURAL 2: Majör yoksa, Diğer Minörün Okunması
    if opener_suit == Suit.CLUBS and ev.length(Suit.DIAMONDS) >= 4 and hcp >= 6:
        return "1♦", "1♣ açışına karşı 4+ Karo yanıtı (6+ HKP)"

    # KURAL 3: Minör Desteği (Majör yoksa)
    supp = ev.length(opener_suit)
    if supp >= 5 and 6 <= hcp <= 9:
        return f"2{sym}", f"Minör rengine basit destek – 5+ {sym}, 6-9 HKP"
    if supp >= 5 and 10 <= hcp <= 12:
        return f"3{sym}", f"Minör rengine davetkar destek – 5+ {sym}, 10-12 HKP"

    # KURAL 4: Dengeli Eller İçin NT Yanıtları
    if 6 <= hcp <= 9: return "1NT", "Dengeli el, majör yok, 6-9 HKP"
    if 10 <= hcp <= 11: return "2NT", "Dengeli el, majör yok, 10-11 HKP davet"
    if 12 <= hcp <= 15: return "3NT", "Dengeli el, majör yok, 12-15 HKP oyun"

    return BID_PASS, "Pas"

def response_to_1nt(ev: HandEvaluator) -> tuple[str, str]:
    hcp = ev.hcp()
    if hcp <= 7: return BID_PASS, "0-7 HKP – pas"
    if hcp >= 8 and (ev.length(Suit.HEARTS) >= 4 or ev.length(Suit.SPADES) >= 4): return "2♣", "Stayman – 4'lü majör sorusu"
    if ev.length(Suit.HEARTS) >= 5: return "2♦", "Jacoby transferi – 5+ Kupa"
    if ev.length(Suit.SPADES) >= 5: return "2♥", "Jacoby transferi – 5+ Maça"
    if 8 <= hcp <= 9: return "2NT", "Davet (8-9 HKP)"
    return "3NT", "Oyun 3NT (10+ HKP)"

# ───────────────────────────────────────────────
# RKCB 0314
# ───────────────────────────────────────────────
def rkcb_response(ev: HandEvaluator, trump: Suit) -> tuple[str, str]:
    kc  = ev.key_cards(trump)
    tq  = ev.has_trump_queen(trump)
    sym = suit_symbol(trump)

    if kc in (0, 3): bid, txt = "5♣", "5♣ – 0 veya 3 anahtar koz (RKCB 0314)"
    elif kc in (1, 4): bid, txt = "5♦", "5♦ – 1 veya 4 anahtar koz (RKCB 0314)"
    elif kc in (2, 5) and not tq: bid, txt = "5♥", f"5♥ – 2 veya 5 anahtar koz, {sym} koz kızı YOK"
    else: bid, txt = "5♠", f"5♠ – 2 veya 5 anahtar koz, {sym} koz kızı VAR"
    return bid, txt + f"\n  Elinizdeki anahtar kozlar: {kc}"

def rkcb_ask_valid(ev: HandEvaluator, trump: Suit) -> bool:
    return ev.hcp() >= 14

# ───────────────────────────────────────────────
# REKABETÇİ DEKLERE KORUMALARI
# ───────────────────────────────────────────────
_SUIT_SYM_RANK: dict[str, int] = {'♣': 0, '♦': 1, '♥': 2, '♠': 3, 'NT': 4}

def _bid_rank(bid: str) -> int:
    if bid in (BID_PASS, BID_DBL, BID_RDBL, ''): return -1
    try:
        level = int(bid[0])
        sym   = bid[1:]
        return (level - 1) * 5 + _SUIT_SYM_RANK.get(sym, 0)
    except (IndexError, ValueError): return -1

def _min_level_bid(suit_sym: str, over_bid: str) -> str | None:
    base = _bid_rank(over_bid)
    for level in range(1, 8):
        cand = f"{level}{suit_sym}"
        if _bid_rank(cand) > base: return cand
    return None

def overcall_or_double(ev: HandEvaluator, opponent_bid: str) -> tuple[str, str]:
    if opponent_bid in (BID_PASS, BID_DBL, BID_RDBL, ''):
        return BID_PASS, "Pas"

    hcp       = ev.hcp()
    opp_level = int(opponent_bid[0]) if opponent_bid and opponent_bid[0].isdigit() else 1
    opp_sym   = opponent_bid[1:] if len(opponent_bid) > 1 else ''
    _smap     = {'♠': Suit.SPADES, '♥': Suit.HEARTS, '♦': Suit.DIAMONDS, '♣': Suit.CLUBS}
    opp_suit  = _smap.get(opp_sym)

    if opponent_bid == "1NT" and hcp < 12:
        return BID_PASS, "Rakip güçlü 1NT açtı, zayıf elle baraj yapılmaz – Pas"

    if opp_suit and hcp >= 12 and ev.length(opp_suit) <= 2:
        others = [s for s in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS] if s != opp_suit]
        if sum(1 for s in others if ev.length(s) >= 3) >= 3:
            return BID_DBL, f"Çıkarma kontrası – {hcp} HKP, {suit_symbol(opp_suit)} kısa"

    if opp_level == 1 and opp_suit and 15 <= hcp <= 18 and ev.is_balanced():
        if any(c.rank in {Rank.ACE, Rank.KING, Rank.QUEEN} for c in ev.suit_cards(opp_suit)):
            return "1NT", f"1NT tekrifi (15-18 HKP, {suit_symbol(opp_suit)} tıkacı)"

    for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
        if suit == opp_suit: continue
        length  = ev.length(suit)
        sym     = suit_symbol(suit)
        min_bid = _min_level_bid(sym, opponent_bid)
        if not min_bid: continue
        min_lvl = int(min_bid[0])

        if min_lvl == 1 and length >= 5 and 8 <= hcp <= 17:
            return min_bid, f"{min_bid} tekrifi – 5+ {sym}, {hcp} HKP"
        if min_lvl == 2 and length >= 5 and 10 <= hcp <= 17:
            return min_bid, f"{min_bid} tekrifi – 5+ {sym}, {hcp} HKP"

        if min_lvl <= 3 and length >= 6 and 6 <= hcp <= 11 and opponent_bid != "1NT":
            jump = f"{min_lvl + 1}{sym}"
            return jump, f"{jump} atlayan tekrif – preemptif (6+ {sym})"

    return BID_PASS, "Pas"

def respond_to_double(doubled_bid: str | None, ev: HandEvaluator) -> tuple[str, str]:
    hcp  = ev.hcp()
    _smap = {'♠': Suit.SPADES, '♥': Suit.HEARTS, '♦': Suit.DIAMONDS, '♣': Suit.CLUBS}
    doubled_sym  = doubled_bid[1:] if doubled_bid and len(doubled_bid) > 1 else ''
    doubled_suit = _smap.get(doubled_sym)

    if doubled_suit and hcp >= 7:
        if any(c.rank in {Rank.ACE, Rank.KING, Rank.QUEEN} for c in ev.suit_cards(doubled_suit)):
            min_nt = _min_level_bid('NT', doubled_bid or '')
            if min_nt and int(min_nt[0]) <= 2:
                return min_nt, f"Kontrasına {min_nt} – {suit_symbol(doubled_suit)} tıkacı"

    best_suit, best_len = None, 0
    for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
        if suit == doubled_suit: continue
        if ev.length(suit) > best_len: best_len, best_suit = ev.length(suit), suit

    if best_suit:
        sym     = suit_symbol(best_suit)
        min_bid = _min_level_bid(sym, doubled_bid or '') or f"1{sym}"
        min_lvl = int(min_bid[0])

        if hcp >= 10 and best_len >= 4 and min_lvl <= 3:
            jump = f"{min_lvl + 1}{sym}"
            return jump, f"Kontrasına atlayan yanıt – {sym}"
        return min_bid, f"Kontrasına {min_bid} yanıtı"

    return BID_PASS, "Pas"

def suggest_response(opener_bid: str, opener_suit: Suit | None, ev: HandEvaluator, partner_hcp: int) -> tuple[str, str]:
    if opener_bid == "1NT": return response_to_1nt(ev)
    
    # Gelen deklerenin seviyesini ve sembolünü ayrıştır (Dinamik süreç koruması)
    lvl = int(opener_bid[0]) if opener_bid and opener_bid[0].isdigit() else 1
    
    # 1 SEVİYESİNDEKİ SİSTEM AÇILIŞLARINA NATÜREL YANITLAR
    if lvl == 1 and opener_suit:
        if opener_suit in (Suit.HEARTS, Suit.SPADES):
            return response_to_major(opener_suit, ev, partner_hcp)
        elif opener_suit in (Suit.CLUBS, Suit.DIAMONDS):
            return response_to_minor(opener_suit, ev)

    # REKABETÇİ VE İLERİ SEVİYE SÜREÇ KORUMALARI (Jacoby 2NT veya Sekans İlerlemesi)
    if opener_suit in (Suit.HEARTS, Suit.SPADES) and lvl == 3:
        sym = suit_symbol(opener_suit)
        return f"4{sym}", f"Jacoby 2NT Sonrası veya Davete İstinaden Zona Tamamlama – 4+ {sym} Fiti ile Oyun"

    return BID_PASS, "Pas"
