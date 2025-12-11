"""
Build comprehensive finetuning dataset from:
1. Six benchmark datasets (ConvFinQA, FinQA, MedMCQA, MIMIC-IV, PubMedQA, TAT-QA)
2. RAG evidence sources from config/evidence_sources.yaml

Outputs instruction-formatted training data for domain-specific LoRA finetuning.
"""
from pathlib import Path
import json
import yaml
import random
from typing import List, Dict, Any
from datasets import load_dataset, load_from_disk

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASETS_DIR = PROJECT_ROOT / "data" / "datasets"
EVIDENCE_CONFIG = PROJECT_ROOT / "config" / "evidence_sources.yaml"
OUTPUT_DIR = PROJECT_ROOT / "data" / "finetune"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Output files
TRAIN_OUTPUT = OUTPUT_DIR / "comprehensive_train.jsonl"
VAL_OUTPUT = OUTPUT_DIR / "comprehensive_val.jsonl"


def load_evidence_sources() -> List[Dict[str, Any]]:
    """Load medical and finance evidence from RAG system."""
    print("Loading RAG evidence sources...")
    
    with open(EVIDENCE_CONFIG, 'r', encoding='utf-8') as f:
        evidence = yaml.safe_load(f)
    
    examples = []
    
    # Process medical sources - create multiple QA pairs per source
    if 'medical_sources' in evidence:
        for source in evidence['medical_sources']:
            # Original format
            examples.append({
                'domain': 'medical',
                'input': f"Explain: {source['title']}",
                'output': source['content'].strip(),
            })
            
            # Add keyword-based question variations
            title = source['title']
            content = source['content'].strip()
            
            examples.append({
                'domain': 'medical',
                'input': f"What should I know about {title.lower()}?",
                'output': content + " Always consult with healthcare professionals for medical decisions specific to your situation.",
            })
    
    # Process finance sources - create multiple QA pairs per source
    if 'finance_sources' in evidence:
        for source in evidence['finance_sources']:
            # Original format
            examples.append({
                'domain': 'finance',
                'input': f"Explain: {source['title']}",
                'output': source['content'].strip(),
            })
            
            # Add keyword-based question variations
            title = source['title']
            content = source['content'].strip()
            
            examples.append({
                'domain': 'finance',
                'input': f"What should I understand about {title.lower()}?",
                'output': content + " This is general information for educational purposes. Consult a qualified financial advisor for personalized advice.",
            })
    
    print(f"  Loaded {len(examples)} evidence-based examples")
    return examples


