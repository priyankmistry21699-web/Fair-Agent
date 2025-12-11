"""
Fetch full content from URLs in evidence_sources.yaml to expand training data.
This downloads the actual articles/guidelines from the curated sources.
"""
from pathlib import Path
import json
import yaml
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_CONFIG = PROJECT_ROOT / "config" / "evidence_sources.yaml"
OUTPUT_FILE = PROJECT_ROOT / "data" / "finetune" / "web_scraped_evidence.jsonl"
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)


def fetch_webpage_content(url: str, max_retries: int = 2) -> str:
    """Fetch and extract main content from a webpage."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                script.decompose()
            
            # Try to find main content
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
            
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
            else:
                text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            text = ' '.join(text.split())
            
            # Limit to reasonable length (first 2000 words for training)
            words = text.split()[:2000]
            return ' '.join(words)
            
        except Exception as e:
            print(f"  ⚠ Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(2)
    
    return ""


def load_and_expand_evidence() -> List[Dict[str, Any]]:
    """Load evidence sources and fetch full content from URLs."""
    print("Loading evidence sources and fetching web content...")
    
    with open(EVIDENCE_CONFIG, 'r', encoding='utf-8') as f:
        evidence = yaml.safe_load(f)
    
    examples = []
    
    # Process medical sources
    if 'medical_sources' in evidence:
        print(f"\nProcessing {len(evidence['medical_sources'])} medical sources...")
        for i, source in enumerate(evidence['medical_sources'], 1):
            source_id = source.get('id', f'med_{i}')
            title = source['title']
            content = source['content'].strip()
            url = source.get('url', '')
            
            print(f"  [{i}/{len(evidence['medical_sources'])}] {source_id}: {title[:50]}...")
            
            # Use existing content as base
            examples.append({
                'domain': 'medical',
                'input': f"Explain {title}",
                'output': content + " Always consult healthcare professionals for medical decisions.",
                'source': 'curated_evidence',
                'source_id': source_id,
            })
            
            # Fetch full content from URL if available
            if url and url.startswith('http'):
                print(f"    Fetching: {url}")
                web_content = fetch_webpage_content(url)
                
                if web_content and len(web_content) > len(content):
                    # Create expanded example with web content
                    examples.append({
                        'domain': 'medical',
                        'input': f"Provide comprehensive information about {title.lower()}",
                        'output': web_content + " This information is from authoritative medical sources. Always consult qualified healthcare providers for medical advice.",
                        'source': 'web_scraped',
                        'source_id': source_id,
                        'url': url,
                    })
                    print(f"    ✓ Added {len(web_content)} chars of web content")
                else:
                    print(f"    ⚠ No additional content from web")
                
                time.sleep(1)  # Be respectful to servers
    
    # Process finance sources
    if 'finance_sources' in evidence:
        print(f"\nProcessing {len(evidence['finance_sources'])} finance sources...")
        for i, source in enumerate(evidence['finance_sources'], 1):
            source_id = source.get('id', f'fin_{i}')
            title = source['title']
            content = source['content'].strip()
            url = source.get('url', '')
            
            print(f"  [{i}/{len(evidence['finance_sources'])}] {source_id}: {title[:50]}...")
            
            # Use existing content as base
            examples.append({
                'domain': 'finance',
                'input': f"Explain {title}",
                'output': content + " This is general financial information. Consult a qualified financial advisor for personalized advice.",
                'source': 'curated_evidence',
                'source_id': source_id,
            })
            
            # Fetch full content from URL if available
            if url and url.startswith('http'):
                print(f"    Fetching: {url}")
                web_content = fetch_webpage_content(url)
                
                if web_content and len(web_content) > len(content):
                    # Create expanded example with web content
                    examples.append({
                        'domain': 'finance',
                        'input': f"Provide comprehensive information about {title.lower()}",
                        'output': web_content + " This is general financial information for educational purposes. Consult a qualified financial advisor for personalized advice.",
                        'source': 'web_scraped',
                        'source_id': source_id,
                        'url': url,
                    })
                    print(f"    ✓ Added {len(web_content)} chars of web content")
                else:
                    print(f"    ⚠ No additional content from web")
                
                time.sleep(1)  # Be respectful to servers
    
    return examples


def main():
    print("=" * 80)
    print("Fetching Full Content from Evidence Source URLs")
    print("=" * 80)
    
    examples = load_and_expand_evidence()
    
    print(f"\n{'=' * 80}")
    print(f"Total examples created: {len(examples)}")
    
    # Count by source type
    curated = sum(1 for ex in examples if ex.get('source') == 'curated_evidence')
    scraped = sum(1 for ex in examples if ex.get('source') == 'web_scraped')
    
    print(f"  Curated summaries: {curated}")
    print(f"  Web-scraped full content: {scraped}")
    
    # Save
    print(f"\nSaving to: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"\n{'=' * 80}")
    print("✅ Complete!")
    print(f"{'=' * 80}")
    print(f"\nNext: Run build_full_dataset.py to include this in training")


if __name__ == "__main__":
    main()
