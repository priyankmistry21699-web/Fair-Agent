"""
Quick Comparison: Baseline Ollama vs Enhanced Model (via Ollama)
Uses Ollama for both models to avoid loading issues
"""
import requests
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OLLAMA_BASE_URL = "http://localhost:11435"

# Simple test queries
TEST_QUERIES = [
    "What are the symptoms of Type 2 diabetes?",
    "Should I invest in index funds?",
    "Can I use my HSA for retirement?",
]

def query_model(model_name, prompt):
    """Query an Ollama model"""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 300}
            },
            timeout=60
        )
        return response.json()["response"]
    except Exception as e:
        return f"Error: {e}"

def compare_models():
    """Compare two Ollama models"""
    
    print("=" * 80)
    print("QUICK MODEL COMPARISON")
    print("=" * 80)
    
    baseline_model = "llama3.2:latest"
    
    # Check available models
    print("\nChecking available Ollama models...")
    try:
        models_response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        models = models_response.json().get("models", [])
        model_names = [m["name"] for m in models]
        print(f"Available models: {', '.join(model_names)}")
    except:
        print("Could not list models")
    
    print(f"\nBaseline model: {baseline_model}")
    print("\n" + "=" * 80)
    
    for idx, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[Query {idx}/{len(TEST_QUERIES)}] {query}")
        print("-" * 80)
        
        # Baseline
        print(f"\n📌 BASELINE ({baseline_model}):")
        baseline_response = query_model(baseline_model, query)
        print(baseline_response[:300] + "..." if len(baseline_response) > 300 else baseline_response)
        
        # Check for disclaimers
        has_disclaimer = any(kw in baseline_response.lower() for kw in 
                            ["disclaimer", "not medical advice", "not financial advice", "consult"])
        print(f"\n✓ Has disclaimer: {'Yes' if has_disclaimer else 'No'}")
        print(f"✓ Length: {len(baseline_response.split())} words")
        
        print("\n" + "=" * 80)
    
    print("\n💡 ANALYSIS:")
    print("Your enhanced model needs to be loaded into Ollama to compare.")
    print("The direct Python loading is hanging due to HuggingFace checkpoint issues.")
    print("\nTo load enhanced model into Ollama:")
    print("1. Merge LoRA with base model")
    print("2. Export to GGUF format")
    print("3. Load into Ollama")
    print("\nFor now, we can see baseline model responses above.")
    print("=" * 80)

if __name__ == "__main__":
    compare_models()
