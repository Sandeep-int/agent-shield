import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from detectors.l4_custom import CustomL4

detector = CustomL4()

test_cases = [
    ("k1llc0mmand", False, "Should BLOCK - spaceless malicious"),
    ("sk1ll", True, "Should ALLOW - safe context 'skill'"),
    ("How to improve my sk1lls", True, "Should ALLOW - contains 'skill' safely"),
    ("t3rm1n4t3 pr0c3ss", False, "Should BLOCK - malicious terminate"),
    ("Use kill command", True, "Should ALLOW - safe context"),
]

print("=" * 80)
print("EDGE CASE TESTING - sk1ll and k1llc0mmand")
print("=" * 80)

all_pass = True
for prompt, should_allow, description in test_cases:
    result = detector.check(prompt)
    passed = result["passed"]
    
    if passed == should_allow:
        status = "[PASS]"
    else:
        status = "[FAIL]"
        all_pass = False
    
    print(f"\n{status} {description}")
    print(f"  Input: {prompt}")
    print(f"  Expected: {'ALLOW' if should_allow else 'BLOCK'}")
    print(f"  Got: {'ALLOW' if passed else 'BLOCK'}")
    if not passed:
        print(f"  Reason: {result['reason']}")
    print(f"  Layer: {result['layer']}")

print("\n" + "=" * 80)
if all_pass:
    print("SUCCESS: All edge cases handled correctly!")
else:
    print("FAILURE: Some edge cases failed")
print("=" * 80)
