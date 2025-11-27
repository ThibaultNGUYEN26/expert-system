"""Biconditional (if and only if) operator support for the expert system.

This module handles the <=> (biconditional/if-and-only-if) operator, which creates
bidirectional implications between expressions.

The biconditional A <=> B is logically equivalent to (A => B) AND (B => A),
meaning both sides must have the same truth value.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from src.parsing.parser import Rule, Condition


def expand_biconditional(condition: "Condition", conclusion: "Condition") -> List["Rule"]:
    """
    Expand a biconditional rule (A <=> B) into two implication rules.

    A biconditional statement A <=> B means:
    - If A is true, then B is true (A => B)
    - If B is true, then A is true (B => A)

    Args:
        condition: Left side of the biconditional
        conclusion: Right side of the biconditional

    Returns:
        List of two Rule objects representing the bidirectional implication

    Example:
        Input: A <=> B
        Output: [A => B, B => A]

        Input: (A + B) <=> C
        Output: [(A + B) => C, C => (A + B)]
    """
    from src.parsing.parser import Rule

    # Create the two rules
    # Rule 1: condition => conclusion (forward direction)
    rule_forward = Rule(condition=condition, conclusion=conclusion)

    # Rule 2: conclusion => condition (reverse direction)
    rule_reverse = Rule(condition=conclusion, conclusion=condition)

    return [rule_forward, rule_reverse]


def is_biconditional_satisfied(left_value: bool, right_value: bool) -> bool:
    """
    Check if a biconditional is satisfied.

    A biconditional is true when both sides have the same truth value:
    - Both true: satisfied
    - Both false: satisfied
    - One true, one false: not satisfied

    Args:
        left_value: Truth value of the left side
        right_value: Truth value of the right side

    Returns:
        True if the biconditional is satisfied, False otherwise

    Examples:
        >>> is_biconditional_satisfied(True, True)
        True
        >>> is_biconditional_satisfied(False, False)
        True
        >>> is_biconditional_satisfied(True, False)
        False
        >>> is_biconditional_satisfied(False, True)
        False
    """
    return left_value == right_value


def explain_biconditional(condition_str: str, conclusion_str: str) -> str:
    """
    Generate a human-readable explanation of a biconditional rule.

    Args:
        condition_str: String representation of the left side
        conclusion_str: String representation of the right side

    Returns:
        Explanation text

    Example:
        >>> explain_biconditional("A", "B")
        'A <=> B means: A is true if and only if B is true
         - When A is true, B must be true
         - When B is true, A must be true
         - When A is false, B must be false
         - When B is false, A must be false'
    """
    explanation = []
    explanation.append(f"{condition_str} <=> {conclusion_str} means: ")
    explanation.append(f"  {condition_str} is true if and only if {conclusion_str} is true")
    explanation.append(f"  - When {condition_str} is true, {conclusion_str} must be true")
    explanation.append(f"  - When {conclusion_str} is true, {condition_str} must be true")
    explanation.append(f"  - When {condition_str} is false, {conclusion_str} must be false")
    explanation.append(f"  - When {conclusion_str} is false, {condition_str} must be false")

    return "\n".join(explanation)


__all__ = ["expand_biconditional", "is_biconditional_satisfied", "explain_biconditional"]
