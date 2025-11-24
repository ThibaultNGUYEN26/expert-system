from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Set

from .status import Status
from .eval_condition import eval_condition

if TYPE_CHECKING:
    from .exec_context import ExecContext
    import src.exec as exec_module


def _extract_fact_symbols(cond: "exec_module.Condition") -> Set[str]:
    """Extract all FactCondition symbols from a Condition tree."""
    import src.exec as exec_module
    if isinstance(cond, exec_module.FactCondition):
        return {cond.symbol}
    elif isinstance(cond, (exec_module.AndCondition, exec_module.OrCondition, exec_module.XorCondition)):
        return _extract_fact_symbols(cond.left) | _extract_fact_symbols(cond.right)
    elif isinstance(cond, exec_module.NotCondition):
        return _extract_fact_symbols(cond.condition)
    return set()


def solve_symbol(ctx: "ExecContext", symbol: str) -> Status:
    """
    Decide if `symbol` is true, false, or undetermined given the rules and facts in `ctx`.

    Backward chaining:
      - use memoised status to avoid recomputation and cycles
      - if it's a base fact, return its status (TRUE/FALSE)
      - otherwise, try all rules that conclude this symbol
      - return UNDETERMINED if the ruleset is ambiguous
    """
    # 1) Check memoised status
    status = ctx.get_status(symbol)

    if status is Status.TRUE:
        return Status.TRUE
    if status is Status.FALSE:
        return Status.FALSE
    if status is Status.UNDETERMINED:
        return Status.UNDETERMINED
    if status is Status.IN_PROGRESS:
        # We came back to the same symbol while trying to prove it -> cycle
        # Treat as undetermined since we can't resolve it
        return Status.UNDETERMINED

    # 2) Base case: initial facts (both positive and negative)
    if ctx.is_fact_true(symbol):
        ctx.set_status(symbol, Status.TRUE)
        return Status.TRUE
    if ctx.is_fact_false(symbol):
        ctx.set_status(symbol, Status.FALSE)
        return Status.FALSE

    # 3) Mark as currently being processed (for cycle detection)
    ctx.set_status(symbol, Status.IN_PROGRESS)

    # 4) Try all rules that can conclude this symbol
    rules = ctx.rules_by_conclusion.get(symbol, [])
    for rule in rules:
        # rule.condition is a Condition tree (AndCondition, NotCondition, etc.)
        cond_status = eval_condition(ctx, rule.condition)
        if cond_status is Status.TRUE:
            # The rule's condition is satisfied
            import src.exec as exec_module

            # Check conclusion type and handle accordingly
            if isinstance(rule.conclusion, (exec_module.OrCondition, exec_module.XorCondition)):
                # Ambiguous conclusion: mark all symbols in the conclusion as UNDETERMINED
                conclusion_symbols = _extract_fact_symbols(rule.conclusion)
                for sym in conclusion_symbols:
                    if ctx.get_status(sym) == Status.UNKNOWN or ctx.get_status(sym) == Status.IN_PROGRESS:
                        ctx.set_status(sym, Status.UNDETERMINED)
                # If we're solving for one of these symbols, return UNDETERMINED
                if symbol in conclusion_symbols:
                    return Status.UNDETERMINED
            elif isinstance(rule.conclusion, exec_module.AndCondition):
                # AND conclusion: all symbols in the conclusion become TRUE
                conclusion_symbols = _extract_fact_symbols(rule.conclusion)
                for sym in conclusion_symbols:
                    if ctx.get_status(sym) in (Status.UNKNOWN, Status.IN_PROGRESS):
                        ctx.set_status(sym, Status.TRUE)
                # If we're solving for one of these symbols, return TRUE
                if symbol in conclusion_symbols:
                    return Status.TRUE
            elif isinstance(rule.conclusion, exec_module.FactCondition):
                # Simple fact conclusion
                if rule.conclusion.symbol == symbol:
                    ctx.set_status(symbol, Status.TRUE)
                    return Status.TRUE
            elif isinstance(rule.conclusion, exec_module.NotCondition):
                # NOT conclusion: negate the inner condition
                # This is unusual but we can handle it
                inner_symbols = _extract_fact_symbols(rule.conclusion.condition)
                if symbol in inner_symbols:
                    # If the conclusion is !A and we're querying A, A should be FALSE
                    ctx.set_status(symbol, Status.FALSE)
                    return Status.FALSE

        elif cond_status is Status.UNDETERMINED:
            # If any rule's condition is undetermined, the conclusion is undetermined
            ctx.set_status(symbol, Status.UNDETERMINED)
            return Status.UNDETERMINED

    # 5) No rule could prove this symbol
    ctx.set_status(symbol, Status.FALSE)
    return Status.FALSE


def run_queries(ctx: "ExecContext") -> Dict[str, Status]:
    """
    Evaluate all queries from the Program and return a dict: label -> Status.
    """
    results: Dict[str, Status] = {}
    for query in ctx.program.queries:
        # query is a string symbol name, e.g. "A"
        res = solve_symbol(ctx, query)
        results[query] = res
    return results
