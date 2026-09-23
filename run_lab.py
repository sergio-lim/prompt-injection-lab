#!/usr/bin/env python3
"""Run every attack against every defense configuration and print a table."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from lab.agent import Agent
from lab.attacks import ATTACKS, Attack
from lab.model import MockModel
from lab.report import render_markdown, write_report

ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
REPORT_PATH = ROOT / "reports" / "lab.md"

ALL_DEFENSES = ("sanitize", "separate", "allowlist", "confirm", "strip")


@dataclass(frozen=True)
class Config:
    """One column of the results matrix."""

    id: str
    label: str
    model_mode: Literal["naive", "hardened"]
    defenses: tuple[str, ...]


CONFIGS: tuple[Config, ...] = (
    Config("naive+no_defenses", "naive", "naive", ()),
    Config("naive+sanitize", "+sanitize", "naive", ("sanitize",)),
    Config("naive+separate", "+separate", "naive", ("separate",)),
    Config("naive+allowlist", "+allowlist", "naive", ("allowlist",)),
    Config("naive+confirm", "+confirm", "naive", ("confirm",)),
    Config("naive+strip", "+strip", "naive", ("strip",)),
    Config("naive+all_defenses", "+all", "naive", ALL_DEFENSES),
    Config("hardened+no_defenses", "hardened", "hardened", ()),
)


def use_color(flag: bool | None) -> bool:
    """Honor --no-color, NO_COLOR, and whether stdout is a TTY."""
    if flag is False:
        return False
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return sys.stdout.isatty()


def paint(text: str, code: str, enabled: bool) -> str:
    """Wrap ``text`` in ANSI if colors are on."""
    if not enabled:
        return text
    return f"\033[{code}m{text}\033[0m"


def run_one(attack: Attack, config: Config) -> bool:
    """Return True if the attacker goal was achieved."""
    agent = Agent(
        docs_dir=DOCS_DIR,
        model=MockModel(config.model_mode),
        defenses=list(config.defenses),
    )
    result = agent.run(attack.user_task, attack.doc, attack.attacker_goal)
    return result.attacker_succeeded


def run_matrix() -> tuple[dict[tuple[str, str], bool], dict[str, float]]:
    """Evaluate the full attack x configuration grid."""
    cells: dict[tuple[str, str], bool] = {}
    for config in CONFIGS:
        for attack in ATTACKS:
            cells[(attack.id, config.id)] = run_one(attack, config)
    rates = {
        config.id: (
            sum(int(cells[(attack.id, config.id)]) for attack in ATTACKS) / len(ATTACKS)
        )
        for config in CONFIGS
    }
    return cells, rates


def format_table(
    cells: dict[tuple[str, str], bool],
    rates: dict[str, float],
    color: bool,
) -> str:
    """Fixed-width ASCII table. OK = attacker won, FAIL = blocked."""
    name_w = max(len(attack.id) for attack in ATTACKS)
    name_w = max(name_w, len("Attack"), len("success rate"))
    col_w = max(9, max(len(cfg.label) for cfg in CONFIGS))

    def mark(hit: bool) -> str:
        raw = "OK".center(col_w) if hit else "FAIL".center(col_w)
        return paint(raw, "32" if hit else "31", color)

    header = (
        f"{'Attack'.ljust(name_w)}  "
        + "  ".join(cfg.label.center(col_w) for cfg in CONFIGS)
    )
    rule = (
        f"{'-' * name_w}  "
        + "  ".join("-" * col_w for _ in CONFIGS)
    )
    lines = [header, rule]
    for attack in ATTACKS:
        row = attack.id.ljust(name_w) + "  "
        row += "  ".join(mark(cells[(attack.id, cfg.id)]) for cfg in CONFIGS)
        lines.append(row)
    lines.append(rule)
    rate_cells = []
    for cfg in CONFIGS:
        pct = f"{int(round(rates[cfg.id] * 100))}%".center(col_w)
        hot = rates[cfg.id] > 0
        rate_cells.append(paint(pct, "33" if hot else "32", color))
    lines.append(f"{'success rate'.ljust(name_w)}  " + "  ".join(rate_cells))
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Offline prompt-injection lab (no API keys, stdlib only).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors (also honors the NO_COLOR env var).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each (attack, config) verdict.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    color = use_color(False if args.no_color else None)

    if not DOCS_DIR.is_dir():
        print(f"docs/ missing at {DOCS_DIR}", file=sys.stderr)
        return 1

    cells, rates = run_matrix()
    if args.verbose:
        for config in CONFIGS:
            for attack in ATTACKS:
                hit = cells[(attack.id, config.id)]
                flag = "OK" if hit else "FAIL"
                print(f"[{config.id}] {attack.id}: {flag} ({attack.attacker_goal})")
        print()

    title = paint("prompt-injection-lab", "1;36", color)
    print(f"{title}  offline  stdlib-only  no API keys")
    print()
    print("OK = attacker goal achieved     FAIL = blocked")
    print()
    print(format_table(cells, rates, color))
    print()

    markdown = render_markdown(
        attacks=ATTACKS,
        config_ids=[cfg.id for cfg in CONFIGS],
        config_labels=[cfg.label for cfg in CONFIGS],
        cells=cells,
        rates=rates,
    )
    write_report(REPORT_PATH, markdown)
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
