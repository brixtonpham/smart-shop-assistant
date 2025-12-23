# Start New Feature

When starting a new feature:

1. First, check GitHub Issues for the task:
```bash
gh issue view $ARGUMENTS
```

2. Create feature branch:
```bash
git checkout develop
git pull origin develop
git checkout -b feature/ISSUE-$ARGUMENTS-<description>
```

3. Update issue status:
```bash
gh issue edit $ARGUMENTS --add-label "status:in-progress" --remove-label "status:todo"
```

4. Read the issue requirements and create a plan in docs/plans/current_sprint.md

5. Commit the plan:
```bash
git add docs/plans/current_sprint.md
git commit -m "docs(plan): add implementation plan for issue #$ARGUMENTS"
```

Now ready to implement!
