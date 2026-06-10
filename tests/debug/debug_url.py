#!/usr/bin/env python3
import urllib.parse

# Test triple encoding
triple = "JUU2JUFEJUEzJUU3JTg0JUI2"
step1 = urllib.parse.unquote(triple)
print(f"Triple Step 1: {step1}")
step2 = urllib.parse.unquote(step1)
print(f"Triple Step 2: {step2}")
step3 = urllib.parse.unquote(step2)
print(f"Triple Step 3: {step3}")

print()

# Test single encoding
single = "%69%67%6e%6f%72%65%20%61%6c%6c"
decoded = urllib.parse.unquote(single)
print(f"Single decoded: {decoded}")
