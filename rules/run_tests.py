#!/usr/bin/env python3
"""
Unit test runner for the expert system.
Tests all operators: AND, OR, XOR, NOT, and UNDETERMINED states.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsing import parse_program
from src.exec.exec_context import ExecContext
from src.exec import solve
from src.exec.status import Status


@dataclass
class TestCase:
    """Represents a single test case."""
    file_path: Path
    expected_results: Dict[str, Status]
    description: str


def run_test(test_case: TestCase) -> Tuple[bool, str, Dict[str, Status], Dict[str, Status]]:
    """
    Run a single test case.

    Returns:
        (success, message, expected_results, actual_results) tuple
    """
    try:
        # Parse the rule file
        config_data = test_case.file_path.read_text(encoding="utf-8")
        program = parse_program(config_data)

        # Build execution context and solve
        ctx = ExecContext.from_program(program)
        results = solve.run_queries(ctx)

        # Check results
        for query, expected_status in test_case.expected_results.items():
            actual_status = results.get(query)
            if actual_status != expected_status:
                return False, f"Query '{query}': expected {expected_status.name}, got {actual_status.name if actual_status else 'None'}", test_case.expected_results, results

        # Check for unexpected queries
        for query in results:
            if query not in test_case.expected_results:
                return False, f"Unexpected query result: {query} = {results[query].name}", test_case.expected_results, results

        return True, "PASS", test_case.expected_results, results

    except Exception as e:
        return False, f"ERROR: {str(e)}", test_case.expected_results, {}


def main():
    """Run all unit tests."""
    rules_dir = Path(__file__).parent

    # Define test cases with expected results
    test_cases: List[TestCase] = [
        # AND operator tests
        TestCase(
            rules_dir / "AND_rules/test1_simple_and.rule",
            {"D": Status.TRUE},
            "AND: Simple A + B with facts"
        ),
        TestCase(
            rules_dir / "AND_rules/test2_multiple_and.rule",
            {"G": Status.TRUE},
            "AND: Chained (D + E) + F"
        ),
        TestCase(
            rules_dir / "AND_rules/test3_and_undetermined.rule",
            {"J": Status.FALSE},
            "AND: One operand undetermined"
        ),
        TestCase(
            rules_dir / "AND_rules/test4_and_with_false.rule",
            {"M": Status.FALSE},
            "AND: One operand false"
        ),
        TestCase(
            rules_dir / "AND_rules/test5_complex_chain.rule",
            {"Z": Status.FALSE},
            "AND: Complex chain"
        ),
        TestCase(
            rules_dir / "AND_rules/test6_triple_and.rule",
            {"D": Status.TRUE},
            "AND: Triple AND all true"
        ),
        TestCase(
            rules_dir / "AND_rules/test7_one_false.rule",
            {"D": Status.FALSE},
            "AND: One false makes all false"
        ),
        TestCase(
            rules_dir / "AND_rules/test8_parentheses.rule",
            {"D": Status.TRUE},
            "AND: With parentheses"
        ),

        # OR operator tests
        TestCase(
            rules_dir / "OR_rules/test1.rule",
            {"C": Status.TRUE},
            "OR: Simple A | B with A true"
        ),
        TestCase(
            rules_dir / "OR_rules/test2_both_false.rule",
            {"C": Status.FALSE},
            "OR: Both false"
        ),
        TestCase(
            rules_dir / "OR_rules/test3_both_true.rule",
            {"C": Status.TRUE},
            "OR: Both true"
        ),
        TestCase(
            rules_dir / "OR_rules/test4_chain_or.rule",
            {"D": Status.TRUE},
            "OR: Chain of OR"
        ),
        TestCase(
            rules_dir / "OR_rules/test5_parentheses.rule",
            {"D": Status.TRUE},
            "OR: With parentheses"
        ),

        # XOR operator tests
        TestCase(
            rules_dir / "XOR_rules/test1_xor_both_false.rule",
            {"C": Status.FALSE},
            "XOR: Both false"
        ),
        TestCase(
            rules_dir / "XOR_rules/test2_xor_first_true.rule",
            {"C": Status.TRUE},
            "XOR: First true, second false"
        ),
        TestCase(
            rules_dir / "XOR_rules/test3_xor_second_true.rule",
            {"C": Status.TRUE},
            "XOR: First false, second true"
        ),
        TestCase(
            rules_dir / "XOR_rules/test4_xor_both_true.rule",
            {"C": Status.FALSE},
            "XOR: Both true"
        ),
        TestCase(
            rules_dir / "XOR_rules/test5_xor_chain.rule",
            {"D": Status.TRUE},
            "XOR: Chained XOR"
        ),
        TestCase(
            rules_dir / "XOR_rules/test6_xor_parentheses.rule",
            {"D": Status.FALSE},
            "XOR: With parentheses"
        ),

        # NOT operator tests
        TestCase(
            rules_dir / "NOT_rules/test1_simple_not.rule",
            {"B": Status.TRUE},
            "NOT: Simple negation of false"
        ),
        TestCase(
            rules_dir / "NOT_rules/test2_not_fact.rule",
            {"B": Status.FALSE},
            "NOT: Negation of true"
        ),
        TestCase(
            rules_dir / "NOT_rules/test3_double_not.rule",
            {"B": Status.TRUE},
            "NOT: Double negation"
        ),
        TestCase(
            rules_dir / "NOT_rules/test4_not_with_and.rule",
            {"C": Status.TRUE},
            "NOT: NOT with AND"
        ),
        TestCase(
            rules_dir / "NOT_rules/test5_not_each_operand.rule",
            {"C": Status.TRUE},
            "NOT: NOT on each operand"
        ),

        # UNDETERMINED tests
        TestCase(
            rules_dir / "UNDETERMINED_rules/test1_simple_or_conclusion.rule",
            {"B": Status.UNDETERMINED, "C": Status.UNDETERMINED},
            "UNDETERMINED: Simple OR in conclusion"
        ),
        TestCase(
            rules_dir / "UNDETERMINED_rules/test2_simple_xor_conclusion.rule",
            {"B": Status.UNDETERMINED, "C": Status.UNDETERMINED},
            "UNDETERMINED: Simple XOR in conclusion"
        ),
        TestCase(
            rules_dir / "UNDETERMINED_rules/test3_complex_or_conclusion.rule",
            {"B": Status.UNDETERMINED, "C": Status.UNDETERMINED, "D": Status.UNDETERMINED},
            "UNDETERMINED: Complex OR in conclusion"
        ),
        TestCase(
            rules_dir / "UNDETERMINED_rules/test4_or_not_triggered.rule",
            {"B": Status.FALSE, "C": Status.FALSE},
            "UNDETERMINED: OR conclusion not triggered"
        ),
        TestCase(
            rules_dir / "UNDETERMINED_rules/test5_multiple_or_conclusions.rule",
            {"B": Status.UNDETERMINED, "C": Status.UNDETERMINED,
             "E": Status.UNDETERMINED, "F": Status.UNDETERMINED},
            "UNDETERMINED: Multiple OR conclusions"
        ),
        TestCase(
            rules_dir / "UNDETERMINED_rules/test6_mixed_determined_undetermined.rule",
            {"B": Status.UNDETERMINED, "C": Status.UNDETERMINED, "D": Status.UNDETERMINED},
            "UNDETERMINED: Mixed determined/undetermined"
        ),

        # CONCLUSION tests (AND, NOT in conclusions)
        TestCase(
            rules_dir / "CONCLUSION_rules/test1_and_conclusion.rule",
            {"B": Status.TRUE, "C": Status.TRUE},
            "CONCLUSION: AND in conclusion"
        ),
        TestCase(
            rules_dir / "CONCLUSION_rules/test2_and_multiple.rule",
            {"B": Status.TRUE, "C": Status.TRUE, "D": Status.TRUE},
            "CONCLUSION: Multiple facts in AND conclusion"
        ),
        TestCase(
            rules_dir / "CONCLUSION_rules/test3_not_conclusion.rule",
            {"B": Status.FALSE},
            "CONCLUSION: NOT in conclusion"
        ),
        TestCase(
            rules_dir / "CONCLUSION_rules/test4_complex_and.rule",
            {"B": Status.TRUE, "C": Status.TRUE, "D": Status.TRUE},
            "CONCLUSION: Complex AND in conclusion"
        ),
        TestCase(
            rules_dir / "CONCLUSION_rules/test5_and_not_triggered.rule",
            {"B": Status.FALSE, "C": Status.FALSE},
            "CONCLUSION: AND conclusion not triggered"
        ),
        TestCase(
            rules_dir / "CONCLUSION_rules/test6_multiple_and.rule",
            {"B": Status.TRUE, "C": Status.TRUE, "E": Status.TRUE, "F": Status.TRUE},
            "CONCLUSION: Multiple rules with AND conclusions"
        ),        # MIXED operator tests
        TestCase(
            rules_dir / "MIXED_rules/test1_and_or_precedence.rule",
            {"D": Status.TRUE},
            "MIXED: AND + OR precedence"
        ),
        TestCase(
            rules_dir / "MIXED_rules/test2_or_and_parentheses.rule",
            {"D": Status.TRUE},
            "MIXED: OR + AND with parentheses"
        ),
        TestCase(
            rules_dir / "MIXED_rules/test3_and_xor_or.rule",
            {"E": Status.FALSE},
            "MIXED: AND + XOR + OR"
        ),
        TestCase(
            rules_dir / "MIXED_rules/test4_not_and_or.rule",
            {"D": Status.TRUE},
            "MIXED: NOT + AND + OR"
        ),
        TestCase(
            rules_dir / "MIXED_rules/test5_deep_nesting.rule",
            {"F": Status.TRUE},
            "MIXED: Deeply nested parentheses"
        ),
        TestCase(
            rules_dir / "MIXED_rules/test6_all_operators.rule",
            {"F": Status.FALSE},
            "MIXED: All operators combined"
        ),
        TestCase(
            rules_dir / "MIXED_rules/test7_multiple_rules.rule",
            {"C": Status.TRUE, "E": Status.TRUE, "G": Status.TRUE},
            "MIXED: Multiple rules with different operators"
        ),
        TestCase(
            rules_dir / "MIXED_rules/test8_chain_implications.rule",
            {"B": Status.TRUE, "D": Status.TRUE, "F": Status.TRUE, "H": Status.TRUE},
            "MIXED: Chain of implications"
        ),

        # IIF (biconditional) operator tests
        TestCase(
            rules_dir / "IIF_rules/test1_simple_iif.rule",
            {"B": Status.TRUE},
            "IIF: Simple A <=> B with A true"
        ),
        TestCase(
            rules_dir / "IIF_rules/test2_reverse_iif.rule",
            {"A": Status.TRUE},
            "IIF: Reverse direction with B true"
        ),
        TestCase(
            rules_dir / "IIF_rules/test3_both_false.rule",
            {"A": Status.UNDETERMINED, "B": Status.UNDETERMINED},
            "IIF: Both sides undetermined (circular)"
        ),
        TestCase(
            rules_dir / "IIF_rules/test4_complex_left.rule",
            {"C": Status.TRUE},
            "IIF: Complex expression (A+B) <=> C"
        ),
        TestCase(
            rules_dir / "IIF_rules/test5_complex_both.rule",
            {"A": Status.TRUE, "C": Status.TRUE},
            "IIF: Complex both sides"
        ),
        TestCase(
            rules_dir / "IIF_rules/test6_chain_iif.rule",
            {"B": Status.TRUE, "C": Status.TRUE},
            "IIF: Chained biconditionals"
        ),
    ]

    # Run tests
    print("=" * 80)
    print("EXPERT SYSTEM UNIT TESTS")
    print("=" * 80)
    print()

    passed = 0
    failed = 0
    errors = 0

    # Group tests by category
    categories = {}
    for test_case in test_cases:
        category = test_case.description.split(":")[0]
        if category not in categories:
            categories[category] = []
        categories[category].append(test_case)

    # Run tests by category
    for category, tests in categories.items():
        print(f"\033[1m{category}\033[0m")

        for test_case in tests:
            success, message, expected, actual = run_test(test_case)

            status_symbol = "✓" if success else "✗"
            status_color = "\033[92m" if success else "\033[91m"
            reset = "\033[0m"

            # Extract description after the category prefix
            desc_parts = test_case.description.split(": ", 1)
            desc = desc_parts[1] if len(desc_parts) > 1 else test_case.description

            print(f"  {status_color}{status_symbol}{reset} {desc}")
            if not success:
                if "ERROR" not in message:
                    # Show query name if available
                    if message.startswith("Query '"):
                        query_name = message.split("'")[1]
                        print(f"    Query '{query_name}':")
                    else:
                        print(f"    {message}")
                    # Show expected vs actual
                    print(f"    \033[93mExpected:\033[0m {', '.join(f'{k}={v.name}' for k, v in expected.items())}")
                    print(f"    \033[93mActual:  \033[0m {', '.join(f'{k}={v.name}' for k, v in actual.items())}")
                    failed += 1
                else:
                    print(f"    {message}")
                    errors += 1
            else:
                passed += 1

            # Show file path for failed tests
            if not success:
                print(f"    File: {test_case.file_path.relative_to(rules_dir.parent)}")

        print()    # Summary
    print("=" * 80)
    total = passed + failed + errors
    print(f"Total: {total} tests")
    print(f"\033[92mPassed: {passed}\033[0m")
    if failed > 0:
        print(f"\033[91mFailed: {failed}\033[0m")
    if errors > 0:
        print(f"\033[93mErrors: {errors}\033[0m")
    print("=" * 80)

    return 0 if (failed == 0 and errors == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
