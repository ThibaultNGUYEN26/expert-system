from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Set

from .status import Status
from .eval_condition import eval_condition
from .format_condition import format_condition

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


def solve_symbol(ctx: "ExecContext", symbol: str, depth: int = 0) -> Status:
    """
    Decide if `symbol` is true, false, or undetermined given the rules and facts in `ctx`.

    Backward chaining:
      - use memoised status to avoid recomputation and cycles
      - if it's a base fact, return its status (TRUE/FALSE)
      - otherwise, try all rules that conclude this symbol
      - return UNDETERMINED if the ruleset is ambiguous

    Args:
        ctx: Execution context
        symbol: Symbol to solve
        depth: Recursion depth for indentation
    """
    # 1) Check memoised status
    status = ctx.get_status(symbol)

    if status is Status.TRUE:
        if depth > 0:
            ctx.log_reasoning(f"\033[92m✓ {symbol} is TRUE (already determined)\033[0m", depth)
        return Status.TRUE
    if status is Status.FALSE:
        if depth > 0:
            ctx.log_reasoning(f"\033[91m✗ {symbol} is FALSE (already determined)\033[0m", depth)
        return Status.FALSE
    if status is Status.UNDETERMINED:
        if depth > 0:
            ctx.log_reasoning(f"\033[93m⚠ {symbol} is UNDETERMINED (already determined)\033[0m", depth)
        return Status.UNDETERMINED
    if status is Status.IN_PROGRESS:
        # We came back to the same symbol while trying to prove it -> cycle
        # Treat as undetermined since we can't resolve it
        return Status.UNDETERMINED

    # 2) Base case: initial facts (both positive and negative)
    if ctx.is_fact_true(symbol):
        ctx.set_status(symbol, Status.TRUE)
        ctx.log_reasoning(f"\033[92m✓ {symbol} is TRUE (given as fact)\033[0m", depth)
        return Status.TRUE
    if ctx.is_fact_false(symbol):
        ctx.set_status(symbol, Status.FALSE)
        ctx.log_reasoning(f"\033[91m✗ {symbol} is FALSE (given as fact)\033[0m", depth)
        return Status.FALSE

    # Log that we're evaluating this symbol
    if depth > 0:
        ctx.log_reasoning(f"\033[94m→ Evaluating {symbol}...\033[0m", depth)

    # 3) Mark as currently being processed (for cycle detection)
    ctx.set_status(symbol, Status.IN_PROGRESS)

    # 4) Try all rules that can conclude this symbol
    rules = ctx.rules_by_conclusion.get(symbol, [])
    for rule in rules:
        # rule.condition is a Condition tree (AndCondition, NotCondition, etc.)
        condition_str = format_condition(rule.condition)
        conclusion_str = format_condition(rule.conclusion)

        ctx.log_reasoning(f"\033[96mChecking rule: {condition_str} => {conclusion_str}\033[0m", depth)

        cond_status = eval_condition(ctx, rule.condition, depth + 1)

        if cond_status is Status.TRUE:
            # The rule's condition is satisfied
            import src.exec as exec_module

            ctx.log_reasoning(f"\033[92m✓ Condition {condition_str} is TRUE\033[0m", depth + 1)

            # Check conclusion type and handle accordingly
            if isinstance(rule.conclusion, (exec_module.OrCondition, exec_module.XorCondition)):
                # Ambiguous conclusion: mark all symbols in the conclusion as UNDETERMINED
                conclusion_symbols = _extract_fact_symbols(rule.conclusion)
                ctx.log_reasoning(f"\033[93m⚠ Conclusion is ambiguous ({conclusion_str}), marking {', '.join(sorted(conclusion_symbols))} as UNDETERMINED\033[0m", depth + 1)
                for sym in conclusion_symbols:
                    if ctx.get_status(sym) == Status.UNKNOWN or ctx.get_status(sym) == Status.IN_PROGRESS:
                        ctx.set_status(sym, Status.UNDETERMINED)
                # If we're solving for one of these symbols, return UNDETERMINED
                if symbol in conclusion_symbols:
                    return Status.UNDETERMINED
            elif isinstance(rule.conclusion, exec_module.AndCondition):
                # AND conclusion: all symbols in the conclusion become TRUE
                conclusion_symbols = _extract_fact_symbols(rule.conclusion)
                ctx.log_reasoning(f"\033[92m✓ Setting all symbols in conclusion ({conclusion_str}) to TRUE: {', '.join(sorted(conclusion_symbols))}\033[0m", depth + 1)
                for sym in conclusion_symbols:
                    if ctx.get_status(sym) in (Status.UNKNOWN, Status.IN_PROGRESS):
                        ctx.set_status(sym, Status.TRUE)
                # If we're solving for one of these symbols, return TRUE
                if symbol in conclusion_symbols:
                    return Status.TRUE
            elif isinstance(rule.conclusion, exec_module.FactCondition):
                # Simple fact conclusion
                if rule.conclusion.symbol == symbol:
                    # Check for contradiction with initial facts
                    if ctx.is_fact_false(symbol):
                        contradiction_msg = f"CONTRADICTION: Rule '{condition_str} => {conclusion_str}' tries to set {symbol}=TRUE, but {symbol}=FALSE is declared as initial fact"
                        ctx.add_contradiction(contradiction_msg)
                        ctx.log_reasoning(f"\033[91m⚠ {contradiction_msg}\033[0m", depth + 1)
                    ctx.log_reasoning(f"\033[92m✓ {symbol} is TRUE (from rule)\033[0m", depth + 1)
                    ctx.set_status(symbol, Status.TRUE)
                    return Status.TRUE
            elif isinstance(rule.conclusion, exec_module.NotCondition):
                # NOT conclusion: negate the inner condition
                # This is unusual but we can handle it
                inner_symbols = _extract_fact_symbols(rule.conclusion.condition)
                if symbol in inner_symbols:
                    # If the conclusion is !A and we're querying A, A should be FALSE
                    # Check for contradiction with initial facts or previously determined value
                    if ctx.is_fact_true(symbol):
                        contradiction_msg = f"CONTRADICTION: Rule '{condition_str} => {conclusion_str}' tries to set {symbol}=FALSE, but {symbol}=TRUE is declared as initial fact"
                        ctx.add_contradiction(contradiction_msg)
                        ctx.log_reasoning(f"\033[91m⚠ {contradiction_msg}\033[0m", depth + 1)
                    elif ctx.get_status(symbol) == Status.TRUE:
                        contradiction_msg = f"CONTRADICTION: Rule '{condition_str} => {conclusion_str}' tries to set {symbol}=FALSE, but {symbol} was already determined to be TRUE (circular dependency)"
                        ctx.add_contradiction(contradiction_msg)
                        ctx.log_reasoning(f"\033[91m⚠ {contradiction_msg}\033[0m", depth + 1)
                    ctx.log_reasoning(f"\033[91m✗ {symbol} is FALSE (negated in conclusion)\033[0m", depth + 1)
                    ctx.set_status(symbol, Status.FALSE)
                    return Status.FALSE

        elif cond_status is Status.UNDETERMINED:
            # If any rule's condition is undetermined, the conclusion is undetermined
            ctx.log_reasoning(f"\033[93m⚠ Condition {condition_str} is UNDETERMINED\033[0m", depth + 1)
            ctx.set_status(symbol, Status.UNDETERMINED)
            return Status.UNDETERMINED
        else:
            # Condition is FALSE, rule doesn't apply
            ctx.log_reasoning(f"\033[91m✗ Condition {condition_str} is FALSE, rule doesn't apply\033[0m", depth + 1)

    # 5) No rule could prove this symbol
    ctx.set_status(symbol, Status.FALSE)
    ctx.log_reasoning(f"\033[91m✗ {symbol} is FALSE (no rule could prove it)\033[0m", depth)
    return Status.FALSE


