# Code Review Checklist

Review the following aspects:

## Code Quality
- [ ] Type hints on all functions
- [ ] Docstrings for public functions (Google style)
- [ ] No print() statements (use logging)
- [ ] Proper error handling

## MCP Patterns
- [ ] Tools return Pydantic models
- [ ] Resources use correct URI patterns
- [ ] Proper async/await usage
- [ ] SSE transport configured correctly

## Testing
- [ ] Unit tests for new functions
- [ ] Edge cases covered
- [ ] Test isolation (no external dependencies)

## Security
- [ ] No hardcoded secrets
- [ ] Input validation
- [ ] SQL injection prevention
- [ ] XSS prevention (if applicable)

## Documentation
- [ ] README updated if needed
- [ ] API changes documented
- [ ] Architecture docs updated
