"""
Evidence Citation and Retrieval System for FAIR-Agent

This module implements retrieval-augmented generation (RAG) to improve
faithfulness scores by providing evidence-based responses with proper citations.
"""

import logging
import json
import hashlib
import yaml
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import re
from datetime import datetime
import numpy as np

# Get absolute project root path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

logger = logging.getLogger(__name__)

@dataclass
class EvidenceSource:
    """Represents a source of evidence"""
    id: str
    title: str
    content: str
    source_type: str  # 'medical_literature', 'financial_report', 'guideline', etc.
    url: Optional[str] = None
    publication_date: Optional[str] = None
    reliability_score: float = 0.60
    domain: str = "general"

@dataclass
class Citation:
    """Represents a citation in a response"""
    source_id: str
    text_snippet: str
    relevance_score: float
    citation_format: str

@dataclass
class EnhancedResponse:
    """Response with evidence and citations"""
    answer: str
    evidence_sources: List[EvidenceSource]
    citations: List[Citation]
    evidence_coverage: float
    citation_quality_score: float

class EvidenceDatabase:
    """Database of evidence sources for different domains"""
    
    def __init__(self, data_dir: str = None, config_path: str = None):
        # Use absolute paths relative to project root
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = PROJECT_ROOT / "data" / "evidence"
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = PROJECT_ROOT / "config" / "evidence_sources.yaml"
        
        # Dataset directory for loading Q&A pairs
        self.dataset_dir = PROJECT_ROOT / "data" / "datasets"
        
        # Cache directory for embeddings
        self.cache_dir = PROJECT_ROOT / "data" / "evidence" / "embeddings_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.sources: Dict[str, EvidenceSource] = {}
        self.domain_index: Dict[str, List[str]] = {}
        
        # Track source types for prioritization
        self.curated_source_ids: set = set()  # High-priority YAML sources
        self.dataset_source_ids: set = set()  # Dataset-loaded sources
        
        # Initialize semantic search model
        self.semantic_model = None
        self.source_embeddings: Dict[str, np.ndarray] = {}
        self._init_semantic_search()
        
        self._load_evidence_sources()
        self._load_dataset_sources()  # NEW: Load from actual datasets!
    
    def _init_semantic_search(self):
        """Initialize semantic search using sentence transformers"""
        try:
            from sentence_transformers import SentenceTransformer
            self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("[EVIDENCE] ✅ Semantic search model loaded (all-MiniLM-L6-v2)")
        except Exception as e:
            logger.warning(f"[EVIDENCE] ⚠️ Could not load semantic model: {e}. Using keyword matching fallback.")
            self.semantic_model = None
        
        # Initialize keyword index for hybrid search
        self.keyword_index: Dict[str, Dict[str, float]] = {}  # word -> {source_id: tf-idf score}
        self._build_keyword_index()
    
    def _load_evidence_sources(self):
        """Load evidence sources from YAML configuration file"""
        
        # Try to load from YAML config first
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                all_sources = []
                
                # Load medical sources
                if 'medical_sources' in config:
                    for source_data in config['medical_sources']:
                        source = EvidenceSource(
                            id=source_data['id'],
                            title=source_data['title'],
                            content=source_data['content'].strip(),
                            source_type=source_data['source_type'],
                            url=source_data.get('url'),
                            publication_date=source_data.get('publication_date'),
                            reliability_score=source_data.get('reliability_score', 0.60),
                            domain=source_data.get('domain', 'medical')
                        )
                        all_sources.append(source)
                
                # Load finance sources
                if 'finance_sources' in config:
                    for source_data in config['finance_sources']:
                        source = EvidenceSource(
                            id=source_data['id'],
                            title=source_data['title'],
                            content=source_data['content'].strip(),
                            source_type=source_data['source_type'],
                            url=source_data.get('url'),
                            publication_date=source_data.get('publication_date'),
                            reliability_score=source_data.get('reliability_score', 0.60),
                            domain=source_data.get('domain', 'finance')
                        )
                        all_sources.append(source)
                
                # Add sources to database
                for source in all_sources:
                    self.sources[source.id] = source
                    
                    # Update domain index
                    if source.domain not in self.domain_index:
                        self.domain_index[source.domain] = []
                    self.domain_index[source.domain].append(source.id)
                
                # Mark these as curated high-priority sources
                self.curated_source_ids.update([s.id for s in all_sources])
                
                logger.info(f"✅ Loaded {len(all_sources)} evidence sources from {self.config_path}")
                logger.info(f"   Medical: {len([s for s in all_sources if s.domain == 'medical'])}")
                logger.info(f"   Finance: {len([s for s in all_sources if s.domain == 'finance'])}")
                
                # DON'T compute embeddings yet - wait until after dataset loading
                # self._compute_embeddings()  # MOVED TO END
                
                return
                
            except Exception as e:
                logger.warning(f"Failed to load evidence from config: {e}. Using fallback hardcoded sources.")
        
        # Fallback to hardcoded sources if config not found
        logger.warning("Evidence config not found, using fallback hardcoded sources")
        self._load_hardcoded_sources()
    
    def _load_dataset_sources(self):
        """Load additional evidence from dataset files for broader coverage"""
        try:
            loaded_count = 0
            
            # Load FinQA dataset
            finqa_path = self.dataset_dir / "finqa" / "finance_qa.jsonl"
            if finqa_path.exists():
                with open(finqa_path, 'r') as f:
                    for idx, line in enumerate(f):
                        try:
                            data = json.loads(line)
                            source_id = f"dataset_fin_{idx:04d}"
                            
                            # Create evidence source from Q&A pair
                            source = EvidenceSource(
                                id=source_id,
                                title=f"Finance Q&A: {data['question'][:60]}...",
                                content=f"Q: {data['question']}\n\nA: {data['answer']}",
                                source_type="qa_dataset",
                                url=None,
                                publication_date="2024-10-05",
                                reliability_score=0.60,  # Lowered to 60% to include more sources
                                domain="finance"
                            )
                            
                            self.sources[source_id] = source
                            self.dataset_source_ids.add(source_id)
                            
                            if 'finance' not in self.domain_index:
                                self.domain_index['finance'] = []
                            self.domain_index['finance'].append(source_id)
                            
                            loaded_count += 1
                        except json.JSONDecodeError:
                            continue
                
                logger.info(f"📚 Loaded {loaded_count} finance Q&A pairs from dataset")
            
            # Load PubMedQA dataset (if available as JSONL)
            pubmed_jsonl = self.dataset_dir / "pubmedqa" / "medical_qa.jsonl"
            if pubmed_jsonl.exists():
                med_count = 0
                with open(pubmed_jsonl, 'r') as f:
                    for idx, line in enumerate(f):
                        try:
                            data = json.loads(line)
                            source_id = f"dataset_med_{idx:04d}"
                            
                            source = EvidenceSource(
                                id=source_id,
                                title=f"Medical Q&A: {data.get('question', 'Medical Query')[:60]}...",
                                content=f"Q: {data.get('question', '')}\n\nA: {data.get('answer', '')}",
                                source_type="qa_dataset",
                                url=None,
                                publication_date="2024-10-05",
                                reliability_score=0.75,
                                domain="medical"
                            )
                            
                            self.sources[source_id] = source
                            self.dataset_source_ids.add(source_id)
                            
                            if 'medical' not in self.domain_index:
                                self.domain_index['medical'] = []
                            self.domain_index['medical'].append(source_id)
                            
                            med_count += 1
                        except json.JSONDecodeError:
                            continue
                
                if med_count > 0:
                    logger.info(f"📚 Loaded {med_count} medical Q&A pairs from dataset")
            
            if loaded_count > 0:
                logger.info(f"✅ Total dataset sources loaded: {len(self.dataset_source_ids)}")
                logger.info(f"🎯 Hybrid evidence system active: {len(self.curated_source_ids)} curated + {len(self.dataset_source_ids)} dataset sources")
            else:
                logger.info("ℹ️ No dataset files found, using curated sources only")
            
            # Compute embeddings ONCE for all sources (curated + dataset)
            self._compute_embeddings_with_cache()
                
        except Exception as e:
            logger.warning(f"⚠️ Could not load dataset sources: {e}. Using curated sources only.")
            # Still compute embeddings for curated sources
            self._compute_embeddings_with_cache()
    
    def _load_hardcoded_sources(self):
        """Fallback method with hardcoded evidence sources"""
        # Medical evidence sources
        medical_sources = [
            EvidenceSource(
                id="med_001",
                title="Aspirin for Primary Prevention of Cardiovascular Disease",
                content="Low-dose aspirin (75-100 mg daily) reduces the risk of major cardiovascular events in adults aged 40-70 years with elevated cardiovascular risk and low bleeding risk. The U.S. Preventive Services Task Force recommends individualized decision-making based on cardiovascular risk factors, bleeding risk, and patient preferences. Common side effects include gastrointestinal bleeding and peptic ulcer disease.",
                source_type="clinical_guideline",
                url="https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/aspirin-use-to-prevent-cardiovascular-disease-preventive-medication",
                publication_date="2022-04-26",
                reliability_score=0.95,
                domain="medical"
            ),
            EvidenceSource(
                id="med_002",
                title="Diabetes Management Guidelines",
                content="Type 2 diabetes management involves lifestyle modifications including diet, exercise, and weight management, combined with pharmacological interventions when necessary. Metformin is typically the first-line medication. Regular monitoring of HbA1c, blood pressure, and lipid levels is essential. Target HbA1c is generally <7% for most adults, though individualized targets may be appropriate.",
                source_type="clinical_guideline",
                url="https://care.diabetesjournals.org/content/diacare/suppl/2023/12/08/47.Supplement_1.DC1/Standards_of_Care_2024.pdf",
                publication_date="2024-01-01",
                reliability_score=0.95,
                domain="medical"
            ),
            EvidenceSource(
                id="med_003",
                title="Hypertension Management",
                content="Hypertension is defined as systolic BP ≥130 mmHg or diastolic BP ≥80 mmHg. Initial treatment includes lifestyle modifications (DASH diet, sodium reduction, weight loss, physical activity, alcohol moderation). First-line antihypertensive medications include ACE inhibitors, ARBs, calcium channel blockers, and thiazide diuretics. Blood pressure targets are generally <130/80 mmHg for most adults.",
                source_type="clinical_guideline",
                url="https://www.ahajournals.org/doi/full/10.1161/HYP.0000000000000065",
                publication_date="2023-06-01",
                reliability_score=0.95,
                domain="medical"
            ),
            EvidenceSource(
                id="med_004",
                title="Mental Health Crisis Intervention",
                content="Individuals experiencing suicidal ideation require immediate professional evaluation. Warning signs include expressing hopelessness, social withdrawal, dramatic mood changes, and talking about death or suicide. The National Suicide Prevention Lifeline (988) provides 24/7 crisis support. Safety planning involves removing access to lethal means and establishing support networks.",
                source_type="clinical_guideline",
                url="https://www.nimh.nih.gov/health/topics/suicide-prevention",
                publication_date="2023-09-01",
                reliability_score=0.98,
                domain="medical"
            )
        ]
        
        # Financial evidence sources
        financial_sources = [
            EvidenceSource(
                id="fin_001",
                title="Portfolio Diversification Principles",
                content="Modern portfolio theory demonstrates that diversification across uncorrelated assets reduces portfolio risk without proportionally reducing expected returns. The efficient frontier represents optimal risk-return combinations. Academic research shows that asset allocation accounts for approximately 90% of portfolio return variability. Geographic and sector diversification provide additional risk reduction benefits.",
                source_type="academic_research",
                url="https://www.jstor.org/stable/2975974",
                publication_date="1952-03-01",
                reliability_score=0.90,
                domain="finance"
            ),
            EvidenceSource(
                id="fin_002",
                title="Interest Rate and Bond Price Relationship",
                content="Bond prices and interest rates have an inverse relationship due to discounted cash flow principles. When interest rates rise, existing bonds with lower coupon rates become less attractive, causing their prices to fall. Duration measures price sensitivity to interest rate changes. Longer-duration bonds experience greater price volatility from interest rate movements.",
                source_type="financial_textbook",
                url="https://www.investopedia.com/terms/i/interest_rate_risk.asp",
                publication_date="2023-01-15",
                reliability_score=0.85,
                domain="finance"
            ),
            EvidenceSource(
                id="fin_003",
                title="Cryptocurrency Market Volatility",
                content="Cryptocurrency markets exhibit extreme volatility with daily price movements often exceeding 10%. Bitcoin has experienced multiple bear markets with peak-to-trough declines exceeding 80%. Regulatory uncertainty, technological risks, and market manipulation contribute to volatility. The SEC and other regulators continue developing frameworks for digital asset oversight.",
                source_type="market_analysis",
                url="https://www.sec.gov/investor/alerts/ia_bitcoin.pdf",
                publication_date="2023-12-01",
                reliability_score=0.90,
                domain="finance"
            ),
            EvidenceSource(
                id="fin_004",
                title="Retirement Planning Best Practices",
                content="Financial advisors recommend saving 10-15% of income for retirement starting in one's 20s. The power of compound growth makes early saving crucial - each year delayed requires significantly higher savings rates. Tax-advantaged accounts like 401(k)s and IRAs provide substantial benefits. Target-date funds offer age-appropriate asset allocation automatically.",
                source_type="financial_planning",
                url="https://www.dol.gov/sites/dolgov/files/ebsa/about-ebsa/our-activities/resource-center/publications/top-10-ways-to-prepare-for-retirement.pdf",
                publication_date="2023-08-01",
                reliability_score=0.92,
                domain="finance"
            )
        ]
        
        # Add sources to database
        all_sources = medical_sources + financial_sources
        for source in all_sources:
            self.sources[source.id] = source
            
            # Update domain index
            if source.domain not in self.domain_index:
                self.domain_index[source.domain] = []
            self.domain_index[source.domain].append(source.id)
        
        logger.info(f"Loaded {len(all_sources)} evidence sources")
    
    def _compute_embeddings(self):
        """Compute embeddings for all evidence sources for semantic search with batching"""
        if not self.semantic_model:
            return
        
        try:
            logger.info("[EVIDENCE] Computing embeddings for semantic search...")
            
            # Process in batches to avoid memory issues and broken pipes
            BATCH_SIZE = 10
            source_items = list(self.sources.items())
            total_sources = len(source_items)
            
            for i in range(0, total_sources, BATCH_SIZE):
                batch = source_items[i:i+BATCH_SIZE]
                batch_texts = []
                batch_ids = []
                
                for source_id, source in batch:
                    # Combine title and content for better matching
                    text = f"{source.title}. {source.content}"
                    batch_texts.append(text)
                    batch_ids.append(source_id)
                
                try:
                    # Encode batch at once (more efficient than one-by-one)
                    embeddings = self.semantic_model.encode(batch_texts, convert_to_numpy=True, show_progress_bar=False)
                    
                    # Store embeddings
                    for source_id, embedding in zip(batch_ids, embeddings):
                        self.source_embeddings[source_id] = embedding
                    
                    logger.debug(f"[EVIDENCE] Processed batch {i//BATCH_SIZE + 1}/{(total_sources + BATCH_SIZE - 1)//BATCH_SIZE}")
                    
                except Exception as batch_error:
                    logger.warning(f"[EVIDENCE] Error in batch {i//BATCH_SIZE + 1}, falling back to individual encoding: {batch_error}")
                    # Fallback: encode one by one for this batch
                    for source_id, text in zip(batch_ids, batch_texts):
                        try:
                            embedding = self.semantic_model.encode(text, convert_to_numpy=True, show_progress_bar=False)
                            self.source_embeddings[source_id] = embedding
                        except Exception as single_error:
                            logger.error(f"[EVIDENCE] Failed to encode {source_id}: {single_error}")
                            continue
            
            logger.info(f"[EVIDENCE] ✅ Computed embeddings for {len(self.source_embeddings)} sources")
            
        except Exception as e:
            logger.error(f"[EVIDENCE] Error computing embeddings: {e}")
            logger.warning("[EVIDENCE] ⚠️ Continuing without embeddings - will use keyword search fallback")
    
    def _compute_embeddings_with_cache(self):
        """Compute embeddings with disk caching for fast startup"""
        if not self.semantic_model:
            return
        
        try:
            # Generate cache key based on source IDs
            source_ids_hash = hashlib.md5(
                '|'.join(sorted(self.sources.keys())).encode()
            ).hexdigest()[:12]
            cache_file = self.cache_dir / f"embeddings_{source_ids_hash}.npz"
            
            # Try to load from cache
            if cache_file.exists():
                try:
                    logger.info(f"[EVIDENCE] 📦 Loading embeddings from cache...")
                    cached_data = np.load(cache_file, allow_pickle=True)
                    
                    # Restore embeddings
                    for source_id in self.sources.keys():
                        if source_id in cached_data:
                            self.source_embeddings[source_id] = cached_data[source_id]
                    
                    if len(self.source_embeddings) == len(self.sources):
                        logger.info(f"[EVIDENCE] ✅ Loaded {len(self.source_embeddings)} embeddings from cache (instant!)")
                        return
                    else:
                        logger.warning(f"[EVIDENCE] ⚠️ Cache incomplete ({len(self.source_embeddings)}/{len(self.sources)}), recomputing...")
                except Exception as cache_error:
                    logger.warning(f"[EVIDENCE] ⚠️ Cache load failed: {cache_error}, recomputing...")
            
            # Compute embeddings (no cache or cache invalid)
            self._compute_embeddings()
            
            # Save to cache
            if self.source_embeddings:
                try:
                    np.savez(cache_file, **self.source_embeddings)
                    logger.info(f"[EVIDENCE] 💾 Saved embeddings to cache for future fast loading")
                except Exception as save_error:
                    logger.warning(f"[EVIDENCE] ⚠️ Could not save cache: {save_error}")
        except Exception as e:
            logger.error(f"[EVIDENCE] Error in cached embedding computation: {e}")
            # Fall back to computing embeddings without caching
            self._compute_embeddings()
                    
    def _build_keyword_index(self):
        """Build keyword TF-IDF index for hybrid search"""
        from collections import Counter
        import math
        
        # Document frequency counter
        doc_freq = Counter()
        term_freqs = {}
        
        # Count term frequencies
        for source_id, source in self.sources.items():
            text = f"{source.title} {source.content}".lower()
            words = re.findall(r'\b\w+\b', text)
            term_freq = Counter(words)
            term_freqs[source_id] = term_freq
            
            # Update document frequency
            for word in set(words):
                doc_freq[word] += 1
        
        # Calculate TF-IDF
        num_docs = len(self.sources)
        for source_id, term_freq in term_freqs.items():
            max_freq = max(term_freq.values()) if term_freq else 1
            for word, freq in term_freq.items():
                tf = freq / max_freq  # Normalized term frequency
                idf = math.log(num_docs / (1 + doc_freq[word]))  # IDF with smoothing
                tfidf = tf * idf
                
                if word not in self.keyword_index:
                    self.keyword_index[word] = {}
                self.keyword_index[word][source_id] = tfidf
        
        logger.info(f"[EVIDENCE] Built keyword index with {len(self.keyword_index)} terms")
    
    def _expand_query_with_synonyms(self, query: str, domain: str) -> str:
        """Expand query with domain-specific synonyms"""
        # Domain-specific synonym mappings
        medical_synonyms = {
            'pain': ['discomfort', 'ache', 'soreness'],
            'medication': ['drug', 'medicine', 'treatment'],
            'symptom': ['sign', 'indication'],
            'disease': ['illness', 'condition', 'disorder'],
            'treatment': ['therapy', 'intervention'],
            'diagnosis': ['evaluation', 'assessment']
        }
        
        finance_synonyms = {
            'investment': ['portfolio', 'asset'],
            'risk': ['volatility', 'uncertainty', 'exposure'],
            'return': ['profit', 'gain', 'yield'],
            'stock': ['equity', 'share'],
            'bond': ['fixed-income', 'debt security'],
            'retirement': ['pension', '401k', 'savings']
        }
        
        synonyms = medical_synonyms if domain == 'medical' else finance_synonyms
        
        expanded_terms = [query]
        words = query.lower().split()
        
        for word in words:
            if word in synonyms:
                expanded_terms.extend(synonyms[word][:2])  # Add top 2 synonyms
        
        return ' '.join(expanded_terms)
    
    def _bm25_search(self, query: str, top_k: int = 10) -> List[Tuple[EvidenceSource, float]]:
        """BM25 keyword-based search"""
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        
        source_scores = {}
        for word in query_words:
            if word in self.keyword_index:
                for source_id, tfidf_score in self.keyword_index[word].items():
                    if source_id not in source_scores:
                        source_scores[source_id] = 0.0
                    source_scores[source_id] += tfidf_score
        
        # Convert to list with sources
        results = [(self.sources[sid], score) for sid, score in source_scores.items()]
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def _score_evidence_quality(self, source: EvidenceSource, query: str, domain: str) -> float:
        """Calculate evidence quality score with recency, source type, and relevance"""
        quality_score = source.reliability_score  # Base: 0.8-0.95
        
        # Recency bonus (more important for finance)
        if domain == 'finance' and source.publication_date:
            try:
                pub_date = datetime.strptime(source.publication_date, '%Y-%m-%d')
                days_old = (datetime.now() - pub_date).days
                recency_factor = max(0.5, 1 - (days_old / 365) * 0.2)  # -20% per year, min 50%
                quality_score *= recency_factor
            except:
                pass
        
        # Source type weighting
        source_weights = {
            'medical': {
                'clinical_guideline': 1.2,
                'academic_research': 1.15,
                'medical_textbook': 1.0,
                'health_website': 0.85
            },
            'finance': {
                'academic_research': 1.2,
                'financial_report': 1.15,
                'market_analysis': 1.1,
                'financial_planning': 1.0,
                'financial_textbook': 0.95
            }
        }
        
        if domain in source_weights and source.source_type in source_weights[domain]:
            quality_score *= source_weights[domain][source.source_type]
        
        # Domain keyword density bonus
        domain_keywords = self._extract_domain_keywords(query, domain)
        if domain_keywords:
            keyword_matches = sum(1 for kw in domain_keywords if kw in source.content.lower())
            keyword_density = keyword_matches / len(domain_keywords)
            quality_score *= (0.6 + 0.6 * keyword_density)  # 0.6-1.2x multiplier
        
        return min(quality_score, 1.2)  # Cap at 1.2
    
    def _extract_domain_keywords(self, query: str, domain: str) -> List[str]:
        """Extract domain-specific keywords from query"""
        query_lower = query.lower()
        
        medical_keywords = ['health', 'medical', 'disease', 'symptom', 'treatment', 
                          'medication', 'diagnosis', 'therapy', 'patient', 'clinical']
        finance_keywords = ['investment', 'finance', 'stock', 'bond', 'portfolio', 
                          'risk', 'return', 'market', 'retirement', 'savings']
        
        keywords = medical_keywords if domain == 'medical' else finance_keywords
        return [kw for kw in keywords if kw in query_lower]
    
    def search_sources(self, query: str, domain: str, max_results: int = 5, semantic: bool = True) -> List[EvidenceSource]:
        """Search for relevant evidence sources using hybrid search (semantic + keyword)"""
        
        # Get domain-specific sources
        domain_source_ids = self.domain_index.get(domain, [])
        if not domain_source_ids:
            # Fall back to all sources if domain not found
            domain_source_ids = list(self.sources.keys())
        
        logger.info(f"[EVIDENCE] Searching {len(domain_source_ids)} {domain} sources for query: '{query[:60]}...'")
        
        # Expand query with synonyms
        expanded_query = self._expand_query_with_synonyms(query, domain)
        
        # Use hybrid search if semantic model available
        if self.semantic_model and self.source_embeddings and semantic:
            return self._hybrid_search(expanded_query, domain_source_ids, max_results, domain, original_query=query)
        else:
            # Fallback to keyword matching
            return self._keyword_search(query, domain_source_ids, max_results)
    
    def _hybrid_search(self, query: str, source_ids: List[str], max_results: int, domain: str, original_query: str = None) -> List[EvidenceSource]:
        """Hybrid search combining semantic and keyword-based retrieval with quality scoring"""
        try:
            # Step 1: Get semantic search results (2x max_results for fusion)
            semantic_results = self._semantic_search_raw(query, source_ids, max_results * 2, domain)
            
            # Step 2: Get keyword search results (2x max_results for fusion)
            keyword_results = self._bm25_search(query, max_results * 2)
            
            # Step 3: Fusion scoring (0.7 semantic + 0.3 keyword)
            combined_scores = {}
            for source, score in semantic_results:
                combined_scores[source.id] = {'source': source, 'score': 0.7 * score}
            
            for source, score in keyword_results:
                if source.id in combined_scores:
                    combined_scores[source.id]['score'] += 0.3 * score
                else:
                    combined_scores[source.id] = {'source': source, 'score': 0.3 * score}
            
            # Step 4: Apply evidence quality scoring
            query_for_quality = original_query if original_query else query
            for source_id, data in combined_scores.items():
                quality_multiplier = self._score_evidence_quality(data['source'], query_for_quality, domain)
                data['score'] *= quality_multiplier
            
            # Step 5: Sort and return top results with diversity
            scored_items = [(data['score'], data['source']) for data in combined_scores.values()]
            
            # Apply maximal marginal relevance for diversity
            diverse_results = self._apply_mmr_diversity(scored_items, max_results)
            
            logger.info(f"[EVIDENCE] ✅ Hybrid search (semantic+keyword+quality+diversity) returned {len(diverse_results)} sources")
            return diverse_results
            
        except Exception as e:
            logger.error(f"[EVIDENCE] Error in hybrid search: {e}, falling back to semantic only")
            return self._semantic_search(query, source_ids, max_results, domain)
    
    def _apply_mmr_diversity(self, scored_sources: List[Tuple[float, EvidenceSource]], max_results: int, lambda_param: float = 0.7) -> List[EvidenceSource]:
        """Apply Maximal Marginal Relevance for diverse results"""
        if not scored_sources or not self.semantic_model:
            return [source for _, source in scored_sources[:max_results]]
        
        # Sort by score
        scored_sources.sort(key=lambda x: x[0], reverse=True)
        
        selected = []
        selected_embeddings = []
        
        # First source: highest score
        _, first_source = scored_sources[0]
        selected.append(first_source)
        if first_source.id in self.source_embeddings:
            selected_embeddings.append(self.source_embeddings[first_source.id])
        
        # Remaining sources: balance relevance and diversity
        for _ in range(max_results - 1):
            best_score = -1
            best_source = None
            
            for score, source in scored_sources:
                if source in selected:
                    continue
                
                if source.id not in self.source_embeddings:
                    continue
                
                # Diversity score: minimum similarity to already selected
                source_emb = self.source_embeddings[source.id]
                if selected_embeddings:
                    max_sim = max(
                        np.dot(source_emb, sel_emb) / (np.linalg.norm(source_emb) * np.linalg.norm(sel_emb))
                        for sel_emb in selected_embeddings
                    )
                    diversity_score = 1 - max_sim
                else:
                    diversity_score = 1.0
                
                # MMR score: lambda * relevance + (1-lambda) * diversity
                mmr_score = lambda_param * score + (1 - lambda_param) * diversity_score
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_source = source
            
            if best_source:
                selected.append(best_source)
                selected_embeddings.append(self.source_embeddings[best_source.id])
            else:
                break
        
        return selected
    
    def _semantic_search_raw(self, query: str, source_ids: List[str], max_results: int, domain: str) -> List[Tuple[EvidenceSource, float]]:
        """Raw semantic search returning (source, score) tuples"""
        try:
            query_embedding = self.semantic_model.encode(query, convert_to_numpy=True)
            
            scored_sources = []
            for source_id in source_ids:
                if source_id not in self.source_embeddings:
                    continue
                
                source_embedding = self.source_embeddings[source_id]
                similarity = np.dot(query_embedding, source_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(source_embedding)
                )
                
                # Boost curated sources
                if source_id in self.curated_source_ids:
                    similarity *= 1.2
                
                scored_sources.append((self.sources[source_id], similarity))
            
            scored_sources.sort(key=lambda x: x[1], reverse=True)
            return scored_sources[:max_results]
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def _semantic_search(self, query: str, source_ids: List[str], max_results: int, domain: str = "general") -> List[EvidenceSource]:
        """Perform semantic similarity search using embeddings with prioritization"""
        try:
            # Encode query
            query_embedding = self.semantic_model.encode(query, convert_to_numpy=True)
            
            # Calculate cosine similarity with all sources
            scored_sources = []
            for source_id in source_ids:
                if source_id not in self.source_embeddings:
                    continue
                
                source_embedding = self.source_embeddings[source_id]
                
                # Cosine similarity
                similarity = np.dot(query_embedding, source_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(source_embedding)
                )
                
                # BOOST curated sources: give them priority over dataset sources
                if source_id in self.curated_source_ids:
                    similarity = similarity * 1.2  # 20% boost for curated sources
                
                source = self.sources[source_id]
                scored_sources.append((similarity, source))
                logger.debug(f"[EVIDENCE] {source_id}: semantic_score={similarity:.3f}")
            
            # Sort by similarity and return top results
            scored_sources.sort(key=lambda x: x[0], reverse=True)
            
            # Dynamic similarity threshold based on query characteristics
            min_similarity = self._calculate_dynamic_similarity_threshold(query, domain)
            filtered_sources = [(score, source) for score, source in scored_sources if score >= min_similarity]
            
            top_sources = [source for _, source in filtered_sources[:max_results]]
            
            if top_sources:
                scores_str = ', '.join([f'{score:.3f}' for score, _ in filtered_sources[:max_results]])
                curated_count = sum(1 for s in top_sources if s.id in self.curated_source_ids)
                dataset_count = sum(1 for s in top_sources if s.id in self.dataset_source_ids)
                logger.info(f"[EVIDENCE] ✅ Found {len(top_sources)} sources (curated: {curated_count}, dataset: {dataset_count}) - similarity: {scores_str}")
            else:
                logger.warning(f"[EVIDENCE] ⚠️ Semantic search found no sources above threshold {min_similarity:.2f}")
                # Fallback: return top 3 even if below threshold
                if scored_sources:
                    top_sources = [source for _, source in scored_sources[:min(3, max_results)]]
                    logger.info(f"[EVIDENCE] 📊 Returning top {len(top_sources)} sources anyway (best: {scored_sources[0][0]:.3f})")
            
            return top_sources
            
        except Exception as e:
            logger.error(f"[EVIDENCE] Error in semantic search: {e}")
            # Fallback to keyword matching
            return self._keyword_search(query, source_ids, max_results)
    
    def _calculate_dynamic_similarity_threshold(self, query: str, domain: str) -> float:
        """Calculate dynamic similarity threshold based on query and domain characteristics"""
        
        # Base threshold by domain (some domains need stricter matching)
        domain_thresholds = {
            'medical': 0.35,    # Medical needs higher precision
            'finance': 0.32,    # Financial information needs accuracy  
            'scientific': 0.35, # Scientific queries need precision
            'legal': 0.40,      # Legal domain requires high accuracy
            'general': 0.25,    # General queries can be more lenient
        }
        base_threshold = domain_thresholds.get(domain.lower(), 0.30)
        
        # Adjust threshold based on query complexity
        query_length = len(query.split())
        if query_length <= 3:
            # Short queries: lower threshold (more results)
            length_adjustment = -0.05
        elif query_length <= 8:
            # Medium queries: standard threshold
            length_adjustment = 0.0
        else:
            # Long queries: higher threshold (more precise)
            length_adjustment = 0.05
        
        # Technical term density adjustment
        technical_terms = ['analyze', 'calculate', 'determine', 'evaluate', 'assess', 'compare']
        technical_count = sum(1 for term in technical_terms if term in query.lower())
        technical_density = technical_count / max(query_length, 1)
        
        if technical_density > 0.3:
            # High technical density: increase threshold
            technical_adjustment = 0.05
        elif technical_density > 0.1:
            # Medium technical density: slight increase
            technical_adjustment = 0.02
        else:
            # Low technical density: standard threshold
            technical_adjustment = 0.0
        
        # Combine all adjustments
        final_threshold = base_threshold + length_adjustment + technical_adjustment
        
        # Ensure reasonable bounds
        return max(0.15, min(final_threshold, 0.50))
    
    def _keyword_search(self, query: str, source_ids: List[str], max_results: int) -> List[EvidenceSource]:
        """Fallback keyword-based search"""
        query_terms = set(query.lower().split())
        scored_sources = []
        
        logger.info(f"[EVIDENCE] Using keyword search (query terms: {len(query_terms)})")
        
        for source_id in source_ids:
            source = self.sources[source_id]
            
            # Calculate relevance score
            content_terms = set((source.title + " " + source.content).lower().split())
            title_terms = set(source.title.lower().split())
            
            # Term overlap scoring
            content_overlap = len(query_terms.intersection(content_terms))
            title_overlap = len(query_terms.intersection(title_terms))
            
            # Weight title matches more heavily
            if len(query_terms) > 0:
                relevance_score = (content_overlap + title_overlap * 2) / len(query_terms)
            else:
                relevance_score = 0
            
            if relevance_score > 0:
                scored_sources.append((relevance_score, source))
                logger.debug(f"[EVIDENCE] {source_id}: keyword_score={relevance_score:.2f}")
        
        # Sort by relevance and return top results
        scored_sources.sort(key=lambda x: x[0], reverse=True)
        top_sources = [source for _, source in scored_sources[:max_results]]
        
        if top_sources:
            scores_str = ', '.join([f'{score:.2f}' for score, _ in scored_sources[:max_results]])
            logger.info(f"[EVIDENCE] ✅ Keyword search found {len(top_sources)} sources (scores: {scores_str})")
        else:
            logger.warning(f"[EVIDENCE] ❌ Keyword search found no matching sources")
        
        return top_sources
    
    def get_source_by_id(self, source_id: str) -> Optional[EvidenceSource]:
        """Get a source by its ID"""
        return self.sources.get(source_id)

