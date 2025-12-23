# Commit Work

After completing a logical unit of work:

1. Stage changes:
```bash
git add -A
```

2. Run linter:
```bash
uv run ruff check . --fix
uv run ruff format .
```

3. Commit with proper format:
```bash
git commit -m "<type>(<scope>): <message> [#ISSUE]"
```

Types: feat, fix, docs, refactor, test, chore

Examples:
- feat(inventory): add check_stock tool [#5]
- fix(rag): handle empty search results [#11]
- docs(readme): add setup instructions [#1]

4. Push to remote:
```bash
git push origin HEAD
```
