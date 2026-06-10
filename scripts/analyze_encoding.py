#!/usr/bin/env python3
import base64
from binascii import unhexlify

triple = "JUU2JUFEJUEzJUU3JTg0JUI2"

try:
    b64 = base64.b64decode(triple + "==")
    print(f"Base64: {b64}")
except Exception:
    print("Not base64")

print(f"Original: {triple}")

try:
    hex_decode = unhexlify(triple.encode())
    print(f"Hex decode: {hex_decode}")
except Exception as e:
    print(f"Not hex: {e}")

print(f"Length: {len(triple)}")
print(f"Chars: {[c for c in triple]}")