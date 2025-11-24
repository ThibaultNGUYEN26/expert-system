from __future__ import annotations

from typing import TYPE_CHECKING

from __init__ import (
    Condition,
    FactCondition,
    NotCondition,
    AndCondition,
    OrCondition,
    XorCondition,
)

if TYPE_CHECKING:
    from exec_context import ExecContext


def eval_condition(ctx: "ExecContext", cond: Condition) -> bool:
    """
    Evaluate a Condition tree to a boolean value.

    - For FactCondition, ask the solver for the symbol's truth value.
    - For NOT / AND / OR / XOR, recurse on children.
    """
    # Local import to avoid circular dependency: solve_symbol() also uses eval_condition()
    from solve import solve_symbol

    # SYMBOL / atomic fact: delegate to the solver
    if isinstance(cond, FactCondition):
        return solve_symbol(ctx, cond.symbol)

    # NOT
    if isinstance(cond, NotCondition):
        return not eval_condition(ctx, cond.condition)

    # AND
    if isinstance(cond, AndCondition):
        return eval_condition(ctx, cond.left) and eval_condition(ctx, cond.right)

    # OR
    if isinstance(cond, OrCondition):
        return eval_condition(ctx, cond.left) or eval_condition(ctx, cond.right)

    # XOR
    if isinstance(cond, XorCondition):
        return eval_condition(ctx, cond.left) != eval_condition(ctx, cond.right)

    # If you ever add new Condition subclasses and forget to handle them here
    raise TypeError(f"Unsupported condition type in eval_condition: {type(cond).__name__}")
