from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from src.exec import (
    AndCondition,
    Condition,
    FactCondition,
    NotCondition,
    OrCondition,
    QueryCondition,
    RuleCondition,
    XorCondition,
)

from .lexer import Token, TokenType, lex
from .validator import ensure_known_operator, ensure_valid_symbol, validate_balanced_parentheses


@dataclass(slots=True)
class Rule:
    """
    Represents a single inference rule.

    Fields:
        condition (Condition): The logical condition (premises) that must be satisfied for the rule to apply.
        conclusion (Condition): The fact or set of facts that are inferred if the condition is met.
            Can be a FactCondition (single fact) or OrCondition/XorCondition for ambiguous conclusions.
        line (int): The line number in the source file where this rule was defined. Useful for error reporting.
    """

    condition: Condition
    conclusion: Condition
    line: int


@dataclass(slots=True)
class Program:
    """
    Container holding every parsed structure.

    Attributes:
        rules: List of Rule objects representing inference rules.
        facts: Dictionary mapping symbols (str) to boolean values, representing known facts.
        queries: List of symbols (str) to evaluate.
    """

    rules: List[Rule] = field(default_factory=list)
    facts: Dict[str, bool] = field(default_factory=dict)
    queries: List[str] = field(default_factory=list)


class ParserError(ValueError):
    """Raised when the parser encounters invalid syntax."""

    def __init__(self, message: str, token: Token | None = None):
        if token is not None:
            location = f" (line {token.line}, column {token.column})"
        else:
            location = ""
        super().__init__(f"{message}{location}")
        self.token = token


class Parser:
    """Recursive descent parser that consumes the lexer output."""

    def __init__(self, tokens: Sequence[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Program:
        validate_balanced_parentheses(self.tokens)
        rules: List[Rule] = []
        facts: Dict[str, bool] = {}
        queries: List[str] = []

        facts_started = False
        queries_started = False

        while not self._is_at_end():
            if self._match(TokenType.EOL):
                continue

            if self._check(TokenType.EQUAL):
                if queries_started:
                    raise self._error("Facts must be declared before queries.")
                facts_started = True
                facts.update(self._parse_fact_line())
                continue

            if self._check(TokenType.QUERY):
                queries_started = True
                queries.extend(self._parse_query_line())
                continue

            if queries_started:
                raise self._error("Unexpected content after queries.")
            if facts_started:
                raise self._error("Rules must appear before the facts declaration.")

            rules.extend(self._parse_rule())

        if not facts_started:
            raise ParserError("No facts declaration found. A facts line starting with '=' is required after all rules.")
        if not queries_started:
            raise ParserError("No queries found. A queries line starting with '?' is required after the facts declaration.")

        return Program(rules=rules, facts=facts, queries=queries)

    def _parse_fact_line(self) -> Dict[str, bool]:
        self._consume(TokenType.EQUAL, "Expected '=' at the beginning of the facts line.")
        line_facts: Dict[str, bool] = {}

        while not self._check(TokenType.EOL) and not self._check(TokenType.EOF):
            token = self._consume(TokenType.IDENT, "Expected a fact symbol.")
            symbol = ensure_valid_symbol(token.lexeme, token)
            line_facts[symbol] = True

        self._consume_line_breaks()
        if not line_facts:
            raise self._error("Facts line must contain at least one fact symbol.")
        return line_facts

    def _parse_query_line(self) -> List[str]:
        self._consume(TokenType.QUERY, "Expected '?' at the beginning of the queries line.")
        result: List[str] = []

        while not self._check(TokenType.EOL) and not self._check(TokenType.EOF):
            token = self._consume(TokenType.IDENT, "Expected a query symbol.")
            symbol = ensure_valid_symbol(token.lexeme, token)
            result.append(symbol)

        self._consume_line_breaks()
        if not result:
            raise ParserError("Query line must contain at least one query symbol.")
        return result

    def _parse_rule(self) -> List[Rule]:
        """
        Parses a rule line, handling both unidirectional ('=>') and bidirectional ('<=>') operators.

        Returns a list of Rule objects. For unidirectional rules ('=>'), the list contains a single Rule.
        For bidirectional rules ('<=>'), the list contains two Rules representing both directions:
        - A <=> B becomes: A => B and B => A

        Raises:
            ParserError: If the rule syntax is invalid or required tokens are missing.
        """
        left_expression = self._parse_expression()

        if self._match(TokenType.IMPLIES):
            operator = self._previous()
            conclusion_expr = self._parse_expression()
            self._consume_line_breaks()
            return [Rule(condition=left_expression, conclusion=conclusion_expr, line=operator.line)]

        if self._match(TokenType.IIF):
            # Biconditional: A <=> B means A => B AND B => A
            operator = self._previous()
            right_expression = self._parse_expression()
            self._consume_line_breaks()
            return [
                Rule(condition=left_expression, conclusion=right_expression, line=operator.line),
                Rule(condition=right_expression, conclusion=left_expression, line=operator.line),
            ]

        raise self._error("Expected '=>' or '<=>' after the rule condition.")

    def _parse_expression(self) -> Condition:
        """
        Parses a boolean expression consisting of fact symbols, parentheses, and logical operators
        (AND, OR, XOR, NOT). Expressions may be nested using parentheses and combined using
        the supported operators. Returns a Condition object representing the parsed expression.
        """
        return self._parse_or()

    def _parse_or(self) -> Condition:
        expression = self._parse_xor()
        while self._match(TokenType.OR):
            ensure_known_operator(self._previous())
            right = self._parse_xor()
            expression = OrCondition(expression, right)
        return expression

    def _parse_xor(self) -> Condition:
        expression = self._parse_and()
        while self._match(TokenType.XOR):
            ensure_known_operator(self._previous())
            right = self._parse_and()
            expression = XorCondition(expression, right)
        return expression

    def _parse_and(self) -> Condition:
        expression = self._parse_unary()
        while self._match(TokenType.AND):
            ensure_known_operator(self._previous())
            right = self._parse_unary()
            expression = AndCondition(expression, right)
        return expression

    def _parse_unary(self) -> Condition:
        if self._match(TokenType.NOT):
            ensure_known_operator(self._previous())
            operand = self._parse_unary()
            return NotCondition(operand)
        return self._parse_primary()

    def _parse_primary(self) -> Condition:
        if self._match(TokenType.IDENT):
            token = self._previous()
            symbol = ensure_valid_symbol(token.lexeme, token)
            return FactCondition(symbol)

        if self._match(TokenType.L_PAREN):
            expression = self._parse_expression()
            self._consume(TokenType.R_PAREN, "Expected ')' after expression.")
            return expression

        raise self._error("Expected a fact symbol or '('.")

    def _consume_line_breaks(self) -> None:
        while self._match(TokenType.EOL):
            continue

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        raise self._error(message)

    def _match(self, token_type: TokenType) -> bool:
        if self._check(token_type):
            self._advance()
            return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == token_type

    def _advance(self) -> Token:
        token = self.tokens[self.current]
        if not self._is_at_end():
            self.current += 1
        return token

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _error(self, message: str) -> ParserError:
        token = self._peek() if not self._is_at_end() else None
        return ParserError(message, token=token)


def parse_program(source: str) -> Program:
    """Parse the contents of a rule file and return a structured program."""
    tokens = lex(source)
    parser = Parser(tokens)
    return parser.parse()


__all__ = ["Parser", "ParserError", "Program", "Rule", "parse_program"]
