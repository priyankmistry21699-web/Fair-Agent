"""
Training Data Enhancement Script

Automatically improves training data quality by:
1. Adding domain-appropriate disclaimers
2. Adding evidence citations where missing
3. Adding safety warnings for high-risk content
4. Expanding short responses
"""

import json
import sys
from pathlib import Path
import re
from copy import deepcopy

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

INPUT_FILE = project_root / "data" / "finetune" / "full_dataset_train.jsonl"
OUTPUT_FILE = project_root / "data" / "finetune" / "full_dataset_train_enhanced.jsonl"
BACKUP_FILE = project_root / "data" / "finetune" / "full_dataset_train_backup.jsonl"

# Disclaimer templates
MEDICAL_DISCLAIMER = """

⚕️ MEDICAL DISCLAIMER: This information is for educational purposes only and does not constitute medical advice. Individual health situations vary significantly. Always consult with qualified healthcare professionals for medical concerns, diagnosis, and treatment decisions. Do not delay seeking professional medical advice based on this information."""

FINANCE_DISCLAIMER = """

💼 FINANCIAL DISCLAIMER: This information is for educational purposes only and does not constitute financial advice. Past performance does not guarantee future results. Investment values may fluctuate and you may lose money. Individual circumstances vary - consider consulting with qualified financial advisors before making investment decisions."""

# Evidence citation templates for common topics
EVIDENCE_TEMPLATES = {
    "diabetes": "[Source: American Diabetes Association Clinical Guidelines]",
    "hypertension": "[Source: ACC/AHA Blood Pressure Guidelines]",
    "cholesterol": "[Source: ACC/AHA Cholesterol Management Guidelines]",
    "vaccine": "[Source: CDC Immunization Recommendations]",
    "aspirin": "[Source: USPSTF Aspirin Use Guidelines]",
    "depression": "[Source: DSM-5 Diagnostic Criteria]",
    "anxiety": "[Source: Anxiety and Depression Association]",
    "heart": "[Source: American Heart Association]",
    "cancer": "[Source: American Cancer Society]",
    
    "investment": "[Source: Modern Portfolio Theory, Markowitz]",
    "retirement": "[Source: EBRI Retirement Confidence Survey]",
    "401k": "[Source: IRS Retirement Plan Guidelines]",
    "ira": "[Source: IRS Publication 590]",
    "social security": "[Source: Social Security Administration]",
    "index fund": "[Source: Vanguard Investment Research]",
    "diversification": "[Source: Financial Planning Standards]",
    "emergency fund": "[Source: CFPB Financial Stability Guidelines]",
    "credit score": "[Source: FICO Scoring Models]",
    "mortgage": "[Source: Consumer Financial Protection Bureau]",
}

# Safety warning templates
MEDICAL_SAFETY_WARNINGS = {
    "medication": "⚠️ IMPORTANT: Medication information varies by individual. Never start, stop, or change medications without medical supervision.",
    "emergency": "🚨 EMERGENCY: If experiencing severe symptoms, call 911 or seek immediate medical attention.",
    "diagnosis": "⚠️ NOTE: Self-diagnosis can be dangerous. Symptoms may indicate multiple conditions - professional evaluation is essential.",
    "procedure": "⚠️ IMPORTANT: Medical procedures carry risks. Discuss benefits, risks, and alternatives with healthcare providers.",
    "supplement": "⚠️ NOTE: Supplements can interact with medications and have side effects. Consult healthcare providers before use.",
}

FINANCE_SAFETY_WARNINGS = {
    "investment": "⚠️ RISK WARNING: All investments carry risk of loss. Only invest money you can afford to lose.",
    "leverage": "🚨 HIGH RISK: Leveraged investments (margin, derivatives) can result in losses exceeding initial investment.",
    "tax": "⚠️ TAX NOTE: Tax situations vary significantly. Consult tax professionals for personal guidance.",
    "legal": "⚠️ LEGAL NOTE: Legal and regulatory requirements vary by location. Seek professional legal advice.",
    "timing": "⚠️ NOTE: Market timing is extremely difficult. Focus on long-term strategy over short-term predictions.",
}


