from datasets import load_dataset
from unsloth import FastLanguageModel
from transformers import TrainingArguments
from trl import SFTTrainer
from pathlib import Path

# Paths
PROJECT_ROOT = Path("/content/Fair-Agent")
TRAIN_DATA_PATH = PROJECT_ROOT / "data" / "finetune" / "qa_med_fin_train.jsonl"
VAL_DATA_PATH = PROJECT_ROOT / "data" / "finetune" / "qa_med_fin_val.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "llama-medfin-lora"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "meta-llama/Llama-3.2-3B-Instruct"
MAX_SEQ_LENGTH = 2048

# 1. Load model with Unsloth
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_NAME,
    max_seq_length=MAX_SEQ_LENGTH,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
)

# 2. Load train (and optionally val) data
raw_train = load_dataset("json", data_files=str(TRAIN_DATA_PATH))["train"]

def format_example(example):
    domain = example.get("domain", "general")
    question = example["input"]
    answer = example["output"]

    system_prompt = (
        f"You are a helpful AI assistant specialized in {domain} questions. "
        "Be accurate, cautious, and clear."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    example["text"] = prompt + answer
    return example

train_dataset = raw_train.map(format_example)

# 3. Training args (no bf16)
training_args = TrainingArguments(
    output_dir=str(OUTPUT_DIR),
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    num_train_epochs=2,
    logging_steps=5,
    save_strategy="epoch",
    report_to=[],
)

# 4. SFTTrainer handles tokenization + padding for text column
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_dataset,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LENGTH,
    args=training_args,
)

trainer.train()

trainer.save_model(str(OUTPUT_DIR))
tokenizer.save_pretrained(str(OUTPUT_DIR))