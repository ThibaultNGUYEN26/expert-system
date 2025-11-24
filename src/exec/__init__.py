from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence, Set

class Condition:
    """Base class that stores the textual representation of a condition."""

    rule_format: str | None = None

    def __str__(self) -> str:
        return self.rule_format or self.__class__.__name__


@dataclass(slots=True)
class FactCondition(Condition):
    """Represents a single fact such as 'A'."""

    symbol: str
    rule_format: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.symbol = self.symbol.strip().upper()
        self.rule_format = self.symbol


@dataclass(slots=True)
class NotCondition(Condition):
    """Negates another condition."""

    condition: Condition
    rule_format: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        label = getattr(self.condition, "rule_format", str(self.condition))
        self.rule_format = f"!{label}"


@dataclass(slots=True)
class BinaryCondition(Condition):
    """Common logic for the AND/OR/XOR conditions."""

    left: Condition
    right: Condition
    operator: str = field(init=False, default="?")
    rule_format: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        left_label = getattr(self.left, "rule_format", str(self.left))
        right_label = getattr(self.right, "rule_format", str(self.right))
        self.rule_format = f"({left_label} {self.operator} {right_label})"


class AndCondition(BinaryCondition):
    operator = "+"


class OrCondition(BinaryCondition):
    operator = "|"


class XorCondition(BinaryCondition):
    operator = "^"


@dataclass(slots=True)
class RuleCondition:
    """Represents a full rule with a left-hand condition and conclusions."""

    raw: str
    requirement: Condition
    conclusions: Sequence[Condition]

    def __str__(self) -> str:
        return self.raw


@dataclass(slots=True)
class QueryCondition:
    """Represents an input query like '?A'."""

    label: str
    expression: Condition


@dataclass(slots=True)
class Program:
    """
    High-level representation of the parsed file:

    - rules: all the 'A + B => C' rules
    - facts: initial true symbols from the '=ABCD' line
    - queries: all '?A', '?B', ... we need to evaluate
    """
    rules: List[RuleCondition]
    facts: Set[str]
    queries: List[QueryCondition]


__all__ = [
    "Condition",
    "FactCondition",
    "NotCondition",
    "AndCondition",
    "OrCondition",
    "XorCondition",
    "RuleCondition",
    "QueryCondition",
    "Program"
]
