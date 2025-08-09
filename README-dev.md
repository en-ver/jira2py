# jira2py

## Upgrade dependencies

List the installed packages:

```bash
uv pip list | grep -f requirements.txt
```

> [!NOTE]
> Dependencies are now specified with compatible version ranges (e.g., `>=X.Y.Z,<X.Y+1.0`) instead of exact pins to allow for easier security updates while maintaining stability.
