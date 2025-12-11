"""
Quick setup verification and training starter.
Run this after PyTorch CUDA installation completes.
"""
import sys
from pathlib import Path

print("=" * 80)
print("FAIR-Agent Training Setup Verification")
print("=" * 80)

# Step 1: Check PyTorch CUDA
print("\n[1/4] Checking PyTorch CUDA installation...")
try:
    import torch
    print(f"  ✓ PyTorch version: {torch.__version__}")
    print(f"  ✓ CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"  ✓ GPU: {torch.cuda.get_device_name(0)}")
        props = torch.cuda.get_device_properties(0)
        print(f"  ✓ GPU memory: {props.total_memory / 1024**3:.2f} GB")
    else:
        print("  ✗ CUDA not available - GPU training will not work")
        sys.exit(1)
except ImportError:
    print("  ✗ PyTorch not installed")
    sys.exit(1)

# Step 2: Check training data
print("\n[2/4] Checking training dataset...")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAIN_FILE = PROJECT_ROOT / "data" / "finetune" / "full_dataset_train.jsonl"

if TRAIN_FILE.exists():
    import json
    with open(TRAIN_FILE) as f:
        count = sum(1 for _ in f)
    print(f"  ✓ Training dataset found: {count} examples")
else:
    print(f"  ✗ Training dataset not found: {TRAIN_FILE}")
    sys.exit(1)

# Step 3: Check dependencies
print("\n[3/4] Checking dependencies...")
try:
    import transformers
    import peft
    import bitsandbytes
    import datasets
    print(f"  ✓ transformers: {transformers.__version__}")
    print(f"  ✓ peft: {peft.__version__}")
    print(f"  ✓ bitsandbytes: available")
    print(f"  ✓ datasets: {datasets.__version__}")
except ImportError as e:
    print(f"  ✗ Missing dependency: {e}")
    sys.exit(1)

# Step 4: Configuration summary
print("\n[4/4] Training configuration:")
print(f"  • Model: Llama-3.2-3B-Instruct")
print(f"  • Quantization: 4-bit NF4")
print(f"  • LoRA rank: 2 (minimal for 4GB GPU)")
print(f"  • Sequence length: 256 tokens")
print(f"  • Target modules: q_proj only")
print(f"  • Training examples: {count}")
print(f"  • Epochs: 2")

print("\n" + "=" * 80)
print("✅ All checks passed! Ready to train.")
print("=" * 80)
print("\nTo start training, run:")
print("  python scripts\\finetune_llama_lora_plain.py")
print("\nEstimated training time: 30-45 minutes")
print("Output location: outputs/llama-medfin-lora-plain/")
print("=" * 80)
