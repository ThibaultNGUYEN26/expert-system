# Expert System Unit Tests

Comprehensive test suite for the expert system covering all logical operators and their combinations.

## Test Organization

Tests are organized by operator type in separate directories:

### AND_rules/
Tests for the AND (`+`) operator:
- `test1.rule` - Simple A + B with facts
- `test2.rule` - Chained (D + E) + F
- `test3.rule` - Basic AND with two conditions
- `test4.rule` - AND with negation
- `test5.rule` - Complex nested AND
- `test6_triple_and.rule` - Multiple AND operations
- `test7_one_false.rule` - One false makes result false
- `test8_parentheses.rule` - Parentheses grouping

### OR_rules/
Tests for the OR (`|`) operator:
- `test1.rule` - Simple A | B with A true
- `test2_both_false.rule` - Both operands false
- `test3_both_true.rule` - Both operands true
- `test4_chain_or.rule` - Chained OR operations
- `test5_parentheses.rule` - Parentheses grouping

### XOR_rules/
Tests for the XOR (`^`) operator:
- `test1_xor_both_false.rule` - Both operands false
- `test2_xor_first_true.rule` - First true, second false
- `test3_xor_second_true.rule` - First false, second true
- `test4_xor_both_true.rule` - Both operands true (returns false)
- `test5_xor_chain.rule` - Chained XOR operations
- `test6_xor_parentheses.rule` - Different grouping with parentheses

### NOT_rules/
Tests for the NOT (`!`) operator:
- `test1_simple_not.rule` - Simple negation of false
- `test2_not_fact.rule` - Negation of true fact
- `test3_double_not.rule` - Double negation (!!A)
- `test4_not_with_and.rule` - NOT combined with AND: !(A + B)
- `test5_not_each_operand.rule` - NOT on each operand: !A + !B

### UNDETERMINED_rules/
Tests for UNDETERMINED state (three-valued logic):
- `test1_simple_or_conclusion.rule` - A => B | C creates undetermined B, C
- `test2_simple_xor_conclusion.rule` - A => B ^ C creates undetermined B, C
- `test3_complex_or_conclusion.rule` - Complex OR in conclusion
- `test4_or_not_triggered.rule` - OR conclusion not triggered (should be false)
- `test5_multiple_or_conclusions.rule` - Multiple rules with OR conclusions
- `test6_mixed_determined_undetermined.rule` - Mix of determined and undetermined

### MIXED_rules/
Tests combining multiple operators:
- `test1_and_or_precedence.rule` - Operator precedence: AND before OR
- `test2_or_and_parentheses.rule` - Parentheses override precedence
- `test3_and_xor_or.rule` - (A + B) ^ (C | D)
- `test4_not_and_or.rule` - !(A + B) | C
- `test5_deep_nesting.rule` - Deeply nested parentheses
- `test6_all_operators.rule` - All operators in one expression
- `test7_multiple_rules.rule` - Multiple rules with different operators
- `test8_chain_implications.rule` - Chain of implications

## Running Tests

Run all tests:
```bash
python rules/run_tests.py
```

Run a specific test file:
```bash
python main.py rules/AND_rules/test1.rule
```

## Test Statistics

- **Total Tests**: 35
- **AND Tests**: 8
- **OR Tests**: 5
- **XOR Tests**: 6
- **NOT Tests**: 5
- **UNDETERMINED Tests**: 6
- **MIXED Tests**: 8

## Expected Results

All tests verify:
- **TRUE**: Fact is provably true
- **FALSE**: Fact is provably false or has no evidence
- **UNDETERMINED**: Fact is ambiguous due to disjunctive conclusions (OR/XOR in rule conclusions)

## Three-Valued Logic

The system implements three-valued logic for operators:

### AND (+)
- TRUE + TRUE = TRUE
- TRUE + FALSE = FALSE
- FALSE + FALSE = FALSE
- Any UNDETERMINED = UNDETERMINED (unless one operand is FALSE)

### OR (|)
- TRUE | TRUE = TRUE
- TRUE | FALSE = TRUE
- FALSE | FALSE = FALSE
- Any UNDETERMINED = UNDETERMINED (unless one operand is TRUE)

### XOR (^)
- TRUE ^ FALSE = TRUE
- FALSE ^ TRUE = TRUE
- TRUE ^ TRUE = FALSE
- FALSE ^ FALSE = FALSE
- Any UNDETERMINED = UNDETERMINED

### NOT (!)
- !TRUE = FALSE
- !FALSE = TRUE
- !UNDETERMINED = UNDETERMINED

## Test Format

Each test file follows this structure:
```
# Comments describing the test

<Rules>

<Facts declaration starting with =>
<Negative facts starting with !>
<Queries starting with ?>
```

Example:
```
# Simple AND test

A + B => C

=AB
?C
```
