# CI/CD

This project uses GitHub Actions for a lightweight Windows-first CI/CD process.

## Workflow

Workflow file:

```text
.github\workflows\ci.yml
```

Triggers:

- Every push
- Every pull request
- Manual runs from GitHub Actions with **Run workflow**

## CI Validation

The `validate` job runs on `windows-latest` and checks:

- Python 3.12 dependency installation
- Backend module compilation
- API contract tests
- Rainmeter WebParser compatibility against API JSON
- Safety boundary tests that reject private API key and order-placement code

The tests do not call Binance. They use deterministic market history so CI is
stable, fast, and safe.

## CD Artifact

The `package` job runs after validation on pushes and manual workflow runs. It
creates:

```text
quant-trading-rainmeter-hud.zip
```

The artifact includes:

- `api`
- `rainmeter`
- `docs`
- `README.md`
- `AGENTS.md`
- `LICENSE`
- `.gitignore`

This is delivery packaging only. It does not deploy a live service and does not
enable trading.

## Auto-Commit Workflow

Workflow file:

```text
.github\workflows\auto-commit.yml
```

This workflow is manual only. It is started from GitHub Actions with
**Run workflow** and requires a target branch.

What it does:

1. Checks out the selected branch.
2. Installs dependencies.
3. Runs compile and contract tests.
4. Regenerates:

```text
docs\build-manifest.json
```

5. Commits the manifest if it changed.
6. Pushes the commit back to the selected branch using GitHub's built-in
   `GITHUB_TOKEN`.

The default commit message includes:

```text
[skip ci]
```

This prevents an infinite CI loop after the workflow pushes its own manifest
commit.

The workflow only stages `docs/build-manifest.json`. It does not commit runtime
SQLite databases, logs, virtual environments, or package zip files.

## Local Equivalent

Run the same validation locally:

```powershell
python -m pip install -r api\requirements.txt
python -m pip install -r api\requirements-dev.txt
python -m compileall api
python -m pytest -q
python scripts\generate_build_manifest.py --output docs\build-manifest.json
```

## Safety Boundary

CI/CD must stay monitoring-only:

- No API keys
- No private exchange endpoints
- No order placement
- No real trading execution

Auto-commit permissions are limited to repository contents and are only used by
the manual manifest workflow.