def run_queries(ctx: "ExecContext") -> Dict[str, Status]:
    """
    Evaluate all queries from the Program and return a dict: label -> Status.
    """
    # First, validate that no rules contradict the initial facts
    _validate_no_contradictions(ctx)

    results: Dict[str, Status] = {}
    for query in ctx.program.queries:
        # query is a string symbol name, e.g. "A"
        ctx.log_reasoning(f"\033[95m{'=' * 60}\033[0m")
        ctx.log_reasoning(f"\033[95mQuery: {query}\033[0m")
        ctx.log_reasoning(f"\033[95m{'=' * 60}\033[0m")
        res = solve_symbol(ctx, query)
        results[query] = res

        # Log final result for this query
        if res is Status.TRUE:
            status_str = f"\033[92m✓ {res.name}\033[0m"
        elif res is Status.FALSE:
            status_str = f"\033[91m✗ {res.name}\033[0m"
        elif res is Status.UNDETERMINED:
            status_str = f"\033[93m⚠ {res.name}\033[0m"
        else:
            status_str = res.name
        ctx.log_reasoning(f"\n\033[1mFinal result: {query} is {status_str}\033[0m\n")
    return results


def _validate_no_contradictions(ctx: "ExecContext") -> None:
    """
    Check if any rules would contradict the initial facts.
    This is a forward pass to detect contradictions before solving queries.
    """
    import src.exec as exec_module

    for rule in ctx.program.rules:
        # Evaluate the condition to see if this rule would fire
        condition_status = eval_condition(ctx, rule.condition, depth=0)

        if condition_status is Status.TRUE:
            # This rule would fire - check if its conclusion contradicts facts
            condition_str = format_condition(rule.condition)
            conclusion_str = format_condition(rule.conclusion)

            # Check conclusion for contradictions
            def check_contradiction(conclusion: "exec_module.Condition") -> None:
                if isinstance(conclusion, exec_module.FactCondition):
                    # Rule concludes symbol=TRUE
                    if ctx.is_fact_false(conclusion.symbol):
                        msg = f"CONTRADICTION: Rule '{condition_str} => {conclusion_str}' concludes {conclusion.symbol}=TRUE, but {conclusion.symbol}=FALSE is declared as fact"
                        ctx.add_contradiction(msg)
                elif isinstance(conclusion, exec_module.NotCondition):
                    # Rule concludes symbol=FALSE
                    inner_symbols = _extract_fact_symbols(conclusion.condition)
                    for sym in inner_symbols:
                        if ctx.is_fact_true(sym):
                            msg = f"CONTRADICTION: Rule '{condition_str} => {conclusion_str}' concludes {sym}=FALSE, but {sym}=TRUE is declared as fact"
                            ctx.add_contradiction(msg)
                elif isinstance(conclusion, exec_module.AndCondition):
                    # All symbols in AND conclusion become TRUE
                    check_contradiction(conclusion.left)
                    check_contradiction(conclusion.right)
                elif isinstance(conclusion, (exec_module.OrCondition, exec_module.XorCondition)):
                    # These create ambiguity, not contradictions with facts
                    # But we can still check if any branch would contradict
                    pass

            check_contradiction(rule.conclusion)
