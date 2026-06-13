# Contributing to Agent Shield

Agent Shield is open source. All contributions are welcome — bug fixes, 
new attack pattern rules, dataset improvements, and documentation.

## How to Contribute

1. Fork the repo
2. Create a feature branch: `git checkout -b fix/your-fix`
3. Make your changes
4. Run the pre-push checklist (see below)
5. Push and raise a PR against `main`

## Pre-Push Checklist

Run all of these before every push. CI will catch failures — but 
fix them locally first.

```bash
# 1. Conflict markers
grep -rn "<<<\|===\|>>>" detectors/ api/
# Must return empty

# 2. Syntax check
python3 -c "import ast; ast.parse(open('api/main.py').read()); print('OK')"
python3 -c "import ast; ast.parse(open('detectors/l3_custom.py').read()); print('OK')"

# 3. Security scan
bandit -r detectors/ api/ app.py -ll -x ./.venv
# Must show 0 High, 0 Medium

# 4. Full test suite
python3 -m pytest tests/ -v --tb=short \
  --ignore=tests/test_rate_limit.py \
  --ignore=tests/test_sanitize.py \
  --ignore=tests/test_l2_bert.py \
  --ignore=tests/manual/
# Must show 146 passed (or more)
```

## Rules

- Never push directly to `main` — always branch → PR → CI green → merge
- Never commit `.onnx`, `.bin`, or model weight files
- All PRs must pass CI (pytest + Bandit gate) before review
- One fix per PR — keep scope tight
- Git commit messages under 72 characters

## Found a Security Issue?

Do not open a public issue. See [SECURITY.md](./SECURITY.md).
