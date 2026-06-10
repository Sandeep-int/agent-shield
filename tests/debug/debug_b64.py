import base64

test_cases = [
    "bXVyZGVy",  # Should decode to "murder"
    "YTJsc2JBPT0=",  # Should decode to "a2lsbA==" then "kill"
]

for token in test_cases:
    print(f"\n{'='*60}")
    print(f"Token: {token}")
    print(f"{'='*60}")
    
    current = token
    for i in range(5):
        try:
            # Pad
            padded = current + "=" * (-len(current) % 4)
            print(f"[{i}] Padded: {padded}")
            
            # Decode
            decoded_bytes = base64.b64decode(padded, validate=False)
            print(f"[{i}] Decoded bytes: {decoded_bytes}")
            
            # To string
            decoded_str = decoded_bytes.decode("utf-8", errors="ignore")
            print(f"[{i}] Decoded string: '{decoded_str}'")
            print(f"[{i}] Length: {len(decoded_str)}")
            
            # Printable check
            printable_count = sum(1 for c in decoded_str if c.isprintable() or c.isspace())
            print(f"[{i}] Printable: {printable_count}/{len(decoded_str)} = {printable_count/len(decoded_str) if len(decoded_str) > 0 else 0:.2f}")
            
            if decoded_str == current:
                print(f"[{i}] No change - stopping")
                break
            
            current = decoded_str
            
        except Exception as e:
            print(f"[{i}] Error: {e}")
            break
    
    print(f"\nFinal result: '{current}'")
