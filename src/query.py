from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from src.indexer import InvertedIndex


class QueryNode:
    pass


@dataclass(frozen=True)
class Term(QueryNode):
    value: str


@dataclass(frozen=True)
class Phrase(QueryNode):
    terms: list[str]


@dataclass(frozen=True)
class And(QueryNode):
    left: QueryNode
    right: QueryNode


@dataclass(frozen=True)
class Or(QueryNode):
    left: QueryNode
    right: QueryNode


@dataclass(frozen=True)
class Not(QueryNode):
    node: QueryNode


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str


def _scan_tokens(query: str) -> list[_Token]:
    tokens: list[_Token] = []
    i = 0

    while i < len(query):
        ch = query[i]

        if ch.isspace():
            i += 1
            continue

        if ch == '"':
            i += 1
            start = i
            while i < len(query) and query[i] != '"':
                i += 1
            phrase = query[start:i]
            if i < len(query) and query[i] == '"':
                i += 1
            tokens.append(_Token(kind="PHRASE", value=phrase))
            continue

        start = i
        while i < len(query) and (not query[i].isspace()) and query[i] != '"':
            i += 1
        word = query[start:i]
        upper = word.upper()
        if upper in {"AND", "OR", "NOT"}:
            tokens.append(_Token(kind=upper, value=upper))
        else:
            tokens.append(_Token(kind="WORD", value=word))

    return tokens


class _Parser:
    def __init__(self, tokens: list[_Token], tokenize: Callable[[str], list[str]]):
        self._tokens = tokens
        self._i = 0
        self._tokenize = tokenize

    def _peek(self) -> _Token | None:
        if self._i >= len(self._tokens):
            return None
        return self._tokens[self._i]

    def _consume(self, kind: str | None = None) -> _Token:
        t = self._peek()
        if t is None:
            raise ValueError("Unexpected end of query")
        if kind is not None and t.kind != kind:
            raise ValueError(f"Expected {kind} but found {t.kind}")
        self._i += 1
        return t

    def _starts_primary(self, t: _Token | None) -> bool:
        return t is not None and t.kind in {"WORD", "PHRASE", "NOT"}

    def parse(self) -> QueryNode:
        node = self._parse_or()
        if self._peek() is not None:
            t = self._peek()
            assert t is not None
            raise ValueError(f"Unexpected token: {t.value}")
        return node

    def _parse_or(self) -> QueryNode:
        left = self._parse_and()
        while True:
            t = self._peek()
            if t is None or t.kind != "OR":
                break
            self._consume("OR")
            right = self._parse_and()
            left = Or(left=left, right=right)
        return left

    def _parse_and(self) -> QueryNode:
        left = self._parse_not()

        while True:
            t = self._peek()
            if t is None:
                break

            if t.kind == "AND":
                self._consume("AND")
                right = self._parse_not()
                left = And(left=left, right=right)
                continue

            if self._starts_primary(t):
                right = self._parse_not()
                left = And(left=left, right=right)
                continue

            break

        return left

    def _parse_not(self) -> QueryNode:
        t = self._peek()
        if t is not None and t.kind == "NOT":
            self._consume("NOT")
            return Not(node=self._parse_not())
        return self._parse_primary()

    def _parse_primary(self) -> QueryNode:
        t = self._peek()
        if t is None:
            raise ValueError("Expected term")

        if t.kind == "WORD":
            raw = self._consume("WORD").value
            terms = self._tokenize(raw)
            if not terms:
                raise ValueError("Empty term")
            if len(terms) == 1:
                return Term(value=terms[0])
            node: QueryNode = Term(value=terms[0])
            for term in terms[1:]:
                node = And(left=node, right=Term(value=term))
            return node

        if t.kind == "PHRASE":
            raw = self._consume("PHRASE").value
            terms = self._tokenize(raw)
            if not terms:
                raise ValueError("Empty phrase")
            if len(terms) == 1:
                return Term(value=terms[0])
            return Phrase(terms=terms)

        raise ValueError(f"Unexpected token: {t.value}")


def parse_query(query: str, tokenize: Callable[[str], list[str]]) -> QueryNode:
    tokens = _scan_tokens(query)
    if not tokens:
        raise ValueError("Empty query")
    return _Parser(tokens, tokenize=tokenize).parse()


def iter_positive_terms(node: QueryNode) -> Iterable[str]:
    yield from _iter_terms(node, negated=False)


def evaluate_query(node: QueryNode, index: InvertedIndex) -> set[str]:
    all_docs = set(index.doc_lengths.keys())
    return _eval(node, index=index, all_docs=all_docs)


def _eval(node: QueryNode, *, index: InvertedIndex, all_docs: set[str]) -> set[str]:
    if isinstance(node, Term):
        return set(index.term_to_doc_tf.get(node.value, {}).keys())

    if isinstance(node, Phrase):
        return _phrase_docs(node.terms, index=index)

    if isinstance(node, And):
        return _eval(node.left, index=index, all_docs=all_docs) & _eval(
            node.right, index=index, all_docs=all_docs
        )

    if isinstance(node, Or):
        return _eval(node.left, index=index, all_docs=all_docs) | _eval(
            node.right, index=index, all_docs=all_docs
        )

    if isinstance(node, Not):
        return all_docs - _eval(node.node, index=index, all_docs=all_docs)

    raise TypeError(f"Unknown query node: {type(node)}")


def _phrase_docs(terms: list[str], *, index: InvertedIndex) -> set[str]:
    if not terms:
        return set()
    if len(terms) == 1:
        return set(index.term_to_doc_tf.get(terms[0], {}).keys())

    doc_sets: list[set[str]] = []
    for t in terms:
        postings = index.term_to_doc_positions.get(t)
        if not postings:
            return set()
        doc_sets.append(set(postings.keys()))
    candidates = set.intersection(*doc_sets) if doc_sets else set()

    matches: set[str] = set()
    for doc_id in candidates:
        positions_per_term: list[list[int]] = []
        for t in terms:
            pos_list = index.term_to_doc_positions[t].get(doc_id)
            if not pos_list:
                positions_per_term = []
                break
            positions_per_term.append(pos_list)
        if not positions_per_term:
            continue

        next_sets = [set(p) for p in positions_per_term[1:]]
        for start_pos in positions_per_term[0]:
            ok = True
            for offset, s in enumerate(next_sets, start=1):
                if (start_pos + offset) not in s:
                    ok = False
                    break
            if ok:
                matches.add(doc_id)
                break

    return matches


def _iter_terms(node: QueryNode, *, negated: bool) -> Iterable[str]:
    if isinstance(node, Term):
        if not negated:
            yield node.value
        return

    if isinstance(node, Phrase):
        if not negated:
            yield from node.terms
        return

    if isinstance(node, Not):
        yield from _iter_terms(node.node, negated=not negated)
        return

    if isinstance(node, And):
        yield from _iter_terms(node.left, negated=negated)
        yield from _iter_terms(node.right, negated=negated)
        return

    if isinstance(node, Or):
        yield from _iter_terms(node.left, negated=negated)
        yield from _iter_terms(node.right, negated=negated)
        return

    raise TypeError(f"Unknown query node: {type(node)}")
