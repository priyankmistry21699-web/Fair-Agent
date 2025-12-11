"""
Generate synthetic medical Q&A examples from RAG evidence sources
to balance the training dataset (currently heavy on finance).
"""
from pathlib import Path
import json
import yaml
from typing import List, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_CONFIG = PROJECT_ROOT / "config" / "evidence_sources.yaml"
OUTPUT_FILE = PROJECT_ROOT / "data" / "datasets" / "medmcqa" / "synthetic_medical_qa.jsonl"
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Question templates for different medical topics
QUESTION_TEMPLATES = [
    "What are the main points about {topic}?",
    "Can you explain {topic}?",
    "Tell me about {topic}.",
    "What should I know regarding {topic}?",
    "How does {topic} work?",
    "What are the guidelines for {topic}?",
    "Explain the key facts about {topic}.",
    "What is important to understand about {topic}?",
]

def extract_topic_questions(source: Dict) -> List[Dict]:
    """Generate multiple Q&A pairs from a single evidence source."""
    examples = []
    title = source['title']
    content = source['content'].strip()
    keywords = source.get('keywords', [])
    
    # Main question
    examples.append({
        'domain': 'medical',
        'input': f"What is {title.lower()}?",
        'output': content + " Always consult with qualified healthcare professionals for medical advice specific to your situation.",
    })
    
    # Keyword-based questions
    if keywords:
        # Pick 3-5 key terms to create focused questions
        key_terms = keywords[:5]
        for term in key_terms:
            if len(term) > 3 and term.lower() not in title.lower():
                examples.append({
                    'domain': 'medical',
                    'input': f"Tell me about {term} in the context of {title.lower()}.",
                    'output': content + f" For questions about {term}, consult your healthcare provider.",
                })
    
    # "Should I" questions (common user pattern)
    if 'medication' in title.lower() or 'drug' in title.lower():
        examples.append({
            'domain': 'medical',
            'input': f"Should I take medication for {title.split('-')[0].strip().lower()}?",
            'output': content + " Medication decisions must be made with your doctor based on your individual health situation.",
        })
    
    if 'prevention' in title.lower() or 'screening' in title.lower():
        examples.append({
            'domain': 'medical',
            'input': f"Do I need screening or prevention for {title.split('-')[0].strip().lower()}?",
            'output': content + " Discuss screening and prevention strategies with your healthcare provider.",
        })
    
    return examples


def main():
    print("Generating synthetic medical Q&A examples...")
    
    with open(EVIDENCE_CONFIG, 'r', encoding='utf-8') as f:
        evidence = yaml.safe_load(f)
    
    all_examples = []
    
    if 'medical_sources' in evidence:
        for source in evidence['medical_sources']:
            examples = extract_topic_questions(source)
            all_examples.extend(examples)
    
    print(f"Generated {len(all_examples)} medical examples")
    
    # Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
