import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from torch.utils.data import DataLoader, Dataset
from datasets import load_dataset
import numpy as np
import os

# Where to save trained model
MODEL_SAVE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "bert_injection")

class PromptDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.encodings = tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=max_length,
            return_tensors='pt'
        )
        self.labels = torch.tensor(labels)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return {
            'input_ids': self.encodings['input_ids'][idx],
            'attention_mask': self.encodings['attention_mask'][idx],
            'labels': self.labels[idx]
        }

def train():
    print("Loading dataset...")
    ds = load_dataset('deepset/prompt-injections', revision="4f61ecb038e9c3fb77e21034b22511b523772cdd")
    
    train_texts = list(ds['train']['text'])
    train_labels = list(ds['train']['label'])
    test_texts = list(ds['test']['text'])
    test_labels = list(ds['test']['label'])

    print("Loading tokenizer...")
    tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased', revision="4f61ecb038e9c3fb77e21034b22511b523772cdd")

    print("Tokenizing data...")
    train_dataset = PromptDataset(train_texts, train_labels, tokenizer)
    test_dataset = PromptDataset(test_texts, test_labels, tokenizer)

    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=16)

    print("Loading model...")
    model = DistilBertForSequenceClassification.from_pretrained(
    'distilbert-base-uncased',
    revision="4f61ecb038e9c3fb77e21034b22511b523772cdd",
    num_labels=2
)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)

    # Train 3 epochs
    print("Training...")
    for epoch in range(3):
        model.train()
        total_loss = 0
        for batch in train_loader:
            optimizer.zero_grad()
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        print(f"Epoch {epoch+1}/3 - Loss: {avg_loss:.4f}")

        # Evaluate after each epoch
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for batch in test_loader:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                predictions = torch.argmax(outputs.logits, dim=1)
                correct += (predictions == labels).sum().item()
                total += labels.size(0)
        accuracy = correct / total * 100
        print(f"Epoch {epoch+1}/3 - Accuracy: {accuracy:.2f}%")

    # Save model
    os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
    model.save_pretrained(MODEL_SAVE_PATH)
    tokenizer.save_pretrained(MODEL_SAVE_PATH)
    print(f"Model saved to {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train()