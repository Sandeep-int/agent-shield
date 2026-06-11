import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from detectors.l3_custom import CustomL3

detector = CustomL3()

prompts = [
    "Use kill command to stop process",
    "Gracefully terminate hung processes",
    "How can I improve my cooking skills at home"
]

for prompt in prompts:
    print(f"\n{'='*80}")
    print(f"Testing: {prompt}")
    print(f"{'='*80}")
    
    # Check if toxic words are present
    prompt_lower = prompt.lower()
    for toxic in ["kill", "terminate"]:
        if toxic in prompt_lower:
            print(f"  Toxic word '{toxic}' found in prompt")
            
            # Check word boundary
            pattern = r'\b' + re.escape(toxic) + r'\b'
            if re.search(pattern, prompt_lower):
                print(f"  Word boundary match: YES")
            else:
                print(f"  Word boundary match: NO")
            
            # Check safe contexts
            if toxic in detector.safe_contexts:
                print(f"  Safe context patterns for '{toxic}':")
                for safe_pattern in detector.safe_contexts[toxic]:
                    match = re.search(safe_pattern, prompt_lower, re.IGNORECASE)
                    print(f"    Pattern: {safe_pattern}")
                    print(f"    Match: {'YES' if match else 'NO'}")
                    if match:
                        print(f"    Matched text: {match.group()}")
                        break
