"""Deterministic stand-in for an LLM. Two modes: naive and hardened."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from typing import Literal

EMAIL_RE = re.compile(
    r"(?:send\s+(?:an\s+)?email\s+to|mail\s+to)\s+"
    r"([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})",
    re.IGNORECASE,
)

# Require a real query token. The system prompt mentions delete_records(query)
# as a signature and must not count as an action.
DELETE_RE = re.compile(
    r"(?:call\s+)?delete_records\s+with\s+query\s+['\"]?(\*|[A-Za-z0-9_\-]+)['\"]?"
    r"|delete_records\s*\(\s*(?:query\s*=\s*)?['\"](\*|[A-Za-z0-9_\-]+)['\"]\s*\)"
    r"|delete_records\s*\(\s*\*\s*\)"
    r"|\bwipe\s+(?:all\s+)?records\b",
    re.IGNORECASE,
)

BASE64_RE = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{24,}={0,2}(?![A-Za-z0-9+/])")
HTML_COMMENT_RE = re.compile(r"<!--(.*?)-->", re.DOTALL)


@dataclass
class ProposedCall:
    """A tool call the mock model wants to make."""

    name: str
    args: dict[str, str]


class MockModel:
    """Gullible concatenating parser, or a model that refuses data-as-orders.

    ``naive`` deobfuscates the whole prompt and obeys the first actionable
    instruction it finds, including text that arrived via a tool.

    ``hardened`` reads only the instruction channel (the INSTRUCTIONS
    fence, or everything before ``Tool output``). Tool text is data.
    """

    def __init__(self, mode: Literal["naive", "hardened"] = "naive") -> None:
        if mode not in {"naive", "hardened"}:
            raise ValueError(f"unsupported model mode: {mode}")
        self.mode = mode

    def complete(self, prompt: str) -> list[ProposedCall]:
        """Return tool calls implied by the prompt under this model's rules."""
        if self.mode == "hardened":
            scope = self._instruction_scope(prompt)
            return self._extract_actions(scope, deobfuscate=False)
        return self._extract_actions(self._deobfuscate(prompt), deobfuscate=False)

    def _instruction_scope(self, prompt: str) -> str:
        start = prompt.find("=== INSTRUCTIONS ===")
        end = prompt.find("=== END INSTRUCTIONS ===")
        if start != -1:
            chunk = prompt[start : end if end != -1 else None]
            return chunk
        for marker in ("=== DATA ===", "Tool output (read_document):", "Tool output:"):
            idx = prompt.find(marker)
            if idx != -1:
                return prompt[:idx]
        return prompt

    def _deobfuscate(self, text: str) -> str:
        """Undo the cheap tricks a naive model 'notices' in untrusted text."""
        pieces = [text]
        pieces.extend(HTML_COMMENT_RE.findall(text))
        for token in BASE64_RE.findall(text):
            decoded = _try_b64(token)
            if decoded:
                pieces.append(decoded)
        merged = "\n".join(pieces)
        for ch in ("\u200b", "\u200c", "\u200d", "\u2060", "\ufeff"):
            merged = merged.replace(ch, "")
        return merged

    def _extract_actions(self, text: str, deobfuscate: bool) -> list[ProposedCall]:
        blob = self._deobfuscate(text) if deobfuscate else text
        calls: list[ProposedCall] = []

        email = EMAIL_RE.search(blob)
        if email:
            to = email.group(1)
            body = _summary_body(blob)
            calls.append(
                ProposedCall(
                    "send_email",
                    {"to": to, "subject": "Summary", "body": body},
                )
            )

        delete_match = DELETE_RE.search(blob)
        if delete_match:
            query = "*"
            for group in delete_match.groups():
                if group:
                    query = "*" if group.lower() == "all" else group
                    break
            calls.append(ProposedCall("delete_records", {"query": query}))

        return calls


def _try_b64(token: str) -> str | None:
    pad = (-len(token)) % 4
    try:
        raw = base64.b64decode(token + ("=" * pad), validate=False)
    except (ValueError, OSError):
        return None
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not text or not all(ch.isprintable() or ch in "\n\r\t" for ch in text):
        return None
    if not re.search(r"(ignore|send|email|delete)", text, re.IGNORECASE):
        return None
    return text


def _summary_body(text: str) -> str:
    """Use a short slice of the prompt as the 'summary' body."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    visible = [line for line in lines if not line.startswith("===")]
    snippet = " ".join(visible)[:240]
    return snippet or "summary"
