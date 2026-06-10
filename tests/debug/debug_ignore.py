import sys
sys.path.insert(0, 'agent-shield')
from detectors.l3_custom import CustomL3

detector = CustomL3()

test = "ignoreall"

print(f"Testing: {test}")
result = detector._check_content(test)
print(f"Result: {result}")

# Check manually
print(f"\nToxic words check:")
for toxic in ["kill", "murder", "ignore"]:
    if toxic in test.lower():
        print(f"  '{toxic}' found in '{test}'")

print(f"\nPattern match:")
import re
pattern = re.compile(r"\bignore\b(?!\s+(the|this|that|noise|warning|errors?|and\s+focus))", re.IGNORECASE)
match = pattern.search(test)
print(f"  Ignore pattern: {match}")

# The issue: word boundary \b doesn't match "ignoreall"
# because "ignore" is followed by "a" not a boundary