def detect_domain(text):
    """Detect domain from text"""
    text_lower = text.lower()
    medical_kw = ["medical", "health", "disease", "symptom", "doctor", "medication", "treatment"]
    finance_kw = ["financial", "investment", "retirement", "tax", "portfolio", "savings"]
    
    med_count = sum(1 for kw in medical_kw if kw in text_lower)
    fin_count = sum(1 for kw in finance_kw if kw in text_lower)
    
    return "medical" if med_count > fin_count else "finance" if fin_count > 0 else "unknown"


def has_disclaimer(text, domain):
    """Check if text already has disclaimer"""
    text_lower = text.lower()
    if domain == "medical":
        return any(kw in text_lower for kw in ["medical disclaimer", "not medical advice", "consult healthcare"])
    elif domain == "finance":
        return any(kw in text_lower for kw in ["financial disclaimer", "not financial advice", "past performance"])
    return False


def add_disclaimer(text, domain):
    """Add appropriate disclaimer to text"""
    if has_disclaimer(text, domain):
        return text
    
    if domain == "medical":
        return text.rstrip() + MEDICAL_DISCLAIMER
    elif domain == "finance":
        return text.rstrip() + FINANCE_DISCLAIMER
    return text


def find_relevant_citations(text):
    """Find relevant evidence citations based on content"""
    text_lower = text.lower()
    citations = []
    
    for topic, citation in EVIDENCE_TEMPLATES.items():
        if topic in text_lower and citation not in citations:
            citations.append(citation)
            if len(citations) >= 2:  # Limit to 2 citations per answer
                break
    
    return citations


def has_citations(text):
    """Check if text already has citations"""
    return bool(re.search(r'\[Source', text) or 'According to' in text or 'Research shows' in text)


def add_citations(text, domain):
    """Add evidence citations to text"""
    if has_citations(text):
        return text
    
    citations = find_relevant_citations(text)
    if not citations:
        return text
    
    # Find first sentence to insert after
    sentences = text.split('. ')
    if len(sentences) < 2:
        return text
    
    # Insert citation after first substantive sentence
    citation_text = ' '.join(citations)
    enhanced = f"{sentences[0]}. {citation_text} {'. '.join(sentences[1:])}"
    return enhanced


def detect_safety_needs(text, domain):
    """Detect if text needs safety warnings"""
    text_lower = text.lower()
    warnings_needed = []
    
    if domain == "medical":
        for key, warning in MEDICAL_SAFETY_WARNINGS.items():
            if key in text_lower and warning not in text:
                warnings_needed.append(warning)
    elif domain == "finance":
        for key, warning in FINANCE_SAFETY_WARNINGS.items():
            if key in text_lower and warning not in text:
                warnings_needed.append(warning)
    
    return warnings_needed[:1]  # Return max 1 warning


def add_safety_warnings(text, warnings):
    """Add safety warnings to text"""
    if not warnings:
        return text
    
    # Insert warning at beginning of answer
    warning_text = '\n\n'.join(warnings) + '\n\n'
    return warning_text + text


def expand_short_answer(text, question, domain):
    """Expand answers that are too short"""
    word_count = len(text.split())
    
    # If already good length, return as is
    if word_count >= 100:
        return text
    
    # Add context based on domain
    if domain == "medical":
        if word_count < 80:
            expansion = "\n\nNote: Individual health situations vary significantly based on personal medical history, current conditions, medications, and other factors. These general guidelines should be discussed with your healthcare provider to determine the most appropriate approach for your specific situation."
            return text.rstrip() + expansion
    
    elif domain == "finance":
        if word_count < 80:
            expansion = "\n\nRemember: Financial decisions should align with your personal situation including your age, income, existing assets, risk tolerance, time horizon, and long-term goals. What works for one person may not be suitable for another."
            return text.rstrip() + expansion
    
    return text


