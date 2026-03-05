"""Lightweight heuristic-based AI-written text detector.

This is a fast, local heuristic useful as a prototype. It computes simple
stylometric features and combines them into an "AI-likeliness" score.
Replace with a learned model later (per README guidance).
"""
import re
from typing import Tuple

# small stopword list for heuristics
STOPWORDS = {
    'the','and','is','in','it','of','to','a','that','this','for','on','with','as','are','was','but','be','by'
}


def features(text: str) -> dict:
    words = re.findall(r"\w+", text)
    word_count = max(1, len(words))
    avg_word_len = sum(len(w) for w in words) / word_count
    sentences = re.split(r'[.!?]+', text)
    sentence_count = max(1, sum(1 for s in sentences if s.strip()))
    avg_sent_len = word_count / sentence_count
    stopword_ratio = sum(1 for w in words if w.lower() in STOPWORDS) / word_count
    punctuation_ratio = sum(1 for c in text if c in '.,;:!?()[]') / max(1, len(text))
    lexical_diversity = len(set(w.lower() for w in words)) / word_count

    return {
        'word_count': word_count,
        'avg_word_len': avg_word_len,
        'avg_sent_len': avg_sent_len,
        'stopword_ratio': stopword_ratio,
        'punctuation_ratio': punctuation_ratio,
        'lexical_diversity': lexical_diversity,
    }


def score_text(text: str) -> Tuple[str, float]:
    """Return (label, score_percent) where score_percent in [0,100].

    Heuristic mapping (prototype):
    - AI-generated tends to have lower lexical diversity, more regular sentence
      lengths, and different stopword/punctuation patterns. These heuristics are
      imperfect but useful as a bootstrap.
    """
    f = features(text)

    # heuristics (weights tuned for prototype behavior)
    w = 0.0
    # lower lexical diversity -> more likely AI
    w += (1.0 - f['lexical_diversity']) * 0.35
    # short average word length -> slightly AI-ish (common in generated text)
    w += max(0.0, (5.0 - f['avg_word_len']) / 5.0) * 0.15
    # very uniform sentence length (low variance) is typical of generated text;
    # here we approximate by penalizing very even average sentence length
    w += (1.0 - min(1.0, f['avg_sent_len'] / 20.0)) * 0.15
    # stopword ratio low or very high might indicate non-human phrasing
    w += abs(0.45 - f['stopword_ratio']) * 0.15
    # punctuation usage: very low punctuation may indicate generated text
    w += (1.0 - min(1.0, f['punctuation_ratio'] * 50.0)) * 0.2

    # clamp
    score = max(0.0, min(1.0, w))
    label = 'AI-Generated' if score >= 0.6 else 'Likely Human'
    return label, float(score * 100.0)


if __name__ == '__main__':
    # quick manual test
    txt = """This is a short sample sentence. It demonstrates typical human-style
    punctuation, varying sentence length, and natural lexical choice."""
    print(score_text(txt))
