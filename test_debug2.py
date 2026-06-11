from detectors.l3_custom import CustomL3
import re

l3 = CustomL3()
test1 = "Use kill command to terminate hung processes"

print("Original:", test1)
print("\nChecking safe patterns for 'kill':")
for pattern in l3.safe_contexts["kill"]:
    match = re.search(pattern, test1.lower(), re.IGNORECASE)
    print(f"  Pattern: {pattern}")
    print(f"  Match: {match}")

print("\nVariants:")
variants = l3._full_preprocessing(test1)
for i, v in enumerate(variants):
    print(f"{i}: {repr(v)}")
    # Check if kill is in this variant
    if re.search(r'\bkill\b', v.lower()):
        print(f"   ^ Contains 'kill' as word")
    if 'kill' in v.lower() and ' ' not in v:
        print(f"   ^ Contains 'kill' substring (no spaces)")
