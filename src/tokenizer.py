from __future__ import annotations

import re
from dataclasses import dataclass


_WORD_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Tokenizer:
    lower: bool = True

    def tokenize(self, text: str) -> list[str]:
        if self.lower:
            text = text.lower()
        return _WORD_RE.findall(text)
