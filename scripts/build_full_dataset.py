"""
Load ALL data from 6 benchmark datasets + RAG evidence sources directly.
No conversion - use the original format to maximize training data.
"""
from pathlib import Path
import json
import yaml
from typing import List, Dict, Any
import random

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASETS_DIR = PROJECT_ROOT / "data" / "datasets"
EVIDENCE_CONFIG = PROJECT_ROOT / "config" / "evidence_sources.yaml"
OUTPUT_DIR = PROJECT_ROOT / "data" / "finetune"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_OUTPUT = OUTPUT_DIR / "full_dataset_train.jsonl"
VAL_OUTPUT = OUTPUT_DIR / "full_dataset_val.jsonl"


def load_all_rag_evidence() -> List[Dict[str, Any]]:
    """Load ALL evidence from RAG system as training examples."""
    print("Loading RAG evidence sources...")
    
    examples = []
    
    # Load curated evidence summaries
    with open(EVIDENCE_CONFIG, 'r', encoding='utf-8') as f:
        evidence = yaml.safe_load(f)
    
    # Medical sources
    if 'medical_sources' in evidence:
        for source in evidence['medical_sources']:
            examples.append({
                'domain': 'medical',
                'input': f"Explain {source['title']}",
                'output': source['content'].strip() + " Always consult healthcare professionals for medical decisions.",
            })
    
    # Finance sources
    if 'finance_sources' in evidence:
        for source in evidence['finance_sources']:
            examples.append({
                'domain': 'finance',
                'input': f"Explain {source['title']}",
                'output': source['content'].strip() + " Consult a qualified financial advisor for personalized advice.",
            })
    
    print(f"  Loaded {len(examples)} curated RAG summaries")
    
    # Load web-scraped full content (if available)
    web_scraped_file = OUTPUT_DIR / "web_scraped_evidence.jsonl"
    if web_scraped_file.exists():
        web_examples = load_jsonl_file(web_scraped_file, "mixed", max_examples=1000)
        print(f"  Loaded {len(web_examples)} web-scraped full articles")
        examples.extend(web_examples)
    else:
        print(f"  No web-scraped content found (run fetch_evidence_urls.py to add)")
    
    return examples


def load_jsonl_file(file_path: Path, domain: str, max_examples: int = 10000) -> List[Dict]:
    """Generic JSONL loader."""
    if not file_path.exists():
        return []
    
    examples = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if len(examples) >= max_examples:
                    break
                
                item = json.loads(line.strip())
                
                # Try different field names
                question = item.get('question', item.get('input', item.get('query', '')))
                answer = item.get('answer', item.get('output', item.get('response', '')))
                
                # If domain not in item, use provided domain
                item_domain = item.get('domain', domain)
                
                if question and answer:
                    examples.append({
                        'domain': item_domain,
                        'input': question,
                        'output': answer,
                    })
                elif 'input' in item and 'output' in item:
                    # Already in correct format
                    examples.append(item)
    
    except Exception as e:
        print(f"  ⚠ Error loading {file_path.name}: {e}")
    
    return examples


