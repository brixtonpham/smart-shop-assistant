# Close Issue

When completing an issue:

1. Ensure all tasks are checked in the issue

2. Update docs/plans/current_sprint.md - check off completed items

3. Create pull request:
```bash
gh pr create --base develop --title "feat: <description>" --body "Closes #$ARGUMENTS"
```

4. After PR is merged, update issue:
```bash
gh issue close $ARGUMENTS
gh issue edit $ARGUMENTS --add-label "status:done" --remove-label "status:in-progress"
```

5. Update memory with learnings:
   Add any new patterns or decisions to CLAUDE.md
