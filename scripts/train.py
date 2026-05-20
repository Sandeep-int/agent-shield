import pandas as pd
from transformers import DistilBertForSequenceClassification, DistilBertTokenizer, Trainer, TrainingArguments
from datasets import Dataset

# 1. Load your training data
df = pd.read_csv("data/training_data.csv")
dataset = Dataset.from_pandas(df)

# 2. Tokenize (Crucial: convert text to numbers the model understands)
tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
def tokenize_function(examples):
    return tokenizer(examples["prompt"], padding="max_length", truncation=True)

tokenized_datasets = dataset.map(tokenize_function, batched=True)

# 3. Initialize the model for 2 classes (0: Clean, 1: Malicious)
model = DistilBertForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=2)

# 4. Training Arguments
training_args = TrainingArguments(
    output_dir="./models/fine_tuned_bert",
    num_train_epochs=5, # Slightly higher for small datasets
    per_device_train_batch_size=4,
    save_strategy="no"
)

# 5. Trainer & Execute
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets,
)

trainer.train()
model.save_pretrained("./models/fine_tuned_bert")
tokenizer.save_pretrained("./models/fine_tuned_bert")
print("Training complete. Hardened model saved to ./models/fine_tuned_bert")