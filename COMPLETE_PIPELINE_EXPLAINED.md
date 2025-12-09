# FAIR-Agent Complete Processing Pipeline

## 📋 Overview

This document explains the **COMPLETE 17-step pipeline** that shows exactly how your FAIR-Agent processes queries from start to finish.

---

## 🔄 Complete Processing Flow

```
USER QUERY: "What are the symptoms of diabetes?"
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  STEP 1: RECEIVE QUERY                                            │
│  Input: { query: "What are the symptoms of diabetes?" }          │
└───────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  STEP 2: EXTRACT & VALIDATE                                       │
│  Output: { query_text, user_id, session_id, timestamp }          │
└───────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  STEP 3: DOMAIN CLASSIFICATION                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Medical Keywords: ['symptom', 'disease', 'diabetes', ...]  │ │
│  │ Finance Keywords: ['stock', 'investment', 'profit', ...]    │ │
│  │                                                              │ │
│  │ Scoring:                                                     │ │
│  │   Medical Score: 2 matches → MEDICAL                        │ │
│  │   Finance Score: 0 matches                                  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  Output: domain = "medical"                                       │
└───────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  STEP 4: ROUTE BY DOMAIN                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐                   │
│  │ Medical  │  │ Finance  │  │ Cross-Domain │                   │
│  │   ✓      │  │          │  │              │                   │
│  └──────────┘  └──────────┘  └──────────────┘                   │
└───────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  STEP 5: GENERATE BASELINE RESPONSE (Ollama)                      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ POST http://localhost:11435/api/generate                    │ │
│  │ {                                                            │ │
│  │   "model": "llama3.2:latest",                               │ │
│  │   "prompt": "What are the symptoms of diabetes?",           │ │
│  │   "options": {                                               │ │
│  │     "temperature": 0.7,                                      │ │
│  │     "top_p": 0.9,                                            │ │
│  │     "num_predict": 512                                       │ │
│  │   }                                                          │ │
│  │ }                                                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  Output: "Diabetes symptoms include increased thirst..."         │
└───────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  STEP 6: PARSE BASELINE                                           │
│  baseline_answer = "Diabetes symptoms include increased..."       │
└───────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  STEP 7: RAG - RETRIEVE EVIDENCE                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ SRC: src/evidence/rag_system.py                             │ │
│  │ METHOD: EvidenceDatabase.retrieve_evidence()                │ │
│  │                                                              │ │
│  │ 1. Load query embedding using SentenceTransformer           │ │
│  │ 2. Search evidence_sources.yaml                             │ │
│  │ 3. Load cached embeddings from:                             │ │
│  │    data/evidence/embeddings_cache/                          │ │
│  │ 4. Compute cosine similarity                                │ │
│  │ 5. Retrieve top 3 sources                                   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  Output:                                                          │
│  evidence_sources = [                                             │
│    {                                                              │
│      source_id: "pubmed_diabetes_001",                           │
│      content: "Diabetes mellitus is characterized by...",        │
│      reliability: 0.95,                                           │
│      domain: "medical"                                            │
│    },                                                             │
│    {                                                              │
│      source_id: "medmcqa_endocrine_045",                         │
│      content: "Common symptoms include polyuria...",             │
│      reliability: 0.90,                                           │
│      domain: "medical"                                            │
│    }                                                              │
│  ]                                                                │
└───────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  STEP 8: FORMAT EVIDENCE INTO ENHANCED PROMPT                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ SRC: src/evidence/rag_system.py                             │ │
│  │ METHOD: format_evidence_for_prompt()                        │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  enhanced_prompt =                                                │
│  """                                                              │
│  You are a medical expert. Use ONLY these trusted sources:       │
│                                                                   │
│  [Source 1] (Reliability: 95%)                                   │
│  Diabetes mellitus is characterized by...                        │
│  URL: https://pubmed.ncbi.nlm.nih.gov/12345                      │
│                                                                   │
│  [Source 2] (Reliability: 90%)                                   │
│  Common symptoms include polyuria...                             │
│                                                                   │
│  QUESTION: What are the symptoms of diabetes?                    │
│                                                                   │
│  Provide a detailed answer based ONLY on sources above.          │
│  Include citations like [Source 1], [Source 2].                  │
│  """                                                              │
└───────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  STEP 9: GENERATE RAG-ENHANCED ANSWER (Ollama)                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ POST http://localhost:11435/api/generate                    │ │
│  │ {                                                            │ │
│  │   "model": "llama3.2:latest",                               │ │
│  │   "prompt": <enhanced_prompt_from_step_8>,                  │ │
│  │   "options": {                                               │ │
│  │     "temperature": 0.7,                                      │ │
│  │     "num_predict": 512                                       │ │
│  │   }                                                          │ │
│  │ }                                                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  Output (RAG Answer):                                             │
│  "Based on trusted medical sources [Source 1], diabetes          │
│   symptoms include increased thirst (polydipsia), frequent       │
│   urination (polyuria) [Source 2], unexplained weight loss,      │
│   and fatigue."                                                   │
└───────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  STEP 10: PARSE RAG ANSWER                                        │
│  rag_answer = "Based on trusted medical sources..."               │
└───────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  STEP 11: CREATE CHAIN-OF-THOUGHT PROMPT                          │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ SRC: src/reasoning/cot_system.py                            │ │
│  │ METHOD: ChainOfThoughtGenerator.generate_reasoning_chain() │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  cot_prompt =                                                     │
│  """                                                              │
│  Question: What are the symptoms of diabetes?                    │
│                                                                   │
│  Answer: Based on trusted medical sources [Source 1]...          │
│                                                                   │
│  Now, provide step-by-step reasoning that explains how           │
│  you arrived at this answer:                                     │
│                                                                   │
│  Step 1:                                                          │
│  Step 2:                                                          │
│  Step 3:                                                          │
│  Final Conclusion:                                                │
│  """                                                              │
└───────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  STEP 12: GENERATE CHAIN-OF-THOUGHT REASONING (Ollama)            │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ POST http://localhost:11435/api/generate                    │ │
│  │ {                                                            │ │
│  │   "model": "llama3.2:latest",                               │ │
│  │   "prompt": <cot_prompt_from_step_11>,                      │ │
│  │   "options": { "temperature": 0.7, "num_predict": 300 }     │ │
│  │ }                                                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  Output (Reasoning):                                              │
│  "Step 1: I analyzed the medical sources provided                │
│   Step 2: I identified the key symptoms mentioned                │
│   Step 3: I verified the reliability of each source              │
│   Final Conclusion: Based on evidence, symptoms are..."          │
└───────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  STEP 13: PARSE REASONING STEPS                                   │
│  reasoning_steps = [                                              │
│    { step_number: 1, thought: "I analyzed medical sources" },    │
│    { step_number: 2, thought: "I identified key symptoms" },     │
│    { step_number: 3, thought: "I verified reliability" }         │
│  ]                                                                │
└───────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  STEP 14: ADD SAFETY DISCLAIMERS                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ SRC: src/safety/disclaimer_system.py                        │ │
│  │ METHOD: ResponseEnhancer.enhance_response()                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  For Medical domain:                                              │
│  disclaimer = "⚕️ MEDICAL DISCLAIMER: This information is for    │
│                educational purposes only and should not replace   │
│                professional medical advice. Always consult with   │
│                a qualified healthcare provider."                  │
│                                                                   │
│  enhanced_answer = rag_answer + disclaimer                        │
│                                                                   │
│  Safety keyword check: ['harmful', 'risk', 'side effect']        │
│  detected_keywords = ['risk'] → safety_score = 0.7               │
└───────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  STEP 15: CALCULATE FAIR METRICS                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ SRC: src/evaluation/                                         │ │
│  │  - faithfulness.py → Evidence alignment                      │ │
│  │  - adaptability.py → Cross-domain handling                   │ │
│  │  - interpretability.py → Reasoning transparency              │ │
│  │  - robustness.py → Answer quality improvement                │ │
│  │  - safety.py → Disclaimer & harmful content detection        │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  FAITHFULNESS CALCULATION:                                        │
│    base_score = 50%                                               │
│    evidence_boost = 0.3 (3 sources provided)                      │
│    citation_count = 2 [Source 1], [Source 2]                     │
│    faithfulness = 50 + (0.3 * 100) + (2 * 5) = 90%               │
│                                                                   │
│  ADAPTABILITY CALCULATION:                                        │
│    domain = 'medical' (not cross-domain)                         │
│    adaptability = 75%                                             │
│                                                                   │
│  INTERPRETABILITY CALCULATION:                                    │
│    base_score = 40%                                               │
│    reasoning_boost = 0.25 (CoT applied)                           │
│    step_count = 3                                                 │
│    interpretability = 40 + (0.25 * 100) + (3 * 10) = 95%         │
│                                                                   │
│  ROBUSTNESS CALCULATION:                                          │
│    baseline_length = 150 chars                                    │
│    rag_length = 280 chars (improved)                              │
│    improvement_score = 0.2                                        │
│    robustness = 60 + (0.2 * 100) = 80%                            │
│                                                                   │
│  SAFETY CALCULATION:                                              │
│    safety_score = 0.7 (keyword detected)                          │
│    disclaimer_boost = 0.2                                         │
│    safety = (0.7 * 50) + (0.2 * 100) = 55%                        │
│                                                                   │
│  OVERALL CONFIDENCE:                                              │
│    confidence = (90 + 75 + 95 + 80 + 55) / 5 = 79%                │
│                                                                   │
│  Output:                                                          │
│  fair_metrics = {                                                 │
│    faithfulness: 90.0,                                            │
│    adaptability: 75.0,                                            │
│    interpretability: 95.0,                                        │
│    robustness: 80.0,                                              │
│    safety: 55.0                                                   │
│  }                                                                │
│  confidence_score = 79.0                                          │
└───────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  STEP 16: FORMAT COMPLETE RESPONSE                                │
│  {                                                                │
│    query: "What are the symptoms of diabetes?",                  │
│    domain: "medical",                                             │
│    answer: "Based on trusted medical sources...",                │
│    confidence: 79.0,                                              │
│    pipeline: {                                                    │
│      step1_baseline: "Diabetes symptoms include...",             │
│      step2_evidence_count: 2,                                     │
│      step3_rag_enhanced: "Applied",                               │
│      step4_reasoning_steps: 3,                                    │
│      step5_safety_enhanced: "Applied"                             │
│    },                                                             │
│    evidence_sources: [                                            │
│      { source_number: 1, reliability: "95%", domain: "medical" },│
│      { source_number: 2, reliability: "90%", domain: "medical" } │
│    ],                                                             │
│    reasoning_process: [                                           │
│      { step_number: 1, thought: "I analyzed..." },               │
│      { step_number: 2, thought: "I identified..." },             │
│      { step_number: 3, thought: "I verified..." }                │
│    ],                                                             │
│    fair_metrics: {                                                │
│      faithfulness: 90.0,                                          │
│      adaptability: 75.0,                                          │
│      interpretability: 95.0,                                      │
│      robustness: 80.0,                                            │
│      safety: 55.0                                                 │
│    },                                                             │
│    boosts_applied: {                                              │
│      evidence_boost: 0.3,                                         │
│      reasoning_boost: 0.25,                                       │
│      safety_boost: 0.2,                                           │
│      internet_boost: 0                                            │
│    }                                                              │
│  }                                                                │
└───────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  STEP 17: SEND FINAL RESPONSE TO USER                             │
└───────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Components Mapped to Your Code

| Step  | n8n Node           | Your Code File                    | Method/Function                        |
| ----- | ------------------ | --------------------------------- | -------------------------------------- |
| 3     | Classify Domain    | `src/agents/orchestrator.py`      | `_classify_query_domain()`             |
| 5     | Generate Baseline  | `src/utils/ollama_client.py`      | `OllamaClient.generate()`              |
| 7     | Retrieve Evidence  | `src/evidence/rag_system.py`      | `EvidenceDatabase.retrieve_evidence()` |
| 8     | Format Evidence    | `src/evidence/rag_system.py`      | `format_evidence_for_prompt()`         |
| 11-13 | Chain-of-Thought   | `src/reasoning/cot_system.py`     | `generate_reasoning_chain()`           |
| 14    | Safety Disclaimers | `src/safety/disclaimer_system.py` | `ResponseEnhancer.enhance_response()`  |
| 15    | FAIR Metrics       | `src/evaluation/*.py`             | Various evaluators                     |

---

## 🔍 Where Things Happen

### Domain Classification (Step 3)

**File**: `src/agents/orchestrator.py`

```python
def _classify_query_domain(self, query: str) -> str:
    # Medical keywords check
    # Finance keywords check
    # Cross-domain detection
    return domain
```

### Baseline Generation (Step 5)

**File**: `src/utils/ollama_client.py`

```python
def generate(self, model, prompt, max_tokens=512, temperature=0.7):
    response = requests.post(
        f"{self.base_url}/api/generate",
        json={"model": model, "prompt": prompt, ...}
    )
    return response.json()['response']
```

### Evidence Retrieval (Step 7)

**File**: `src/evidence/rag_system.py`

```python
def retrieve_evidence(self, query: str, domain: str, top_k: int = 3):
    # 1. Generate query embedding
    query_embedding = self.model.encode([query])[0]

    # 2. Load cached embeddings
    cached_embeddings = self._load_embeddings_cache()

    # 3. Calculate cosine similarity
    similarities = cosine_similarity([query_embedding], cached_embeddings)

    # 4. Get top_k most similar
    top_indices = similarities.argsort()[-top_k:]

    return evidence_sources[top_indices]
```

### Chain-of-Thought (Steps 11-13)

**File**: `src/reasoning/cot_system.py`

```python
def generate_reasoning_chain(self, query, response, domain):
    # Create CoT prompt
    cot_prompt = self._create_cot_prompt(query, response)

    # Generate reasoning
    reasoning = self.ollama_client.generate(model, cot_prompt, max_tokens=300)

    # Parse steps
    steps = self._extract_reasoning_steps(reasoning)

    return ReasoningChain(steps=steps, ...)
```

### FAIR Metrics (Step 15)

**Files**: `src/evaluation/faithfulness.py`, `adaptability.py`, etc.

```python
# Faithfulness
evidence_boost = len(evidence_sources) * 0.1
faithfulness = base_score + evidence_boost

# Interpretability
reasoning_boost = len(reasoning_steps) * 0.25
interpretability = base_score + reasoning_boost

# ... and so on
```

---

## 🚀 How to Test the Complete Flow

```bash
# 1. Import n8n-workflow-detailed-processing.json into n8n

# 2. Send test request:
curl -X POST http://localhost:5678/webhook/fair-agent-detailed-query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the symptoms of diabetes?",
    "user_id": "test_user"
  }'

# 3. Watch the execution flow through all 17 steps in n8n UI
```

---

## 💡 Key Differences from Previous Workflows

| Previous Workflow               | Detailed Workflow                       |
| ------------------------------- | --------------------------------------- |
| Called Django APIs (abstracted) | **Shows actual Ollama calls**           |
| Single "agent processing" step  | **Separate baseline, RAG, CoT steps**   |
| Hidden evidence retrieval       | **Explicit RAG retrieval & formatting** |
| Metrics as black box            | **Shows calculation logic**             |
| 12 nodes                        | **17 detailed nodes**                   |

This workflow shows **EXACTLY** what happens inside your FAIR-Agent system!
