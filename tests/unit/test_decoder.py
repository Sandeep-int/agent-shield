import sys
import re
import base64
import string

sys.path.insert(0, 'agent-shield')
from detectors.l4_custom import CustomL4

detector = CustomL4()

test = "bXVyZGVy"
print(f"Testing: {test}")
print()

# Call the function directly
result = detector._try_decode_base64_single(test)
print(f"Result: '{result}'")
print()

# Manual step-by-step
print("Manual step-by-step:")
current = test
for i in range(5):
    print(f"\n[{i}] Current: '{current}'")
    
    # Check format
    is_b64_format = re.match(r'^[A-Za-z0-9+/]+={0,2}$', current)
    print(f"[{i}] Is Base64 format: {bool(is_b64_format)}")
    
    if not is_b64_format:
        print(f"[{i}] Not Base64 format - stopping")
        break
    
    try:
        padded = current + "=" * (-len(current) % 4)
        print(f"[{i}] Padded: '{padded}'")
        
        decoded_bytes = base64.b64decode(padded, validate=True)
        print(f"[{i}] Decoded bytes: {decoded_bytes}")
        
        decoded_str = decoded_bytes.decode("utf-8", errors="ignore")
        print(f"[{i}] Decoded string: '{decoded_str}'")
        
        if not decoded_str:
            print(f"[{i}] Empty - stopping")
            break
        
        printable = sum(1 for c in decoded_str if c.isprintable() or c.isspace())
        ratio = printable / len(decoded_str)
        print(f"[{i}] Printable: {printable}/{len(decoded_str)} = {ratio:.2f}")
        
        if ratio < 0.8:
            print(f"[{i}] Low printability - stopping")
            break
        
        if decoded_str == current:
            print(f"[{i}] No change - stopping")
            break
        
        current = decoded_str
        
    except Exception as e:
        print(f"[{i}] Exception: {e}")
        break

print(f"\nFinal: '{current}'")
