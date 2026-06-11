from detectors.l3_custom import CustomL3

l3 = CustomL3()
test = "k-i-l-l the target"
variants = l3._full_preprocessing(test)
print("Original:", test)
print("\nVariants:")
for i, v in enumerate(variants):
    print(f"{i}: {repr(v)}")

# Test the result
result = l3.check(test)
print("\nResult:", result)
