The CI pipeline has failed. Please analyze the errors and fix them.

Error Summary:
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
Error: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'
failed: 0, jobs succeeded: 0
TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'

Full logs are available in ci-failure-logs.txt

Please:
1. Analyze the CI failure logs
2. Identify the root cause of the failures
3. Make the necessary code changes to fix the issues
4. Ensure the fix is minimal and targeted
5. Do not modify unrelated code

Focus on these types of common CI failures:
- Test failures (unit or e2e)
- Linting errors (ruff, black, isort)
- Type checking errors (mypy)
- Import errors
- Syntax errors
- Configuration issues

After making fixes, provide a summary of what was changed and why.
