"""
Analyze full_dataset_train.jsonl to show source attribution and domain breakdown.
"""
from pathlib import Path
import json
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAIN_FILE = PROJECT_ROOT / "data" / "finetune" / "full_dataset_train.jsonl"


def analyze_dataset():
    """Analyze training dataset to show sources."""
    
    print("=" * 80)
    print("Dataset Source Analysis")
    print("=" * 80)
    
    if not TRAIN_FILE.exists():
        print(f"❌ File not found: {TRAIN_FILE}")
        return
    
    examples = []
    with open(TRAIN_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            examples.append(json.loads(line.strip()))
    
    total = len(examples)
    print(f"\nTotal training examples: {total}")
    
    # Domain breakdown
    print("\n" + "=" * 80)
    print("Domain Breakdown:")
    print("=" * 80)
    domains = Counter(ex.get('domain', 'unknown') for ex in examples)
    for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100
        print(f"  {domain:20s}: {count:4d} examples ({percentage:5.1f}%)")
    
    # Identify source types by analyzing content patterns
    print("\n" + "=" * 80)
    print("Source Identification (by content analysis):")
    print("=" * 80)
    
    # RAG evidence (has specific disclaimer patterns)
    rag_medical = sum(1 for ex in examples if 
                      ex.get('domain') == 'medical' and 
                      'Always consult healthcare professionals' in ex.get('output', ''))
    rag_finance = sum(1 for ex in examples if 
                      ex.get('domain') == 'finance' and 
                      'Consult a qualified financial advisor for personalized advice' in ex.get('output', ''))
    
    print(f"  RAG Evidence (curated sources):")
    print(f"    Medical: {rag_medical} examples")
    print(f"    Finance: {rag_finance} examples")
    print(f"    Total RAG: {rag_medical + rag_finance}")
    
    # Synthetic examples (other disclaimers)
    synth_medical = sum(1 for ex in examples if 
                        ex.get('domain') == 'medical' and 
                        'consult your healthcare provider' in ex.get('output', '').lower())
    synth_finance = sum(1 for ex in examples if 
                        ex.get('domain') == 'finance' and 
                        'Important: This information is for educational purposes' in ex.get('output', ''))
    
    print(f"\n  Benchmark Datasets (synthetic/original):")
    print(f"    Medical (MedMCQA-style): {synth_medical} examples")
    print(f"    Finance (FinQA/TAT-QA/ConvFinQA): {synth_finance} examples")
    print(f"    Total Benchmarks: {synth_medical + synth_finance}")
    
    # Cross-domain
    cross_domain = domains.get('medical_finance', 0)
    print(f"\n  Cross-domain (medical_finance):")
    print(f"    {cross_domain} examples")
    
    # Show sample from each source type
    print("\n" + "=" * 80)
    print("Sample Examples from Each Source:")
    print("=" * 80)
    
    # RAG medical
    rag_med_ex = next((ex for ex in examples if 
                       ex.get('domain') == 'medical' and 
                       'Always consult healthcare professionals' in ex.get('output', '')), None)
    if rag_med_ex:
        print("\n1. RAG Evidence - Medical:")
        print(f"   Q: {rag_med_ex['input'][:100]}...")
        print(f"   A: {rag_med_ex['output'][:150]}...")
    
    # RAG finance
    rag_fin_ex = next((ex for ex in examples if 
                       ex.get('domain') == 'finance' and 
                       'Consult a qualified financial advisor for personalized advice' in ex.get('output', '')), None)
    if rag_fin_ex:
        print("\n2. RAG Evidence - Finance:")
        print(f"   Q: {rag_fin_ex['input'][:100]}...")
        print(f"   A: {rag_fin_ex['output'][:150]}...")
    
    # Synthetic medical
    synth_med_ex = next((ex for ex in examples if 
                         ex.get('domain') == 'medical' and 
                         'consult your healthcare provider' in ex.get('output', '').lower()), None)
    if synth_med_ex:
        print("\n3. Benchmark Dataset - Medical:")
        print(f"   Q: {synth_med_ex['input'][:100]}...")
        print(f"   A: {synth_med_ex['output'][:150]}...")
    
    # Synthetic finance
    synth_fin_ex = next((ex for ex in examples if 
                         ex.get('domain') == 'finance' and 
                         'Important: This information is for educational purposes' in ex.get('output', '')), None)
    if synth_fin_ex:
        print("\n4. Benchmark Dataset - Finance:")
        print(f"   Q: {synth_fin_ex['input'][:100]}...")
        print(f"   A: {synth_fin_ex['output'][:150]}...")
    
    # Cross-domain
    cross_ex = next((ex for ex in examples if ex.get('domain') == 'medical_finance'), None)
    if cross_ex:
        print("\n5. Cross-domain (medical_finance):")
        print(f"   Q: {cross_ex['input'][:100]}...")
        print(f"   A: {cross_ex['output'][:150]}...")
    
    print("\n" + "=" * 80)
    print("Verification Summary:")
    print("=" * 80)
    print(f"✅ RAG curated sources: {rag_medical + rag_finance} examples")
    print(f"✅ Benchmark datasets: {synth_medical + synth_finance} examples")
    print(f"✅ Cross-domain: {cross_domain} examples")
    print(f"✅ Total accounted: {rag_medical + rag_finance + synth_medical + synth_finance + cross_domain}")
    print(f"✅ Total in file: {total}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    analyze_dataset()