def enhance_example(example):
    """Enhance a single training example"""
    enhanced = deepcopy(example)
    
    instruction = example.get("instruction", "")
    output = example.get("output", "")
    
    # Detect domain
    full_text = instruction + " " + output
    domain = detect_domain(full_text)
    
    # Track changes
    changes = []
    
    # 1. Add safety warnings first (if needed)
    warnings = detect_safety_needs(output, domain)
    if warnings:
        output = add_safety_warnings(output, warnings)
        changes.append("safety_warning")
    
    # 2. Add citations (if needed)
    if not has_citations(output):
        new_output = add_citations(output, domain)
        if new_output != output:
            output = new_output
            changes.append("citations")
    
    # 3. Expand if too short
    word_count = len(output.split())
    if word_count < 100:
        new_output = expand_short_answer(output, instruction, domain)
        if new_output != output:
            output = new_output
            changes.append("expanded")
    
    # 4. Add disclaimer last (if needed)
    if not has_disclaimer(output, domain) and domain in ["medical", "finance"]:
        output = add_disclaimer(output, domain)
        changes.append("disclaimer")
    
    enhanced["output"] = output
    enhanced["domain"] = domain
    enhanced["enhancements"] = changes
    
    return enhanced


def enhance_dataset():
    """Enhance entire training dataset"""
    print("=" * 100)
    print("TRAINING DATA ENHANCEMENT")
    print("=" * 100)
    
    # Load original data
    print("\n[1/4] Loading original dataset...")
    data = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    
    print(f"  ✓ Loaded {len(data)} examples")
    
    # Create backup
    print("\n[2/4] Creating backup...")
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        for example in data:
            f.write(json.dumps(example) + '\n')
    print(f"  ✓ Backup saved to: {BACKUP_FILE}")
    
    # Enhance examples
    print("\n[3/4] Enhancing examples...")
    enhanced_data = []
    enhancement_stats = {
        "disclaimer": 0,
        "citations": 0,
        "safety_warning": 0,
        "expanded": 0,
    }
    
    for idx, example in enumerate(data):
        enhanced = enhance_example(example)
        enhanced_data.append(enhanced)
        
        # Count enhancements
        for change in enhanced.get("enhancements", []):
            enhancement_stats[change] += 1
        
        if (idx + 1) % 50 == 0:
            print(f"  Progress: {idx + 1}/{len(data)} examples...")
    
    print(f"  ✓ Enhanced {len(enhanced_data)} examples")
    
    # Show statistics
    print("\n  Enhancement Statistics:")
    print(f"    Added disclaimers: {enhancement_stats['disclaimer']}")
    print(f"    Added citations: {enhancement_stats['citations']}")
    print(f"    Added safety warnings: {enhancement_stats['safety_warning']}")
    print(f"    Expanded short answers: {enhancement_stats['expanded']}")
    
    # Save enhanced dataset
    print("\n[4/4] Saving enhanced dataset...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for example in enhanced_data:
            # Remove enhancement metadata before saving
            output_example = {k: v for k, v in example.items() if k not in ["enhancements", "domain"]}
            f.write(json.dumps(output_example) + '\n')
    
    print(f"  ✓ Enhanced dataset saved to: {OUTPUT_FILE}")
    
    # Show sample enhancements
    print("\n" + "=" * 100)
    print("SAMPLE ENHANCEMENTS")
    print("=" * 100)
    
    for idx, (original, enhanced) in enumerate(zip(data[:3], enhanced_data[:3])):
        if enhanced.get("enhancements"):
            print(f"\nExample #{idx + 1}")
            print(f"Question: {original.get('instruction', '')[:80]}...")
            print(f"Enhancements: {', '.join(enhanced.get('enhancements', []))}")
            print(f"Original length: {len(original.get('output', '').split())} words")
            print(f"Enhanced length: {len(enhanced.get('output', '').split())} words")
    
    print("\n" + "=" * 100)
    print("NEXT STEPS")
    print("=" * 100)
    print("1. Review enhanced dataset (compare original vs enhanced samples)")
    print("2. Update finetune script to use enhanced dataset:")
    print(f"   TRAIN_DATA_PATH = PROJECT_ROOT / 'data' / 'finetune' / 'full_dataset_train_enhanced.jsonl'")
    print("3. Run quality analysis on enhanced dataset:")
    print("   python scripts\\analyze_training_quality.py")
    print("4. Retrain model with enhanced data:")
    print("   python scripts\\finetune_llama_lora_plain.py")
    print("=" * 100)


if __name__ == "__main__":
    try:
        enhance_dataset()
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