def load_medmcqa() -> List[Dict[str, Any]]:
    """Load medical multiple choice QA dataset."""
    print("Loading MedMCQA dataset...")
    
    # Try synthetic medical QA first
    synthetic_file = DATASETS_DIR / "medmcqa" / "synthetic_medical_qa.jsonl"
    if synthetic_file.exists():
        examples = []
        try:
            with open(synthetic_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if len(examples) >= 500:
                        break
                    item = json.loads(line.strip())
                    examples.append(item)
            
            print(f"  Loaded {len(examples)} MedMCQA synthetic examples")
            return examples
        except Exception as e:
            print(f"  ⚠ Error loading synthetic MedMCQA: {e}")
    
    # Fallback: try loading from disk
    dataset_path = DATASETS_DIR / "medmcqa"
    if not dataset_path.exists():
        print(f"  ⚠ MedMCQA not found, skipping")
        return []
    
    print(f"  ⚠ MedMCQA original data not available, skipping")
    return []


def load_pubmedqa() -> List[Dict[str, Any]]:
    """Load PubMed biomedical QA dataset."""
    print("Loading PubMedQA dataset...")
    dataset_path = DATASETS_DIR / "pubmedqa"
    
    if not dataset_path.exists():
        print(f"  ⚠ PubMedQA not found at {dataset_path}, skipping")
        return []
    
    examples = []
    try:
        dataset = load_from_disk(str(dataset_path))
        
        # Handle both dict-style and dataset-style
        splits_to_check = ['train'] if isinstance(dataset, dict) else [None]
        
        for split in splits_to_check:
            data = dataset[split] if split else dataset
            if data is None:
                continue
            
            for item in data:
                question = item.get('question', '')
                answer = item.get('final_decision', item.get('answer', 'yes'))
                
                if question:
                    examples.append({
                        'domain': 'medical',
                        'input': question,
                        'output': f"Based on biomedical research: {answer}. This information is derived from medical literature. Always verify with qualified healthcare professionals for clinical decisions.",
                    })
                
                if len(examples) >= 300:
                    break
    
    except Exception as e:
        print(f"  ⚠ Error loading PubMedQA: {e}")
        return []
    
    print(f"  Loaded {len(examples)} PubMedQA examples")
    return examples


def load_finqa() -> List[Dict[str, Any]]:
    """Load financial QA dataset."""
    print("Loading FinQA dataset...")
    
    examples = []
    
    # Load original finance_qa.jsonl
    dataset_file = DATASETS_DIR / "finqa" / "finance_qa.jsonl"
    if dataset_file.exists():
        try:
            with open(dataset_file, 'r', encoding='utf-8') as f:
                for line in f:
                    item = json.loads(line.strip())
                    question = item.get('question', item.get('input', ''))
                    answer = item.get('answer', item.get('output', ''))
                    
                    if question and answer:
                        examples.append({
                            'domain': 'finance',
                            'input': question,
                            'output': f"{answer} This is general financial information for educational purposes. Consult a qualified financial advisor for personalized advice.",
                        })
        except Exception as e:
            print(f"  ⚠ Error loading finance_qa.jsonl: {e}")
    
    # Load synthetic finance QA
    synthetic_file = DATASETS_DIR / "finqa" / "synthetic_finance_qa.jsonl"
    if synthetic_file.exists():
        try:
            with open(synthetic_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if len(examples) >= 1000:  # Total limit
                        break
                    item = json.loads(line.strip())
                    examples.append(item)
        except Exception as e:
            print(f"  ⚠ Error loading synthetic_finance_qa.jsonl: {e}")
    
    print(f"  Loaded {len(examples)} FinQA examples")
    return examples


def load_tatqa() -> List[Dict[str, Any]]:
    """Load TAT-QA (financial table QA) dataset."""
    print("Loading TAT-QA dataset...")
    dataset_file = DATASETS_DIR / "tatqa" / "tatqa_synthetic.jsonl"
    
    if not dataset_file.exists():
        print(f"  ⚠ TAT-QA not found at {dataset_file}, skipping")
        return []
    
    examples = []
    try:
        with open(dataset_file, 'r', encoding='utf-8') as f:
            for line in f:
                if len(examples) >= 800:  # Increased limit
                    break
                    
                item = json.loads(line.strip())
                question = item.get('question', item.get('input', ''))
                answer = item.get('answer', item.get('output', ''))
                
                if question and answer:
                    examples.append({
                        'domain': 'finance',
                        'input': question,
                        'output': f"{answer} This analysis is based on financial data interpretation. Always verify calculations and consult financial professionals for investment decisions.",
                    })
    
    except Exception as e:
        print(f"  ⚠ Error loading TAT-QA: {e}")
        return []
    
    print(f"  Loaded {len(examples)} TAT-QA examples")
    return examples


def load_convfinqa() -> List[Dict[str, Any]]:
    """Load ConvFinQA (conversational finance) dataset."""
    print("Loading ConvFinQA dataset...")
    dataset_file = DATASETS_DIR / "convfinqa" / "convfinqa_synthetic.jsonl"
    
    if not dataset_file.exists():
        print(f"  ⚠ ConvFinQA not found at {dataset_file}, skipping")
        return []
    
    examples = []
    try:
        with open(dataset_file, 'r', encoding='utf-8') as f:
            for line in f:
                if len(examples) >= 800:  # Increased limit
                    break
                    
                item = json.loads(line.strip())
                question = item.get('question', item.get('input', ''))
                answer = item.get('answer', item.get('output', ''))
                
                if question and answer:
                    examples.append({
                        'domain': 'finance',
                        'input': question,
                        'output': f"{answer} This is general financial information. Consult a certified financial advisor for personalized guidance.",
                    })
    
    except Exception as e:
        print(f"  ⚠ Error loading ConvFinQA: {e}")
        return []
    
    print(f"  Loaded {len(examples)} ConvFinQA examples")
    return examples


def load_mimiciv() -> List[Dict[str, Any]]:
    """Load MIMIC-IV clinical notes (if available)."""
    print("Loading MIMIC-IV dataset...")
    dataset_path = DATASETS_DIR / "mimiciv"
    
    if not dataset_path.exists():
        print(f"  ⚠ MIMIC-IV not found at {dataset_path}, skipping")
        return []
    
    # MIMIC-IV requires special access and processing
    # For now, return empty list (can be implemented with proper credentials)
    print(f"  ⚠ MIMIC-IV requires special processing, skipping for now")
    return []


def load_cross_domain() -> List[Dict[str, Any]]:
    """Load medical_finance cross-domain examples."""
    print("Loading cross-domain medical_finance examples...")
    cross_file = OUTPUT_DIR / "cross_domain_qa.jsonl"
    
    if not cross_file.exists():
        print(f"  ⚠ Cross-domain file not found, skipping")
        return []
    
    examples = []
    try:
        with open(cross_file, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line.strip())
                examples.append(item)
    except Exception as e:
        print(f"  ⚠ Error loading cross-domain examples: {e}")
        return []
    
    print(f"  Loaded {len(examples)} cross-domain examples")
    return examples


def create_train_val_split(examples: List[Dict], val_ratio: float = 0.15):
    """Split examples into train and validation sets."""
    print(f"\nCreating train/validation split ({int((1-val_ratio)*100)}/{int(val_ratio*100)})...")
    
    # Shuffle
    random.shuffle(examples)
    
    # Split
    split_idx = int(len(examples) * (1 - val_ratio))
    train_examples = examples[:split_idx]
    val_examples = examples[split_idx:]
    
    print(f"  Train: {len(train_examples)} examples")
    print(f"  Val: {len(val_examples)} examples")
    
    return train_examples, val_examples


def save_jsonl(examples: List[Dict], output_path: Path):
    """Save examples to JSONL format."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    print(f"  Saved to: {output_path}")


def main():
    print("=" * 80)
    print("Building Comprehensive Finetuning Dataset")
    print("=" * 80)
    
    random.seed(42)  # Reproducible splits
    
    all_examples = []
    
    # Load all data sources
    all_examples.extend(load_evidence_sources())
    all_examples.extend(load_medmcqa())
    all_examples.extend(load_pubmedqa())
    all_examples.extend(load_finqa())
    all_examples.extend(load_tatqa())
    all_examples.extend(load_convfinqa())
    all_examples.extend(load_mimiciv())
    all_examples.extend(load_cross_domain())  # Add cross-domain examples
    
    print(f"\n{'=' * 80}")
    print(f"Total examples collected: {len(all_examples)}")
    
    # Count by domain
    medical_count = sum(1 for ex in all_examples if ex['domain'] == 'medical')
    finance_count = sum(1 for ex in all_examples if ex['domain'] == 'finance')
    cross_count = sum(1 for ex in all_examples if ex['domain'] == 'medical_finance')
    
    print(f"  Medical: {medical_count}")
    print(f"  Finance: {finance_count}")
    print(f"  Cross-domain: {cross_count}")
    
    if len(all_examples) == 0:
        print("\n⚠ No examples found! Check dataset paths and formats.")
        return
    
    # Create splits
    train_examples, val_examples = create_train_val_split(all_examples)
    
    # Save
    print(f"\nSaving datasets...")
    save_jsonl(train_examples, TRAIN_OUTPUT)
    save_jsonl(val_examples, VAL_OUTPUT)
    
    print(f"\n{'=' * 80}")
    print("✅ Dataset build complete!")
    print(f"{'=' * 80}")
    print(f"\nNext steps:")
    print(f"1. Review datasets: {TRAIN_OUTPUT}")
    print(f"2. Update finetune script to use: comprehensive_train.jsonl")
    print(f"3. Run: python scripts\\finetune_llama_lora_plain.py")


if __name__ == "__main__":
    main()
