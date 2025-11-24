from __init__ import (
    Program,
    RuleCondition,
    FactCondition,
    NotCondition,
    AndCondition,
    OrCondition,
    XorCondition,
    QueryCondition,
)

from exec_context import ExecContext
from solve import solve_symbol, run_queries


# ========= BASE EXAMPLE =========
def make_program_and_chain() -> Program:
    """
    A + B => C
    C => D
    =AB
    ?CD

    Expected:
      C: True
      D: True
    """
    rule1 = RuleCondition(
        raw="A + B => C",
        requirement=AndCondition(
            left=FactCondition("A"),
            right=FactCondition("B"),
        ),
        conclusions=[FactCondition("C")],
    )

    rule2 = RuleCondition(
        raw="C => D",
        requirement=FactCondition("C"),
        conclusions=[FactCondition("D")],
    )

    facts = {"A", "B"}
    queries = [
        QueryCondition(label="C", expression=FactCondition("C")),
        QueryCondition(label="D", expression=FactCondition("D")),
    ]

    return Program(rules=[rule1, rule2], facts=facts, queries=queries)


# ========= NOT TESTS =========
def make_program_not_with_fact() -> Program:
    """
    !A => B
    =A
    ?B

    A is a fact → A = True
    !A = False → rule condition is False → B should be False
    """
    rule = RuleCondition(
        raw="!A => B",
        requirement=NotCondition(FactCondition("A")),
        conclusions=[FactCondition("B")],
    )

    facts = {"A"}
    queries = [QueryCondition(label="B", expression=FactCondition("B"))]

    return Program(rules=[rule], facts=facts, queries=queries)


def make_program_not_without_fact() -> Program:
    """
    !A => B
    =
    ?B

    A is not a fact → A = False by default
    !A = True → rule condition is True → B should be True
    """
    rule = RuleCondition(
        raw="!A => B",
        requirement=NotCondition(FactCondition("A")),
        conclusions=[FactCondition("B")],
    )

    facts: set[str] = set()
    queries = [QueryCondition(label="B", expression=FactCondition("B"))]

    return Program(rules=[rule], facts=facts, queries=queries)


# ========= OR TESTS =========
def make_program_or() -> Program:
    """
    A | B => C

    Case 1: =A      → C should be True
    Case 2: =B      → C should be True
    Case 3: =       → C should be False

    We'll just build the Program once; tests will change facts.
    """
    rule = RuleCondition(
        raw="A | B => C",
        requirement=OrCondition(FactCondition("A"), FactCondition("B")),
        conclusions=[FactCondition("C")],
    )

    # facts will be set manually in tests
    facts: set[str] = set()
    queries = [QueryCondition(label="C", expression=FactCondition("C"))]

    return Program(rules=[rule], facts=facts, queries=queries)


# ========= XOR TESTS =========
def make_program_xor() -> Program:
    """
    A ^ B => C

    Truth table intention:
      =A       → C True
      =B       → C True
      =AB      → C False
      =        → C False
    """
    rule = RuleCondition(
        raw="A ^ B => C",
        requirement=XorCondition(FactCondition("A"), FactCondition("B")),
        conclusions=[FactCondition("C")],
    )

    facts: set[str] = set()
    queries = [QueryCondition(label="C", expression=FactCondition("C"))]

    return Program(rules=[rule], facts=facts, queries=queries)


# ========= CYCLE TESTS =========
def make_program_cycle() -> Program:
    """
    A => B
    B => A

    We'll test:
      - with =A  → A True, B True
      - with =   → A False, B False (no base facts, cycle only)
    """
    rule1 = RuleCondition(
        raw="A => B",
        requirement=FactCondition("A"),
        conclusions=[FactCondition("B")],
    )
    rule2 = RuleCondition(
        raw="B => A",
        requirement=FactCondition("B"),
        conclusions=[FactCondition("A")],
    )

    facts: set[str] = set()
    queries = [
        QueryCondition(label="A", expression=FactCondition("A")),
        QueryCondition(label="B", expression=FactCondition("B")),
    ]

    return Program(rules=[rule1, rule2], facts=facts, queries=queries)


# ========= RUN ALL TESTS =========
def run_and_print(title: str, program: Program) -> None:
    print(f"\n=== {title} ===")
    ctx = ExecContext.from_program(program)
    results = run_queries(ctx)
    for sym, val in results.items():
        print(f"{sym}: {val}")


if __name__ == "__main__":
    # 1) AND + chain (your original one)
    prog_and_chain = make_program_and_chain()
    run_and_print("AND + CHAIN", prog_and_chain)

    # 2) NOT with fact (=A)
    prog_not_fact = make_program_not_with_fact()
    run_and_print("NOT with A as fact (expect B=False)", prog_not_fact)

    # 3) NOT without fact (=)
    prog_not_no_fact = make_program_not_without_fact()
    run_and_print("NOT with no facts (expect B=True)", prog_not_no_fact)

    # 4) OR: change facts between runs
    base_or = make_program_or()

    # Case =A
    base_or_A = Program(
        rules=base_or.rules,
        facts={"A"},
        queries=base_or.queries,
    )
    run_and_print("OR with =A (expect C=True)", base_or_A)

    # Case =B
    base_or_B = Program(
        rules=base_or.rules,
        facts={"B"},
        queries=base_or.queries,
    )
    run_and_print("OR with =B (expect C=True)", base_or_B)

    # Case =
    base_or_none = Program(
        rules=base_or.rules,
        facts=set(),
        queries=base_or.queries,
    )
    run_and_print("OR with no facts (expect C=False)", base_or_none)

    # 5) XOR
    base_xor = make_program_xor()

    xor_A = Program(rules=base_xor.rules, facts={"A"}, queries=base_xor.queries)
    run_and_print("XOR with =A (expect C=True)", xor_A)

    xor_B = Program(rules=base_xor.rules, facts={"B"}, queries=base_xor.queries)
    run_and_print("XOR with =B (expect C=True)", xor_B)

    xor_AB = Program(
        rules=base_xor.rules, facts={"A", "B"}, queries=base_xor.queries
    )
    run_and_print("XOR with =AB (expect C=False)", xor_AB)

    xor_none = Program(
        rules=base_xor.rules, facts=set(), queries=base_xor.queries
    )
    run_and_print("XOR with no facts (expect C=False)", xor_none)

    # 6) CYCLES
    base_cycle = make_program_cycle()

    # with =A
    cycle_with_A = Program(
        rules=base_cycle.rules, facts={"A"}, queries=base_cycle.queries
    )
    run_and_print("CYCLE with =A (expect A=True, B=True)", cycle_with_A)

    # with no facts
    cycle_no_facts = Program(
        rules=base_cycle.rules, facts=set(), queries=base_cycle.queries
    )
    run_and_print("CYCLE with no facts (expect A=False, B=False)", cycle_no_facts)
