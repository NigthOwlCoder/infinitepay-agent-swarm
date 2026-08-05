import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

TOKEN = re.compile(r"[a-záàâãéêíóôõúç0-9]+", re.I)
def tokenize(text): return TOKEN.findall(text.casefold())

@dataclass(frozen=True)
class SearchHit:
    text: str
    source: str
    score: float

class RagService:
    """Small dependency-free BM25 index suitable for the challenge corpus."""
    def __init__(self, documents):
        self.documents = documents
        self.tokens = [tokenize(text) for text, _ in documents]
        self.avg_len = sum(map(len, self.tokens)) / max(len(self.tokens), 1)
        self.df = Counter(term for doc in self.tokens for term in set(doc))

    @classmethod
    def from_directory(cls, directory):
        documents = []
        for path in sorted(Path(directory).glob("*.txt")):
            text = path.read_text(encoding="utf-8")
            for block in filter(str.strip, re.split(r"\n\s*\n", text)):
                documents.append((block.strip(), str(path)))
        return cls(documents)

    def search(self, query, limit=3):
        scores = []
        n = len(self.documents)
        for (text, source), tokens in zip(self.documents, self.tokens):
            counts, score = Counter(tokens), 0.0
            for term in set(tokenize(query)):
                if not counts[term]: continue
                idf = math.log(1 + (n - self.df[term] + .5) / (self.df[term] + .5))
                tf = counts[term]
                score += idf * tf * 2.5 / (tf + 1.5 * (.25 + .75 * len(tokens) / max(self.avg_len, 1)))
            scores.append(SearchHit(text, source, round(score, 4)))
        return sorted(scores, key=lambda hit: hit.score, reverse=True)[:limit]
