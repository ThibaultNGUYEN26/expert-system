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

Use the following naming convention for issue titles:
- `[Feature] <short description>` → for new features
- `[Bug] <short description>` → for bugs
- `[Docs] <short description>` → for documentation tasks
- `[Chore] <short description>` → for maintenance

⚠️ The brackets `[]` indicate the **category label**.
Replace the text inside with the type of issue.
Do **not** include the brackets themselves in the description.

### Examples
- `[Feature] Add backward chaining`
- `[Bug] Infinite loop in inference engine`
- `[Docs] Add usage section to README`
- `[Chore] Setup GitHub Actions workflow`

---
