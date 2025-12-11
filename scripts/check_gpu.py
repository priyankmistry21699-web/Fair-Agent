"""Check GPU availability for training."""
import torch

print("=" * 60)
print("GPU Check")
print("=" * 60)

print(f"\nCUDA available: {torch.cuda.is_available()}")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA version: {torch.version.cuda if torch.version.cuda else 'Not available'}")
print(f"GPU count: {torch.cuda.device_count()}")

if torch.cuda.is_available():
    print(f"\nGPU 0 name: {torch.cuda.get_device_name(0)}")
    props = torch.cuda.get_device_properties(0)
    print(f"GPU 0 total memory: {props.total_memory / 1024**3:.2f} GB")
    print(f"GPU 0 compute capability: {props.major}.{props.minor}")
else:
    print("\n⚠️ NO GPU DETECTED!")
    print("\nPossible issues:")
    print("1. PyTorch CPU-only version installed")
    print("2. NVIDIA drivers not installed")
    print("3. CUDA toolkit not installed")
    print("4. GPU disabled in system")
    print("\nTo fix:")
    print("- Reinstall PyTorch with CUDA support:")
    print("  pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")

print("=" * 60)
