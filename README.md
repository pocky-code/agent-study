# agent-study

Minimal Python project scaffold with a small example package and tests.

Try it:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; pytest -q
```

For lambda(ローカルでインストールするとWindows OSに最適化され、LambdaのOS上では動かないことがある。Dockerを入れてもよいがその代替として)
pip install `
  --platform manylinux2014_x86_64 `
  --target . `
  --implementation cp `
  --python-version 3.12 `
  --only-binary=:all: `
  -r ../requirements.txt