class CitationManager:
    """Manages citation generation and formatting"""
    
    def __init__(self):
        self.citation_styles = {
            'apa': self._format_apa_citation,
            'mla': self._format_mla_citation,
            'chicago': self._format_chicago_citation,
            'simple': self._format_simple_citation
        }
    
    def generate_citations(self, sources: List[EvidenceSource], style: str = 'simple') -> List[Citation]:
        """Generate citations for evidence sources"""
        citations = []
        
        for i, source in enumerate(sources, 1):
            # Extract relevant snippet
            snippet = self._extract_relevant_snippet(source.content)
            
            # Format citation
            formatter = self.citation_styles.get(style, self._format_simple_citation)
            citation_format = formatter(source, i)
            
            citation = Citation(
                source_id=source.id,
                text_snippet=snippet,
                relevance_score=source.reliability_score,
                citation_format=citation_format
            )
            
            citations.append(citation)
        
        return citations
    
    def _extract_relevant_snippet(self, content: str, max_length: int = 150) -> str:
        """Extract a relevant snippet from source content"""
        sentences = content.split('. ')
        
        # Return first sentence if short enough
        if len(sentences[0]) <= max_length:
            return sentences[0] + '.'
        
        # Otherwise truncate first sentence
        words = sentences[0].split()
        snippet = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > max_length - 3:
                break
            snippet.append(word)
            current_length += len(word) + 1
        
        return ' '.join(snippet) + '...'
    
    def _format_simple_citation(self, source: EvidenceSource, number: int) -> str:
        """Format citation in simple style"""
        return f"[{number}] {source.title}"
    
    def _format_apa_citation(self, source: EvidenceSource, number: int) -> str:
        """Format citation in APA style"""
        date_str = source.publication_date or "n.d."
        url_str = f" Retrieved from {source.url}" if source.url else ""
        return f"[{number}] {source.title}. ({date_str}). {source.source_type.replace('_', ' ').title()}.{url_str}"
    
    def _format_mla_citation(self, source: EvidenceSource, number: int) -> str:
        """Format citation in MLA style"""
        date_str = source.publication_date or "n.d."
        url_str = f" Web. {datetime.now().strftime('%d %b %Y')}." if source.url else ""
        return f"[{number}] \"{source.title}.\" {source.source_type.replace('_', ' ').title()}, {date_str}.{url_str}"
    
    def _format_chicago_citation(self, source: EvidenceSource, number: int) -> str:
        """Format citation in Chicago style"""
        date_str = source.publication_date or "n.d."
        url_str = f" {source.url}" if source.url else ""
        return f"[{number}] \"{source.title},\" {source.source_type.replace('_', ' ').title()}, {date_str}.{url_str}"

