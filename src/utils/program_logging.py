from __future__ import annotations

import logging
from typing import Dict, List

from src.parsing import Program


# Color constants - centralized for the entire project
class Colors:
    """ANSI color codes for terminal output."""
    # Basic colors
    RESET = "\033[0m"

    # Status colors
    GREEN = "\033[92m"   # Success, TRUE
    RED = "\033[91m"     # Error, FALSE
    YELLOW = "\033[93m"  # Warning, UNDETERMINED
    BLUE = "\033[94m"    # Debug
    CYAN = "\033[96m"    # Info, labels
    MAGENTA = "\033[95m" # Headers, critical
    WHITE = "\033[97m"   # Normal text

    # Text formatting
    BOLD = "\033[1m"

    @classmethod
    def color(cls, text: str, color: str) -> str:
        """Wrap text with a color code."""
        return f"{color}{text}{cls.RESET}"


# Legacy constants for backward compatibility
RESET = Colors.RESET
CYAN = Colors.CYAN
YELLOW = Colors.YELLOW
WHITE = Colors.WHITE
MAGENTA = Colors.MAGENTA


def _color(text: str, color: str) -> str:
    return Colors.color(text, color)


def log_program(program: Program) -> None:
    """Emit a detailed log of the rules, facts, and queries."""
    logging.info("")
    logging.info(_color("Parsing summary", MAGENTA))
    _log_rules(program)
    logging.info("")
    _log_facts(program.facts)
    logging.info("")
    _log_queries(program.queries)
    logging.info("")


def _log_rules(program: Program) -> None:
    rules = program.rules
    logging.info(_color(f"  Rules ({len(rules)}):", CYAN))
    if not rules:
        logging.info(_color("    (none)", WHITE))
        return

    width = len(str(len(rules)))
    for index, rule in enumerate(rules, 1):
        label = str(rule.condition)
        # Conclusion can now be any Condition, not just FactCondition
        conclusion_str = getattr(rule.conclusion, 'rule_format', None) or str(rule.conclusion)
        logging.info(
            _color(
                f"    [{index:0{width}d}] line {rule.line} -> {label} => {conclusion_str}",
                WHITE,
            )
        )


def _log_facts(facts: Dict[str, bool]) -> None:
    if not facts:
        logging.info(_color("  Facts: (none)", CYAN))
        return

    true_facts = sorted(symbol for symbol, value in facts.items() if value)
    false_facts = sorted(symbol for symbol, value in facts.items() if not value)

    logging.info(_color(f"  Facts ({len(facts)}):", CYAN))
    if true_facts:
        logging.info(_color(f"    true : {' '.join(true_facts)}", YELLOW))
    if false_facts:
        logging.info(_color(f"    false: {' '.join(false_facts)}", YELLOW))


def _log_queries(queries: List[str]) -> None:
    logging.info(
        _color(
            f"  Queries ({len(queries)}): {(' '.join(queries) or '(none)')}",
            CYAN,
        )
    )


__all__ = ["log_program", "Colors"]
