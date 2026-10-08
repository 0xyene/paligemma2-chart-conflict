"""Accept lists shared by all stimuli, so the same answer scores the same way everywhere.

Usage in a make.py:   from answers import YES, NO, UP, DOWN, num_accept
"""

YES = {"en": ["yes"], "tr": ["evet"]}
NO = {"en": ["no"], "tr": ["hayır", "^değil"]}          # a bare "değil" (it isn't) is a no

UP = {"en": ["up", "went up", "increased", "increase", "increases", "increasing", "rose", "rise", "risen", "rising",
             "grew", "grown", "growing", "upward", "higher"],
      "tr": ["arttı", "artış", "artmış", "artıyor", "artan", "çoğaldı", "yükseldi", "yükselmiş", "yükseliyor",
             "yükseliş", "yukarı"]}
DOWN = {"en": ["down", "went down", "decreased", "decrease", "decreases", "decreasing", "fell", "fall", "fallen",
               "falling", "dropped", "drop", "declined", "decline", "declining", "downward", "lower"],
        "tr": ["azaldı", "azalış", "azalmış", "azalıyor", "azalan", "düştü", "düşmüş", "düşüyor", "düşüş", "geriledi",
               "aşağı"]}

_EN1 = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen " \
       "seventeen eighteen nineteen".split()
_EN10 = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
_TR1 = "sıfır bir iki üç dört beş altı yedi sekiz dokuz".split()
_TR10 = "_ on yirmi otuz kırk elli altmış yetmiş seksen doksan".split()


def _en(n):
    if n < 20:
        return [_EN1[n]]
    if n < 100:
        t, o = divmod(n, 10)
        return [_EN10[t]] if o == 0 else [f"{_EN10[t]}-{_EN1[o]}", f"{_EN10[t]} {_EN1[o]}"]
    h, r = divmod(n, 100)
    head = f"{_EN1[h]} hundred"
    return [head] if r == 0 else [f"{head} {w}" for w in _en(r)] + [f"{head} and {w}" for w in _en(r)]


def _tr(n):
    if n < 10:
        return [_TR1[n]]
    if n < 100:
        t, o = divmod(n, 10)
        return [_TR10[t]] if o == 0 else [f"{_TR10[t]} {_TR1[o]}", f"{_TR10[t]}{_TR1[o]}"]
    h, r = divmod(n, 100)
    head = "yüz" if h == 1 else f"{_TR1[h]} yüz"
    heads = [head, head.replace(" ", "")]
    return heads if r == 0 else [f"{hd} {w}" for hd in heads for w in _tr(r)] + [f"{hd}{w}".replace(" ", "") for hd in heads[:1] for w in _tr(r)[:1]]


def num_accept(n, lang, words=True, extra=()):
    """Accepted forms of an integer: the digits (matched anywhere, by value) plus spelled-out forms that must be the
    whole answer ("^"), so "iki" can't collide with "on iki"."""
    out = [str(n)]
    if words and isinstance(n, int) and abs(n) < 1000:
        ws = (_en if lang == "en" else _tr)(abs(n))
        if n < 0:
            ws = [("minus " if lang == "en" else "eksi ") + w for w in ws]
        out += ["^" + w for w in dict.fromkeys(ws)]
    return out + list(extra)
