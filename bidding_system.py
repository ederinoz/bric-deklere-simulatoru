from evaluator import HandEvaluator
from cards import Card, Suit, Rank

BID_PASS = "PAS"
BID_DBL  = "KON"
BID_RDBL = "RKON"

def suit_symbol(s: Suit) -> str:
    return {Suit.CLUBS: '♣', Suit.DIAMONDS: '♦', Suit.HEARTS: '♥', Suit.SPADES: '♠'}[s]

def has_two_honors(ev: HandEvaluator, suit: Suit) -> bool:
    honors = {Rank.ACE, Rank.KING, Rank.QUEEN, Rank.JACK}
    return sum(1 for c in ev.suit_cards(suit) if c.rank in honors) >= 2

def _bid_rank(bid: str) -> int:
    if bid in (BID_PASS, BID_DBL, BID_RDBL, ''): return -1
    _smap = {'♣': 0, '♦': 1, '♥': 2, '♠': 3, 'NT': 4}
    try:
        level = int(bid[0])
        sym   = bid[1:]
        return (level - 1) * 5 + _smap.get(sym, 0)
    except (IndexError, ValueError):
        return -1

def _min_level_bid(suit_sym: str, over_bid: str) -> str | None:
    base = _bid_rank(over_bid)
    for level in range(1, 7):
        cand = f"{level}{suit_sym}"
        if _bid_rank(cand) > base: return cand
    return None

def opening_bid(ev: HandEvaluator, seat: int = 1) -> tuple[str, str]:
    hcp = ev.hcp()
    tp  = ev.total_points()

    if hcp >= 22 or tp >= 25:
        return "2♣", "Yapay Güçlü Açılış (22+ HKP / Çok Güçlü El)"

    for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
        if ev.length(suit) >= 7 and 5 <= hcp <= 10:
            return f"3{suit_symbol(suit)}", f"Preemptif Baraj Açış (7+ {suit_symbol(suit)}, 5-10 HKP)"

    for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS]:
        if ev.length(suit) == 6 and 6 <= hcp <= 10:
            sym = suit_symbol(suit)
            if seat == 3:
                return f"2{sym}", f"Zayıf İki Açılışı — 3. Koltuk (Ortak Pas Geçtiği İçin Kalite Aranmaz)"
            elif has_two_honors(ev, suit):
                return f"2{sym}", f"Zayıf İki Açılışı — {seat}. Koltuk (6 Kart + En Az 2 Büyük Onör Zorunlu)"

    if tp < 12: return BID_PASS, "PAS"
    if 20 <= hcp <= 21 and ev.is_balanced(): return "2NT", "Dengeli El Açışı (20-21 HKP)"
    if 15 <= hcp <= 17 and ev.is_balanced(): return "1NT", "Dengeli El Açışı (15-17 HKP)"

    for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
        if ev.length(suit) >= 6: return f"1{suit_symbol(suit)}", f"6+ {suit_symbol(suit)} Uzun Renk Öncelikli Natürel Açış"

    sp, ht = ev.length(Suit.SPADES), ev.length(Suit.HEARTS)
    if sp >= 5 and ht >= 5: return "1♠", "5-5 Majör — Her Zaman Yüksek Majör (1♠) Önce Açılır"
    if sp >= 5 and sp >= ht: return "1♠", "5+ Maça Natürel Açış (TBF 5'li Majör Kuralı)"
    if ht >= 5: return "1♥", "5+ Kupa Natürel Açış (TBF 5'li Majör Kuralı)"

    di, cl = ev.length(Suit.DIAMONDS), ev.length(Suit.CLUBS)
    if di >= 4 and di >= cl: return "1♦", "4+ Karo Natürel Açış (Eşitlikte Veya Uzunlukta 1♦)"
    if di == 3 and cl == 3: return "1♦", "3-3 Minör Dağılımı — TBF Standardına Göre 1♦ Açılır"
    return "1♣", "3+ Sinek Natürel Açış"

