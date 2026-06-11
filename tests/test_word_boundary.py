import re

text = "killcommand"
toxic_words = ["kill", "murder", "terminate", "execute"]

print(f"Testing word boundaries on: '{text}'")
print(f"=" * 80)

for toxic in toxic_words:
    pattern = r'\b' + re.escape(toxic) + r'\b'
    match = re.search(pattern, text)
    print(f"Toxic: '{toxic}'")
    print(f"  Pattern: {pattern}")
    print(f"  Match: {match}")
    if match:
        print(f"  Matched: '{match.group()}'")
    print()
