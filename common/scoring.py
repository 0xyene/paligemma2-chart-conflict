"""Answer matching shared by the build-time checks and the Colab notebook (copied there verbatim).

match(answer, accepts, lang) -> True if any accepted phrase appears in the answer as a whole-word sequence.
Numbers must match exactly ("12" never matches "120"); in Turkish a word may carry a suffix
("haziranda" matches "haziran"), because Turkish answers are often inflected.
A suffix that negates the verb does not count ("azal" doesn't match "azalmadı").
Numbers compare by value ("64.0" == "64").
Prefixes on an accepted phrase: "=" matches exactly, without the Turkish suffix rule ("=bir" must not match "birkaç");
"^" must be the whole answer ("^değil" matches "Değil." but not "altında değil").
"""
import re
import unicodedata

_TOKEN = re.compile(r"(?:(?<![^\W_])-)?\d+(?:\.\d+)?|[^\W\d_]+")   # minus only when not glued to a word
# Turkish verb negation right after the matched stem: azal|madı, yüksel|medi, art|mamış, art|maz (text is ı/i-folded)
_NEG = re.compile(r"m[ae](?:d[iuü]|m[iuü]ş|z)|m[iuü]yor")      # …|madı, …|mamış, …|maz, …|mıyor


def tokens(s):
    s = unicodedata.normalize("NFKC", s).replace("−", "-").replace("–", "-")
    s = s.replace("İ", "i").lower().replace("ı", "i")      # fold I/İ/ı/i together: "Hayır" == "hayir", "Ivydale" == "ıvydale"
    s = re.sub(r"(\d),(\d)", r"\1.\2", s)                    # 18,4 -> 18.4
    s = re.sub(r"(?<![\w-])\+(?=\d)", "", s)                  # +18.4 -> 18.4 (sign kept only for minus)
    return _TOKEN.findall(s)


def _num(t):
    try:
        return float(t)
    except ValueError:
        return None


def _tok_eq(accept_tok, answer_tok, lang, exact=False):
    if accept_tok == answer_tok:
        return True
    na, nt = _num(accept_tok), _num(answer_tok)
    if na is not None or nt is not None:                      # numbers compare by value: "64" == "64.0"
        return na is not None and nt is not None and na == nt
    if exact or lang != "tr" or not accept_tok.isalpha() or len(accept_tok) < 3 or not answer_tok.startswith(accept_tok):
        return False
    # a suffix may be added, but not a negation: "azal" must not match "azalmadı" ("did not decrease")
    return not _NEG.search(answer_tok[len(accept_tok) - 2:])


def _contains(answer_toks, accept_toks, lang, exact=False):
    n = len(accept_toks)
    return n > 0 and any(
        all(_tok_eq(a, t, lang, exact) for a, t in zip(accept_toks, answer_toks[i:i + n]))
        for i in range(len(answer_toks) - n + 1))


def _whole(answer_toks, accept_toks, lang):
    return len(answer_toks) == len(accept_toks) and all(_tok_eq(a, t, lang, True) for a, t in zip(accept_toks, answer_toks))


def match(answer, accepts, lang):
    at = tokens(answer)
    for a in accepts:
        if a.startswith("^"):                                 # whole answer only: "^değil" matches "Değil." but not "altında değil"
            if _whole(at, tokens(a[1:]), lang):
                return True
        elif _contains(at, tokens(a.removeprefix("=")), lang, exact=a.startswith("=")):
            return True
    return False


def classify(answer, visual, text, lang):
    """For a conflict image: which cue did the answer follow?"""
    v, t = match(answer, visual, lang), match(answer, text, lang)
    return "both" if v and t else "visual" if v else "text" if t else "neither"
