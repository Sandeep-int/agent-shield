import sys
sys.path.insert(0, 'agent-shield')
from detectors.l3_custom import CustomL3

detector = CustomL3()

payload = "bXVyZGVy"  # Base64: murder

print(f"Testing payload: {payload}")
print(f"Expected: murder")
print()

# Step 1: Check original
print("Step 1: Check original")
result = detector._check_content(payload)
print(f"  Result: {result}")
print()

# Step 2: Get variants
print("Step 2: Get preprocessing variants")
variants = detector._full_preprocessing(payload)
print(f"  Variants ({len(variants)}):")
for i, v in enumerate(variants):
    print(f"    [{i}] {v}")
print()

# Step 3: Check each variant
print("Step 3: Check each variant")
for i, v in enumerate(variants):
    result = detector._check_content(v)
    print(f"  [{i}] '{v}' -> {result}")
print()

# Step 4: Base64 decode each variant
print("Step 4: Base64 decode each variant")
for i, v in enumerate(variants):
    b64 = detector._decode_base64_aggressive(v)
    print(f"  [{i}] '{v}' -> '{b64}'")
    if b64 != v:
        result = detector._check_content(b64)
        print(f"       Check: {result}")
print()

# Step 5: Full check
print("Step 5: Full check()")
result = detector.check(payload)
print(f"  Result: {result}")
