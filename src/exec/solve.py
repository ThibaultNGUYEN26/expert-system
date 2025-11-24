from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from status import Status
from eval_condition import eval_condition

if TYPE_CHECKING:
    from exec_context import ExecContext


def solve_symbol(ctx: "ExecContext", symbol: str) -> bool:
    """
    Decide if `symbol` is true or false given the rules and facts in `ctx`.

    Backward chaining:
      - use memoised status to avoid recomputation and cycles
      - if it's a base fact, it's true
      - otherwise, try all rules that conclude this symbol
    """
    # 1) Check memoised status
    status = ctx.get_status(symbol)

    if status is Status.TRUE:
        return True
    if status is Status.FALSE:
        return False
    if status is Status.IN_PROGRESS:
        # We came back to the same symbol while trying to prove it -> cycle
        # For now we treat it as not provable.
        return False

    # 2) Base case: initial facts
    if ctx.is_fact(symbol):
        ctx.set_status(symbol, Status.TRUE)
        return True

    # 3) Mark as currently being processed (for cycle detection)
    ctx.set_status(symbol, Status.IN_PROGRESS)

    # 4) Try all rules that can conclude this symbol
    rules = ctx.rules_by_conclusion.get(symbol, [])
    for rule in rules:
        # rule.requirement is a Condition tree (AndCondition, NotCondition, etc.)
        if eval_condition(ctx, rule.requirement):
            ctx.set_status(symbol, Status.TRUE)
            return True

    # 5) No rule could prove this symbol
    ctx.set_status(symbol, Status.FALSE)
    return False


def run_queries(ctx: "ExecContext") -> Dict[str, bool]:
    """
    Evaluate all queries from the Program and return a dict: label -> bool.
    """
    results: Dict[str, bool] = {}
    for query in ctx.program.queries:
        # QueryCondition.label is the symbol name, e.g. "A"
        res = solve_symbol(ctx, query.label)
        results[query.label] = res
    return results
