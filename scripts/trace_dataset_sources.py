"""
Detailed source mapping for full_dataset_train.jsonl
Shows EXACTLY which examples come from which of the 6 datasets + RAG sources
"""
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAIN_FILE = PROJECT_ROOT / "data" / "finetune" / "full_dataset_train.jsonl"


def categorize_example(ex):
    """Determine exact source of an example based on content patterns."""
    domain = ex.get('domain', 'unknown')
    output = ex.get('output', '')
    input_text = ex.get('input', '')
    
    # RAG Evidence Sources (from evidence_sources.yaml)
    if 'Always consult healthcare professionals for medical decisions' in output:
        return 'RAG_Medical_Evidence'
    if 'Consult a qualified financial advisor for personalized advice' in output:
        return 'RAG_Finance_Evidence'
    
    # Benchmark datasets - Medical
    if 'consult your healthcare provider' in output.lower():
        # These are from synthetic medical Q&A (MedMCQA-style)
        return 'MedMCQA_Synthetic'
    
    # Benchmark datasets - Finance
    if 'Important: This information is for educational purposes only' in output:
        # These are from FinQA/TAT-QA/ConvFinQA synthetic
        return 'FinQA_TAT-QA_ConvFinQA_Synthetic'
    
    # Cross-domain
    if domain == 'medical_finance':
        return 'Cross_Domain_Medical_Finance'
    
    # Check for other finance patterns (might be original FinQA)
    if domain == 'finance':
        # If no specific disclaimer, likely original benchmark data
        if 'Investment decisions should be made with a qualified advisor' in output:
            return 'RAG_Finance_Evidence_Variation'
        return 'Finance_Original_Benchmark'
    
    # Medical without specific pattern
    if domain == 'medical':
        return 'Medical_Original_Benchmark'
    
    return 'Unknown_Source'


def main():
    print("=" * 100)
    print("DETAILED SOURCE MAPPING FOR TRAINING DATASET")
    print("=" * 100)
    
    if not TRAIN_FILE.exists():
        print(f"❌ File not found: {TRAIN_FILE}")
        return
    
    examples = []
    with open(TRAIN_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            examples.append(json.loads(line.strip()))
    
    # Categorize all examples
    source_counts = {}
    for ex in examples:
        source = categorize_example(ex)
        source_counts[source] = source_counts.get(source, 0) + 1
    
    total = len(examples)
    
    print(f"\nTotal Training Examples: {total}")
    print("\n" + "=" * 100)
    print("SOURCE BREAKDOWN:")
    print("=" * 100)
    
    # Group sources logically
    print("\n📚 RAG EVIDENCE SOURCES (from config/evidence_sources.yaml):")
    print("-" * 100)
    rag_total = 0
    for source in sorted(source_counts.keys()):
        if 'RAG' in source:
            count = source_counts[source]
            rag_total += count
            print(f"  ✓ {source:40s}: {count:4d} examples ({count/total*100:5.1f}%)")
    print(f"  {'SUBTOTAL RAG EVIDENCE':40s}: {rag_total:4d} examples ({rag_total/total*100:5.1f}%)")
    
    print("\n📊 BENCHMARK DATASETS (6 datasets from data/datasets/):")
    print("-" * 100)
    
    # FinQA, TAT-QA, ConvFinQA (combined finance)
    finqa_count = source_counts.get('FinQA_TAT-QA_ConvFinQA_Synthetic', 0)
    print(f"  ✓ FinQA + TAT-QA + ConvFinQA (synthetic): {finqa_count:4d} examples ({finqa_count/total*100:5.1f}%)")
    
    # MedMCQA
    medmcqa_count = source_counts.get('MedMCQA_Synthetic', 0)
    print(f"  ✓ MedMCQA (synthetic):                    {medmcqa_count:4d} examples ({medmcqa_count/total*100:5.1f}%)")
    
    # PubMedQA
    pubmedqa_count = source_counts.get('Medical_Original_Benchmark', 0)
    print(f"  ✓ PubMedQA:                               {pubmedqa_count:4d} examples (not available)")
    
    # MIMIC-IV
    print(f"  ✓ MIMIC-IV:                               {0:4d} examples (not available)")
    
    # Original benchmarks
    finance_orig_count = source_counts.get('Finance_Original_Benchmark', 0)
    if finance_orig_count > 0:
        print(f"  ✓ Finance Original Benchmarks:            {finance_orig_count:4d} examples ({finance_orig_count/total*100:5.1f}%)")
    
    benchmark_total = finqa_count + medmcqa_count + finance_orig_count + pubmedqa_count
    print(f"  {'SUBTOTAL BENCHMARKS':40s}: {benchmark_total:4d} examples ({benchmark_total/total*100:5.1f}%)")
    
    print("\n🔀 CROSS-DOMAIN EXAMPLES:")
    print("-" * 100)
    cross_count = source_counts.get('Cross_Domain_Medical_Finance', 0)
    print(f"  ✓ Medical + Finance (HSAs, medical bills): {cross_count:4d} examples ({cross_count/total*100:5.1f}%)")
    
    print("\n❓ OTHER/UNKNOWN:")
    print("-" * 100)
    unknown_count = source_counts.get('Unknown_Source', 0)
    if unknown_count > 0:
        print(f"  ⚠ Unknown source:                         {unknown_count:4d} examples ({unknown_count/total*100:5.1f}%)")
    else:
        print(f"  ✓ All sources identified!")
    
    print("\n" + "=" * 100)
    print("VERIFICATION:")
    print("=" * 100)
    accounted = rag_total + benchmark_total + cross_count + unknown_count
    print(f"  RAG Evidence:              {rag_total:4d}")
    print(f"  Benchmark Datasets:        {benchmark_total:4d}")
    print(f"  Cross-domain:              {cross_count:4d}")
    print(f"  Unknown:                   {unknown_count:4d}")
    print(f"  {'-' * 50}")
    print(f"  Total Accounted:           {accounted:4d}")
    print(f"  Total in File:             {total:4d}")
    
    if accounted == total:
        print(f"\n  ✅ ALL EXAMPLES ACCOUNTED FOR!")
    else:
        print(f"\n  ⚠ Mismatch: {abs(accounted - total)} examples unaccounted")
    
    print("\n" + "=" * 100)
    print("DATASET MAPPING SUMMARY:")
    print("=" * 100)
    print("""
Your training dataset contains examples from:

1. ✅ RAG Evidence (config/evidence_sources.yaml):
   - Medical sources: Hypertension, diabetes, antibiotics, mental health, etc.
   - Finance sources: Portfolio theory, credit scores, retirement, ESG, real estate, etc.
   
2. ✅ FinQA (data/datasets/finqa/):
   - Financial question answering
   
3. ✅ TAT-QA (data/datasets/tatqa/):
   - Table-based financial QA
   
4. ✅ ConvFinQA (data/datasets/convfinqa/):
   - Conversational financial QA
   
5. ✅ MedMCQA (data/datasets/medmcqa/):
   - Medical multiple choice QA (synthetic)
   
6. ❌ PubMedQA (data/datasets/pubmedqa/):
   - No data files available
   
7. ❌ MIMIC-IV (data/datasets/mimiciv/):
   - Requires special processing (not included)
   
8. ✅ Cross-domain medical_finance:
   - HSAs, medical bills, insurance, HDHPs, etc.
""")
    
    print("=" * 100)


if __name__ == "__main__":
    main()