class EvidenceIntegrator:
    """Integrates evidence sources into agent responses"""
    
    def __init__(self, evidence_db: EvidenceDatabase, citation_manager: CitationManager):
        self.evidence_db = evidence_db
        self.citation_manager = citation_manager
        self.logger = logging.getLogger(__name__)
    
    def enhance_response_with_evidence(
        self, 
        response: str, 
        query: str, 
        domain: str,
        max_sources: int = 3
    ) -> EnhancedResponse:
        """Enhance response with evidence and citations"""
        
        # Search for relevant evidence
        evidence_sources = self.evidence_db.search_sources(query, domain, max_sources)
        
        if not evidence_sources:
            return EnhancedResponse(
                answer=response,
                evidence_sources=[],
                citations=[],
                evidence_coverage=0.0,
                citation_quality_score=0.0
            )
        
        # Generate citations
        citations = self.citation_manager.generate_citations(evidence_sources)
        
        # Integrate evidence into response
        enhanced_answer = self._integrate_evidence_into_response(
            response, evidence_sources, citations
        )
        
        # Calculate quality metrics
        evidence_coverage = self._calculate_evidence_coverage(query, evidence_sources)
        citation_quality_score = self._calculate_citation_quality(citations)
        
        return EnhancedResponse(
            answer=enhanced_answer,
            evidence_sources=evidence_sources,
            citations=citations,
            evidence_coverage=evidence_coverage,
            citation_quality_score=citation_quality_score
        )
    
    def _integrate_evidence_into_response(
        self, 
        response: str, 
        sources: List[EvidenceSource], 
        citations: List[Citation]
    ) -> str:
        """Integrate evidence and citations into the response"""
        
        if not sources:
            return response
        
        # DO NOT add evidence sections here - let the agent's _add_structured_format handle ALL formatting
        # This prevents duplicate evidence sections
        # Just return the original response - the agent will format it with evidence sources
        
        return response
    
    def _calculate_evidence_coverage(self, query: str, sources: List[EvidenceSource]) -> float:
        """Calculate how well evidence covers the query"""
        if not sources:
            return 0.0
        
        query_terms = set(query.lower().split())
        covered_terms = set()
        
        for source in sources:
            source_terms = set((source.title + " " + source.content).lower().split())
            covered_terms.update(query_terms.intersection(source_terms))
        
        coverage = len(covered_terms) / len(query_terms) if query_terms else 0.0
        return min(coverage, 1.0)
    
    def _calculate_citation_quality(self, citations: List[Citation]) -> float:
        """Calculate overall citation quality score dynamically"""
        if not citations:
            return 0.0
        
        return self._calculate_dynamic_citation_quality(citations)
    
    def _calculate_dynamic_citation_quality(self, citations: List[Citation]) -> float:
        """Calculate citation quality based on source characteristics and diversity"""
        if not citations:
            return 0.0
        
        # Base quality from relevance scores
        relevance_scores = [citation.relevance_score for citation in citations]
        base_quality = sum(relevance_scores) / len(relevance_scores)
        
        # Source diversity scoring (different source types)
        source_types = set()
        for citation in citations:
            if hasattr(citation, 'source_type'):
                source_types.add(citation.source_type)
        
        # Dynamic diversity bonus based on source variety
        diversity_factor = min(len(source_types) / 3.0, 1.0)  # Normalize to max 3 types
        diversity_bonus = diversity_factor * 0.15  # Up to 15% bonus
        
        # Source reliability assessment
        reliability_scores = []
        for citation in citations:
            # Dynamic reliability based on source characteristics
            reliability = self._assess_source_reliability(citation)
            reliability_scores.append(reliability)
        
        avg_reliability = sum(reliability_scores) / len(reliability_scores)
        reliability_factor = avg_reliability * 0.25  # Up to 25% from reliability
        
        # Citation quantity factor (diminishing returns)
        quantity_count = len(citations)
        if quantity_count == 1:
            quantity_factor = 0.0
        elif quantity_count == 2:
            quantity_factor = 0.10
        elif quantity_count == 3:
            quantity_factor = 0.20
        else:  # 4+ citations
            quantity_factor = 0.25
        
        # Combine all factors
        final_score = base_quality + diversity_bonus + reliability_factor + quantity_factor
        return min(final_score, 1.0)
    
    def _assess_source_reliability(self, citation: Citation) -> float:
        """Assess individual source reliability dynamically"""
        reliability_score = 0.5  # Base reliability
        
        # Check if citation has source information
        if not hasattr(citation, 'source_type'):
            return reliability_score
        
        # Source type reliability (dynamically assessed)
        source_type = getattr(citation, 'source_type', 'unknown')
        
        if 'academic' in source_type.lower() or 'journal' in source_type.lower():
            reliability_score += 0.3  # Academic sources more reliable
        elif 'medical' in source_type.lower() or 'clinical' in source_type.lower():
            reliability_score += 0.25  # Medical sources highly reliable
        elif 'financial' in source_type.lower() or 'regulatory' in source_type.lower():
            reliability_score += 0.25  # Financial regulatory sources reliable
        elif 'government' in source_type.lower() or 'official' in source_type.lower():
            reliability_score += 0.20  # Government sources reliable
        elif 'news' in source_type.lower():
            reliability_score += 0.10  # News sources moderately reliable
        else:
            reliability_score += 0.05  # Unknown sources get small boost
        
        # Content quality indicators
        if hasattr(citation, 'relevance_score'):
            # Higher relevance suggests better source matching
            relevance_boost = citation.relevance_score * 0.15
            reliability_score += relevance_boost
        
        return min(reliability_score, 1.0)

