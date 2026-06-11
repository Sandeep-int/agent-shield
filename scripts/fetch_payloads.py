import os
import pandas as pd
from datasets import load_dataset

OUTPUT_FILE = "data/training_data.csv"

def fetch_and_build_dataset():
    print("[+] Initializing clean-room dataset pipeline...")
    os.makedirs("data", exist_ok=True)

    payloads = []
    labels = []

    # ── Block 1: neuralchemy (label=1, with FP reclassification)
    try:
        print("[+] Fetching neuralchemy/Prompt-injection-dataset...")
        ds = load_dataset("neuralchemy/Prompt-injection-dataset", revision="7d70432dfcf47a821612cbf9d34e9d9e3ad20e75", split="train")
        FP_KEYWORDS = [
            "best practices", "secure coding", "dependency injection",
            "spring boot", "bypass the cache", "fetch fresh data",
            "deployment script", "research paper", "adversarial machine learning",
            "reset my password", "prompt engineering", "filter input",
            "summarize", "clean document"
        ]
        skipped = 0
        for item in ds:
            text = item["text"]
            if any(kw.lower() in text.lower() for kw in FP_KEYWORDS):
                payloads.append(text); labels.append(0); skipped += 1
            else:
                payloads.append(text); labels.append(1)
        print(f"    Rows: {len(ds)} | Reclassified benign: {skipped}")
    except Exception as e:
        print(f"[-] neuralchemy failed: {e}")

    # ── Block 2: JailbreakBench (label=1)
    try:
        print("[+] Fetching JailbreakBench/JBB-Behaviors...")
        jbb = load_dataset("JailbreakBench/JBB-Behaviors", revision="886acc352a31533ffbcf4ef22c744658688086fc", split="train")
        added = 0
        for item in jbb:
            text = item.get("Goal") or item.get("goal") or item.get("behavior") or ""
            if text.strip():
                payloads.append(text.strip()); labels.append(1); added += 1
        print(f"    Rows: {added}")
    except Exception as e:
        print(f"[-] JBB failed: {e}")
        try:
            jbb_check = load_dataset("JailbreakBench/JBB-Behaviors", revision="886acc352a31533ffbcf4ef22c744658688086fc", split="train")
            print(f"    Available columns: {jbb_check.column_names}")
        except Exception as e:
            print(f"    Column check also failed: {e}")

    # ── Block 3: Harelix mixed techniques (label=1)
    try:
        print("[+] Fetching Harelix/Prompt-Injection-Mixed-Techniques-2024...")
        ds_harelix = load_dataset("Harelix/Prompt-Injection-Mixed-Techniques-2024", split="train") # nosec B615 Harelix dataset
        added = 0
        for item in ds_harelix:
            text = item.get("prompt") or item.get("text") or item.get("instruction") or ""
            if text.strip():
                payloads.append(text.strip()); labels.append(1); added += 1
        print(f"    Rows: {added}")
    except Exception as e:
        print(f"[-] Harelix failed: {e}")

    # ── Block 4: jackhhao jailbreak-classification (mixed labels)
    try:
        print("[+] Fetching jackhhao/jailbreak-classification...")
        ds_jack = load_dataset("jackhhao/jailbreak-classification", revision="2f2ceeb39658696fd3f462403562b6eea5306287", split="train")
        added_mal = 0; added_ben = 0
        for item in ds_jack:
            text = item.get("prompt") or item.get("text") or ""
            if not text.strip():
                continue
            if item.get("type") == "jailbreak":
                payloads.append(text.strip()); labels.append(1); added_mal += 1
            else:
                payloads.append(text.strip()); labels.append(0); added_ben += 1
        print(f"    Rows: {added_mal + added_ben} (malicious: {added_mal}, benign: {added_ben})")
    except Exception as e:
        print(f"[-] jackhhao failed: {e}")

    # ── Block 5: OpenSafetyLab Salad-Data (label=1)
    try:
        print("[+] Fetching OpenSafetyLab/Salad-Data...")
        ds_salad = load_dataset("OpenSafetyLab/Salad-Data", name="base_set", revision="70a1ddce6be3f0239b2fe7c70d0d96cb3be1fcad", split="train")
        added = 0
        for item in ds_salad:
            text = item.get("question") or ""
            if text.strip():
                payloads.append(text.strip()); labels.append(1); added += 1
        print(f"    Rows: {added}")
    except Exception as e:
        print(f"[-] Salad-Data failed: {e}")

    # ── Block 6: deepset classic baseline (native labels)
    try:
        print("[+] Fetching deepset/prompt-injections...")
        ds_deepset = load_dataset("deepset/prompt-injections", revision="4f61ecb038e9c3fb77e21034b22511b523772cdd", split="train")
        added = 0
        for item in ds_deepset:
            text = item.get("text") or ""
            if text.strip():
                payloads.append(text.strip()); labels.append(item["label"]); added += 1
        print(f"    Rows: {added}")
    except Exception as e:
        print(f"[-] deepset failed: {e}")

    # ── Block 7: Benign counterweights (label=0)
    try:
        print("[+] Fetching HuggingFaceH4/grok-conversation-harmless...")
        ds_b1 = load_dataset("HuggingFaceH4/grok-conversation-harmless", revision="01185ad52860775c65cbd6d0c9254ac8e9089fe0", split="train_sft")
        added = 0
        for item in ds_b1:
            text = item.get("prompt") or item.get("init_prompt") or item.get("text") or ""
            if text.strip():
                payloads.append(text.strip()); labels.append(0); added += 1
        print(f"    Rows: {added}")
    except Exception as e:
        print(f"[-] grok-harmless failed: {e}")

    try:
        print("[+] Fetching alespalla/chatbot_instruction_prompts...")
        ds_b2 = load_dataset("alespalla/chatbot_instruction_prompts", revision="6ea5ce09647e5451860801a46db6a46b28e259bf", split="train")
        added = 0
        for item in ds_b2:
            text = item.get("prompt") or item.get("text") or ""
            if text.strip():
                payloads.append(text.strip()); labels.append(0); added += 1
        print(f"    Rows: {added}")
    except Exception as e:
        print(f"[-] chatbot_instruction failed: {e}")

    # ── Finalize
    df = pd.DataFrame({"prompt": payloads, "label": labels})
    df = df.drop_duplicates(subset="prompt").reset_index(drop=True)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    malicious = int(df["label"].sum())
    benign = len(df) - malicious

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n[✓] Dataset saved → {OUTPUT_FILE}")
    print(f"    Total rows : {len(df)}")
    print(f"    Malicious  : {malicious}")
    print(f"    Benign     : {benign}")
    print(f"    Balance    : {benign/malicious:.2f}:1")

if __name__ == "__main__":
    fetch_and_build_dataset()
