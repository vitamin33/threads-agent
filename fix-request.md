The CI pipeline has failed. Please analyze the errors and fix them.

Error Summary:
Error: failed post-install: 1 error occurred:
failed: 0, jobs succeeded: 0
failed: Get "http://10.42.0.13:8080/health": dial tcp 10.42.0.13:8080: connect: connection refused

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
