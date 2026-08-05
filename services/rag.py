import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

TOKEN = re.compile(r"[a-záàâãéêíóôõúç0-9]+", re.I)
STOPWORDS = {
    "a", "as", "ao", "com", "como", "da", "das", "de", "do", "dos", "e",
    "dia", "em", "eu", "é", "foi", "hoje", "o", "os", "para", "por", "qual", "que",
    "quem", "se",
    "um", "uma", "the", "is", "of", "to", "what", "who",
}
SYNONYMS: dict[str, tuple[str, ...]] = {
    "fees": ("taxas", "tarifas"),
    "fee": ("taxa", "tarifa"),
    "rates": ("taxas", "tarifas"),
    "rate": ("taxa", "tarifa"),
    "cost": ("preço", "custo"),
    "price": ("preço", "custo"),
    "debit": ("débito",),
    "credit": ("crédito",),
    "card": ("cartão",),
    "phone": ("celular", "infinitetap"),
    "machine": ("maquininha",),
    "account": ("conta",),
    "transfers": ("transferências",),
}


def tokenize(text: str) -> list[str]:
    tokens = [token for token in TOKEN.findall(text.casefold()) if token not in STOPWORDS]
    return tokens + [word for token in tokens for word in SYNONYMS.get(token, ())]

@dataclass(frozen=True)
class SearchHit:
    text: str
    source: str
    score: float

class RagService:
    """Small dependency-free BM25 index suitable for the challenge corpus."""
    def __init__(self, documents: list[tuple[str, str]]) -> None:
        self.documents = documents
        self.tokens = [tokenize(text) for text, _ in documents]
        self.avg_len = sum(map(len, self.tokens)) / max(len(self.tokens), 1)
        self.df = Counter(term for doc in self.tokens for term in set(doc))

    @classmethod
    def from_directory(cls, directory: str | Path) -> "RagService":
        documents: list[tuple[str, str]] = []
        for path in sorted(Path(directory).glob("*.txt")):
            text = path.read_text(encoding="utf-8")
            for block in filter(str.strip, re.split(r"\n\s*\n", text)):
                documents.append((block.strip(), str(path)))
        return cls(documents)

    def search(self, query: str, limit: int = 3) -> list[SearchHit]:
        scores: list[SearchHit] = []
        n = len(self.documents)
        for (text, source), tokens in zip(self.documents, self.tokens, strict=False):
            counts = Counter(tokens)
            score = 0.0
            for term in set(tokenize(query)):
                if not counts[term]:
                    continue
                idf = math.log(
                    1 + (n - self.df[term] + 0.5) / (self.df[term] + 0.5)
                )
                tf = counts[term]
                length_normalization = 0.25 + (
                    0.75 * len(tokens) / max(self.avg_len, 1)
                )
                score += idf * tf * 2.5 / (tf + 1.5 * length_normalization)
            scores.append(SearchHit(text, source, round(score, 4)))
        return sorted(scores, key=lambda hit: hit.score, reverse=True)[:limit]
