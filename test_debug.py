from detectors.l3_custom import CustomL3

l3 = CustomL3()

test1 = "Use kill command to terminate hung processes"
test2 = "Terminate EC2 instances to reduce costs"

print("Test 1:", test1)
result1 = l3.check(test1)
print("Result:", result1)
print()

print("Test 2:", test2)
result2 = l3.check(test2)
print("Result:", result2)
