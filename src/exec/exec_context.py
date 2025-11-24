from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Set

from .status import Status

if TYPE_CHECKING:
    from src.parsing.parser import Program, Rule
    from src.exec import Condition, FactCondition
else:
    from typing import Any as Program, Any as Rule, Any as Condition, Any as FactCondition


@dataclass
class ExecContext:
    """
    Runtime context for the expert system.

    It wraps the parsed Program and adds:
    - facts as a set (for O(1) lookup)
    - rules_by_conclusion: index rules by conclusion symbol
    - status: memoisation + cycle detection for each symbol
    """
    program: "Program"

    facts_true: Set[str] = field(default_factory=set)
    facts_false: Set[str] = field(default_factory=set)
    rules_by_conclusion: Dict[str, List["Rule"]] = field(default_factory=dict)
    status: Dict[str, Status] = field(default_factory=dict)

    # -------------- CONSTRUCTOR FROM PROGRAM --------------

    @classmethod
    def from_program(cls, program: Program) -> "ExecContext":
        """
        Build an ExecContext from a parsed Program.

        This is the 'setup' phase before we start solving:
        - store the program
        - copy facts into a set
        - build the rules_by_conclusion index
        - initialise each symbol's status to UNKNOWN
        """
        ctx = cls(program=program)

        # Separate true and false facts
        ctx.facts_true = {symbol for symbol, value in program.facts.items() if value}
        ctx.facts_false = {symbol for symbol, value in program.facts.items() if not value}

        ctx.rules_by_conclusion = {}

        # Helper to extract all fact symbols from a conclusion condition tree
        def extract_conclusion_symbols(cond: "Condition") -> Set[str]:
            """Recursively extract all FactCondition symbols from a Condition tree."""
            import src.exec as exec_module
            if isinstance(cond, exec_module.FactCondition):
                return {cond.symbol}
            elif isinstance(cond, (exec_module.AndCondition, exec_module.OrCondition, exec_module.XorCondition)):
                return extract_conclusion_symbols(cond.left) | extract_conclusion_symbols(cond.right)
            elif isinstance(cond, exec_module.NotCondition):
                return extract_conclusion_symbols(cond.condition)
            return set()

        for rule in program.rules:
            # Conclusions can now be complex (OrCondition, XorCondition, etc.)
            # Index by all symbols that appear in the conclusion
            conclusion_symbols = extract_conclusion_symbols(rule.conclusion)
            for sym in conclusion_symbols:
                ctx.rules_by_conclusion.setdefault(sym, []).append(rule)

        symbols: Set[str] = set()

        # Add all fact symbols (both true and false)
        symbols |= set(program.facts.keys())

        # Add query symbols
        for query in program.queries:
            symbols.add(query)

        # Add conclusion symbols from rules
        for rule in program.rules:
            symbols |= extract_conclusion_symbols(rule.conclusion)

        ctx.status = {sym: Status.UNKNOWN for sym in symbols}

        return ctx

    def get_status(self, symbol: str) -> Status:
        return self.status.get(symbol, Status.UNKNOWN)

    def set_status(self, symbol: str, new_status: Status) -> None:
        self.status[symbol] = new_status

    def is_fact_true(self, symbol: str) -> bool:
        return symbol in self.facts_true

    def is_fact_false(self, symbol: str) -> bool:
        return symbol in self.facts_false
