from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List


class TokenType(Enum):
    """Types of lexemes recognized by the expert-system language."""

    IDENT = auto()
    AND = auto()
    OR = auto()
    XOR = auto()
    NOT = auto()
    L_PAREN = auto()
    R_PAREN = auto()
    IMPLIES = auto()
    IIF = auto()
    EQUAL = auto()
    QUERY = auto()
    EOL = auto()
    EOF = auto()


@dataclass(frozen=True, slots=True)
class Token:
    """Represents a token with positional metadata."""

    type: TokenType
    lexeme: str
    line: int
    column: int

    def __repr__(self) -> str:  # pragma: no cover - used for debugging
        return f"Token({self.type.name}, {self.lexeme!r}, {self.line}:{self.column})"


class LexerError(ValueError):
    """Raised when the lexer encounters an invalid character sequence."""


class Lexer:
    """Converts rule file text into a stream of tokens."""

    def __init__(self, source: str):
        self.source = source
        self._length = len(source)
        self._index = 0
        self._line = 1
        self._column = 1
        self._start_line = 1
        self._start_column = 1

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while not self._is_at_end():
            self._mark_token_start()
            char = self._advance()

            if char in {" ", "\t", "\r"}:
                continue

            if char == "\n":
                tokens.append(self._make_token(TokenType.EOL, char))
                continue

            if char == "#":
                self._skip_comment()
                continue

            if char == "+":
                tokens.append(self._make_token(TokenType.AND, char))
                continue
            if char == "|":
                tokens.append(self._make_token(TokenType.OR, char))
                continue
            if char == "^":
                tokens.append(self._make_token(TokenType.XOR, char))
                continue
            if char == "!":
                tokens.append(self._make_token(TokenType.NOT, char))
                continue
            if char == "(":
                tokens.append(self._make_token(TokenType.L_PAREN, char))
                continue
            if char == ")":
                tokens.append(self._make_token(TokenType.R_PAREN, char))
                continue
            if char == "?":
                tokens.append(self._make_token(TokenType.QUERY, char))
                continue

            if char == "<":
                if self._match("="):
                    if self._match(">"):
                        tokens.append(self._make_token(TokenType.IIF, "<=>"))
                        continue
                    raise self._error("Expected '>' to complete '<=>' operator.")
                raise self._error("Unexpected '<' character.")

            if char == "=":
                if self._match(">"):
                    tokens.append(self._make_token(TokenType.IMPLIES, "=>"))
                else:
                    tokens.append(self._make_token(TokenType.EQUAL, char))
                continue

            if char.isalpha():
                tokens.append(self._make_token(TokenType.IDENT, char))
                continue

            raise self._error(f"Unsupported character '{char}'.")

        tokens.append(Token(TokenType.EOF, "", self._line, self._column))
        return tokens

    def _skip_comment(self) -> None:
        """Consume characters until the end of line or file."""
        while not self._is_at_end() and self._peek() != "\n":
            self._advance()

    def _mark_token_start(self) -> None:
        self._start_line = self._line
        self._start_column = self._column

    def _make_token(self, token_type: TokenType, lexeme: str) -> Token:
        return Token(token_type, lexeme, self._start_line, self._start_column)

    def _is_at_end(self) -> bool:
        return self._index >= self._length

    def _advance(self) -> str:
        char = self.source[self._index]
        self._index += 1
        if char == "\n":
            self._line += 1
            self._column = 1
        else:
            self._column += 1
        return char

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self._index]

    def _match(self, expected: str) -> bool:
        if self._is_at_end():
            return False
        if self.source[self._index] != expected:
            return False
        self._advance()
        return True

    def _error(self, message: str) -> LexerError:
        location = f"(line {self._start_line}, column {self._start_column})"
        return LexerError(f"{message} {location}")


def lex(source: str) -> List[Token]:
    """Convenience function to tokenize the provided source."""
    return Lexer(source).tokenize()


__all__ = ["Lexer", "LexerError", "Token", "TokenType", "lex"]
