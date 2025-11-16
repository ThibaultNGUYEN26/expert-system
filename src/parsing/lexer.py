from __future__ import annotations

from typing import Dict, List

ConfigSections = Dict[str, List[str]]


def parse_config_sections(config_data: str) -> ConfigSections:
    """Split the config text into rule, fact, and query sections."""
    sections: ConfigSections = {"rules": [], "facts": [], "queries": []}
    current = "rules"

    for raw_line in config_data.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue

        if stripped.startswith("#"):
            header = stripped[1:].strip().lower()
            if header.startswith("rule"):
                current = "rules"
            elif header.startswith("fact"):
                current = "facts"
            elif header.startswith("quer"):
                current = "queries"
            continue

        sections[current].append(stripped)

    return sections


def normalize_expression(expression: str) -> str:
    """Normalise expressions so 'A B' is treated as 'A+B'."""
    stripped = expression.strip()
    if not stripped:
        return ""

    has_operator = any(op in stripped for op in ("+", "|", "^"))
    if not has_operator and " " in stripped:
        stripped = "+".join(part for part in stripped.split() if part)

    return stripped


def tokenize_expression(text: str) -> List[str]:
    """Convert an expression string into tokens for the parser."""
    tokens: List[str] = []
    for char in text:
        if char.isspace():
            continue
        if char in {"+", "|", "^", "!", "(", ")"}:
            tokens.append(char)
            continue
        if char.isalpha():
            tokens.append(char.upper())
            continue
        raise ValueError(f"Unsupported character '{char}' in expression '{text}'")
    return tokens


__all__ = ["ConfigSections", "normalize_expression", "parse_config_sections", "tokenize_expression"]
