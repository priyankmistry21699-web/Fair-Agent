"""
Training Data Quality Analysis Script

Analyzes the quality of training data for FAIR-Agent finetuning:
- Disclaimer presence by domain
- Citation patterns
- Safety language coverage
- Response length distribution
- Domain balance
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

TRAINING_DATA_PATH = project_root / "data" / "finetune" / "full_dataset_train_enhanced.jsonl"

# Quality patterns to check
DISCLAIMER_PATTERNS = {
    "medical": [
        "medical disclaimer",
        "not medical advice",
        "consult healthcare",
        "consult.*physician",
        "consult.*doctor",
        "seek medical attention",
        "healthcare professional",
        "educational purposes only"
    ],
    "finance": [
        "financial disclaimer",
        "not financial advice",
        "consult.*financial advisor",
        "past performance",
        "may lose money",
        "investment risk",
        "educational purposes only",
        "does not guarantee"
    ]
}

CITATION_PATTERNS = [
    r"\[Source \d+\]",
    r"According to",
    r"Research shows",
    r"Studies indicate",
    r"Evidence suggests",
    r"Data from",
    r"\[Evidence:",
    r"Based on research"
]

SAFETY_KEYWORDS = [
    "risk", "warning", "caution", "important", "never", "always",
    "seek immediate", "emergency", "danger", "serious", "critical"
]


def load_training_data():
    """Load training dataset (JSONL format)"""
    data = []
    with open(TRAINING_DATA_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def detect_domain(text):
    """Detect domain from text content"""
    text_lower = text.lower()
    
    medical_keywords = ["medical", "health", "disease", "symptom", "treatment", "doctor", 
                        "medication", "patient", "diagnosis", "clinical", "physician"]
    finance_keywords = ["financial", "investment", "portfolio", "retirement", "tax",
                       "stock", "fund", "savings", "debt", "advisor", "capital"]
    
    medical_count = sum(1 for kw in medical_keywords if kw in text_lower)
    finance_count = sum(1 for kw in finance_keywords if kw in text_lower)
    
    if medical_count > finance_count:
        return "medical"
    elif finance_count > medical_count:
        return "finance"
    else:
        return "unknown"


def check_disclaimer(text, domain):
    """Check if text contains appropriate disclaimer"""
    text_lower = text.lower()
    patterns = DISCLAIMER_PATTERNS.get(domain, [])
    
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return True
    return False


def count_citations(text):
    """Count evidence citations in text"""
    count = 0
    for pattern in CITATION_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        count += len(matches)
    return count


def check_safety_language(text):
    """Check for safety-related language"""
    text_lower = text.lower()
    found_keywords = [kw for kw in SAFETY_KEYWORDS if kw in text_lower]
    return len(found_keywords) > 0, found_keywords


def calculate_quality_score(example, domain):
    """Calculate quality score (0-100) for an example"""
    score = 0.0
    feedback = []
    
    output = example.get("output", "")
    word_count = len(output.split())
    
    # Disclaimer check (30 points)
    if check_disclaimer(output, domain):
        score += 30
        feedback.append("✓ Has disclaimer")
    else:
        feedback.append("✗ Missing disclaimer (-30)")
    
    # Citation check (25 points)
    citation_count = count_citations(output)
    citation_score = min(citation_count * 10, 25)
    score += citation_score
    if citation_count > 0:
        feedback.append(f"✓ Has {citation_count} citations (+{citation_score})")
    else:
        feedback.append("✗ No citations (-25)")
    
    # Safety language (20 points)
    has_safety, safety_words = check_safety_language(output)
    if has_safety:
        score += 20
        feedback.append(f"✓ Has safety language ({len(safety_words)} keywords)")
    else:
        feedback.append("✗ No safety language (-20)")
    
    # Length appropriateness (15 points)
    if 100 <= word_count <= 400:
        score += 15
        feedback.append(f"✓ Good length ({word_count} words)")
    elif 50 <= word_count < 100:
        score += 8
        feedback.append(f"⚠ Short ({word_count} words, -7)")
    elif word_count < 50:
        feedback.append(f"✗ Too short ({word_count} words, -15)")
    else:
        score += 10
        feedback.append(f"⚠ Long ({word_count} words, -5)")
    
    # Structure check (10 points)
    has_structure = any([
        "\n\n" in output,  # Paragraphs
        output.count("\n-") >= 2,  # Bullet points
        output.count("\n•") >= 2,  # Bullet points
        output.count(". ") >= 3,  # Multiple sentences
    ])
    if has_structure:
        score += 10
        feedback.append("✓ Well-structured")
    else:
        feedback.append("✗ Poor structure (-10)")
    
    return score, feedback


def analyze_dataset():
    """Perform comprehensive quality analysis"""
    
    print("=" * 100)
    print("TRAINING DATA QUALITY ANALYSIS")
    print("=" * 100)
    
    data = load_training_data()
    print(f"\n📊 Total examples: {len(data)}")
    
    # Domain distribution
    domain_counts = defaultdict(int)
    domain_examples = defaultdict(list)
    
    for idx, example in enumerate(data):
        text = example.get("instruction", "") + " " + example.get("output", "")
        domain = detect_domain(text)
        domain_counts[domain] += 1
        domain_examples[domain].append((idx, example))
    
    print("\n" + "=" * 100)
    print("DOMAIN DISTRIBUTION")
    print("=" * 100)
    for domain, count in sorted(domain_counts.items()):
        percentage = (count / len(data)) * 100
        print(f"  {domain.capitalize():<15} {count:>4} examples ({percentage:>5.1f}%)")
    
    # Disclaimer analysis
    print("\n" + "=" * 100)
    print("DISCLAIMER COVERAGE")
    print("=" * 100)
    
    disclaimer_stats = {}
    for domain in ["medical", "finance"]:
        if domain in domain_examples:
            examples = domain_examples[domain]
            with_disclaimer = sum(1 for _, ex in examples if check_disclaimer(ex.get("output", ""), domain))
            total = len(examples)
            percentage = (with_disclaimer / total * 100) if total > 0 else 0
            disclaimer_stats[domain] = (with_disclaimer, total, percentage)
            
            status = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
            print(f"  {status} {domain.capitalize():<15} {with_disclaimer}/{total} ({percentage:.1f}%)")
    
    # Citation analysis
    print("\n" + "=" * 100)
    print("EVIDENCE CITATION COVERAGE")
    print("=" * 100)
    
    total_with_citations = 0
    citation_counts = []
    
    for example in data:
        citations = count_citations(example.get("output", ""))
        citation_counts.append(citations)
        if citations > 0:
            total_with_citations += 1
    
    citation_percentage = (total_with_citations / len(data)) * 100
    avg_citations = sum(citation_counts) / len(citation_counts) if citation_counts else 0
    
    status = "✅" if citation_percentage >= 40 else "⚠️" if citation_percentage >= 20 else "❌"
    print(f"  {status} Examples with citations: {total_with_citations}/{len(data)} ({citation_percentage:.1f}%)")
    print(f"  📊 Average citations per example: {avg_citations:.2f}")
    
    # Safety language analysis
    print("\n" + "=" * 100)
    print("SAFETY LANGUAGE COVERAGE")
    print("=" * 100)
    
    safety_stats = defaultdict(int)
    for domain in ["medical", "finance"]:
        if domain in domain_examples:
            examples = domain_examples[domain]
            with_safety = sum(1 for _, ex in examples if check_safety_language(ex.get("output", ""))[0])
            total = len(examples)
            percentage = (with_safety / total * 100) if total > 0 else 0
            
            target = 80 if domain == "medical" else 60
            status = "✅" if percentage >= target else "⚠️" if percentage >= target - 20 else "❌"
            print(f"  {status} {domain.capitalize():<15} {with_safety}/{total} ({percentage:.1f}%)")
    
    # Length distribution
    print("\n" + "=" * 100)
    print("RESPONSE LENGTH DISTRIBUTION")
    print("=" * 100)
    
    lengths = [len(ex.get("output", "").split()) for ex in data]
    avg_length = sum(lengths) / len(lengths) if lengths else 0
    
    length_buckets = {
        "Too short (<50 words)": sum(1 for l in lengths if l < 50),
        "Short (50-99 words)": sum(1 for l in lengths if 50 <= l < 100),
        "Good (100-300 words)": sum(1 for l in lengths if 100 <= l <= 300),
        "Long (301-500 words)": sum(1 for l in lengths if 301 <= l <= 500),
        "Very long (>500 words)": sum(1 for l in lengths if l > 500),
    }
    
    print(f"  📏 Average length: {avg_length:.1f} words")
    for bucket, count in length_buckets.items():
        percentage = (count / len(data)) * 100
        status = "✅" if "Good" in bucket else "⚠️" if "Short" in bucket else "❌" if "Too short" in bucket else "ℹ️"
        print(f"  {status} {bucket:<25} {count:>4} ({percentage:>5.1f}%)")
    
    # Overall quality scoring
    print("\n" + "=" * 100)
    print("OVERALL QUALITY SCORES")
    print("=" * 100)
    
    quality_scores = []
    low_quality_examples = []
    
    for idx, example in enumerate(data):
        text = example.get("instruction", "") + " " + example.get("output", "")
        domain = detect_domain(text)
        score, feedback = calculate_quality_score(example, domain)
        quality_scores.append(score)
        
        if score < 50:
            low_quality_examples.append((idx, score, feedback, example))
    
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    
    quality_buckets = {
        "Excellent (80-100)": sum(1 for s in quality_scores if s >= 80),
        "Good (60-79)": sum(1 for s in quality_scores if 60 <= s < 80),
        "Fair (40-59)": sum(1 for s in quality_scores if 40 <= s < 60),
        "Poor (<40)": sum(1 for s in quality_scores if s < 40),
    }
    
    print(f"  📊 Average quality score: {avg_quality:.1f}/100")
    for bucket, count in quality_buckets.items():
        percentage = (count / len(data)) * 100
        status = "✅" if "Excellent" in bucket or "Good" in bucket else "⚠️" if "Fair" in bucket else "❌"
        print(f"  {status} {bucket:<20} {count:>4} ({percentage:>5.1f}%)")
    
    # Show sample low-quality examples
    if low_quality_examples:
        print("\n" + "=" * 100)
        print(f"SAMPLE LOW-QUALITY EXAMPLES (Score < 50)")
        print("=" * 100)
        
        for idx, score, feedback, example in low_quality_examples[:3]:
            print(f"\n  Example #{idx+1} - Score: {score:.1f}/100")
            print(f"  Question: {example.get('instruction', '')[:80]}...")
            print(f"  Answer: {example.get('output', '')[:100]}...")
            print(f"  Issues:")
            for fb in feedback:
                if "✗" in fb or "⚠" in fb:
                    print(f"    {fb}")
    
    # Recommendations
    print("\n" + "=" * 100)
    print("RECOMMENDATIONS")
    print("=" * 100)
    
    recommendations = []
    
    # Check disclaimer coverage
    for domain in ["medical", "finance"]:
        if domain in disclaimer_stats:
            _, total, percentage = disclaimer_stats[domain]
            if percentage < 80:
                missing = int(total * (80 - percentage) / 100)
                recommendations.append(f"❗ Add disclaimers to {missing}+ {domain} examples (current: {percentage:.1f}%)")
    
    # Check citations
    if citation_percentage < 40:
        needed = int(len(data) * (40 - citation_percentage) / 100)
        recommendations.append(f"❗ Add evidence citations to {needed}+ examples (current: {citation_percentage:.1f}%)")
    
    # Check length
    too_short = length_buckets.get("Too short (<50 words)", 0)
    if too_short > 0:
        recommendations.append(f"❗ Expand {too_short} examples that are too short (<50 words)")
    
    # Check quality score
    poor_quality = quality_buckets.get("Poor (<40)", 0)
    if poor_quality > 0:
        recommendations.append(f"❗ Improve or replace {poor_quality} poor-quality examples (score <40)")
    
    # Overall dataset size
    if len(data) < 300:
        recommendations.append(f"❗ Increase dataset size from {len(data)} to 300-500 examples for better results")
    
    if recommendations:
        for rec in recommendations:
            print(f"  {rec}")
    else:
        print("  ✅ Training data meets quality targets!")
    
    # Expected impact
    print("\n" + "=" * 100)
    print("EXPECTED IMPACT AFTER IMPROVEMENTS")
    print("=" * 100)
    
    current_metrics = {
        "Safety": 0.50,  # Current baseline from comparison
        "Faithfulness": 0.58,
        "Interpretability": 0.50,
        "Robustness": 0.50,
    }
    
    # Calculate expected improvements
    improvements = {}
    if avg_quality < 70:
        improvements["Safety"] = 0.15 if disclaimer_stats.get("medical", (0, 1, 0))[2] < 80 else 0.05
        improvements["Faithfulness"] = 0.12 if citation_percentage < 40 else 0.05
        improvements["Interpretability"] = 0.10 if avg_length < 100 else 0.05
        improvements["Robustness"] = 0.08
    else:
        improvements = {"Safety": 0.05, "Faithfulness": 0.05, "Interpretability": 0.05, "Robustness": 0.05}
    
    print(f"\n  {'Metric':<20} {'Current':<12} {'Expected':<12} {'Gain':<12}")
    print("  " + "-" * 60)
    for metric, current in current_metrics.items():
        improvement = improvements.get(metric, 0.05)
        expected = current + improvement
        print(f"  {metric:<20} {current:<12.3f} {expected:<12.3f} +{improvement:<11.3f}")
    
    avg_improvement = sum(improvements.values()) / len(improvements)
    print(f"\n  📈 Expected overall improvement: +{avg_improvement:.1%} to +{avg_improvement*1.5:.1%}")
    
    print("\n" + "=" * 100)
    
    return {
        "total_examples": len(data),
        "avg_quality_score": avg_quality,
        "disclaimer_coverage": disclaimer_stats,
        "citation_coverage": citation_percentage,
        "recommendations": recommendations,
    }


if __name__ == "__main__":
    try:
        results = analyze_dataset()
    except FileNotFoundError:
        print(f"❌ Error: Training data not found at {TRAINING_DATA_PATH}")
        print("   Expected location: data/finetune/full_dataset_train.jsonl")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
