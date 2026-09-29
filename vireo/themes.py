"""Rule-based complaint theme tagger.

Why rules and not an LLM: the bot's intake category is unreliable (see DECISIONS.md), but the
messages are short and repetitive, so typo-tolerant keyword rules recover the real theme at zero
cost per run and zero surprise on the bill (Finance asked for that). Rules are ordered: first
match wins, so put the most specific themes first.
"""
import re
from difflib import get_close_matches

# (theme, [phrases]). A phrase matches if every word in it is found (exact stem or fuzzy) in order-free fashion.
RULES = [
    ("Pre-sale / how-to enquiry", ["connect two", "cnnect two"]),
    ("Payment taken, no order / duplicate charge", ["charged twice", "card charged", "charged two", "double charge", "deducted", "went through but", "no order id", "no orders", "no order was", "payment failed", "went to you", "page failed", "paid once", "statement disagrees", "nothing shows in my account", "paid and now", "two entries", "on my statement", "debited", "upi shows", "order not showing"]),
    ("Price / coupon / discount", ["discount", "coupon", "festive offer", "offer vanished", "promo", "20% off", "cart says", "price drop", "offer price"]),
    ("Invoice / GST request", ["gst", "tax bill", "tax invoice", "share invoice", "need the invoice", "need invoice", "need teh bill", "need the bill", "bill with", "gstin"]),
    ("Refund not received", ["refund was promised", "was promised", "money hasnt come back", "money hasn't come back", "hasnt come back", "amount is nowhere", "where is the money", "money for the return", "refund still", "not received refund", "refund pending", "refund not", "waiting for my refund", "waiting for refund", "refund still"]),
    ("Return / pickup problem", ["pickup", "pick up", "pick-up", "return request", "return was accepted", "return label"]),
    ("Warranty / repair status", ["warranty", "service centre", "service center", "sevrice", "heard nothing", "snet the unit", "sent the unit", "sent the unit", "repair", "rma"]),
    ("Wrong / damaged item received", ["wrong item", "different colour", "different color", "got something else", "something else", "incorrect product", "crushed", "cracked", "damaged", "kicked", "wrong product", "not what i paid", "different thing", "whats inside", "what's inside", "dent", "scratch", "broken", "snapped", "box says", "not what i asked", "got white", "got black", "ordered black"]),
    ("Order change / cancellation", ["flat number", "address", "cancel my order", "change my order", "cancel the order", "moved houses", "old flat", "wrong colour", "dont ship", "stop the shipment", "change of mind", "ordered by mistake", "please cancel", "cancel order", "cancel", "pincode", "pin code", "without asking", "please reverse", "wrong address"]),
    ("Delivery delayed / tracking", ["not delivered", "tracking", "out for delivery", "still waiting for something", "show up", "packed the box", "courier", "shipped", "nothing in hand", "havent received", "haven't received", "not received", "havent recceived", "havent receievd", "recceived", "receievd", "delivery", "not arrived", "hasnt arrived", "yet to arrive"]),
    ("Login / OTP / account", ["otp", "login", "log in", "locked out", "password", "sign in", "verification code"]),
    ("App / firmware / update", ["firmware", "update", "app not", "app crash", "app keeps", "spinning circle", "loading screen", "closes itself", "progress bar", "app closes", "app wont", "app won't"]),
    ("Pairing / Bluetooth / connection", ["pairing", "pairng", "cannot pair", "cant pair", "not pair", "pair my", "pair with", "pair it", "bluetooth", "disconnect", "connects for", "vanishes", "device list", "connection drop", "keeps dropping", "stutter", "losing my phone", "other room", "doesnt see it", "doesn't see it", "wont connect", "not connecting"]),
    ("Battery / charging", ["battery", "charge", "charging", "case led", "no light", "0 percent", "drain", "dead case", "case dead", "dies by", "promised 40 hours", "promised 45", "promised 20", "hours is nowhere", "no power", "paperweight", "brick", "no lights", "full to empty", "goes from full", "wont turn on", "won't turn on", "speaker wont", "wont turn on", "wont switch on", "only the right one", "only the left one", "one lights", "battery"]),
    ("Audio quality / mic", ["no audio", "crackl", "static", "frying", "buzz", "cannot hear me", "hear me", "mic ", "no sound", "sound", "distort", "bass", "volume", "one ear", "other is mute", "hiss", "microphone", "meetings", "one side", "left side", "right side", "muffled", "his that wasnt", "his that wasn't", "goes silent", "completely silent", "silent for", "left one is dead", "right one is dead", "one is dead", "decoration", "repeat myself", "asking me to repeat"]),
    ("Physical defect", ["display", "strap", "peeling", "screen", "button", "touch", "ignores my finger", "metal pin", "fell out", "wrist", "stay on", "swipe", "tap ten"]),
    ("Pre-sale / how-to enquiry", ["compatible", "work with", "survive", "waterproof", "how do i", "does the", "does it", "does strata", "does nexa", "will this", "will the", "old nokia", "compatible", "support ios", "iphone", "connect two", "cnnect two", "wifi setup", "setup fails"]),
]
STATUS_CHASE = ["same thing", "same issue", "fourth time", "third ticket", "third time", "still not fixed", "raised this last month", "any update", "status of my"]
OTHER = "Unclear / other"

_tok = re.compile(r"[a-z0-9']+")

def _norm(s):
    return " ".join(_tok.findall(str(s).lower().replace("\n", " ")))

def _phrase(p, norm):
    """Multi-word phrase with word boundaries, so "refund not" does not fire on "refund nothing"."""
    return re.search(r"(?<![a-z0-9])" + re.escape(p.strip()) + r"(?![a-z0-9])", norm) is not None

def _has(norm, words, vocab):
    for w in words:
        if w in norm:      # substring hit (handles stems: "crackl", "pair")
            continue
        # fuzzy hit on a single token, catches typos: "pairng", "chagring", "warrenty"
        if " " not in w and len(w) >= 5 and get_close_matches(w, vocab, n=1, cutoff=0.82):
            continue
        return False
    return True

def tag(message):
    """Return the theme name for one customer message."""
    norm = _norm(message)
    vocab = norm.split()
    for theme, phrases in RULES:
        for p in phrases:
            if (_has(norm, p.split(), vocab) if " " not in p else _phrase(p, norm)):
                return theme
    return OTHER

def is_chase(message):
    """True if the customer says they've already raised this / are chasing (Neha's 'I already told your colleague')."""
    n = _norm(message)
    return any(p in n for p in STATUS_CHASE + ["already told", "colleague", "again", "yet again", "same problem"])
