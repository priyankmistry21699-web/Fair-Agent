"""Minimal LoRA finetuning script using only Unsloth.

This avoids transformers.Trainer / trl version issues and is meant
to run in a clean GPU environment (e.g., a dedicated finetune venv).
"""

from pathlib import Path

from datasets import load_dataset

try:
    from unsloth import FastLanguageModel
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "unsloth is not installed. Install with: pip install 'unsloth[torch]'"
    ) from exc


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEED_DATA_PATH = PROJECT_ROOT / "data" / "finetune" / "qa_med_fin_seed.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "llama-medfin-lora"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# You can change this to any small instruct model you have access to.
MODEL_NAME = "meta-llama/Llama-3.2-3B-Instruct"
MAX_SEQ_LENGTH = 2048


def build_texts(tokenizer):
    if not SEED_DATA_PATH.exists():
        raise SystemExit(
            f"Seed data not found at {SEED_DATA_PATH}. "
            "Run scripts/prepare_finetune_seed_data.py first."
        )

    dataset = load_dataset("json", data_files=str(SEED_DATA_PATH))["train"]

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

    dataset = dataset.map(format_example)
    return [ex["text"] for ex in dataset]


def main() -> None:
    print(f"Loading base model: {MODEL_NAME}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=True,
    )

    print("Wrapping model with LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )

    print(f"Loading and formatting seed dataset from {SEED_DATA_PATH}")
    texts = build_texts(tokenizer)

    # Unsloth exposes a simple fit interface in recent versions.
    # If your version differs, check `pip show unsloth` docs.
    print("Starting LoRA finetuning with Unsloth...")
    model.fit(
        texts=texts,
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=2,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=10,
    )

    print(f"Saving tokenizer to {OUTPUT_DIR}")
    tokenizer.save_pretrained(str(OUTPUT_DIR))


if __name__ == "__main__":
    main()