def response_to_major(opener_suit: Suit, ev: HandEvaluator) -> tuple[str, str]:
    hcp  = ev.hcp()
    supp = ev.length(opener_suit)
    sym  = suit_symbol(opener_suit)

    if hcp < 6: return BID_PASS, "PAS"
    if supp >= 4 and hcp >= 13: return "2NT", "Jacoby 2NT — 4+ Koz Desteği, 13+ HKP ile Şlem Zorlaması (GF)"
    
    if hcp >= 12 and supp < 4:
        for s in [Suit.CLUBS, Suit.DIAMONDS]:
            if ev.length(s) >= 5: return f"2{suit_symbol(s)}", f"GF Kuvvetli El ile Uzun Yeni Minör Önceliği Zorlayıcı ({suit_symbol(s)}, 12+ HKP)"

    if supp >= 3 and 10 <= hcp <= 12: return f"3{sym}", f"Limitli Davet Artışı — 3+ Desteğe Karşı 10-12 HKP"
    if supp >= 3 and 6 <= hcp <= 9: return f"2{sym}", f"Basit Yapıcı Artış — 3+ Desteğe Karşı 6-9 HKP"
    if supp >= 5 and hcp < 10: return f"4{sym}", f"Zayıf Kapatma Artışı — 5+ Koz Desteği ile Direkt Oyun"

    if opener_suit == Suit.HEARTS and ev.length(Suit.SPADES) >= 4 and hcp >= 6:
        return "1♠", "1♥ Açışına Karşı En Az 4'lü Maça Yanıtı (6+ HKP)"

    if hcp >= 10:
        for s in [Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES]:
            if s != opener_suit and ev.length(s) >= 4:
                cand = f"2{suit_symbol(s)}"
                if _bid_rank(cand) > _bid_rank(f"1{sym}"): return cand, f"Yeni Renk 2 Seviyesinde Tur Zorlaması ({suit_symbol(s)}, 10+ HKP)"

    if 6 <= hcp <= 9: return "1NT", "Dengeli Veya Uygunsuz El — 6-9 HKP Limitli NT"
    return BID_PASS, "PAS"

def response_to_minor(opener_suit: Suit, ev: HandEvaluator) -> tuple[str, str]:
    hcp = ev.hcp()
    sym = suit_symbol(opener_suit)
    if hcp < 6: return BID_PASS, "PAS"

    ht_len = ev.length(Suit.HEARTS)
    sp_len = ev.length(Suit.SPADES)
    if ht_len >= 4 and ht_len >= sp_len: return "1♥", "Minör açışına karşı öncelikle 4+ Kupa majörü gösterilir (TBF Hiyerarşisi)."
    if sp_len >= 4: return "1♠", "Minör açışına karşı öncelikle 4+ Maça majörü gösterilir (TBF Hiyerarşisi)."

    if opener_suit == Suit.CLUBS and ev.length(Suit.DIAMONDS) >= 4 and hcp >= 6:
        return "1♦", "1♣ Açışına Karşı Ekonomik 4+ Karo Yanıtı (6+ HKP)"

    supp = ev.length(opener_suit)
    if supp >= 5 and 6 <= hcp <= 9: return f"2{sym}", f"Minör Rengine Basit Destek — 5+ {sym}, 6-9 HKP"
    if supp >= 5 and 10 <= hcp <= 12: return f"3{sym}", f"Minör Rengine Davetkar Davet Artışı — 5+ {sym}, 10-12 HKP"

    if 6 <= hcp <= 9: return "1NT", "Dengeli El, Majör Yok — 6-9 HKP"
    if 10 <= hcp <= 11: return "2NT", "Dengeli El, Majör Yok — 10-11 HKP Davetkar"
    if 12 <= hcp <= 15: return "3NT", "Dengeli El, Majör Yok — 12-15 HKP Direkt Oyun"
    return BID_PASS, "PAS"

def response_to_weak_or_preempt(opener_bid: str, opener_suit: Suit, ev: HandEvaluator) -> tuple[str, str]:
    hcp = ev.hcp()
    supp = ev.length(opener_suit)
    sym = suit_symbol(opener_suit)
    lvl = int(opener_bid[0])
    
    if hcp < 16:
        if supp >= 3 and lvl == 2: return f"3{sym}", "Zayıf açışa fitle rekabetçi baraj yükseltme artışı"
        return BID_PASS, "PAS"
        
    for s in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
        if s != opener_suit and ev.length(s) >= 5:
            cand = f"3{suit_symbol(s)}" if lvl == 2 else f"4{suit_symbol(s)}"
            return cand, f"Zayıf açışa karşı 16+ HKP kuvvetiyle yeni renk zorlaması ({suit_symbol(s)})"
    return BID_PASS, "PAS"

