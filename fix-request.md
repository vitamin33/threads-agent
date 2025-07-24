The CI pipeline has failed. Please analyze the errors and fix them.

Error Summary:
Error: 'client rate limiter Wait returned an error: context deadline exceeded', Resource details: 'Resource: "/v1, Resource=services", GroupVersionKind: "/v1, Kind=Service"
Error: context deadline exceeded
error: code = Unknown desc = failed to pull and unpack image "docker.io/library/celery-worker:local": failed to resolve reference "docker.io/library/celery-worker:local": pull access denied, repository does not exist or may require authorization: server message: insufficient_scope: authorization failed
Error: ErrImagePull
error: code = Unknown desc = failed to pull and unpack image "docker.io/library/persona-runtime:local": failed to resolve reference "docker.io/library/persona-runtime:local": pull access denied, repository does not exist or may require authorization: server message: insufficient_scope: authorization failed
error: code = Unknown desc = failed to pull and unpack image "docker.io/library/fake-threads:local": failed to resolve reference "docker.io/library/fake-threads:local": pull access denied, repository does not exist or may require authorization: server message: insufficient_scope: authorization failed
error: code = Unknown desc = failed to pull and unpack image "docker.io/library/orchestrator:local": failed to resolve reference "docker.io/library/orchestrator:local": pull access denied, repository does not exist or may require authorization: server message: insufficient_scope: authorization failed
error: code = Unknown desc = failed to pull and unpack image "docker.io/library/viral-engine:local": failed to resolve reference "docker.io/library/viral-engine:local": pull access denied, repository does not exist or may require authorization: server message: insufficient_scope: authorization failed
Error: ImagePullBackOff

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
