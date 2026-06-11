import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from detectors.l3_custom import CustomL3

detector = CustomL3()

test_input = "k1llc0mmand"

print(f"Testing: {test_input}")
print(f"=" * 80)

# Test leetspeak decode
leet_decoded = detector._decode_leetspeak(test_input)
print(f"Leet decoded: '{leet_decoded}'")
print(f"Has spaces: {' ' in leet_decoded}")
print(f"Changed: {leet_decoded != test_input}")

# Check variants from preprocessing
variants = detector._full_preprocessing(test_input)
print(f"\nPreprocessing variants ({len(variants)}):")
for i, v in enumerate(variants):
    print(f"  {i+1}. '{v}'")

# Check if each variant would decode differently
print(f"\nLeetspeak decode for each variant:")
for i, v in enumerate(variants):
    decoded = detector._decode_leetspeak(v)
    if decoded != v:
        print(f"  Variant {i+1}: '{v}' -> '{decoded}' (has spaces: {' ' in decoded})")
