#!/usr/bin/env python3
import urllib.parse
import base64

# This looks like base64 OR hex - let me try both
triple = "JUU2JUFEJUEzJUU3JTg0JUI2"

# Try as base64
try:
    b64 = base64.b64decode(triple + "==")
    print(f"Base64: {b64}")
except:
    print("Not base64")

# It's actually %HEX format - let me decode it as URL
# %E6%AD%A3%E7%84%B6 would be Chinese chars
# But JUU2 means %U-encoded? Let me check the pattern
print(f"Original: {triple}")

# JU = %25 (percent) + U
# So JUU2 = %U + U2... this is Java/JavaScript unicode escape!
# OR it could be double-URL encoded where % became %25

# Let's try treating J as literal and UU2 as part of encoding
# Actually,

 looking at the pattern: J-U-U-2-J-U-F-D...
# This might be: %U escapes OR literal text

# Let me try hex decode of the string itself
try:
    from binascii import unhexlify
    hex_decode = unhexlify(triple.encode())
    print(f"Hex decode: {hex_decode}")
except Exception as e:
    print(f"Not hex: {e}")

# Check if it's custom encoding
print(f"Length: {len(triple)}")
print(f"Chars: {[c for c in triple]}")
