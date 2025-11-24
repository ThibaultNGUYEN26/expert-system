from __future__ import annotations

from typing import TYPE_CHECKING

import src.exec as exec_module

Condition = exec_module.Condition
FactCondition = exec_module.FactCondition
NotCondition = exec_module.NotCondition
AndCondition = exec_module.AndCondition
OrCondition = exec_module.OrCondition
XorCondition = exec_module.XorCondition

from .status import Status

if TYPE_CHECKING:
    from .exec_context import ExecContext


def eval_condition(ctx: "ExecContext", cond: Condition) -> Status:
    """
    Evaluate a Condition tree to a Status value using three-valued logic.

    - For FactCondition, ask the solver for the symbol's truth value.
    - For NOT / AND / OR / XOR, recurse on children with three-valued logic:
      - TRUE, FALSE, UNDETERMINED

    Three-valued logic rules:
    - NOT: TRUE->FALSE, FALSE->TRUE, UNDETERMINED->UNDETERMINED
    - AND: TRUE if both TRUE, FALSE if any FALSE, else UNDETERMINED
    - OR: TRUE if any TRUE, FALSE if both FALSE, else UNDETERMINED
    - XOR: TRUE if exactly one TRUE, FALSE if both same, else UNDETERMINED
    """
    # Local import to avoid circular dependency: solve_symbol() also uses eval_condition()
    from .solve import solve_symbol

    # SYMBOL / atomic fact: delegate to the solver
    if isinstance(cond, FactCondition):
        return solve_symbol(ctx, cond.symbol)

    # NOT
    if isinstance(cond, NotCondition):
        status = eval_condition(ctx, cond.condition)
        if status is Status.TRUE:
            return Status.FALSE
        elif status is Status.FALSE:
            return Status.TRUE
        else:  # UNDETERMINED
            return Status.UNDETERMINED

    # AND
    if isinstance(cond, AndCondition):
        left = eval_condition(ctx, cond.left)
        right = eval_condition(ctx, cond.right)

        # FALSE if either is FALSE
        if left is Status.FALSE or right is Status.FALSE:
            return Status.FALSE
        # TRUE only if both are TRUE
        elif left is Status.TRUE and right is Status.TRUE:
            return Status.TRUE
        # Otherwise UNDETERMINED
        else:
            return Status.UNDETERMINED

    # OR
    if isinstance(cond, OrCondition):
        left = eval_condition(ctx, cond.left)
        right = eval_condition(ctx, cond.right)

        # TRUE if either is TRUE
        if left is Status.TRUE or right is Status.TRUE:
            return Status.TRUE
        # FALSE only if both are FALSE
        elif left is Status.FALSE and right is Status.FALSE:
            return Status.FALSE
        # Otherwise UNDETERMINED
        else:
            return Status.UNDETERMINED

    # XOR
    if isinstance(cond, XorCondition):
        left = eval_condition(ctx, cond.left)
        right = eval_condition(ctx, cond.right)

        # If either is UNDETERMINED, result is UNDETERMINED
        if left is Status.UNDETERMINED or right is Status.UNDETERMINED:
            return Status.UNDETERMINED
        # TRUE if exactly one is TRUE
        elif (left is Status.TRUE and right is Status.FALSE) or (left is Status.FALSE and right is Status.TRUE):
            return Status.TRUE
        # FALSE if both are same (both TRUE or both FALSE)
        else:
            return Status.FALSE

    # If you ever add new Condition subclasses and forget to handle them here
    raise TypeError(f"Unsupported condition type in eval_condition: {type(cond).__name__}")
