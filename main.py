import argparse
import logging
import os

from utils.conditions import Conditions
from utils.handle_logging import ColoredFormatter
from logging import StreamHandler


logging.root.handlers.clear()
handler = StreamHandler()
handler.setFormatter(ColoredFormatter())
logging.root.addHandler(handler)
logging.root.setLevel(logging.DEBUG)


def parse_config_sections(config_data):
    sections = {"rules": [], "facts": [], "queries": []}
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


def build_context(fact_lines):
    context = {}
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


def normalize_expression(expression):
    stripped = expression.strip()
    if not stripped:
        return ""

    has_operator = any(op in stripped for op in ("+", "|", "^"))
    if not has_operator and " " in stripped:
        stripped = "+".join(part for part in stripped.split() if part)

    return stripped


class ExpressionParser:
    def __init__(self, text):
        self.text = text
        self.tokens = self._tokenize(text)
        self.index = 0

    def parse(self):
        expression = self._parse_xor()
        if self._peek() is not None:
            raise ValueError(f"Unexpected token '{self._peek()}' in expression '{self.text}'")
        return expression

    def _tokenize(self, text):
        tokens = []
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

    def _peek(self):
        if self.index < len(self.tokens):
            return self.tokens[self.index]
        return None

    def _consume(self, expected=None):
        token = self._peek()
        if token is None:
            return None
        if expected and token != expected:
            raise ValueError(f"Expected '{expected}' but found '{token}' in expression '{self.text}'")
        self.index += 1
        return token

    def _parse_xor(self):
        expression = self._parse_or()
        while self._peek() == "^":
            self._consume("^")
            right = self._parse_or()
            expression = self._combine(expression, right, "^", XorCondition)
        return expression

    def _parse_or(self):
        expression = self._parse_and()
        while self._peek() == "|":
            self._consume("|")
            right = self._parse_and()
            expression = self._combine(expression, right, "|", OrCondition)
        return expression

    def _parse_and(self):
        expression = self._parse_unary()
        while self._peek() == "+":
            self._consume("+")
            right = self._parse_unary()
            expression = self._combine(expression, right, "+", AndCondition)
        return expression

    def _parse_unary(self):
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
            return FactCondition(symbol)

        raise ValueError(f"Unexpected token '{token}' in expression '{self.text}'")

    @staticmethod
    def _combine(left, right, operator, constructor):
        condition = constructor(left, right)
        left_label = getattr(left, "rule_format", str(left))
        right_label = getattr(right, "rule_format", str(right))
        condition.rule_format = f"({left_label} {operator} {right_label})"
        return condition


def parse_expression(expression):
    normalized = normalize_expression(expression)
    if not normalized:
        return None
    parser = ExpressionParser(normalized)
    condition = parser.parse()
    condition.rule_format = normalized
    return condition


def build_fact_condition(token):
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


def build_rule_condition(rule_line):
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


def build_query_condition(query_line):
    body = query_line[1:] if query_line.startswith("?") else query_line
    expression = parse_expression(body)
    if not expression:
        return None

    label = query_line if query_line.startswith("?") else f"?{body.strip()}"
    return QueryCondition(label, expression)


def build_conditions(sections):
    conditions = []

    for rule_line in sections["rules"]:
        condition = build_rule_condition(rule_line)
        if condition:
            conditions.append(condition)

    for query_line in sections["queries"]:
        condition = build_query_condition(query_line)
        if condition:
            conditions.append(condition)

    return conditions


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the expert system.")
    parser.add_argument("config", type=str, help="Path to the configuration file")
    args = parser.parse_args()

    if not os.path.isfile(args.config):
        logging.error(f"File '{args.config}' does not exist.")
        exit(1)

    logging.info(f"Using configuration file: {args.config}")

    with open(args.config, "r", encoding="utf-8") as file:
        config_data = file.read()

    sections = parse_config_sections(config_data)
    context = build_context(sections["facts"])

    conditions = build_conditions(sections)
    if not conditions:
        logging.warning("No conditions found to evaluate.")
        exit(0)

    and_condition = Conditions.and_operation(True, False)
    logging.info(f"AND condition evaluation result: {and_condition}")

    or_condition = Conditions.or_operation(True, False)
    logging.info(f"OR condition evaluation result: {or_condition}")

    xor_condition = Conditions.xor_operation(True, False)
    logging.info(f"XOR condition evaluation result: {xor_condition}")

    not_condition = Conditions.not_operation(True)
    logging.info(f"NOT condition evaluation result: {not_condition}")