def response_to_1nt(ev: HandEvaluator) -> tuple[str, str]:
    hcp = ev.hcp()
    if hcp <= 7: return BID_PASS, "PAS"
    if hcp >= 8 and (ev.length(Suit.HEARTS) >= 4 or ev.length(Suit.SPADES) >= 4): return "2♣", "Stayman Konvansiyonu — 8+ HKP ile 4'lü Majör Arama Sorusu"
    if ev.length(Suit.HEARTS) >= 5: return "2♦", "Jacoby Transferi — 5+ Kupa Gösterir, Ortağa 2♥ Dedirtir"
    if ev.length(Suit.SPADES) >= 5: return "2♥", "Jacoby Transferi — 5+ Maça Gösterir, Ortağa 2♠ Dedirtir"
    if 8 <= hcp <= 9: return "2NT", "Dengeli El Davet — 8-9 HKP"
    return "3NT", "Dengeli El Oyun — 10+ HKP"

def rkcb_response(ev: HandEvaluator, trump: Suit) -> tuple[str, str]:
    kc  = ev.key_cards(trump)
    tq  = ev.has_trump_queen(trump)
    sym = suit_symbol(trump)
    if kc in (0, 3): bid, txt = "5♣", "5♣ Yanıtı — 0 Veya 3 Anahtar Kart"
    elif kc in (1, 4): bid, txt = "5♦", "5♦ Yanıtı — 1 Veya 4 Anahtar Kart"
    elif kc in (2, 5) and not tq: bid, txt = "5♥", f"5♥ Yanıtı — 2 Veya 5 Anahtar Kart, {sym} Koz Kızı YOK"
    else: bid, txt = "5♠", f"5♠ Yanıtı — 2 Veya 5 Anahtar Kart, {sym} Koz Kızı VAR"
    return bid, txt + f" (Toplam Anahtar Kart: {kc})"

def suggest_response(opener_bid: str, opener_suit: Suit | None, ev: HandEvaluator, partner_hcp: int = 12) -> tuple[str, str]:
    hcp = ev.hcp()
    is_game_forcing = (partner_hcp + hcp >= 25) or (hcp >= 16)
    
    # KATİ SEVİYE DOĞRULAYICI (LEVEL VALIDATOR): Masadaki son deklere 5 seviyesindeyse 4NT üretilmesi engellenir
    if opener_bid and opener_bid[0].isdigit():
        if int(opener_bid[0]) >= 5 and not opener_bid == "4NT":
            if is_game_forcing:
                return "PAS", "Masa 5. Seviyede, Kural Dışı Geriye Dönük Deklere (4NT) Bloklandı. Pas Geçilmesi Emniyetlidir."

    if opener_bid == "1NT": return response_to_1nt(ev)
    
    lvl = int(opener_bid[0]) if opener_bid and opener_bid[0].isdigit() else 1
    if lvl >= 2 and opener_suit: return response_to_weak_or_preempt(opener_bid, opener_suit, ev)

    if lvl == 1 and opener_suit:
        if hcp >= 10 and ev.length(opener_suit) == 0:
            for s in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
                if s != opener_suit and ev.length(s) >= 5:
                    target = _min_level_bid(suit_symbol(s), opener_bid)
                    if target: return target, f"Yeni Renk 2 Seviyesinde Tur Zorlaması ({suit_symbol(s)}, 10+ HKP)"
        
        if is_game_forcing:
            if opener_suit in (Suit.HEARTS, Suit.SPADES):
                supp = ev.length(opener_suit)
                if supp >= 4: return "2NT", "Jacoby 2NT — Şlem ve Oyun Zorlaması (GF)"
                if hcp >= 13: return "3NT", "Dengeli Güçlü El — Direkt Oyun İlanı"
            else:
                if hcp >= 13: return "3NT", "Dengeli Güçlü El — Direkt Oyun İlanı"
                
        if opener_suit in (Suit.HEARTS, Suit.SPADES): return response_to_major(opener_suit, ev)
        if opener_suit in (Suit.CLUBS, Suit.DIAMONDS): return response_to_minor(opener_suit, ev)
            
    if opener_bid == "4NT" and opener_suit: return rkcb_response(ev, opener_suit)
    
    if is_game_forcing:
        return _min_level_bid("NT", opener_bid) or "3NT", "Zon Gücü Kilidi Aktif — Pas Geçilemez, Oyun Değerli Dağılım"
        
    if hcp < 6: return BID_PASS, "PAS"
    return BID_PASS, "PAS"

