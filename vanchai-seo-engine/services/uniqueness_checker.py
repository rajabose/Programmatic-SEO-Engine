#!/usr/bin/env python3
"""
uniqueness_checker.py — TF-IDF cosine similarity gate.

Compares a new page's text against every existing page in docs/.
Gate: max cosine similarity must be ≤ 20% to pass.
No external dependencies — pure stdlib TF-IDF.
"""

import math
import re
from collections import Counter
from pathlib import Path

MAX_OVERLAP = 0.20  # 20%

_STOP_WORDS = frozenset({
    'the','a','an','and','or','but','in','on','at','to','for','of','with',
    'by','from','is','are','was','were','be','been','have','has','had',
    'do','does','did','will','would','could','should','may','might',
    'this','that','these','those','it','its','we','you','he','she','they',
    'our','your','his','her','their','what','which','who','when','where','how',
    'i','me','my','us','not','no','so','if','as','up','out','all','can',
})

_SKIP_STEMS = ('index', '404', '_admin')


def _extract_text(html: str) -> str:
    text = re.sub(r'<(script|style|head|nav|footer)[^>]*>.*?</\1>', '', html, flags=re.S | re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def _tokenize(text: str) -> list[str]:
    return [w for w in re.findall(r'[a-z]+', text.lower())
            if w not in _STOP_WORDS and len(w) > 2]


def _cosine(v1: dict[str, float], v2: dict[str, float]) -> float:
    common = set(v1) & set(v2)
    if not common:
        return 0.0
    dot  = sum(v1[w] * v2[w] for w in common)
    mag1 = math.sqrt(sum(x * x for x in v1.values()))
    mag2 = math.sqrt(sum(x * x for x in v2.values()))
    return dot / (mag1 * mag2) if mag1 and mag2 else 0.0


def _tfidf(tokens: list[str], all_docs: list[list[str]]) -> dict[str, float]:
    """TF-IDF vector for tokens given a corpus of all_docs (including self)."""
    n  = len(all_docs)
    tf = Counter(tokens)
    total = len(tokens) or 1
    result: dict[str, float] = {}
    for word, count in tf.items():
        df  = sum(1 for doc in all_docs if word in set(doc))
        idf = math.log((n + 1) / (df + 1)) + 1  # smoothed IDF
        result[word] = (count / total) * idf
    return result


def check(new_html: str, docs_dir: Path, current_slug: str = '') -> tuple[float, str]:
    """
    Return (max_similarity, most_similar_slug).
    Passes when max_similarity ≤ MAX_OVERLAP.
    """
    new_tokens = _tokenize(_extract_text(new_html))
    if not new_tokens:
        return 0.0, ''

    # Load existing corpus, skip self and non-content pages
    corpus: list[tuple[str, list[str]]] = []
    for html_file in sorted(docs_dir.glob('*.html')):
        stem = html_file.stem
        if stem == current_slug or stem in _SKIP_STEMS or stem.startswith('category-'):
            continue
        try:
            tokens = _tokenize(_extract_text(html_file.read_text(encoding='utf-8')))
            if tokens:
                corpus.append((stem, tokens))
        except OSError:
            continue

    if not corpus:
        return 0.0, ''

    # Full doc list for IDF (corpus + new page)
    all_docs = [tokens for _, tokens in corpus] + [new_tokens]

    new_vec   = _tfidf(new_tokens, all_docs)
    max_sim   = 0.0
    most_sim  = ''

    for slug, tokens in corpus:
        corp_vec = _tfidf(tokens, all_docs)
        sim = _cosine(new_vec, corp_vec)
        if sim > max_sim:
            max_sim  = sim
            most_sim = slug

    return max_sim, most_sim
