import pandas as pd
import random
import torch
from torch.utils.data import Dataset
from transformers import (
    T5Tokenizer,
    T5ForConditionalGeneration,
    Trainer,
    TrainingArguments,
    DataCollatorForSeq2Seq,
)
import os

csv_file_path = 'vocabulary.csv'
df = pd.read_csv(csv_file_path)

vocabulary = []
for col in df.columns:
    words = df[col].dropna().astype(str).tolist()
    vocabulary.extend(words)

russian_letters = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'

def simulate_complex_typo(word, error_rate=0.9):
    """Simulates a single typo (deletion, insertion, substitution, transposition)."""
    if not isinstance(word, str) or len(word) < 1 or random.random() > error_rate:
        return word
    possible_errors = ['insertion', 'substitution']
    if len(word) >= 1: possible_errors.append('deletion')
    if len(word) >= 2: possible_errors.append('transposition')
    error_type = random.choice(possible_errors)
    try:
        if error_type == 'deletion':
            idx = random.randint(0, len(word) - 1)
            return word[:idx] + word[idx+1:]
        elif error_type == 'insertion':
            idx = random.randint(0, len(word))
            return word[:idx] + random.choice(russian_letters) + word[idx:]
        elif error_type == 'substitution':
            idx = random.randint(0, len(word) - 1)
            return word[:idx] + random.choice(russian_letters) + word[idx+1:]
        elif error_type == 'transposition':
            idx = random.randint(0, len(word) - 2)
            chars = list(word)
            chars[idx], chars[idx+1] = chars[idx+1], chars[idx]
            return ''.join(chars)
    except Exception:
        return word 
    return word

training_pairs = []
num_variants_per_word = 100 
task_prefix = "correct: "

for word in vocabulary:
    if not isinstance(word, str) or not word: continue
    for _ in range(num_variants_per_word):
        misspelled = simulate_complex_typo(word)
        if misspelled != word and misspelled:
            training_pairs.append((task_prefix + misspelled, word))

print(f"Training pairs were generated.")
if not training_pairs:
    raise ValueError("No training pairs were generated. Check vocabulary or typo simulation.")

class CorrectionDataset(Dataset):
    def __init__(self, pairs, tokenizer, max_len=32):
        self.pairs = pairs
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        source_text, target_text = self.pairs[idx]

        source_encoding = self.tokenizer(
            source_text,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )


        target_encoding = self.tokenizer(
            text_target=target_text,
            max_length=self.max_len,
            padding="max_length", 
            truncation=True,
            return_tensors="pt"
        )

        labels = target_encoding["input_ids"]
        labels[labels == self.tokenizer.pad_token_id] = -100
        return {
            "input_ids": source_encoding.input_ids.squeeze(0),
            "attention_mask": source_encoding.attention_mask.squeeze(0),
            "labels": labels.squeeze(0)
        }

model_name = "t5-small"
tokenizer = T5Tokenizer.from_pretrained(model_name, legacy=False)
model = T5ForConditionalGeneration.from_pretrained(model_name)
train_dataset = CorrectionDataset(training_pairs, tokenizer)
data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

output_dir = "./t5_typo_correction_simple"
os.makedirs(output_dir, exist_ok=True)
use_mps = torch.backends.mps.is_available() and torch.backends.mps.is_built()

training_args = TrainingArguments(
    output_dir=output_dir,
    num_train_epochs=100, 
    learning_rate=5e-5,
    per_device_train_batch_size=16, 
    save_steps=1000,             
    logging_steps=100,          
    use_mps_device=use_mps,     
    report_to="none",           
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    data_collator=data_collator,
)

trainer.train()
print("Training finished.")

save_directory = "./ketuvim_nert"
os.makedirs(save_directory, exist_ok=True)
trainer.save_model(save_directory)
tokenizer.save_pretrained(save_directory)
print(f"Model and tokenizer saved to {save_directory}")

device = torch.device("mps" if use_mps else "cpu")
model.to(device)
model.eval() 
test_words = ["Абрим", "ймкипур", "Чернавцы", "Голдштуин"]
for word in test_words:
    input_text = task_prefix + word 
    inputs = tokenizer(input_text, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=32,  
            num_beams=3      
            )
    corrected_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Input: '{word}' -> Corrected: '{corrected_text}'")