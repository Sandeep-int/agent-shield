import os
import pandas as pd
from datasets import load_dataset

OUTPUT_FILE = "data/training_data.csv"

def fetch_and_build_dataset():
    print("[+] Initializing clean-room dataset pipeline...")
    os.makedirs("data", exist_ok=True)
    
    payloads = []
    labels = []
    
    # 1. Fetch Real Malicious Prompt Injections (Label = 1)
    try:
        print("[+] Fetching neuralchemy/Prompt-injection-dataset...")
        ds_injection = load_dataset("neuralchemy/Prompt-injection-dataset", split="train")
        for item in ds_injection:
            payloads.append(item["text"])
            labels.append(1)
    except Exception as e:
        print(f"[-] Failed to fetch neuralchemy dataset: {e}")

    # 2. Append Explicit Benign Counterweights (Label = 0)
    # These are the EXACT prompts you listed, properly re-mapped to 0 (Benign)
    print("[+] Stitching verified benign engineering counterweights...")
    true_benign = [
        "What are the best practices for secure coding in Python?",
        "Can you help me write a Python script that filters input from users?",
        "What does 'prompt engineering' mean?",
        "Execute the deployment script and push the changes to production.",
        "Please bypass the cache and fetch fresh data from the API.",
        "Forget the previous draft and start with a clean document.",
        "How do I inject a dependency in a Spring Boot application?",
        "Can you summarize this research paper on adversarial machine learning?",
        "How do I reset my password if I forgot it?"
    ]
    
    # Balance out the dataset size 1:1 using standard systems queries
    extended_benign = true_benign * (len(payloads) // len(true_benign) + 1)
    extended_benign = extended_benign[:len(payloads)]
    
    payloads.extend(extended_benign)
    labels.extend([0] * len(extended_benign))

    # Save to workspace target directory
    df = pd.DataFrame({"prompt": payloads, "label": labels})
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"[✓] Success. Fixed dataset saved to {OUTPUT_FILE}")
    print(f"Total rows compiled: {len(df)}")

if __name__ == "__main__":
    fetch_and_build_dataset()