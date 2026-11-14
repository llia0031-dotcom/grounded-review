"""Policy library: cut clause text out of the source files and search it.

Every clause text returned here is an exact substring of its source file, so a model that quotes
a clause can be checked with evidence-check's script against policies/sources/.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml
from rank_bm25 import BM25Okapi

HERE = Path(__file__).resolve().parent
SOURCES = HERE / "sources"

ARTICLE_RE = re.compile(r"(?m)^第[一二三四五六七八九十百]+条 ")
CHAPTER_RE = re.compile(r"(?m)^## ")


@dataclass(frozen=True)
class Clause:
    id: str
    source: str
    title: str
    category: str
    kind: str
    jurisdiction: str  # "CN" or "TikTok"
    text: str


def _article(doc: str, head: str) -> str:
    m = re.search(rf"(?m)^{head} ", doc)
    if not m:
        raise KeyError(head)
    rest = doc[m.start():]
    nxt = [x.start() for x in ARTICLE_RE.finditer(rest) if x.start() > 0]
    nxt += [x.start() for x in CHAPTER_RE.finditer(rest) if x.start() > 0]
    return rest[: min(nxt)].strip() if nxt else rest.strip()


def _extract(doc: str, locator: dict) -> str:
    (kind, value), = locator.items()
    if kind == "article":
        return _article(doc, value)
    if kind == "article_item":
        art = _article(doc, value[0])
        line = next(l for l in art.splitlines() if l.startswith(value[1]))
        return line.strip()
    if kind == "article_para":
        art = _article(doc, value[0])
        return art.splitlines()[value[1] - 1].strip()
    if kind == "guide_item":
        m = re.search(rf"(?m)^{value}", doc)
        rest = doc[m.start():]
        nxt = re.search(r"(?m)^[一二三四五六七八九十]+、", rest[len(value):])
        return (rest[: nxt.start() + len(value)] if nxt else rest).strip()
    if kind == "section":
        m = re.search(rf"(?m)^## {re.escape(value)}\s*$", doc)
        if not m:
            raise KeyError(value)
        body = doc[m.end():]
        nxt = re.search(r"(?m)^## ", body)
        return (body[: nxt.start()] if nxt else body).strip()
    raise ValueError(kind)


_KEYWORDS: dict[str, str] = {}
MISSING: set[str] = set()  # source files not present


@lru_cache(maxsize=1)
def load() -> tuple[Clause, ...]:
    cfg = yaml.safe_load((HERE / "clauses.yaml").read_text(encoding="utf-8"))
    out = []
    _KEYWORDS.update(cfg.get("keywords", {}))
    for c in cfg["clauses"]:
        path = SOURCES / c["source"]
        if not path.exists():  # the TikTok pages are not redistributed; see README
            MISSING.add(c["source"])
            text = ""
        else:
            doc = path.read_text(encoding="utf-8")
            text = _extract(doc, c["locator"])
            assert text in doc, c["id"]
        out.append(Clause(c["id"], c["source"], c["title"], c["category"], c["kind"],
                          "CN" if c["id"].startswith("CN-") else "TikTok", text))
    return tuple(out)


@lru_cache(maxsize=1)
def categories() -> dict:
    return yaml.safe_load((HERE / "clauses.yaml").read_text(encoding="utf-8"))["categories"]


def by_id() -> dict[str, Clause]:
    return {c.id: c for c in load()}


def _tokens(text: str) -> list[str]:
    text = text.lower()
    words = re.findall(r"[a-z0-9]+", text)
    han = re.findall(r"[一-鿿]+", text)
    grams = [run[i:i + 2] for run in han for i in range(max(1, len(run) - 1))]
    return words + grams


@lru_cache(maxsize=2)
def _index(jurisdiction: str):
    docs = [c for c in load() if c.jurisdiction == jurisdiction]
    return docs, BM25Okapi([_tokens(" ".join([c.title, _KEYWORDS.get(c.id, ""), c.text])) for c in docs])


def search(query: str, jurisdiction: str, k: int = 4) -> list[Clause]:
    """BM25 over clause titles and text, within one jurisdiction ("CN" or "TikTok")."""
    docs, bm25 = _index(jurisdiction)
    scores = bm25.get_scores(_tokens(query))
    ranked = sorted(zip(scores, range(len(docs))), key=lambda x: -x[0])
    return [docs[i] for s, i in ranked[:k] if s > 0] or [docs[i] for _, i in ranked[:k]]


def render(clauses, with_text: bool = True) -> str:
    parts = []
    for c in clauses:
        head = f"[{c.id}] {c.title} (source file: {c.source}; {c.kind})"
        parts.append(head + ("\n" + c.text if with_text else ""))
    return "\n\n".join(parts)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for c in load():
        print(c.id, c.category, len(c.text), c.text[:60].replace("\n", " "))
    print()
    print(render(search("最好 第一 顶级", "CN", 3), with_text=False))
    print(render(search("lose weight fast without exercise", "TikTok", 3), with_text=False))
