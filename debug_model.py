from detectors.bert_classifier import BertClassifier
c = BertClassifier()
print("Model loaded successfully!")
print(f"Is 'What is Python?' an injection? {c.classify('What is Python?')['is_injection']}")