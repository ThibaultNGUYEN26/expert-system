from dataclasses import dataclass, field
from typing import Dict, List, Set

from __init__ import Program, RuleCondition, FactCondition
from status import Status


@dataclass
class ExecContext:
    """
    Runtime context for the expert system.

    It wraps the parsed Program and adds:
    - facts as a set (for O(1) lookup)
    - rules_by_conclusion: index rules by conclusion symbol
    - status: memoisation + cycle detection for each symbol
    """
    program: Program

    facts: Set[str] = field(default_factory=set)
    rules_by_conclusion: Dict[str, List[RuleCondition]] = field(default_factory=dict)
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

        ctx.facts = program.facts

        ctx.rules_by_conclusion = {}

        for rule in program.rules:
            for conclusion in rule.conclusions:
                if isinstance(conclusion, FactCondition):
                    sym = conclusion.symbol
                    ctx.rules_by_conclusion.setdefault(sym, []).append(rule)
                else:
                    pass

        symbols: Set[str] = set()

        symbols |= set(program.facts)

        for query in program.queries:
            symbols.add(query.label)

        for rule in program.rules:
            for conclusion in rule.conclusions:
                if isinstance(conclusion, FactCondition):
                    symbols.add(conclusion.symbol)

        ctx.status = {sym: Status.UNKNOWN for sym in symbols}

        return ctx

    def get_status(self, symbol: str) -> Status:
        return self.status.get(symbol, Status.UNKNOWN)

    def set_status(self, symbol: str, new_status: Status) -> None:
        self.status[symbol] = new_status

    def is_fact(self, symbol: str) -> bool:
        return symbol in self.facts
