# Contributing

## Branching

We use GitHub Flow:
- Work from `main`.
- Create a branch for each change.
- Use lowercase, hyphens for spaces.

Branch types:
- `feat/<scope>-<desc>` — new feature
- `fix/<scope>-<desc>` — bug fix
- `docs/<scope>-<desc>` — documentation
- `chore/<scope>-<desc>` — setup, maintenance
- `refactor/<scope>-<desc>` — reorganization without new features
- `test/<scope>-<desc>` — testing only

### Examples
- `feat/parser-handle-negation`
- `fix/inference-stack-overflow`
- `docs/readme-installation`
- `chore/setup-precommit`

---

## Commits

We use [Conventional Commits](https://www.conventionalcommits.org/).

Format:
```
<type>(<scope>): <short imperative summary>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

### Examples
- `feat(parser): add support for XOR operator`
- `fix(engine): prevent infinite loop in backward chaining`
- `docs(readme): add usage section`
- `refactor(kb): simplify rule normalization`
- `test(parser): add unit tests for parentheses support`

### Breaking changes
If your change breaks compatibility:
```
feat(engine)!: change inference API to return trace

BREAKING CHANGE: trace() is now returned by default
```

---

## Pull Requests

- Keep PRs focused and small.
- Title = main commit message (Conventional Commit format).
- Use **Draft PRs** if not finished.
- Link issues in the description (`Closes #42`).
- Squash and merge after approval.

### Example PR title
```
feat(parser): add support for negation operator
```

### Example PR description
```
This PR adds support for the "!" operator in the parser.

Updated tokenizer to recognize "!"

Modified parser to handle negated facts

Added unit tests

Closes #17
```

---

## Issues

When creating an issue:
1. Add context (what’s the problem?).
2. Describe the expected solution.
3. Define acceptance criteria (how we know it’s done).

### Example feature issue
**Title:** `[Feature] Add backward chaining`
**Description:**
- Implement backward chaining algorithm.
- Must support AND/OR rules.
- Stop on circular dependencies.

**Acceptance criteria:**
- Given ruleset X, query Y returns expected result.
- Tests cover edge cases (circular, undefined facts).

---
