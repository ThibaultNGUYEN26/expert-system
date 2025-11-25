"""Helper to format Condition objects as readable strings."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import src.exec as exec_module


def format_condition(cond: "exec_module.Condition") -> str:
    """Convert a Condition tree to a human-readable string."""
    import src.exec as exec_module

    if isinstance(cond, exec_module.FactCondition):
        return cond.symbol
    elif isinstance(cond, exec_module.NotCondition):
        inner = format_condition(cond.condition)
        # Add parentheses if inner is complex
        if isinstance(cond.condition, (exec_module.AndCondition, exec_module.OrCondition, exec_module.XorCondition)):
            return f"!({inner})"
        return f"!{inner}"
    elif isinstance(cond, exec_module.AndCondition):
        left = format_condition(cond.left)
        right = format_condition(cond.right)
        # Add parentheses for nested OR/XOR to show precedence
        if isinstance(cond.left, (exec_module.OrCondition, exec_module.XorCondition)):
            left = f"({left})"
        if isinstance(cond.right, (exec_module.OrCondition, exec_module.XorCondition)):
            right = f"({right})"
        return f"{left} + {right}"
    elif isinstance(cond, exec_module.OrCondition):
        left = format_condition(cond.left)
        right = format_condition(cond.right)
        return f"{left} | {right}"
    elif isinstance(cond, exec_module.XorCondition):
        left = format_condition(cond.left)
        right = format_condition(cond.right)
        return f"{left} ^ {right}"
    else:
        return str(cond)