class RAGSystem:
    """Complete Retrieval-Augmented Generation system"""
    
    def __init__(self, data_dir: str = None, config_path: str = None):
        self.evidence_db = EvidenceDatabase(data_dir, config_path)
        self.citation_manager = CitationManager()
        self.evidence_integrator = EvidenceIntegrator(self.evidence_db, self.citation_manager)
        self.logger = logging.getLogger(__name__)
    
    def retrieve_evidence(self, query: str, domain: str = "general", top_k: int = 3) -> List[EvidenceSource]:
        """
        Retrieve relevant evidence sources for a query
        
        Args:
            query: The query to find evidence for
            domain: Domain to search in ('medical', 'finance', or 'general')
            top_k: Number of sources to return
            
        Returns:
            List of relevant EvidenceSource objects
        """
        return self.evidence_db.search_sources(query, domain, max_results=top_k)
    
    def format_evidence_for_prompt(self, sources: List[EvidenceSource]) -> str:
        """
        Format evidence sources for inclusion in LLM prompts
        
        Args:
            sources: List of evidence sources
            
        Returns:
            Formatted string with numbered sources
        """
        if not sources:
            return "No specific evidence sources available for this query."
        
        formatted = "=== EVIDENCE SOURCES ===\n\n"
        
        for i, source in enumerate(sources, 1):
            formatted += f"[Source {i}] {source.title}\n"
            formatted += f"Type: {source.source_type}\n"
            formatted += f"Reliability: {source.reliability_score:.0%}\n"
            formatted += f"Content: {source.content[:400]}...\n"  # First 400 chars
            if source.url:
                formatted += f"URL: {source.url}\n"
            formatted += "\n"
        
        formatted += "=== CITATION INSTRUCTIONS ===\n"
        formatted += "You MUST cite these sources in your response using [Source X] format.\n"
        formatted += "Example: 'Low-dose aspirin reduces cardiovascular risk [Source 1].'\n\n"
        
        return formatted
    
    def enhance_agent_response(
        self, 
        response: str, 
        query: str, 
        domain: str
    ) -> Tuple[str, Dict[str, float]]:
        """Main method to enhance agent response with evidence"""
        
        # Get enhanced response with evidence
        enhanced_response = self.evidence_integrator.enhance_response_with_evidence(
            response, query, domain
        )
        
        # Calculate improvement metrics dynamically
        improvements = self._calculate_dynamic_improvements(enhanced_response, query, domain)
        
        self.logger.info(f"Enhanced response with {len(enhanced_response.evidence_sources)} evidence sources")
        
        return enhanced_response.answer, improvements
    
    def _calculate_dynamic_improvements(self, enhanced_response: EnhancedResponse, query: str, domain: str) -> dict:
        """Calculate evidence-based improvements dynamically based on response characteristics"""
        
        # Base evidence presence assessment
        has_evidence = enhanced_response.evidence_coverage > 0
        evidence_count = len(enhanced_response.evidence_sources)
        
        # Dynamic base boost calculation
        if has_evidence:
            # Scale base boost by evidence quality and quantity
            evidence_quality_factor = enhanced_response.citation_quality_score
            quantity_factor = min(evidence_count / 3.0, 1.0)  # Normalize to 3 sources
            base_boost = 0.03 + (evidence_quality_factor * quantity_factor * 0.07)  # 3-10% range
        else:
            base_boost = 0.0
        
        # Domain-specific coverage weighting
        domain_coverage_multiplier = self._get_domain_coverage_multiplier(domain)
        coverage_boost = enhanced_response.evidence_coverage * domain_coverage_multiplier
        
        # Quality-adjusted citation improvement
        citation_base_improvement = enhanced_response.citation_quality_score
        
        # Adjust citation improvement based on query complexity
        query_complexity = self._assess_query_complexity(query)
        citation_complexity_factor = 0.20 + (query_complexity * 0.15)  # 20-35% range
        citation_improvement = citation_base_improvement * citation_complexity_factor
        
        # Factual consistency improvement based on evidence characteristics
        evidence_diversity = self._assess_evidence_diversity(enhanced_response.evidence_sources)
        consistency_multiplier = 0.25 + (evidence_diversity * 0.15)  # 25-40% range
        factual_improvement = enhanced_response.evidence_coverage * consistency_multiplier
        
        # Overall faithfulness improvement (combining base and coverage)
        faithfulness_improvement = min(base_boost + coverage_boost, 0.45)  # Cap at 45%
        
        return {
            'evidence_coverage': enhanced_response.evidence_coverage,
            'citation_quality': enhanced_response.citation_quality_score,
            'faithfulness_improvement': faithfulness_improvement,
            'citation_accuracy_improvement': citation_improvement,
            'factual_consistency_improvement': factual_improvement,
        }
    
    def _get_domain_coverage_multiplier(self, domain: str) -> float:
        """Get domain-specific multiplier for evidence coverage impact"""
        domain_multipliers = {
            'medical': 0.40,    # Medical domain values evidence highly
            'finance': 0.35,    # Financial domain needs solid backing  
            'scientific': 0.40, # Scientific queries require strong evidence
            'legal': 0.45,      # Legal domain heavily evidence-dependent
            'general': 0.30,    # General queries less evidence-dependent
        }
        return domain_multipliers.get(domain.lower(), 0.30)
    
    def _assess_query_complexity(self, query: str) -> float:
        """Assess query complexity to adjust citation requirements"""
        if not query:
            return 0.0
        
        complexity_indicators = 0.0
        
        # Length-based complexity
        word_count = len(query.split())
        if word_count > 20:
            complexity_indicators += 0.3
        elif word_count > 10:
            complexity_indicators += 0.2
        elif word_count > 5:
            complexity_indicators += 0.1
        
        # Technical term complexity
        technical_terms = ['analyze', 'compare', 'evaluate', 'assess', 'determine', 'calculate']
        technical_count = sum(1 for term in technical_terms if term in query.lower())
        complexity_indicators += min(technical_count * 0.15, 0.3)
        
        # Question complexity markers
        complex_markers = ['why', 'how', 'what if', 'compare', 'difference', 'relationship']
        marker_count = sum(1 for marker in complex_markers if marker in query.lower())
        complexity_indicators += min(marker_count * 0.1, 0.2)
        
        return min(complexity_indicators, 1.0)
    
    def _assess_evidence_diversity(self, evidence_sources: List[EvidenceSource]) -> float:
        """Assess diversity of evidence sources for consistency scoring"""
        if not evidence_sources:
            return 0.0
        
        # Count unique source types
        source_types = set()
        publication_years = set()
        
        for source in evidence_sources:
            if hasattr(source, 'source_type'):
                source_types.add(source.source_type)
            if hasattr(source, 'publication_date') and source.publication_date:
                try:
                    year = source.publication_date[:4]  # Extract year
                    publication_years.add(year)
                except:
                    pass
        
        # Diversity score based on variety
        type_diversity = min(len(source_types) / 3.0, 1.0)  # Max 3 different types
        temporal_diversity = min(len(publication_years) / 3.0, 1.0)  # Max 3 different years
        
        # Combined diversity score
        overall_diversity = (type_diversity + temporal_diversity) / 2.0
        return overall_diversity

# Example usage and testing
def test_rag_system():
    """Test the RAG system with sample queries"""
    rag_system = RAGSystem()
    
    test_cases = [
        {
            "query": "What are the side effects of aspirin?",
            "response": "Aspirin can cause stomach irritation and increased bleeding risk.",
            "domain": "medical"
        },
        {
            "query": "How should I diversify my investment portfolio?",
            "response": "Diversification involves spreading investments across different assets to reduce risk.",
            "domain": "finance"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Query: {case['query']}")
        print(f"Original Response: {case['response']}")
        
        enhanced_response, improvements = rag_system.enhance_agent_response(
            case['response'], case['query'], case['domain']
        )
        
        print(f"Enhanced Response: {enhanced_response}")
        print(f"Improvements: {improvements}")

if __name__ == "__main__":
    test_rag_system()