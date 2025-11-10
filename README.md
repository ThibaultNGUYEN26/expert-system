# Expert System (WIP)

An implementation of an expert system that parses a knowledge base and applies inference rules using forward and backward chaining. The project is under active development — expect things to change.

## Status
Work in progress. Core inference engine and parsing logic are evolving.

## Contributing
See CONTRIBUTING.md for our branching, commit, and PR conventions.

---

### Table of Contents
- [0. Truth tables](#0-truth-tables)
- [1. Lexer - Transform text to tokens](#1-lexer---transform-text-to-tokens)
  - [1.1 Define the tokens type](#11-define-the-tokens-type)
  - [1.2 Lexer logic](#12-lexer-logic)
  - [1.3 Result](#13-result)
- [2. Parser - Build structures from the tokens](#2-parser---build-structures-from-the-tokens)
  - [2.1 Data structures](#21-data-structures)
  - [2.2 Parser skeleton](#22-parser-skeleton)
  - [2.3 Boolean expression parser](#23-boolean-expression-parser)
  - [2.4 Parse facts and queries](#24-parse-facts-and-queries)
- [3. Exec - Run the expert system](#3-exec---run-the-expert-system)
  - [3.1 Backward chaining](#31-backward-chaining)
  - [3.2 Preprocessing for backward chaining](#32-preprocessing-for-backward-chaining)
  - [3.3 State/memoization](#33-statememoization)
  - [3.4 Core: `solve(symbol)`](#34-core-solvesymbol)
  - [3.5 Expression evaluation](#35-expression-evaluation)
  - [3.6 Handling queries](#36-handling-queries)

# 0. Truth tables

# 1. Lexer - Transform text to tokens

## 1.1 Define the tokens type

| Token Name        | Description                        |
|-------------------|------------------------------------|
| `TOKEN_IDENT`     | An uppercase letter for a fact (A, B, C, ...) |
| `TOKEN_AND`       | AND operator                       |
| `TOKEN_OR`        | OR operator                        |
| `TOKEN_XOR`       | XOR operator                       |
| `TOKEN_NOT`       | NOT operator                       |
| `TOKEN_L_PAREN`  | Left parenthesis                   |
| `TOKEN_R_PAREN`  | Right parenthesis                  |
| `TOKEN_IMPLIES`   | Implication operator               |
| `TOKEN_IIF`       | If and only if operator            |
| `TOKEN_EQUAL`     | Equal operator                     |
| `TOKEN_QUERY`     | Query operator                     |
| `TOKEN_EOL`       | End of line                        |
| `TOKEN_EOF`       | End of file                        |

## 1.2 Lexer logic

For each character of the file:
- Ignore whitespace
- Handle comments (starts with `#`)
- Tokenize characters:
  - `A - Z` -> `TOKEN_IDENT`
  - `+` -> `TOKEN_AND`
  - `|` -> `TOKEN_OR`
  - `^` -> `TOKEN_XOR`
  - `!` -> `TOKEN_NOT`
  - `(` -> `TOKEN_L_PAREN`
  - `)` -> `TOKEN_R_PAREN`
  - `=>` -> `TOKEN_IMPLIES`
  - `<=>` -> `TOKEN_IIF`
  - `=` -> `TOKEN_EQUAL`
  - `?` -> `TOKEN_QUERY`
  - `\n` -> `TOKEN_EOL`
- When the end of the file is reached, emit `TOKEN_EOF`.

## 1.3 Result

The lexer produces a stream/list of tokens that will be easier for the parser to consume.

# 2. Parser - Build structures from the tokens

The parser will read the list of tokens to produce:
- A list of **rules**
- A set of **initial facts** 
- A list of **queries**

## 2.1 Data structures

Example pseudo-code:

```c
enum NodeType { SYMBOL, NOT, AND, OR, XOR }

struct Expr {
    NodeType type;
    Expr* left;    // for AND/OR/XOR
    Expr* right;   // for AND/OR/XOR
    Expr* child;   // for NOT
    char symbol;   // for SYMBOL (A, B, C...)
}

struct Rule {
    Expr* condition;   // left side of =>
    Expr* conclusion;  // in your project, often a single SYMBOL (C)
}

struct Program {
    List<Rule> rules;
    Set<char> facts;
    List<char> queries;
}
```

## 2.2 Parser skeleton

Pseudo-grammar:

```c
program    := rule_list fact_line query_line

rule_list  := (rule ENDLINE)*

rule       := expr "=>" expr_or_symbol

fact_line  := "=" ident_list

query_line := "?" ident_list

ident_list := IDENT*
```

## 2.3 Boolean expression parser

There is an operator priority to respect:
`!` > `+` > `^` > `|` plus parenthesis

Classic **recursive descent parser**:

```c
expr        := or_expr

or_expr     := xor_expr ( '|' xor_expr )*

xor_expr    := and_expr ( '^' and_expr )*

and_expr    := unary_expr ( '+' unary_expr )*

unary_expr  := '!' unary_expr
             | primary

primary     := IDENT
             | '(' expr ')'

```

For each rule:
- Parse **left side** with `expr`
- Consume `=>`
- Parse **right side**: here we have **single IDENT** (like `C`)

## 2.4 Parse facts and queries

- When you see `=`:
  - Read every `IDENT` on that line -> add each letter to `facts`.
- When you see `?`:
  - Read every `IDENT` on the line -> add each to `queries`.

# 3. Exec - Run the expert system

Now you have:
- `rules`: list of `Rule`
- `facts`: initial set of symbols that are true
- `queries`: list of symbols to evaluate

## 3.1 Backward Chaining

Backward chaining = **start from the query**, and ask: "Can I prove this symbol from facts and rules?" \
Instead of pushing facts forwards, you **pull** information from the goal.

So for each query `Q` we will call a function like:

```c
bool solve(symbol Q)
```

And this function will:
- Check if `Q` is in the initial facts -> then true.
- Otherwise, look for all rules that conclude `Q` (like `... => Q`)
- For each such rule, try to prove the **condition expression** of that rule.
  - If at least one rule's condition is true => Q is true.
- If no rule can prove it => Q is false.

The twist: \
Conditions are boolean expressions (AND, OR, XOR, NOT), and those expressions contains **other symbols** that may themselves need to be proved recursively.

## 3.2 Preprocessing for backward chaining

After parsing, build:

```c
rules_by_conclusion: Map<char, List<Rule>>
facts: Set<char>           // initial known true
queries: List<char>        // symbols to answer
```

Fill `rules_by_conclusion` like: 

```c
for rule in rules:
    let X = rule.conclusion.symbol
    rules_by_conclusion[X].append(rule)
```

## 3.3 State/memoization

We don't want infinite recursion with cycles like:

```c
A => B
B => A
```

So we keep a state map:

```c
enum Status { UNKNOWN, IN_PROGRESS, TRUE, FALSE }

status: Map<char, Status>
```

Initialize all seen symbols to `UNKNOWN`.

## 3.4 Core: `solve(symbol)`

Pseudo-code:

```c
bool solve(char S):
    // 1. Already computed?
    if status[S] == TRUE:
        return true
    if status[S] == FALSE:
        return false
    if status[S] == IN_PROGRESS:
        // cycle detected – treat as false (or handle specially)
        return false

    // 2. If S is in base facts → true
    if S in facts:
        status[S] = TRUE
        return true

    // 3. Mark we are currently trying to prove S
    status[S] = IN_PROGRESS

    // 4. Try all rules that conclude S
    for rule in rules_by_conclusion[S]:
        if eval_expr(rule.condition):   // uses solve() inside
            status[S] = TRUE
            return true

    // 5. No rule can prove S
    status[S] = FALSE
    return false
```

## 3.5 Expression evaluation

The magic part: `eval_expr` must be **goal-directed**.

We don't look into a static `value_map`; we call `solve()` when we hit a symbol.

```c
bool eval_expr(Expr* e):
    switch e.type:
        case SYMBOL:
            return solve(e.symbol)

        case NOT:
            return !eval_expr(e.child)

        case AND:
            return eval_expr(e.left) && eval_expr(e.right)

        case OR:
            return eval_expr(e.left) || eval_expr(e.right)

        case XOR:
            return eval_expr(e.left) != eval_expr(e.right)
```

This way:
- If we need `A` in some condition, we call `solve('A')`.
- `solve('A')` might:
  - Return true because `A` is a fact, or
  - Try to prove `A` from other rules.

Everything stays fully **recursive** and **lazy**: we only evaluate what is needed to answer the queries.

# 3.6 Handling queries

Once everything is set:

```c
for Q in queries:
    result = solve(Q)
    print Q, result ? "TRUE" : "FALSE"
```

Because of the memoization with `status`, if one query needs a symbol and another query reuses the same symbol, we **don't recompute** everything.
