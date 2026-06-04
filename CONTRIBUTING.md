# Contributing to Agent Shield

## How to Contribute
1. Fork the repo
2. Create feature branch: `git checkout -b fix/your-fix`
3. Make changes
4. Run pre-push checklist
5. Push and raise PR

## Pre-Push Checklist
```bash
grep -rn "<<<\|===\|>>>" detectors/ api/
python3 -c "import ast; ast.parse(open('api/main.py').read()); print('OK')"
bandit -r detectors/ api/ app.py -ll -x ./.venv
```

## Rules
- Never push to main directly
- Never commit .onnx or .bin files
- All PRs must pass CI before merge
- One fix per PR