def load_all_datasets() -> List[Dict[str, Any]]:
    """Load all 6 benchmark datasets."""
    all_examples = []
    
    # 1. FinQA
    print("Loading FinQA...")
    finqa_orig = load_jsonl_file(DATASETS_DIR / "finqa" / "finance_qa.jsonl", "finance")
    finqa_synth = load_jsonl_file(DATASETS_DIR / "finqa" / "synthetic_finance_qa.jsonl", "finance")
    print(f"  FinQA: {len(finqa_orig)} original + {len(finqa_synth)} synthetic")
    all_examples.extend(finqa_orig)
    all_examples.extend(finqa_synth)
    
    # 2. TAT-QA
    print("Loading TAT-QA...")
    tatqa = load_jsonl_file(DATASETS_DIR / "tatqa" / "tatqa_synthetic.jsonl", "finance")
    print(f"  TAT-QA: {len(tatqa)} examples")
    all_examples.extend(tatqa)
    
    # 3. ConvFinQA
    print("Loading ConvFinQA...")
    convfinqa = load_jsonl_file(DATASETS_DIR / "convfinqa" / "convfinqa_synthetic.jsonl", "finance")
    print(f"  ConvFinQA: {len(convfinqa)} examples")
    all_examples.extend(convfinqa)
    
    # 4. MedMCQA
    print("Loading MedMCQA...")
    medmcqa = load_jsonl_file(DATASETS_DIR / "medmcqa" / "synthetic_medical_qa.jsonl", "medical")
    print(f"  MedMCQA: {len(medmcqa)} examples")
    all_examples.extend(medmcqa)
    
    # 5. PubMedQA - check if any synthetic version exists
    print("Loading PubMedQA...")
    pubmedqa = load_jsonl_file(DATASETS_DIR / "pubmedqa" / "synthetic_medical_qa.jsonl", "medical")
    if len(pubmedqa) == 0:
        print("  PubMedQA: No data available")
    else:
        print(f"  PubMedQA: {len(pubmedqa)} examples")
    all_examples.extend(pubmedqa)
    
    # 6. MIMIC-IV - check if processed
    print("Loading MIMIC-IV...")
    mimiciv = load_jsonl_file(DATASETS_DIR / "mimiciv" / "clinical_notes_qa.jsonl", "medical")
    if len(mimiciv) == 0:
        print("  MIMIC-IV: No processed data available")
    else:
        print(f"  MIMIC-IV: {len(mimiciv)} examples")
    all_examples.extend(mimiciv)
    
    # 7. Cross-domain medical_finance
    print("Loading cross-domain examples...")
    cross = load_jsonl_file(OUTPUT_DIR / "cross_domain_qa.jsonl", "medical_finance")
    print(f"  Cross-domain: {len(cross)} examples")
    all_examples.extend(cross)
    
    return all_examples


def create_train_val_split(examples: List[Dict], val_ratio: float = 0.15):
    """Split into train/validation sets."""
    print(f"\nCreating train/validation split ({int((1-val_ratio)*100)}/{int(val_ratio*100)})...")
    
    random.shuffle(examples)
    
    split_idx = int(len(examples) * (1 - val_ratio))
    train = examples[:split_idx]
    val = examples[split_idx:]
    
    print(f"  Train: {len(train)} examples")
    print(f"  Val: {len(val)} examples")
    
    return train, val


def save_jsonl(examples: List[Dict], path: Path):
    """Save to JSONL."""
    with open(path, 'w', encoding='utf-8') as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')
    print(f"  Saved: {path}")


def main():
    print("=" * 80)
    print("Building FULL Dataset from ALL Sources")
    print("=" * 80)
    
    random.seed(42)
    
    all_examples = []
    
    # Load RAG evidence
    all_examples.extend(load_all_rag_evidence())
    
    # Load all 6 datasets
    all_examples.extend(load_all_datasets())
    
    print(f"\n{'=' * 80}")
    print(f"Total examples: {len(all_examples)}")
    
    # Count by domain
    medical = sum(1 for ex in all_examples if ex.get('domain') == 'medical')
    finance = sum(1 for ex in all_examples if ex.get('domain') == 'finance')
    cross = sum(1 for ex in all_examples if ex.get('domain') == 'medical_finance')
    
    print(f"  Medical: {medical}")
    print(f"  Finance: {finance}")
    print(f"  Cross-domain: {cross}")
    
    if len(all_examples) == 0:
        print("\n⚠ No data found!")
        return
    
    # Split
    train, val = create_train_val_split(all_examples)
    
    # Save
    print(f"\nSaving datasets...")
    save_jsonl(train, TRAIN_OUTPUT)
    save_jsonl(val, VAL_OUTPUT)
    
    print(f"\n{'=' * 80}")
    print("✅ Complete!")
    print(f"{'=' * 80}")
    print(f"\nTrain on: {TRAIN_OUTPUT}")
    print(f"  → {len(train)} examples from RAG evidence + 6 benchmark datasets")


if __name__ == "__main__":
    main()
