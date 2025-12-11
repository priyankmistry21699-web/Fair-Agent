from pathlib import Path
import json
import torch

from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAIN_DATA_PATH = PROJECT_ROOT / "data" / "finetune" / "full_dataset_train_enhanced.jsonl"  # Enhanced dataset with disclaimers & citations
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "llama-medfin-lora-enhanced"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "meta-llama/Llama-3.2-3B-Instruct"  # 3B model
MAX_SEQ_LENGTH = 384  # Reduced for 3B on 4GB GPU (384 words = better context than 256)


def load_model_and_tokenizer():
    # Check GPU availability
    if not torch.cuda.is_available():
        raise RuntimeError(
            "No GPU detected! This script requires a CUDA-capable GPU.\n"
            "Please check:\n"
            "1. GPU drivers are installed\n"
            "2. CUDA toolkit is installed\n"
            "3. PyTorch CUDA version matches your GPU\n"
            f"Current PyTorch CUDA available: {torch.cuda.is_available()}"
        )
    
    print(f"GPU detected: {torch.cuda.get_device_name(0)}")
    print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Clear GPU cache before loading
    torch.cuda.empty_cache()
    
    # 4-bit quantization config to reduce memory usage
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )

    # Don't specify max_memory if GPU not detected properly
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        low_cpu_mem_usage=True,
        trust_remote_code=True,
    )

    lora_config = LoraConfig(
        r=8,  # Minimal rank for 3B model on 4GB GPU
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "v_proj", "k_proj"],  # Only 1 module to minimize memory
    )

    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, lora_config)
    model.config.use_cache = False  # Disable KV cache for training

    return model, tokenizer


def format_example(example, tokenizer):
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

    # Simple chat template: system + user + answer
    prompt = (
        f"<|system|>\n{system_prompt}\n<|end|>\n"
        f"<|user|>\n{question}\n<|end|>\n"
        f"<|assistant|>\n"
    )

    text = prompt + answer
    encoded = tokenizer(
        text,
        max_length=MAX_SEQ_LENGTH,
        truncation=True,
        padding="max_length",
    )

    input_ids = encoded["input_ids"]
    attention_mask = encoded["attention_mask"]
    labels = input_ids.copy()

    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
    }


def main() -> None:
    if not TRAIN_DATA_PATH.exists():
        raise FileNotFoundError(f"Train file not found: {TRAIN_DATA_PATH}")

    model, tokenizer = load_model_and_tokenizer()

    raw_dataset = load_dataset("json", data_files=str(TRAIN_DATA_PATH))["train"]

    tokenized_dataset = raw_dataset.map(
        lambda ex: format_example(ex, tokenizer),
        remove_columns=raw_dataset.column_names,
    )

    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        num_train_epochs=4,
        logging_steps=5,
        save_strategy="epoch",
        save_total_limit=1,
        report_to=[],
        fp16=True,
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",
        max_grad_norm=0.3,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
    )

    trainer.train()

    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))


if __name__ == "__main__":
    main()
