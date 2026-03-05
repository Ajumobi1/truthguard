"""Simple humanizer for text: lightweight paraphrasing and stylistic changes.

This is a prototype meant to simulate human-like changes such as contractions,
small synonym swaps, filler insertion, and varied punctuation. Replace with
an actual seq2seq model (T5/BART/etc.) when available.
"""
import random
import re
from typing import Tuple

# small synonym / contraction maps for lightweight changes
CONTRACTIONS = {
    "do not": "don't",
    "does not": "doesn't",
    "cannot": "can't",
    "is not": "isn't",
    "I am": "I'm",
    "I will": "I'll",
}

SYNONYMS = {
    'important': ['crucial', 'vital', 'notable'],
    'show': ['demonstrate', 'reveal', 'display'],
    'help': ['assist', 'aid', 'support'],
}

FILLERS = ["Well,", "You know,", "Actually,", "Look,"]


def _replace_contractions(text: str) -> str:
    for k, v in CONTRACTIONS.items():
        text = re.sub(r'\b' + re.escape(k) + r'\b', v, text, flags=re.IGNORECASE)
    return text


def _synonym_swap(words, rate=0.07):
    out = []
    for w in words:
        lw = w.lower()
        if lw in SYNONYMS and random.random() < rate:
            out.append(random.choice(SYNONYMS[lw]))
        else:
            out.append(w)
    return out


def humanize(text: str, max_words: int = 1000) -> Tuple[str, int]:
    """Return (humanized_text, words_used).

    - Does light contraction replacement, occasional synonym swaps,
      inserts fillers and varies punctuation.
    - Respects max_words by trimming output.
    """
    # basic normalization
    text = text.strip()
    words = re.findall(r"\w+|[.,!?;:]", text)
    # synonym swaps
    words = _synonym_swap(words, rate=0.08)

    # rebuild sentences loosely
    out_words = []
    for i, w in enumerate(words):
        out_words.append(w)
        # occasionally insert a filler at sentence boundaries
        if w in '.!?' and random.random() < 0.12:
            out_words.append(random.choice(FILLERS))

    out = ' '.join(out_words)
    out = _replace_contractions(out)

    # add varied punctuation: randomly replace some commas with ellipses
    out = re.sub(r",", lambda m: '...' if random.random() < 0.05 else ',', out)

    # trim to max words
    final_words = re.findall(r"\w+", out)
    if len(final_words) > max_words:
        final_words = final_words[:max_words]
        out = ' '.join(final_words)

    return out, len(final_words)


if __name__ == '__main__':
    sample = "This is an important note that will help show how the humanizer works."
    print(humanize(sample, max_words=50))