def overcall_or_double(ev: HandEvaluator, opponent_bid: str, partner_passed: bool = False) -> tuple[str, str]:
    if opponent_bid in (BID_PASS, BID_DBL, BID_RDBL, ''): return BID_PASS, "PAS"
    hcp       = ev.hcp()
    opp_sym   = opponent_bid[1:] if len(opponent_bid) > 1 else ''
    _smap     = {'♠': Suit.SPADES, '♥': Suit.HEARTS, '♦': Suit.DIAMONDS, '♣': Suit.CLUBS}
    opp_suit  = _smap.get(opp_sym)

    if opponent_bid == "1NT" and hcp < 12: return BID_PASS, "PAS"
    
    if opp_suit and hcp >= 12 and ev.length(opp_suit) <= 2:
        others = [s for s in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS] if s != opp_suit]
        if sum(1 for s in others if ev.length(s) >= 3) >= 3:
            return BID_DBL, f"TBF Çıkarma Kontru (Takeout) — {hcp} HKP, Rakip {suit_symbol(opp_suit)} Kısa"

    for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
        if suit == opp_suit: continue
        length  = ev.length(suit)
        sym     = suit_symbol(suit)
        min_bid = _min_level_bid(sym, opponent_bid)
        if min_bid:
            lvl = int(min_bid[0])
            if partner_passed and lvl >= 2 and hcp < 11:
                continue
            if lvl <= 2 and length >= 5 and 8 <= hcp <= 17:
                return min_bid, f"Araya Giriş (Overcall) — 5+ {sym}, {hcp} HKP"
                
    return BID_PASS, "PAS"

def competitive_fallback(ev: HandEvaluator, last_bid: str, my_previous_bid: str | None, partner_passed_twice: bool = False) -> tuple[str, str]:
    hcp = ev.hcp()
    if my_previous_bid and len(my_previous_bid) > 1:
        my_suit_sym = my_previous_bid[1:]
        _smap = {'♠': Suit.SPADES, '♥': Suit.HEARTS, '♦': Suit.DIAMONDS, '♣': Suit.CLUBS}
        my_suit = _smap.get(my_suit_sym)
        if my_suit and ev.length(my_suit) == 4 and partner_passed_twice and hcp < 16:
            return BID_PASS, "Ortak pas geçmeye devam ediyor ve majörünüz 4 parça limitli. Yarışmadan çekilip PAS geçilmesi uygundur."
            
    return overcall_or_double(ev, last_bid, partner_passed=True)

def respond_to_double(doubled_bid: str | None, ev: HandEvaluator) -> tuple[str, str]:
    _smap = {'♠': Suit.SPADES, '♥': Suit.HEARTS, '♦': Suit.DIAMONDS, '♣': Suit.CLUBS}
    doubled_sym  = doubled_bid[1:] if doubled_bid and len(doubled_bid) > 1 else ''
    doubled_suit = _smap.get(doubled_sym)
    best_suit, best_len = None, 0
    for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
        if suit == doubled_suit: continue
        if ev.length(suit) > best_len: best_len, best_suit = ev.length(suit), suit
    if best_suit:
        sym     = suit_symbol(best_suit)
        min_bid = _min_level_bid(sym, doubled_bid or '') or f"1{sym}"
        return min_bid, f"Ortağın Kontrasına Mecburi Yanıt ({sym})"
    return BID_PASS, "PAS"
