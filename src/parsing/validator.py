from __future__ import annotations

from typing import Iterable, Sequence

from .lexer import Token, TokenType


VALID_FACT_SYMBOLS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
ALLOWED_OPERATORS = frozenset(
    {
        TokenType.AND,
        TokenType.OR,
        TokenType.XOR,
        TokenType.NOT,
        TokenType.IMPLIES,
        TokenType.IIF,
    }
)


class ValidationError(ValueError):
    """Raised when a syntactic validation rule fails."""


def ensure_valid_symbol(symbol: str, token: Token | None = None) -> str:
    """Validate and normalize a fact symbol."""
    cleaned = symbol.strip()
    if len(cleaned) != 1 or cleaned.upper() not in VALID_FACT_SYMBOLS:
        location = f" at line {token.line}, column {token.column}" if token else ""
        raise ValidationError(f"Invalid fact symbol '{symbol}'{location}.")

    upper_symbol = cleaned.upper()
    if cleaned != upper_symbol:
        location = f" at line {token.line}, column {token.column}" if token else ""
        raise ValidationError(
            f"Fact symbols must be uppercase letters: got '{symbol}'{location}."
        )
    return upper_symbol


def validate_balanced_parentheses(tokens: Sequence[Token]) -> None:
    """Ensure that parentheses are balanced across the token stream."""
    depth = 0
    lparen_stack = []
    for token in tokens:
        if token.type == TokenType.L_PAREN:
            lparen_stack.append(token)
        elif token.type == TokenType.R_PAREN:
            if not lparen_stack:
                raise ValidationError(
                    f"Unmatched ')' at line {token.line}, column {token.column}."
                )
            lparen_stack.pop()

    if lparen_stack:
        first_unmatched = lparen_stack[0]
        raise ValidationError(
            f"Unmatched '(' at line {first_unmatched.line}, column {first_unmatched.column}."
        )


def ensure_known_operator(token: Token) -> None:
    """Ensure that a token corresponds to a supported operator."""
    if token.type not in ALLOWED_OPERATORS:
        raise ValidationError(
            f"Unsupported operator '{token.lexeme}' at line {token.line}, column {token.column}."
        )


def ensure_valid_fact_sequence(tokens: Iterable[Token]) -> None:
    """Validate that an iterable of tokens only contains valid fact identifiers."""
    for token in tokens:
        ensure_valid_symbol(token.lexeme, token)


__all__ = [
    "ALLOWED_OPERATORS",
    "ValidationError",
    "ensure_known_operator",
    "ensure_valid_fact_sequence",
    "ensure_valid_symbol",
    "validate_balanced_parentheses",
    "VALID_FACT_SYMBOLS",
]
