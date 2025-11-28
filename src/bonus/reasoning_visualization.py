"""Reasoning visualization module for the expert system.

Provides human-readable explanations of how the system arrived at conclusions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Dict, Set
from dataclasses import dataclass

if TYPE_CHECKING:
    from src.parsing.parser import Program, Rule
    from src.exec import Condition
    from src.exec.status import Status
    from src.exec.exec_context import ExecContext

from src.utils.program_logging import Colors


@dataclass
class ReasoningStep:
    """Represents a single step in the reasoning process."""
    symbol: str
    status: str
    reason: str
    rule_used: str | None = None
    dependencies: List[str] | None = None


class ReasoningVisualizer:
    """Generates human-readable explanations for query results."""

    def __init__(self, ctx: "ExecContext", program: "Program"):
        self.ctx = ctx
        self.program = program
        self.explanations: List[str] = []

    def explain_query(self, symbol: str, result: "Status") -> str:
        """
        Generate a natural language explanation for a query result.

        Args:
            symbol: The queried symbol
            result: The result status (TRUE/FALSE/UNDETERMINED)

        Returns:
            Human-readable explanation string
        """
        from src.exec.status import Status

        explanation_lines = []

        # Header
        explanation_lines.append(f"\n{'=' * 70}")
        explanation_lines.append(f"REASONING FOR: {symbol}")
        explanation_lines.append(f"{'=' * 70}\n")

        if result == Status.TRUE:
            explanation = self._explain_true(symbol)
        elif result == Status.FALSE:
            explanation = self._explain_false(symbol)
        else:  # UNDETERMINED
            explanation = self._explain_undetermined(symbol)

        explanation_lines.extend(explanation)
        explanation_lines.append(f"\nCONCLUSION: {symbol} is {result.name}\n")
        explanation_lines.append("=" * 70)

        return "\n".join(explanation_lines)

    def _explain_true(self, symbol: str) -> List[str]:
        """Explain why a symbol is TRUE."""
        explanation = []

        # Check if it's a direct fact
        if self.ctx.is_fact_true(symbol):
            explanation.append(f"We know that {symbol} is true (given as initial fact).")
            return explanation

        # Find the rule that proved it
        rules = self.ctx.rules_by_conclusion.get(symbol, [])
        for rule in rules:
            from src.exec.eval_condition import eval_condition
            from src.exec.status import Status

            # Check if this rule fired
            condition_status = eval_condition(self.ctx, rule.condition, depth=0)
            if condition_status == Status.TRUE:
                explanation.append(self._explain_rule_firing(symbol, rule))
                break

        return explanation

    def _explain_false(self, symbol: str) -> List[str]:
        """Explain why a symbol is FALSE."""
        explanation = []

        # Check if it's a direct fact
        if self.ctx.is_fact_false(symbol):
            explanation.append(f"We know that {symbol} is false (given as initial fact).")
            return explanation

        # Check if negated by a rule
        rules = self.ctx.rules_by_conclusion.get(symbol, [])
        negated_by_rule = False

        for rule in rules:
            from src.exec import NotCondition
            if isinstance(rule.conclusion, NotCondition):
                from src.exec.eval_condition import eval_condition
                from src.exec.status import Status

                condition_status = eval_condition(self.ctx, rule.condition, depth=0)
                if condition_status == Status.TRUE:
                    explanation.append(self._explain_negation_rule(symbol, rule))
                    negated_by_rule = True
                    break

        if not negated_by_rule:
            # Check if there are rules that could conclude this symbol, but their conditions aren't met
            rules_for_symbol = self.ctx.rules_by_conclusion.get(symbol, [])
            if rules_for_symbol:
                explanation.append(f"We cannot prove that {symbol} is true.")
                explanation.append(f"There are rules that conclude {symbol}, but none of their conditions are satisfied:")
                explanation.append("")

                for rule in rules_for_symbol:
                    from src.exec.format_condition import format_condition
                    from src.exec.eval_condition import eval_condition
                    from src.exec.status import Status

                    condition_str = format_condition(rule.condition)
                    conclusion_str = format_condition(rule.conclusion)
                    condition_status = eval_condition(self.ctx, rule.condition, depth=0)

                    explanation.append(f"  Rule: {condition_str} => {conclusion_str}")
                    if condition_status == Status.FALSE:
                        # First show what's needed
                        explanation.append(f"    Requirements to make {symbol} true:")
                        requirements = self._collect_requirements(rule.condition, indent=6)
                        explanation.extend(requirements)
                        explanation.append("")

                        # Then show why it fails
                        explanation.append(f"    Why the condition is FALSE:")
                        why_false = self._explain_why_condition_false_detailed(rule.condition, indent=6)
                        explanation.extend(why_false)
                    elif condition_status == Status.UNDETERMINED:
                        explanation.append(f"    Condition is UNDETERMINED")
                    else:
                        explanation.append(f"    Condition status: {condition_status.name}")
                    explanation.append("")

                explanation.append(f"Therefore, {symbol} is false (closed-world assumption).")
            else:
                explanation.append(f"We cannot prove that {symbol} is true.")
                explanation.append(f"No rule concludes {symbol}, and it is not given as a fact.")
                explanation.append(f"Therefore, {symbol} is false (closed-world assumption).")

        return explanation

    def _explain_undetermined(self, symbol: str) -> List[str]:
        """Explain why a symbol is UNDETERMINED."""
        explanation = []

        # Check for OR/XOR in conclusions
        rules = self.ctx.rules_by_conclusion.get(symbol, [])
        for rule in rules:
            from src.exec import OrCondition, XorCondition
            if isinstance(rule.conclusion, (OrCondition, XorCondition)):
                from src.exec.eval_condition import eval_condition
                from src.exec.status import Status

                condition_status = eval_condition(self.ctx, rule.condition, depth=0)
                if condition_status == Status.TRUE:
                    explanation.append(self._explain_ambiguous_conclusion(symbol, rule))
                    break

        # Check for circular dependencies
        if not explanation:
            explanation.append(f"The value of {symbol} cannot be determined.")
            explanation.append(f"This may be due to circular dependencies or insufficient information.")

        return explanation

    def _explain_rule_firing(self, symbol: str, rule: "Rule") -> str:
        """Explain how a rule proves a symbol."""
        from src.exec.format_condition import format_condition

        condition_str = format_condition(rule.condition)
        conclusion_str = format_condition(rule.conclusion)

        # Explain the condition
        condition_explanation = self._explain_condition(rule.condition)

        explanation = []
        explanation.append(f"We can prove {symbol} is true using the rule:")
        explanation.append(f"  Rule: {condition_str} => {conclusion_str}")
        explanation.append(f"\n{condition_explanation}")
        explanation.append(f"\nSince the condition is satisfied, we conclude {symbol} is true.")

        return "\n".join(explanation)

    def _explain_negation_rule(self, symbol: str, rule: "Rule") -> str:
        """Explain how a rule proves a symbol is false."""
        from src.exec.format_condition import format_condition

        condition_str = format_condition(rule.condition)
        conclusion_str = format_condition(rule.conclusion)

        condition_explanation = self._explain_condition(rule.condition)

        explanation = []
        explanation.append(f"We can prove {symbol} is false using the rule:")
        explanation.append(f"  Rule: {condition_str} => {conclusion_str}")
        explanation.append(f"\n{condition_explanation}")
        explanation.append(f"\nSince the condition is satisfied, we conclude {symbol} is false.")

        return "\n".join(explanation)

    def _explain_ambiguous_conclusion(self, symbol: str, rule: "Rule") -> str:
        """Explain why a conclusion is ambiguous."""
        from src.exec.format_condition import format_condition
        from src.exec import OrCondition, XorCondition

        condition_str = format_condition(rule.condition)
        conclusion_str = format_condition(rule.conclusion)

        condition_explanation = self._explain_condition(rule.condition)

        operator = "OR" if isinstance(rule.conclusion, OrCondition) else "XOR"

        explanation = []
        explanation.append(f"The rule that applies is:")
        explanation.append(f"  Rule: {condition_str} => {conclusion_str}")
        explanation.append(f"\n{condition_explanation}")
        explanation.append(f"\nThe conclusion uses {operator}, which creates ambiguity:")
        explanation.append(f"We know one of the facts in '{conclusion_str}' must be true,")
        explanation.append(f"but we cannot determine which one without additional information.")
        explanation.append(f"\nTherefore, {symbol} is UNDETERMINED.")

        return "\n".join(explanation)

    def _explain_how_proven(self, symbol: str) -> str:
        """Explain how a symbol was proven true by finding the rule that concluded it."""
        # Find the rule that proved this symbol
        rules = self.ctx.rules_by_conclusion.get(symbol, [])
        for rule in rules:
            from src.exec.eval_condition import eval_condition
            from src.exec.status import Status
            from src.exec.format_condition import format_condition

            condition_status = eval_condition(self.ctx, rule.condition, depth=0)
            if condition_status == Status.TRUE:
                condition_str = format_condition(rule.condition)
                conclusion_str = format_condition(rule.conclusion)

                # Recursively explain the condition
                condition_explanation = self._explain_condition(rule.condition)
                return f"Proven by rule: {condition_str} => {conclusion_str}\n  Because: {condition_explanation}"

        return "Proven by another rule."

    def _explain_how_disproven(self, symbol: str) -> str:
        """Explain how a symbol was proven false."""
        # Check if it's a fact
        if self.ctx.is_fact_false(symbol):
            return "Given as false (initial fact)."

        # Check if negated by a rule
        rules = self.ctx.rules_by_conclusion.get(symbol, [])
        for rule in rules:
            from src.exec import NotCondition
            from src.exec.format_condition import format_condition
            if isinstance(rule.conclusion, NotCondition):
                from src.exec.eval_condition import eval_condition
                from src.exec.status import Status

                condition_status = eval_condition(self.ctx, rule.condition, depth=0)
                if condition_status == Status.TRUE:
                    condition_str = format_condition(rule.condition)

                    # Recursively explain the condition
                    condition_explanation = self._explain_condition(rule.condition)
                    return f"Negated by rule: {condition_str} => !{symbol}\n  Because: {condition_explanation}"

        return "Cannot be proven true (closed-world assumption)."

    def _collect_requirements(self, condition: "Condition", indent: int = 0) -> List[str]:
        """Recursively collect all requirements needed to satisfy a condition."""
        from src.exec import FactCondition, AndCondition, OrCondition, XorCondition, NotCondition
        from src.exec.format_condition import format_condition

        prefix = " " * indent
        lines = []

        if isinstance(condition, FactCondition):
            symbol = condition.symbol
            # Check if it's already a fact
            if self.ctx.is_fact_true(symbol):
                lines.append(f"{prefix}✓ {symbol} (already given as fact)")
            else:
                # Need to find how to get this symbol
                rules_for_symbol = self.ctx.rules_by_conclusion.get(symbol, [])
                if rules_for_symbol:
                    # Show the first rule that could prove it
                    for rule in rules_for_symbol:
                        from src.exec import NotCondition as NC
                        if isinstance(rule.conclusion, NC):
                            continue

                        cond_str = format_condition(rule.condition)
                        lines.append(f"{prefix}• {symbol} requires: {cond_str}")
                        # Recursively get requirements for this condition
                        inner_reqs = self._collect_requirements(rule.condition, indent + 2)
                        lines.extend(inner_reqs)
                        break
                else:
                    lines.append(f"{prefix}✗ {symbol} (cannot be proven, not a fact)")

        elif isinstance(condition, NotCondition):
            from src.exec import FactCondition as FC
            if isinstance(condition.condition, FC):
                symbol = condition.condition.symbol
                if self.ctx.is_fact_false(symbol) or self.ctx.get_status(symbol).name == 'FALSE':
                    lines.append(f"{prefix}✓ !{symbol} (already satisfied)")
                else:
                    lines.append(f"{prefix}✗ !{symbol} ({symbol} must be false)")
            else:
                cond_str = format_condition(condition.condition)
                lines.append(f"{prefix}• NOT({cond_str})")

        elif isinstance(condition, AndCondition):
            left_reqs = self._collect_requirements(condition.left, indent)
            lines.extend(left_reqs)
            right_reqs = self._collect_requirements(condition.right, indent)
            lines.extend(right_reqs)

        elif isinstance(condition, OrCondition):
            left_str = format_condition(condition.left)
            right_str = format_condition(condition.right)
            lines.append(f"{prefix}• Either {left_str} OR {right_str}:")
            lines.append(f"{prefix}  Option 1:")
            left_reqs = self._collect_requirements(condition.left, indent + 4)
            lines.extend(left_reqs)
            lines.append(f"{prefix}  Option 2:")
            right_reqs = self._collect_requirements(condition.right, indent + 4)
            lines.extend(right_reqs)

        elif isinstance(condition, XorCondition):
            left_str = format_condition(condition.left)
            right_str = format_condition(condition.right)
            lines.append(f"{prefix}• Exactly one of {left_str} XOR {right_str}")

        return lines

    def _explain_why_condition_false(self, condition: "Condition") -> str:
        """Explain why a condition is false."""
        from src.exec import FactCondition, AndCondition, OrCondition, XorCondition, NotCondition
        from src.exec.eval_condition import eval_condition
        from src.exec.status import Status
        from src.exec.format_condition import format_condition

        if isinstance(condition, FactCondition):
            symbol = condition.symbol
            status = self.ctx.get_status(symbol)
            if status == Status.FALSE:
                # Check if there's a rule that could prove this symbol
                rules_for_symbol = self.ctx.rules_by_conclusion.get(symbol, [])
                if rules_for_symbol:
                    # Find why the rules don't fire
                    reasons = []
                    for rule in rules_for_symbol:
                        from src.exec import NotCondition as NC
                        if isinstance(rule.conclusion, NC):
                            continue  # Skip negation rules

                        cond_status = eval_condition(self.ctx, rule.condition, depth=0)
                        if cond_status != Status.TRUE:
                            cond_str = format_condition(rule.condition)
                            conclusion_str = format_condition(rule.conclusion)
                            inner_reason = self._explain_why_condition_false(rule.condition)
                            reasons.append(f"{symbol} is false because rule '{cond_str} => {conclusion_str}' does not fire ({inner_reason})")

                    if reasons:
                        return reasons[0]  # Return the first explanation

                return f"{symbol} is false"
            else:
                return f"{symbol} is {status.name}"

        elif isinstance(condition, NotCondition):
            inner_status = eval_condition(self.ctx, condition.condition, depth=0)
            if inner_status == Status.TRUE:
                return f"The negation fails because the inner condition is true"
            return f"The negation status: {inner_status.name}"

        elif isinstance(condition, AndCondition):
            left_status = eval_condition(self.ctx, condition.left, depth=0)
            right_status = eval_condition(self.ctx, condition.right, depth=0)

            parts = []
            if left_status != Status.TRUE:
                left_str = format_condition(condition.left)
                left_reason = self._explain_why_condition_false(condition.left)
                parts.append(f"{left_str} is {left_status.name} ({left_reason})")
            if right_status != Status.TRUE:
                right_str = format_condition(condition.right)
                right_reason = self._explain_why_condition_false(condition.right)
                parts.append(f"{right_str} is {right_status.name} ({right_reason})")

            return " and ".join(parts) if parts else "AND condition is false"

        elif isinstance(condition, OrCondition):
            left_status = eval_condition(self.ctx, condition.left, depth=0)
            right_status = eval_condition(self.ctx, condition.right, depth=0)

            if left_status == Status.FALSE and right_status == Status.FALSE:
                left_str = format_condition(condition.left)
                right_str = format_condition(condition.right)
                return f"Both {left_str} and {right_str} are false"
            return "OR condition is false"

        elif isinstance(condition, XorCondition):
            left_status = eval_condition(self.ctx, condition.left, depth=0)
            right_status = eval_condition(self.ctx, condition.right, depth=0)

            if left_status == right_status:
                return f"XOR fails because both sides have the same status: {left_status.name}"
            return "XOR condition is false"

        return "Condition is false"

    def _explain_why_condition_false_detailed(self, condition: "Condition", indent: int = 0) -> List[str]:
        """Explain why a condition is false with proper indentation."""
        from src.exec import FactCondition, AndCondition, OrCondition, XorCondition, NotCondition
        from src.exec.eval_condition import eval_condition
        from src.exec.status import Status
        from src.exec.format_condition import format_condition

        prefix = " " * indent
        lines = []

        if isinstance(condition, FactCondition):
            symbol = condition.symbol
            status = self.ctx.get_status(symbol)

            if status == Status.FALSE:
                # Check if there's a rule that could prove this symbol
                rules_for_symbol = self.ctx.rules_by_conclusion.get(symbol, [])
                has_positive_rule = False

                for rule in rules_for_symbol:
                    from src.exec import NotCondition as NC
                    if not isinstance(rule.conclusion, NC):
                        has_positive_rule = True
                        cond_status = eval_condition(self.ctx, rule.condition, depth=0)
                        if cond_status != Status.TRUE:
                            cond_str = format_condition(rule.condition)
                            conclusion_str = format_condition(rule.conclusion)
                            lines.append(f"{prefix}{symbol} is FALSE because rule '{cond_str} => {conclusion_str}' does not fire:")
                            inner_lines = self._explain_why_condition_false_detailed(rule.condition, indent + 2)
                            lines.extend(inner_lines)
                        break

                if not has_positive_rule:
                    lines.append(f"{prefix}{symbol} is FALSE (cannot be proven)")
            elif status == Status.TRUE:
                # Explain why the symbol is true
                if self.ctx.is_fact_true(symbol):
                    lines.append(f"{prefix}{symbol} is TRUE (given as fact)")
                else:
                    # Find the rule that proved it
                    rules_for_symbol = self.ctx.rules_by_conclusion.get(symbol, [])
                    for rule in rules_for_symbol:
                        from src.exec import NotCondition as NC
                        if isinstance(rule.conclusion, NC):
                            continue  # Skip negation rules for now

                        cond_status = eval_condition(self.ctx, rule.condition, depth=0)
                        if cond_status == Status.TRUE:
                            cond_str = format_condition(rule.condition)
                            conclusion_str = format_condition(rule.conclusion)
                            lines.append(f"{prefix}{symbol} is TRUE because rule '{cond_str} => {conclusion_str}' fires:")
                            inner_lines = self._explain_why_condition_true_detailed(rule.condition, indent + 2)
                            lines.extend(inner_lines)
                            break
            else:
                lines.append(f"{prefix}{symbol} is {status.name}")

        elif isinstance(condition, NotCondition):
            from src.exec import FactCondition as FC
            if isinstance(condition.condition, FC):
                symbol = condition.condition.symbol
                status = self.ctx.get_status(symbol)
                cond_str = format_condition(condition.condition)
                lines.append(f"{prefix}!{symbol} is FALSE because {symbol} is {status.name}")
                if status == Status.TRUE:
                    # Explain why the symbol is true
                    inner_lines = self._explain_why_condition_false_detailed(condition.condition, indent + 2)
                    lines.extend(inner_lines)
            else:
                inner_status = eval_condition(self.ctx, condition.condition, depth=0)
                lines.append(f"{prefix}Negation is FALSE (inner condition is {inner_status.name})")

        elif isinstance(condition, AndCondition):
            left_status = eval_condition(self.ctx, condition.left, depth=0)
            right_status = eval_condition(self.ctx, condition.right, depth=0)

            if left_status != Status.TRUE:
                left_str = format_condition(condition.left)
                lines.append(f"{prefix}AND fails because {left_str} is {left_status.name}:")
                left_lines = self._explain_why_condition_false_detailed(condition.left, indent + 2)
                lines.extend(left_lines)

            if right_status != Status.TRUE:
                right_str = format_condition(condition.right)
                lines.append(f"{prefix}AND fails because {right_str} is {right_status.name}:")
                right_lines = self._explain_why_condition_false_detailed(condition.right, indent + 2)
                lines.extend(right_lines)

        elif isinstance(condition, OrCondition):
            left_status = eval_condition(self.ctx, condition.left, depth=0)
            right_status = eval_condition(self.ctx, condition.right, depth=0)

            if left_status == Status.FALSE and right_status == Status.FALSE:
                lines.append(f"{prefix}OR fails because both sides are FALSE:")
                left_str = format_condition(condition.left)
                right_str = format_condition(condition.right)
                lines.append(f"{prefix}  {left_str} is FALSE")
                lines.append(f"{prefix}  {right_str} is FALSE")

        elif isinstance(condition, XorCondition):
            left_status = eval_condition(self.ctx, condition.left, depth=0)
            right_status = eval_condition(self.ctx, condition.right, depth=0)

            if left_status == right_status:
                lines.append(f"{prefix}XOR fails (both sides are {left_status.name})")

        return lines if lines else [f"{prefix}Condition is false"]

    def _explain_why_condition_true_detailed(self, condition: "Condition", indent: int = 0) -> List[str]:
        """Explain why a condition is true with proper indentation."""
        from src.exec import FactCondition, AndCondition, OrCondition, XorCondition, NotCondition
        from src.exec.eval_condition import eval_condition
        from src.exec.status import Status
        from src.exec.format_condition import format_condition

        prefix = " " * indent
        lines = []

        if isinstance(condition, FactCondition):
            symbol = condition.symbol
            if self.ctx.is_fact_true(symbol):
                lines.append(f"{prefix}{symbol} is TRUE (given as fact)")
            else:
                status = self.ctx.get_status(symbol)
                if status == Status.TRUE:
                    # Find the rule that proved it
                    rules_for_symbol = self.ctx.rules_by_conclusion.get(symbol, [])
                    for rule in rules_for_symbol:
                        from src.exec import NotCondition as NC
                        if isinstance(rule.conclusion, NC):
                            continue

                        cond_status = eval_condition(self.ctx, rule.condition, depth=0)
                        if cond_status == Status.TRUE:
                            cond_str = format_condition(rule.condition)
                            conclusion_str = format_condition(rule.conclusion)
                            lines.append(f"{prefix}{symbol} is TRUE (proven by rule '{cond_str} => {conclusion_str}'):")
                            inner_lines = self._explain_why_condition_true_detailed(rule.condition, indent + 2)
                            lines.extend(inner_lines)
                            break
                else:
                    lines.append(f"{prefix}{symbol} is {status.name}")

        elif isinstance(condition, NotCondition):
            from src.exec import FactCondition as FC
            if isinstance(condition.condition, FC):
                symbol = condition.condition.symbol
                status = self.ctx.get_status(symbol)
                lines.append(f"{prefix}!{symbol} is TRUE because {symbol} is FALSE")
            else:
                lines.append(f"{prefix}Negation is TRUE")

        elif isinstance(condition, AndCondition):
            left_str = format_condition(condition.left)
            right_str = format_condition(condition.right)
            lines.append(f"{prefix}AND condition satisfied ({left_str} AND {right_str}):")
            left_lines = self._explain_why_condition_true_detailed(condition.left, indent + 2)
            lines.extend(left_lines)
            right_lines = self._explain_why_condition_true_detailed(condition.right, indent + 2)
            lines.extend(right_lines)

        elif isinstance(condition, OrCondition):
            left_status = eval_condition(self.ctx, condition.left, depth=0)
            right_status = eval_condition(self.ctx, condition.right, depth=0)

            if left_status == Status.TRUE:
                left_str = format_condition(condition.left)
                lines.append(f"{prefix}OR satisfied because {left_str} is TRUE:")
                left_lines = self._explain_why_condition_true_detailed(condition.left, indent + 2)
                lines.extend(left_lines)
            elif right_status == Status.TRUE:
                right_str = format_condition(condition.right)
                lines.append(f"{prefix}OR satisfied because {right_str} is TRUE:")
                right_lines = self._explain_why_condition_true_detailed(condition.right, indent + 2)
                lines.extend(right_lines)

        elif isinstance(condition, XorCondition):
            left_status = eval_condition(self.ctx, condition.left, depth=0)
            right_status = eval_condition(self.ctx, condition.right, depth=0)

            if left_status == Status.TRUE and right_status == Status.FALSE:
                left_str = format_condition(condition.left)
                lines.append(f"{prefix}XOR satisfied (only {left_str} is TRUE)")
            elif left_status == Status.FALSE and right_status == Status.TRUE:
                right_str = format_condition(condition.right)
                lines.append(f"{prefix}XOR satisfied (only {right_str} is TRUE)")

        return lines if lines else [f"{prefix}Condition is true"]

    def _explain_condition(self, condition: "Condition") -> str:
        """Recursively explain how a condition is satisfied."""
        from src.exec import FactCondition, AndCondition, OrCondition, XorCondition, NotCondition
        from src.exec.status import Status

        if isinstance(condition, FactCondition):
            symbol = condition.symbol
            if self.ctx.is_fact_true(symbol):
                return f"We know that {symbol} is true (given as fact)."
            else:
                status = self.ctx.get_status(symbol)
                if status == Status.TRUE:
                    # Explain how this symbol was proven
                    explanation = self._explain_how_proven(symbol)
                    return f"We know that {symbol} is true.\n  {explanation}"
                elif status == Status.FALSE:
                    # Explain how this symbol was disproven
                    explanation = self._explain_how_disproven(symbol)
                    return f"We know that {symbol} is false.\n  {explanation}"
                else:
                    return f"We know that {symbol} is false."

        elif isinstance(condition, NotCondition):
            # For negation, we need to explain why the inner condition is false/true
            from src.exec import FactCondition as FC
            if isinstance(condition.condition, FC):
                symbol = condition.condition.symbol
                status = self.ctx.get_status(symbol)
                if status == Status.FALSE:
                    # Symbol is false, so !symbol is true
                    explanation = self._explain_how_disproven(symbol)
                    return f"The negation !{symbol} is true because {symbol} is false.\n  {explanation}"
                else:
                    return f"The negation is satisfied because {symbol} is false."
            else:
                inner_explanation = self._explain_condition(condition.condition)
                return f"The negation is satisfied:\n  {inner_explanation}"

        elif isinstance(condition, AndCondition):
            left_exp = self._explain_condition(condition.left)
            right_exp = self._explain_condition(condition.right)
            from src.exec.format_condition import format_condition
            return f"Both conditions of '{format_condition(condition)}' are satisfied:\n  {left_exp}\n  {right_exp}"

        elif isinstance(condition, OrCondition):
            # Check which branch is true
            from src.exec.eval_condition import eval_condition
            left_status = eval_condition(self.ctx, condition.left, depth=0)
            right_status = eval_condition(self.ctx, condition.right, depth=0)

            from src.exec.format_condition import format_condition

            if left_status == Status.TRUE and right_status == Status.TRUE:
                left_exp = self._explain_condition(condition.left)
                right_exp = self._explain_condition(condition.right)
                return f"Both conditions of '{format_condition(condition)}' are true:\n  {left_exp}\n  {right_exp}"
            elif left_status == Status.TRUE:
                left_exp = self._explain_condition(condition.left)
                return f"At least one condition of '{format_condition(condition)}' is satisfied:\n  {left_exp}"
            else:
                right_exp = self._explain_condition(condition.right)
                return f"At least one condition of '{format_condition(condition)}' is satisfied:\n  {right_exp}"

        elif isinstance(condition, XorCondition):
            from src.exec.eval_condition import eval_condition
            from src.exec.format_condition import format_condition
            left_status = eval_condition(self.ctx, condition.left, depth=0)
            right_status = eval_condition(self.ctx, condition.right, depth=0)

            if left_status == Status.TRUE and right_status == Status.FALSE:
                left_exp = self._explain_condition(condition.left)
                return f"Exactly one condition of '{format_condition(condition)}' is true:\n  {left_exp}"
            elif left_status == Status.FALSE and right_status == Status.TRUE:
                right_exp = self._explain_condition(condition.right)
                return f"Exactly one condition of '{format_condition(condition)}' is true:\n  {right_exp}"
            else:
                return f"The XOR condition '{format_condition(condition)}' is satisfied."

        return "Condition is satisfied."


def visualize_reasoning(ctx: "ExecContext", program: "Program", results: Dict[str, "Status"]) -> None:
    """
    Display reasoning explanations for all queries.

    Args:
        ctx: Execution context
        program: Parsed program
        results: Query results
    """
    visualizer = ReasoningVisualizer(ctx, program)

    cyan = Colors.CYAN
    reset = Colors.RESET

    print(f"\n{cyan}REASONING EXPLANATIONS{reset}")
    print("=" * 70)

    for symbol, status in results.items():
        explanation = visualizer.explain_query(symbol, status)
        print(explanation)


__all__ = ["ReasoningVisualizer", "visualize_reasoning", "ReasoningStep"]
