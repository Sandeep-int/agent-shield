import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from detectors.l3_custom import CustomL3

detector = CustomL3()

# Manually test the leetspeak layer logic
variant = "k1llc0mmand"
leet_decoded = detector._decode_leetspeak(variant)

print(f"Variant: {variant}")
print(f"Leet decoded: {leet_decoded}")
print(f"Changed: {leet_decoded != variant}")
print(f"Has no spaces: {' ' not in leet_decoded}")

if leet_decoded != variant and ' ' not in leet_decoded:
    print("\nCondition MET - should check for toxic words")
    leet_lower = leet_decoded.lower()
    for toxic in detector.toxic_words:
        import re
        pattern = r'\b' + re.escape(toxic) + r'\b'
        if re.search(pattern, leet_lower):
            print(f"  Found toxic word: {toxic}")
            print(f"  Pattern: {pattern}")
            print(f"  Would BLOCK")
            break
else:
    print("\nCondition NOT MET")

# Now test full check
print(f"\n{'='*80}")
print("Full check result:")
result = detector.check(variant)
print(f"  Passed: {result['passed']}")
print(f"  Reason: {result['reason']}")
print(f"  Layer: {result['layer']}")
