import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import (
    DistilBertForSequenceClassification,
    DistilBertTokenizer,
    Trainer,
    TrainingArguments
)
from datasets import Dataset
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, classification_report

# ── 1. Load + split
df = pd.read_csv("data/prompt_injection_dataset.csv").dropna(subset=["prompt", "label"])
df["label"] = df["label"].astype(int)

train_df, eval_df = train_test_split(df, test_size=0.15, random_state=42, stratify=df["label"])
train_dataset = Dataset.from_pandas(train_df.reset_index(drop=True))
eval_dataset  = Dataset.from_pandas(eval_df.reset_index(drop=True))

print(f"Train: {len(train_df)} | Eval: {len(eval_df)}")

# ── 2. Tokenize
tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")

def tokenize(examples):
    return tokenizer(examples["prompt"], padding="max_length", truncation=True, max_length=256)

train_dataset = train_dataset.map(tokenize, batched=True)
eval_dataset  = eval_dataset.map(tokenize, batched=True)

# ── 3. Metrics
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    print("\n" + classification_report(labels, preds, target_names=["Benign", "Malicious"]))
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1":       f1_score(labels, preds, average="weighted")
    }

# ── 4. Model
model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased", num_labels=2
)

# ── 5. Training args — CPU optimized
training_args = TrainingArguments(
    output_dir="./models/fine_tuned_bert",
    num_train_epochs=3,               # 3 sufficient for large dataset
    per_device_train_batch_size=16,   # was 4 — 4x faster
    per_device_eval_batch_size=32,
    eval_strategy="epoch",            # accuracy visible each epoch
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    logging_steps=50,
    report_to="none",                 # no wandb crash
    dataloader_num_workers=0,         # WSL safe
)

# ── 6. Train
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    compute_metrics=compute_metrics,
)

trainer.train()

# ── 7. Save best model
trainer.save_model("./models/fine_tuned_bert")
tokenizer.save_pretrained("./models/fine_tuned_bert")
print("\n[✓] Best model saved → ./models/fine_tuned_bert")