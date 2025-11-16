from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from src.core import (
    AndCondition,
    Condition,
    FactCondition,
    NotCondition,
    OrCondition,
    QueryCondition,
    RuleCondition,
    XorCondition,
)

from .lexer import ConfigSections, normalize_expression, tokenize_expression


def build_context(fact_lines: Sequence[str]) -> Dict[str, bool]:
    """Initialise the fact context from provided fact declarations."""
    context: Dict[str, bool] = {}
    for line in fact_lines:
        if not line:
            continue

        if line.startswith("="):
            negate = False
            for char in line[1:]:
                if char == "!":
                    negate = True
                    continue
                if char.isalpha():
                    context[char.upper()] = not negate
                    negate = False
            continue

        condition = build_fact_condition(line)
        if isinstance(condition, FactCondition):
            context[condition.symbol] = True
        elif isinstance(condition, NotCondition) and isinstance(condition.condition, FactCondition):
            context[condition.condition.symbol] = False

    return context


class ExpressionParser:
    """Simple recursive descent parser for the boolean expressions."""

    def __init__(self, text: str):
        self.text = text
        self.tokens = tokenize_expression(text)
        self.index = 0

    def parse(self) -> Condition:
        expression = self._parse_xor()
        if self._peek() is not None:
            raise ValueError(f"Unexpected token '{self._peek()}' in expression '{self.text}'")
        return expression

    def _peek(self) -> Optional[str]:
        if self.index < len(self.tokens):
            return self.tokens[self.index]
        return None

    def _consume(self, expected: Optional[str] = None) -> Optional[str]:
        token = self._peek()
        if token is None:
            return None
        if expected and token != expected:
            raise ValueError(f"Expected '{expected}' but found '{token}' in expression '{self.text}'")
        self.index += 1
        return token

    def _parse_xor(self) -> Condition:
        expression = self._parse_or()
        while self._peek() == "^":
            self._consume("^")
            right = self._parse_or()
            expression = XorCondition(expression, right)
        return expression

    def _parse_or(self) -> Condition:
        expression = self._parse_and()
        while self._peek() == "|":
            self._consume("|")
            right = self._parse_and()
            expression = OrCondition(expression, right)
        return expression

    def _parse_and(self) -> Condition:
        expression = self._parse_unary()
        while self._peek() == "+":
            self._consume("+")
            right = self._parse_unary()
            expression = AndCondition(expression, right)
        return expression

    def _parse_unary(self) -> Condition:
        token = self._peek()
        if token == "!":
            self._consume("!")
            condition = self._parse_unary()
            return NotCondition(condition)

        if token == "(":
            self._consume("(")
            expression = self._parse_xor()
            self._consume(")")
            return expression

        if token and token.isalpha():
            symbol = self._consume()
            assert symbol is not None
            return FactCondition(symbol)

        raise ValueError(f"Unexpected token '{token}' in expression '{self.text}'")


def parse_expression(expression: str) -> Optional[Condition]:
    normalized = normalize_expression(expression)
    if not normalized:
        return None

    parser = ExpressionParser(normalized)
    condition = parser.parse()
    condition.rule_format = normalized
    return condition


def build_fact_condition(token: str) -> Optional[Condition]:
    token = token.strip()
    if not token:
        return None

    negate = token.startswith("!")
    symbol = token[1:] if negate else token
    symbol = symbol.strip().upper()
    if not symbol:
        return None

    base = FactCondition(symbol)
    return NotCondition(base) if negate else base


def build_rule_condition(rule_line: str) -> Optional[RuleCondition]:
    if "=>" not in rule_line:
        return None

    lhs_raw, rhs_raw = rule_line.split("=>", 1)
    lhs_condition = parse_expression(lhs_raw)
    if lhs_condition is None:
        return None

    rhs_tokens = [token for token in rhs_raw.replace("+", " ").split() if token]
    rhs_conditions = [build_fact_condition(token) for token in rhs_tokens]
    rhs_conditions = [condition for condition in rhs_conditions if condition]

    return RuleCondition(rule_line, lhs_condition, rhs_conditions)


def build_query_condition(query_line: str) -> Optional[QueryCondition]:
    body = query_line[1:] if query_line.startswith("?") else query_line
    expression = parse_expression(body)
    if not expression:
        return None

    label = query_line if query_line.startswith("?") else f"?{body.strip()}"
    return QueryCondition(label, expression)


def build_conditions(sections: ConfigSections) -> List[Condition]:
    conditions: List[Condition] = []

    for rule_line in sections["rules"]:
        condition = build_rule_condition(rule_line)
        if condition:
            conditions.append(condition)

    for query_line in sections["queries"]:
        condition = build_query_condition(query_line)
        if condition:
            conditions.append(condition)

    return conditions


__all__ = [
    "build_conditions",
    "build_context",
    "build_fact_condition",
    "build_query_condition",
    "build_rule_condition",
    "parse_expression",
]
