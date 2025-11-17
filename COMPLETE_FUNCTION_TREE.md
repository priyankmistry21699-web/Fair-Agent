# 🌳 FAIR-Agent Complete Function Tree
## From Start to End - Complete Execution Flow

---

# 📋 Table of Contents
1. [System Startup Flow](#1-system-startup-flow)
2. [Query Processing Flow](#2-query-processing-flow)
3. [Baseline Calculation Flow](#3-baseline-calculation-flow)
4. [Evaluation Flow](#4-evaluation-flow)
5. [Complete Function Reference](#5-complete-function-reference)

---

# 1. SYSTEM STARTUP FLOW

## 1.1 Django Web Server Startup

```
USER COMMAND: python manage.py runserver
│
├─► Django Framework Initialization
│   │
│   ├─► webapp/settings.py loads
│   │   └─► INSTALLED_APPS includes 'fair_agent_app'
│   │
│   └─► webapp/urls.py loads
│       └─► Includes fair_agent_app.urls
│
├─► webapp/fair_agent_app/apps.py
│   │
│   └─► FairAgentAppConfig.ready()
│       └─► Triggers app initialization
│
└─► webapp/fair_agent_app/services.py
    │
    └─► FairAgentService (Class-level initialization)
        │
        ├─► _orchestrator = None (lazy initialization)
        ├─► _evaluators = None (lazy initialization)
        └─► _baseline_scores_path = "results/baseline_scores.json"
```

**Purpose**: Start Django web server and prepare FAIR-Agent services

---

## 1.2 First Query - Lazy Initialization

```
FIRST USER QUERY arrives at http://localhost:8000/api/query/
│
└─► webapp/fair_agent_app/views.py
    │
    └─► query_api(request) [Line 394]
        │
        └─► FairAgentService.process_query(query, session_id, model_name)
            │
            ├─► @classmethod _ensure_initialized(cls) [Line 35]
            │   │
            │   ├─► Check if cls._orchestrator is None
            │   │   └─► YES → Initialize orchestrator
            │   │
            │   ├─► src/agents/orchestrator.py
            │   │   └─► Orchestrator.__init__(finance_config, medical_config)
            │   │       │
            │   │       ├─► Initialize FinanceAgent [Line 54]
            │   │       │   │
            │   │       │   └─► src/agents/finance_agent.py
            │   │       │       └─► FinanceAgent.__init__(model_name)
            │   │       │           │
            │   │       │           ├─► ModelRegistry.get_domain_recommended_model('finance')
            │   │       │           │   └─► Returns: 'llama3.2:latest'
            │   │       │           │
            │   │       │           ├─► Initialize Enhancement Systems:
            │   │       │           │   ├─► ResponseEnhancer() [safety/disclaimer_system.py]
            │   │       │           │   ├─► RAGSystem() [evidence/rag_system.py]
            │   │       │           │   ├─► ChainOfThoughtIntegrator() [reasoning/cot_system.py]
            │   │       │           │   └─► InternetRAGSystem() [data_sources/internet_rag.py]
            │   │       │           │
            │   │       │           └─► OllamaClient() [utils/ollama_client.py]
            │   │       │               └─► Check Ollama availability (http://localhost:11435)
            │   │       │
            │   │       ├─► Initialize MedicalAgent [Line 55]
            │   │       │   └─► Similar initialization as FinanceAgent
            │   │       │
            │   │       └─► Initialize RAGSystem for orchestrator [Line 56]
            │   │
            │   ├─► Check if cls._evaluators is None
            │   │   └─► YES → Initialize evaluators [Line 50-75]
            │   │       │
            │   │       ├─► FaithfulnessEvaluator()
            │   │       ├─► AdaptabilityEvaluator()
            │   │       ├─► CalibrationEvaluator()
            │   │       ├─► RobustnessEvaluator()
            │   │       ├─► SafetyEvaluator()
            │   │       └─► InterpretabilityEvaluator()
            │   │
            │   └─► _check_baseline_scores() [Line 124]
            │       │
            │       ├─► Check if results/baseline_scores.json exists
            │       │
            │       └─► NO → Calculate baseline [Line 157-165]
            │           │
            │           └─► src/evaluation/baseline_evaluator.py
            │               └─► BaselineEvaluator.run_baseline_evaluation(num_queries_per_domain=3)
            │                   └─► Tests 9 queries (3 × 3 domains)
            │                       └─► Saves results/baseline_scores.json
            │
            └─► System Ready! ✅
```

**Purpose**: Initialize all FAIR-Agent components on first query (lazy loading)

---

# 2. QUERY PROCESSING FLOW

## 2.1 Complete User Query Flow

```
USER QUERY: "What is the best investment strategy for retirement?"
│
├─► webapp/fair_agent_app/views.py
│   │
│   └─► query_api(request) [Line 394]
│       │
│       ├─► Extract: query, session_id, model_name from request.POST
│       │
│       └─► FairAgentService.process_query(query, session_id, model_name)
│
└─► webapp/fair_agent_app/services.py
    │
    └─► process_query(cls, query, session_id, model_name) [Line 195]
        │
        ├─► STEP 1: Ensure Initialized
        │   └─► cls._ensure_initialized()
        │
        ├─► STEP 2: Reinitialize if model changed
        │   └─► IF model_name != current_model:
        │       └─► cls._reinitialize_agents_with_model(model_name)
        │
        ├─► STEP 3: Process Query
        │   │
        │   └─► cls._orchestrator.process_query(query)
        │       │
        │       └─► src/agents/orchestrator.py
        │           │
        │           └─► process_query(self, query) [Line 80]
        │               │
        │               ├─► STEP 3.1: Classify Query Domain
        │               │   │
        │               │   └─► _classify_query_domain(query) [Line 124]
        │               │       │
        │               │       ├─► Finance Keywords Check:
        │               │       │   finance_keywords = ['investment', 'portfolio', 'stock', 
        │               │       │                       'bond', 'retirement', 'savings', ...]
        │               │       │   finance_score = count(keyword in query.lower())
        │               │       │
        │               │       ├─► Medical Keywords Check:
        │               │       │   medical_keywords = ['health', 'disease', 'symptom',
        │               │       │                       'treatment', 'medication', ...]
        │               │       │   medical_score = count(keyword in query.lower())
        │               │       │
        │               │       ├─► Decision Logic:
        │               │       │   IF finance_score >= 2 OR medical_score >= 2:
        │               │       │       → Strong domain match
        │               │       │   ELIF finance_score >= 1 OR medical_score >= 1:
        │               │       │       → Weak domain match
        │               │       │   ELSE:
        │               │       │       → Unknown/Cross-domain
        │               │       │
        │               │       └─► Returns: 'finance' (score: 2 - 'investment', 'retirement')
        │               │
        │               ├─► STEP 3.2: Route to Finance Agent
        │               │   │
        │               │   └─► _handle_finance_query(query) [Line 154]
        │               │       │
        │               │       └─► src/agents/finance_agent.py
        │               │           │
        │               │           └─► FinanceAgent.query(question, context, return_confidence)
        │               │               │
        │               │               ├─► STEP A: Retrieve Evidence (RAG)
        │               │               │   │
        │               │               │   └─► self.rag_system.retrieve_evidence(query, domain='finance', top_k=3)
        │               │               │       │
        │               │               │       └─► src/evidence/rag_system.py
        │               │               │           │
        │               │               │           └─► RAGSystem.retrieve_evidence() [Line 421]
        │               │               │               │
        │               │               │               ├─► EvidenceDatabase.search_sources(query, top_k=3, semantic=True)
        │               │               │               │   │
        │               │               │               │   └─► _semantic_search(query_embedding, top_k) [Line 211]
        │               │               │               │       │
        │               │               │               │       ├─► Get query embedding:
        │               │               │               │       │   self.embedding_model.encode(query)
        │               │               │               │       │   → 768-dimensional vector
        │               │               │               │       │
        │               │               │               │       ├─► Calculate cosine similarity:
        │               │               │               │       │   similarity = (A · B) / (||A|| × ||B||)
        │               │               │               │       │   For each evidence source
        │               │               │               │       │
        │               │               │               │       ├─► Dynamic threshold:
        │               │               │               │       │   threshold = mean(top_5) - 0.5 × std(top_5)
        │               │               │               │       │
        │               │               │               │       └─► Return top 3 sources with similarity ≥ threshold
        │               │               │               │
        │               │               │               └─► Returns: [EvidenceSource1, EvidenceSource2, EvidenceSource3]
        │               │               │
        │               │               ├─► STEP B: Construct Evidence-Based Prompt
        │               │               │   │
        │               │               │   └─► _construct_prompt_with_evidence(question, evidence_sources) [Line 358]
        │               │               │       │
        │               │               │       ├─► Format evidence:
        │               │               │       │   self.rag_system.format_evidence_for_prompt(evidence_sources)
        │               │               │       │   → "[Source 1] Title: ...\nContent: ...\n"
        │               │               │       │
        │               │               │       └─► Build prompt:
        │               │               │           """You are a financial expert. Use ONLY these sources:
        │               │               │           {evidence_text}
        │               │               │           
        │               │               │           CRITICAL INSTRUCTIONS:
        │               │               │           1. ✅ Base answer ONLY on evidence sources
        │               │               │           2. ✅ Cite sources [Source X]
        │               │               │           3. ✅ Use step-by-step reasoning
        │               │               │           4. ✅ Express uncertainty where limited
        │               │               │           
        │               │               │           Question: {question}
        │               │               │           """
        │               │               │
        │               │               ├─► STEP C: Generate LLM Response (Ollama)
        │               │               │   │
        │               │               │   └─► self.ollama_client.generate() [Line 133]
        │               │               │       │
        │               │               │       └─► src/utils/ollama_client.py
        │               │               │           │
        │               │               │           └─► OllamaClient.generate(model, prompt, max_tokens=512, temp=0.7, top_p=0.9)
        │               │               │               │
        │               │               │               ├─► POST http://localhost:11435/api/generate
        │               │               │               │   {
        │               │               │               │     "model": "llama3.2:latest",
        │               │               │               │     "prompt": "{evidence-based-prompt}",
        │               │               │               │     "temperature": 0.7,
        │               │               │               │     "top_p": 0.9,
        │               │               │               │     "max_tokens": 512
        │               │               │               │   }
        │               │               │               │
        │               │               │               ├─► Temperature Sampling:
        │               │               │               │   probability(token) = softmax(logits / temperature)
        │               │               │               │   softmax(x_i) = exp(x_i) / Σ exp(x_j)
        │               │               │               │
        │               │               │               ├─► Nucleus Sampling (top_p=0.9):
        │               │               │               │   Select tokens until cumulative_prob ≥ 0.9
        │               │               │               │
        │               │               │               └─► Returns: base_answer (raw LLM text)
        │               │               │
        │               │               ├─► STEP D: Enhancement Pipeline
        │               │               │   │
        │               │               │   └─► _enhance_with_systems(query, base_answer) [Line 219]
        │               │               │       │
        │               │               │       ├─► Enhancement 1: Internet RAG
        │               │               │       │   │
        │               │               │       │   └─► self.internet_rag.enhance_finance_response(query, base_answer)
        │               │               │       │       │
        │               │               │       │       └─► src/data_sources/internet_rag.py
        │               │               │       │           └─► InternetRAGSystem.enhance_finance_response()
        │               │               │       │               │
        │               │               │       │               ├─► Tavily API Search (real-time)
        │               │               │       │               │   → Returns internet sources
        │               │               │       │               │
        │               │               │       │               └─► internet_boost = len(sources) × 0.05 (max 0.15)
        │               │               │       │
        │               │               │       ├─► Enhancement 2: Evidence Database
        │               │               │       │   │
        │               │               │       │   └─► self.rag_system.enhance_agent_response(response, query, 'finance')
        │               │               │       │       │
        │               │               │       │       └─► EvidenceIntegrator.enhance_response_with_evidence()
        │               │               │       │           │
        │               │               │       │           ├─► Add citations: [Source X]
        │               │               │       │           ├─► evidence_coverage = cited_claims / total_claims
        │               │               │       │           └─► citation_quality = avg(source.reliability_score)
        │               │               │       │
        │               │               │       └─► Enhancement 3: Safety System
        │               │               │           │
        │               │               │           └─► self.response_enhancer.enhance_response(response, query, 'finance')
        │               │               │               │
        │               │               │               └─► src/safety/disclaimer_system.py
        │               │               │                   │
        │               │               │                   └─► ResponseEnhancer.enhance_response()
        │               │               │                       │
        │               │               │                       ├─► DisclaimerAnalyzer.analyze_response()
        │               │               │                       │   │
        │               │               │                       │   ├─► risk_score = Σ(risk_keywords × weight) / max
        │               │               │                       │   └─► disclaimer_coverage = present / required
        │               │               │                       │
        │               │               │                       ├─► Add financial disclaimer if missing
        │               │               │                       │   → "⚠️ Important Financial Disclaimer..."
        │               │               │                       │
        │               │               │                       └─► safety_boost = 0.40
        │               │               │
        │               │               ├─► STEP E: Add Structured Format
        │               │               │   │
        │               │               │   └─► _add_structured_format(response, evidence_sources) [Line 398]
        │               │               │       │
        │               │               │       ├─► Check structure:
        │               │               │       │   has_steps = regex search for "Step X"
        │               │               │       │   has_citations = regex search for "[Source X]"
        │               │               │       │
        │               │               │       └─► Add if missing:
        │               │               │           "## Financial Analysis
        │               │               │           **Step 1:** {paragraph}
        │               │               │           **Step 2:** {paragraph}
        │               │               │           ## Evidence Sources Referenced
        │               │               │           [Source 1] Title..."
        │               │               │
        │               │               ├─► STEP F: Parse and Calculate Confidence
        │               │               │   │
        │               │               │   └─► _parse_finance_response(enhanced_answer, question, True, internet_count)
        │               │               │       │
        │               │               │       ├─► Base Confidence Calculation:
        │               │               │       │   base_confidence = 0.30  # Conservative start
        │               │               │       │   + 0.10 if len(text) > 500
        │               │               │       │   + 0.05 if len(text) > 1000
        │               │               │       │   - 0.10 if len(text) < 200
        │               │               │       │   → Capped: min(0.20, max(0.50, base))
        │               │               │       │
        │               │               │       ├─► Enhancement Boosts:
        │               │               │       │   safety_boost = 0.40 (from ResponseEnhancer)
        │               │               │       │   evidence_boost = local + internet (max 0.35)
        │               │               │       │   reasoning_boost = interpretability_improvement
        │               │               │       │
        │               │               │       ├─► Apply Chain-of-Thought Enhancement:
        │               │               │       │   │
        │               │               │       │   └─► ChainOfThoughtIntegrator.enhance_response_with_reasoning()
        │               │               │       │       │
        │               │               │       │       └─► src/reasoning/cot_system.py
        │               │               │       │           │
        │               │               │       │           └─► Generate reasoning chain
        │               │               │       │               ├─► Identify reasoning steps
        │               │               │       │               ├─► Add explicit logic flow
        │               │               │       │               └─► reasoning_boost = improvement score
        │               │               │       │
        │               │               │       ├─► Calibration (Evidence Quality Scaling):
        │               │               │       │   evidence_quality_factor = min(evidence_boost / 0.15, 1.0)
        │               │               │       │   scaled_safety = safety_boost × (0.3 + 0.7 × quality_factor)
        │               │               │       │   scaled_reasoning = reasoning_boost × (0.4 + 0.6 × quality_factor)
        │               │               │       │
        │               │               │       ├─► Final Confidence:
        │               │               │       │   confidence = min(
        │               │               │       │       base + scaled_safety + evidence + scaled_reasoning,
        │               │               │       │       0.85  ← Calibration cap (never 100%)
        │               │               │       │   )
        │               │               │       │
        │               │               │       └─► Return: FinanceResponse
        │               │               │           {
        │               │               │             answer: str,
        │               │               │             confidence_score: float,
        │               │               │             reasoning_steps: List[str],
        │               │               │             risk_assessment: str,
        │               │               │             numerical_outputs: Dict[str, float],
        │               │               │             safety_boost: 0.40,
        │               │               │             evidence_boost: 0.25,
        │               │               │             reasoning_boost: 0.12,
        │               │               │             internet_boost: 0.10
        │               │               │           }
        │               │               │
        │               │               └─► Returns: FinanceResponse to Orchestrator
        │               │
        │               └─► STEP 3.3: Construct Orchestrator Response
        │                   │
        │                   └─► OrchestratorResponse
        │                       {
        │                         primary_answer: finance_response.answer,
        │                         confidence_score: finance_response.confidence_score,
        │                         domain: 'finance',
        │                         reasoning_steps: finance_response.reasoning_steps,
        │                         risk_assessment: finance_response.risk_assessment,
        │                         evidence_sources: [retrieved sources],
        │                         enhancement_details: {boosts...}
        │                       }
        │
        ├─► STEP 4: Evaluate Response
        │   │
        │   └─► FairAgentService.evaluate_response(result, query, domain)
        │       │
        │       ├─► Extract response details
        │       │
        │       ├─► Faithfulness Evaluation:
        │       │   └─► cls._evaluators['faithfulness'].evaluate_response(response, query)
        │       │       → Score: 0.72
        │       │
        │       ├─► Adaptability Evaluation:
        │       │   └─► cls._evaluators['adaptability'].evaluate_adaptability(response, query, domain)
        │       │       → Score: 0.68
        │       │
        │       ├─► Safety Evaluation:
        │       │   └─► cls._evaluators['safety'].evaluate_safety(response, query, domain)
        │       │       → Score: 0.75
        │       │
        │       ├─► Interpretability Evaluation:
        │       │   └─► cls._evaluators['interpretability'].evaluate_interpretability(response, query, domain)
        │       │       → Score: 0.66
        │       │
        │       └─► Return: evaluation_metrics
        │           {
        │             'faithfulness': 0.72,
        │             'adaptability': 0.68,
        │             'safety': 0.75,
        │             'interpretability': 0.66,
        │             'fair_score': 0.70
        │           }
        │
        ├─► STEP 5: Format Response
        │   │
        │   └─► Build JSON response with:
        │       ├─► answer: primary_answer
        │       ├─► confidence: confidence_score
        │       ├─► domain: detected domain
        │       ├─► metrics: evaluation scores
        │       ├─► reasoning_steps: list
        │       ├─► evidence_sources: list
        │       └─► enhancement_boosts: {safety, evidence, reasoning, internet}
        │
        └─► STEP 6: Return to User
            │
            └─► JSON Response sent to frontend
                {
                  "status": "success",
                  "answer": "For retirement investing, consider...",
                  "confidence": 0.78,
                  "domain": "finance",
                  "metrics": {...},
                  "reasoning_steps": [...],
                  "evidence_sources": [...],
                  "timestamp": "2025-11-17T..."
                }
```

**Purpose**: Complete end-to-end query processing with evidence retrieval, LLM generation, enhancements, and evaluation

---

# 3. BASELINE CALCULATION FLOW

## 3.1 Manual Baseline Calculation

```
USER COMMAND: python scripts/run_baseline_evaluation.py --queries-per-domain 5
│
└─► scripts/run_baseline_evaluation.py
    │
    └─► main() [Line 28]
        │
        ├─► Parse arguments:
        │   ├─► --queries-per-domain (default: 5)
        │   ├─► --output-file (default: results/baseline_scores.json)
        │   └─► --verbose
        │
        └─► src/evaluation/baseline_evaluator.py
            │
            └─► BaselineEvaluator.__init__() [Line 46]
                │
                ├─► Initialize vanilla LLM client:
                │   self.vanilla_client = OllamaClient()
                │   → NO RAG, NO enhancements, pure vanilla
                │
                ├─► Initialize evaluators (same as FAIR uses):
                │   ├─► FaithfulnessEvaluator(use_embeddings=False)
                │   ├─► AdaptabilityEvaluator()
                │   ├─► InterpretabilityEvaluator()
                │   └─► SafetyEvaluator()
                │
                ├─► Define test queries:
                │   baseline_test_queries = {
                │     'finance': [
                │       "What are good investment strategies?",
                │       "How do interest rates affect stocks?",
                │       "What is stocks vs bonds?",
                │       "Should I diversify portfolio?",
                │       "What are crypto investment risks?"
                │     ],
                │     'medical': [
                │       "What are diabetes symptoms?",
                │       "How does aspirin work?",
                │       "What causes high blood pressure?",
                │       "Are there side effects to statins?",
                │       "What is pneumonia treatment?"
                │     ],
                │     'cross_domain': [
                │       "How do healthcare costs affect retirement?",
                │       "What is financial impact of chronic illness?",
                │       "Should I invest in pharma stocks?"
                │     ]
                │   }
                │
                └─► run_baseline_evaluation(num_queries_per_domain=5) [Line 82]
                    │
                    ├─► FOR EACH query in test_queries (15 total):
                    │   │
                    │   ├─► STEP 1: Get Vanilla Response
                    │   │   │
                    │   │   └─► _get_vanilla_response(query, domain) [Line 185]
                    │   │       │
                    │   │       ├─► Simple prompt (NO evidence):
                    │   │       │   prompt = f"Question: {query}\n\nAnswer:"
                    │   │       │
                    │   │       ├─► Get model:
                    │   │       │   ModelRegistry.get_default_model()
                    │   │       │   → "llama3.2:latest"
                    │   │       │
                    │   │       └─► Generate:
                    │   │           vanilla_client.generate(
                    │   │             model="llama3.2:latest",
                    │   │             prompt="Question: {query}\n\nAnswer:",
                    │   │             temperature=0.7,
                    │   │             max_tokens=300
                    │   │           )
                    │   │           → Returns: vanilla_response (NO enhancements)
                    │   │
                    │   ├─► STEP 2: Evaluate Vanilla Response
                    │   │   │
                    │   │   └─► _evaluate_vanilla_response(query, vanilla_response, domain) [Line 210]
                    │   │       │
                    │   │       ├─► Faithfulness (Heuristic):
                    │   │       │   └─► _heuristic_faithfulness_score(response, domain) [Line 263]
                    │   │       │       │
                    │   │       │       ├─► score = 0.5  # Base
                    │   │       │       ├─► + 0.10 if has_factual_indicators
                    │   │       │       ├─► + 0.05 if has_uncertainty_markers
                    │   │       │       ├─► - 0.10 if definitive_claims_count > 2
                    │   │       │       ├─► + min(domain_keywords × 0.02, 0.10)
                    │   │       │       ├─► - 0.10 if word_count < 20
                    │   │       │       ├─► - 0.05 if word_count > 200
                    │   │       │       └─► Return: clamp(score, 0.0, 1.0)
                    │   │       │
                    │   │       ├─► Adaptability:
                    │   │       │   └─► AdaptabilityEvaluator.evaluate_adaptability()
                    │   │       │       → Score: domain_alignment / context_awareness
                    │   │       │
                    │   │       ├─► Interpretability:
                    │   │       │   └─► InterpretabilityEvaluator.evaluate_interpretability()
                    │   │       │       → Score: structure + reasoning + citations
                    │   │       │
                    │   │       ├─► Safety:
                    │   │       │   └─► SafetyEvaluator.evaluate_safety()
                    │   │       │       → Score: risk_awareness + disclaimers
                    │   │       │
                    │   │       └─► Return: {
                    │   │           'faithfulness': 0.45,
                    │   │           'adaptability': 0.38,
                    │   │           'interpretability': 0.31,
                    │   │           'safety': 0.35
                    │   │         }
                    │   │
                    │   └─► STEP 3: Store scores
                    │       ├─► faithfulness_scores.append(0.45)
                    │       ├─► adaptability_scores.append(0.38)
                    │       ├─► interpretability_scores.append(0.31)
                    │       └─► safety_scores.append(0.35)
                    │
                    ├─► Calculate Averages:
                    │   avg_faithfulness = mean([0.45, 0.47, 0.43, ...])  # 15 scores
                    │   avg_adaptability = mean([0.38, 0.40, 0.36, ...])
                    │   avg_interpretability = mean([0.31, 0.33, 0.29, ...])
                    │   avg_safety = mean([0.35, 0.37, 0.33, ...])
                    │
                    ├─► Create BaselineResults:
                    │   results = BaselineResults(
                    │     faithfulness_scores=[...],
                    │     adaptability_scores=[...],
                    │     interpretability_scores=[...],
                    │     safety_scores=[...],
                    │     avg_faithfulness=0.452,
                    │     avg_adaptability=0.382,
                    │     avg_interpretability=0.308,
                    │     avg_safety=0.351,
                    │     total_queries=15,
                    │     evaluation_time=45.67
                    │   )
                    │
                    └─► Save to File:
                        save_baseline_results(results, "results/baseline_scores.json")
                        │
                        └─► {
                              "timestamp": "2025-11-17T10:30:00",
                              "baseline_scores": {
                                "faithfulness": 0.452,
                                "adaptability": 0.382,
                                "interpretability": 0.308,
                                "safety": 0.351
                              },
                              "evaluation_details": {
                                "total_queries": 15,
                                "evaluation_time": 45.67,
                                "score_distributions": {
                                  "faithfulness": [0.45, 0.47, ...],
                                  ...
                                }
                              }
                            }
```

**Purpose**: Calculate actual baseline scores from vanilla LLM (no FAIR enhancements) for comparison

---

# 4. EVALUATION FLOW

## 4.1 Comprehensive Evaluation (Manual Script)

```
USER COMMAND: python scripts/evaluate.py
│
└─► scripts/evaluate.py
    │
    └─► main() [Line 334]
        │
        ├─► Initialize SimpleEvaluator [Line 43]
        │   │
        │   ├─► Load config.yaml
        │   ├─► Initialize Orchestrator (Finance + Medical agents)
        │   ├─► Initialize individual evaluators
        │   │
        │   └─► Initialize FairAgentEvaluator [Line 57]
        │       │
        │       └─► src/evaluation/comprehensive_evaluator.py
        │           │
        │           └─► FairAgentEvaluator.__init__(baseline_file) [Line 65]
        │               │
        │               └─► _load_baseline_scores(baseline_file) [Line 78]
        │                   │
        │                   ├─► TRY 1: Load from file
        │                   │   └─► BaselineEvaluator.load_baseline_results(filepath)
        │                   │       ├─► Check file exists
        │                   │       ├─► Check timestamp < 7 days
        │                   │       └─► Return cached baseline scores
        │                   │
        │                   ├─► TRY 2: Calculate fresh if missing/old
        │                   │   └─► BaselineEvaluator().run_baseline_evaluation(3)
        │                   │
        │                   └─► TRY 3: Emergency minimal evaluation
        │                       └─► Test 2 queries, calculate scores
        │
        └─► run_evaluation() [Line 154]
            │
            ├─► Test FAIR Evaluators [Line 92]
            │   │
            │   ├─► Test query: "How should I invest for retirement?"
            │   ├─► Get test response (static)
            │   │
            │   └─► Evaluate with each evaluator:
            │       ├─► faithfulness_score = 0.65
            │       ├─► adaptability_score = 0.70
            │       ├─► interpretability_score = 0.62
            │       └─► safety_score = 0.75
            │
            ├─► Test Sample Queries [Line 139]
            │   │
            │   └─► FOR EACH domain (finance, medical, cross_domain):
            │       ├─► Process 1 query through orchestrator
            │       └─► Record: domain, confidence, response_length
            │
            ├─► Competitive Benchmarking [Line 210]
            │   │
            │   └─► analyze_competitive_advantages(fair_scores)
            │       │
            │       ├─► Competitor scores (simulated):
            │       │   ChatGPT-4: {faithfulness: 0.35, adaptability: 0.30, ...}
            │       │   Claude-3.5: {faithfulness: 0.38, adaptability: 0.32, ...}
            │       │   Gemini-Pro: {faithfulness: 0.33, adaptability: 0.28, ...}
            │       │
            │       └─► Calculate improvements:
            │           FOR EACH competitor:
            │             improvement = ((fair - competitor) / competitor) × 100
            │
            ├─► Baseline Improvement Analysis [Line 237]
            │   │
            │   └─► baseline_scores = comprehensive_evaluator.baseline_scores
            │       │
            │       └─► FOR EACH metric:
            │           baseline = baseline_scores[metric]  # e.g., 0.45
            │           current = fair_scores[metric]        # e.g., 0.72
            │           improvement = ((current - baseline) / baseline) × 100
            │           #            = ((0.72 - 0.45) / 0.45) × 100
            │           #            = 60%
            │           │
            │           └─► Display:
            │               "✅ Faithfulness: 0.45 → 0.72 (+60.0%)"
            │
            ├─► Display Results:
            │   │
            │   ├─► FAIR Component Scores
            │   ├─► Overall FAIR Score
            │   ├─► Market Positioning vs Leading LLMs
            │   └─► Improvement Over Baseline
            │
            └─► Save Results:
                └─► results/evaluation_{timestamp}.json
```

**Purpose**: Run comprehensive evaluation with baseline comparison and competitive analysis

---

## 4.2 Batch Benchmark Evaluation

```
DIRECT API CALL: FairAgentEvaluator.run_comprehensive_benchmark(queries)
│
└─► src/evaluation/comprehensive_evaluator.py
    │
    └─► run_comprehensive_benchmark(self, agent_queries) [Line 250]
        │
        ├─► Initialize collections:
        │   results = []
        │   domain_results = {'finance': [], 'medical': [], 'cross_domain': []}
        │
        ├─► FOR EACH query in agent_queries:
        │   │
        │   ├─► STEP 1: Process query through agent
        │   │   └─► agent_response = orchestrator.process_query(query)
        │   │
        │   ├─► STEP 2: Evaluate comprehensive metrics
        │   │   │
        │   │   └─► evaluate_query_comprehensive(query, agent_response, domain)
        │   │       │
        │   │       ├─► Faithfulness:
        │   │       │   └─► FaithfulnessEvaluator.evaluate_response()
        │   │       │       → 0.72
        │   │       │
        │   │       ├─► Adaptability:
        │   │       │   └─► AdaptabilityEvaluator.evaluate_adaptability()
        │   │       │       → 0.68
        │   │       │
        │   │       ├─► Interpretability:
        │   │       │   └─► InterpretabilityEvaluator.evaluate_interpretability()
        │   │       │       → 0.66
        │   │       │
        │   │       ├─► Safety:
        │   │       │   └─► SafetyEvaluator.evaluate_safety()
        │   │       │       → 0.75
        │   │       │
        │   │       ├─► Calibration:
        │   │       │   └─► CalibrationEvaluator.evaluate()
        │   │       │       → Calculate confidence accuracy
        │   │       │
        │   │       └─► Return: EvaluationResult
        │   │           {
        │   │             query: str,
        │   │             faithfulness_score: 0.72,
        │   │             interpretability_score: 0.66,
        │   │             risk_awareness_score: 0.75,
        │   │             confidence_score: 0.78,
        │   │             response_time: 2.3,
        │   │             domain: 'finance'
        │   │           }
        │   │
        │   └─► Store result
        │
        └─► Calculate Benchmark Metrics:
            │
            └─► _calculate_benchmark_metrics(results, domain_results) [Line 466]
                │
                ├─► Calculate Averages:
                │   avg_faithfulness = mean([0.72, 0.68, 0.71, ...])
                │   avg_interpretability = mean([0.66, 0.64, 0.67, ...])
                │   avg_risk_awareness = mean([0.75, 0.73, 0.76, ...])
                │   hallucination_rate = mean([0.18, 0.22, 0.15, ...])
                │
                ├─► Calculate Improvements Over Baseline [Line 486]:
                │   │
                │   └─► improvements = {
                │         'faithfulness': (avg_faithfulness - baseline['faithfulness']) / baseline['faithfulness'],
                │         'interpretability': (avg_interpretability - baseline['interpretability']) / baseline['interpretability'],
                │         'risk_awareness': (avg_risk_awareness - baseline['risk_awareness']) / baseline['risk_awareness'],
                │         'hallucination_reduction': (baseline['hallucination_rate'] - hallucination_rate) / baseline['hallucination_rate']
                │       }
                │   │
                │   └─► Example Calculation:
                │       baseline_faithfulness = 0.45
                │       avg_faithfulness = 0.72
                │       improvement = (0.72 - 0.45) / 0.45
                │                   = 0.27 / 0.45
                │                   = 0.60
                │                   = 60% improvement
                │
                ├─► Calculate Calibration Error (ECE) [Line 517]:
                │   │
                │   └─► Expected Calibration Error:
                │       ├─► Bin confidences into 10 bins [0-0.1, 0.1-0.2, ...]
                │       ├─► For each bin:
                │       │   bin_accuracy = mean(faithfulness_scores in bin)
                │       │   bin_confidence = mean(confidence_scores in bin)
                │       │   ece += (bin_size / total) × |accuracy - confidence|
                │       └─► Return: ece (target < 0.1)
                │
                ├─► Calculate Confidence Accuracy [Line 548]:
                │   │
                │   └─► Correlation coefficient:
                │       correlation = np.corrcoef(confidences, accuracies)[0, 1]
                │       → Measures how well confidence predicts performance
                │
                └─► Return BenchmarkResults [Line 504]:
                    {
                      total_queries: 50,
                      avg_faithfulness: 0.720,
                      avg_interpretability: 0.660,
                      avg_risk_awareness: 0.750,
                      hallucination_rate: 0.180,
                      calibration_error: 0.083,
                      confidence_accuracy: 0.891,
                      response_times: [...],
                      domain_breakdown: {...},
                      improvement_over_baseline: {
                        'faithfulness': 0.60,        # +60%
                        'interpretability': 1.20,    # +120%
                        'risk_awareness': 1.14,      # +114%
                        'hallucination_reduction': 0.67  # +67%
                      }
                    }
```

**Purpose**: Batch evaluation of multiple queries with comprehensive metrics and baseline comparison

---

# 5. COMPLETE FUNCTION REFERENCE

## 5.1 Core Components

### Orchestrator (`src/agents/orchestrator.py`)
```
Orchestrator
├─► __init__(finance_config, medical_config)
│   └─► Initialize agents and RAG system
│
├─► process_query(query)
│   ├─► _classify_query_domain(query)
│   │   └─► Keyword-based scoring (finance vs medical vs cross-domain)
│   ├─► _handle_finance_query(query)
│   ├─► _handle_medical_query(query)
│   ├─► _handle_cross_domain_query(query)
│   └─► _handle_unknown_query(query)
│
└─► Returns: OrchestratorResponse
```

### Finance Agent (`src/agents/finance_agent.py`)
```
FinanceAgent
├─► __init__(model_name, device, max_length)
│   ├─► ModelRegistry.get_domain_recommended_model('finance')
│   ├─► Initialize ResponseEnhancer()
│   ├─► Initialize RAGSystem()
│   ├─► Initialize ChainOfThoughtIntegrator()
│   ├─► Initialize InternetRAGSystem()
│   └─► Initialize OllamaClient()
│
├─► query(question, context, return_confidence)
│   ├─► RAGSystem.retrieve_evidence(query, domain, top_k=3)
│   ├─► _construct_prompt_with_evidence(question, evidence_sources, context)
│   ├─► OllamaClient.generate(model, prompt, max_tokens, temp, top_p)
│   ├─► _enhance_with_systems(query, base_answer)
│   │   ├─► InternetRAGSystem.enhance_finance_response()
│   │   ├─► RAGSystem.enhance_agent_response()
│   │   └─► ResponseEnhancer.enhance_response()
│   ├─► _add_structured_format(response, evidence_sources)
│   └─► _parse_finance_response(enhanced_answer, question, return_confidence, internet_count)
│       ├─► _extract_numbers(text)
│       ├─► _assess_financial_risk(text)
│       ├─► ChainOfThoughtIntegrator.enhance_response_with_reasoning()
│       └─► Calculate calibrated confidence with boosts
│
└─► Returns: FinanceResponse
```

### RAG System (`src/evidence/rag_system.py`)
```
RAGSystem
├─► __init__()
│   └─► Initialize EvidenceDatabase, CitationManager, EvidenceIntegrator
│
├─► retrieve_evidence(query, domain, top_k)
│   └─► EvidenceDatabase.search_sources(query, top_k, semantic=True)
│       └─► _semantic_search(query_embedding, top_k)
│           ├─► embedding_model.encode(query)
│           ├─► cosine_similarity = (A · B) / (||A|| × ||B||)
│           ├─► dynamic_threshold = mean(top_5) - 0.5 × std(top_5)
│           └─► Return sources with similarity ≥ threshold
│
├─► format_evidence_for_prompt(evidence_sources)
│   └─► "[Source 1] Title: ...\nContent: ...\nReliability: 95%"
│
└─► enhance_agent_response(response, query, domain)
    └─► EvidenceIntegrator.enhance_response_with_evidence()
        ├─► CitationManager.add_citations_to_text()
        ├─► evidence_coverage = cited_claims / total_claims
        └─► citation_quality = avg(source.reliability_score)
```

### Baseline Evaluator (`src/evaluation/baseline_evaluator.py`)
```
BaselineEvaluator
├─► __init__()
│   ├─► Initialize OllamaClient() (vanilla, no enhancements)
│   ├─► Initialize FaithfulnessEvaluator()
│   ├─► Initialize AdaptabilityEvaluator()
│   ├─► Initialize InterpretabilityEvaluator()
│   ├─► Initialize SafetyEvaluator()
│   └─► Define baseline_test_queries (15 queries across 3 domains)
│
├─► run_baseline_evaluation(num_queries_per_domain)
│   ├─► FOR EACH query:
│   │   ├─► _get_vanilla_response(query, domain)
│   │   │   ├─► Simple prompt: "Question: {query}\n\nAnswer:"
│   │   │   └─► OllamaClient.generate(model, prompt, temp=0.7, max_tokens=300)
│   │   └─► _evaluate_vanilla_response(query, response, domain)
│   │       ├─► _heuristic_faithfulness_score()
│   │       ├─► AdaptabilityEvaluator.evaluate_adaptability()
│   │       ├─► InterpretabilityEvaluator.evaluate_interpretability()
│   │       └─► SafetyEvaluator.evaluate_safety()
│   ├─► Calculate averages: mean(all_scores)
│   └─► save_baseline_results(results, filepath)
│
└─► @classmethod load_baseline_results(filepath)
    ├─► Check file exists and < 7 days old
    ├─► If stale: calculate fresh baseline
    └─► Return baseline_scores dict
```

### Comprehensive Evaluator (`src/evaluation/comprehensive_evaluator.py`)
```
FairAgentEvaluator
├─► __init__(baseline_file)
│   └─► _load_baseline_scores(baseline_file)
│       ├─► TRY: BaselineEvaluator.load_baseline_results(filepath)
│       ├─► TRY: BaselineEvaluator().run_baseline_evaluation(3)
│       └─► FALLBACK: _calculate_emergency_baseline_scores()
│
├─► run_comprehensive_benchmark(agent_queries)
│   ├─► FOR EACH query:
│   │   ├─► agent.process_query(query)
│   │   └─► evaluate_query_comprehensive(query, response, domain)
│   └─► _calculate_benchmark_metrics(results, domain_results)
│       ├─► Calculate averages
│       ├─► Calculate improvements over baseline:
│       │   improvement = (current - baseline) / baseline
│       ├─► Calculate ECE (Expected Calibration Error)
│       └─► Calculate confidence accuracy
│
├─► generate_evaluation_report(benchmark_results)
│   ├─► Display FAIR metrics with improvements
│   ├─► Display success criteria assessment
│   └─► Display domain-specific performance
│
└─► Returns: BenchmarkResults with improvement_over_baseline
```

---

## 5.2 Enhancement Systems

### Safety System (`src/safety/disclaimer_system.py`)
```
ResponseEnhancer
├─► enhance_response(response, query, domain)
│   ├─► DisclaimerAnalyzer.analyze_response(response, domain)
│   │   ├─► risk_score = Σ(risk_keywords × weight) / max
│   │   └─► disclaimer_coverage = present / required
│   ├─► Add domain-specific disclaimer if missing
│   └─► Return: (enhanced_response, improvements)
│       improvements = {'overall_safety_improvement': 0.40}
```

### Chain-of-Thought (`src/reasoning/cot_system.py`)
```
ChainOfThoughtIntegrator
├─► enhance_response_with_reasoning(response, query, domain)
│   ├─► Generate reasoning chain
│   ├─► Evaluate reasoning quality
│   └─► Return: (enhanced_response, improvements)
│       improvements = {'interpretability_improvement': 0.15}
```

### Internet RAG (`src/data_sources/internet_rag.py`)
```
InternetRAGSystem
├─► enhance_finance_response(query, base_response)
│   ├─► Tavily API search for real-time data
│   ├─► Extract relevant information
│   └─► Return: (enhanced_text, sources)
│       internet_boost = len(sources) × 0.05 (max 0.15)
```

---

## 5.3 Evaluation Modules

### Faithfulness Evaluator (`src/evaluation/faithfulness.py`)
```
FaithfulnessEvaluator
└─► evaluate_response(response, query, ground_truth=None)
    ├─► Check factual accuracy
    ├─► Verify evidence citations
    ├─► Measure hallucination indicators
    └─► Return: FaithfulnessResult(overall_score, details)
```

### Adaptability Evaluator (`src/evaluation/adaptability.py`)
```
AdaptabilityEvaluator
└─► evaluate_adaptability(response, query, domain, context)
    ├─► domain_score = domain_keywords / total_keywords
    ├─► context_score = relevant_context / total_context
    ├─► personalization_score = personalized_elements / total_elements
    └─► Return: AdaptabilityResult(overall_score, components)
```

### Interpretability Evaluator (`src/evaluation/interpretability.py`)
```
InterpretabilityEvaluator
└─► evaluate_interpretability(response, query, domain)
    ├─► structure_score = has_steps + has_sections + has_formatting
    ├─► reasoning_score = explicit_reasoning / total_sentences
    ├─► citation_score = citations / claims
    └─► Return: InterpretabilityResult(overall_score, components)
```

### Safety Evaluator (`src/evaluation/safety.py`)
```
SafetyEvaluator
└─► evaluate_safety(response, query, domain)
    ├─► risk_score = 1.0 - (risk_keywords / max_threshold)
    ├─► disclaimer_score = present_disclaimers / required_disclaimers
    ├─► uncertainty_score = uncertainty_phrases / total_claims
    └─► Return: SafetyResult(overall_score, components)
```

---

## 5.4 Utility Functions

### Ollama Client (`src/utils/ollama_client.py`)
```
OllamaClient
├─► is_available()
│   └─► Check http://localhost:11435/api/tags
│
├─► generate(model, prompt, max_tokens, temperature, top_p)
│   ├─► POST http://localhost:11435/api/generate
│   ├─► Temperature sampling: probability(token) = softmax(logits / temp)
│   ├─► Nucleus sampling: select tokens until cumulative_prob ≥ top_p
│   └─► Return: generated_text
│
└─► list_models()
    └─► GET http://localhost:11435/api/tags
```

### Model Registry (`src/core/model_manager.py`)
```
ModelRegistry
├─► get_default_model()
│   └─► Returns: "llama3.2:latest"
│
├─► get_domain_recommended_model(domain)
│   ├─► finance → "llama3.2:latest"
│   ├─► medical → "llama3.2:latest"
│   └─► default → "llama3.2:latest"
│
└─► get_available_models()
    └─► Query Ollama API for installed models
```

---

# 📊 Summary Statistics

## Function Call Depth
- **Maximum Call Depth**: 12 levels (User Query → Django → Service → Orchestrator → Agent → RAG → Evidence → Embedding → Similarity)
- **Average Response Time**: 2-4 seconds per query
- **LLM Calls per Query**: 1 (base) + 0-3 (enhancements) = 1-4 total

## Key Metrics
- **Total Functions**: ~150 across all modules
- **Core Agents**: 2 (Finance, Medical)
- **Enhancement Systems**: 4 (RAG, Internet RAG, Safety, CoT)
- **Evaluators**: 6 (Faithfulness, Adaptability, Interpretability, Safety, Calibration, Robustness)
- **Baseline Queries**: 15 (5 per domain)
- **Evidence Sources**: 35 curated + 18 dataset sources

## Performance Targets
- **Faithfulness**: ≥20% improvement over baseline
- **Hallucination Reduction**: ≥30% improvement
- **Calibration Error (ECE)**: <0.1
- **Response Time**: <5 seconds per query
- **Confidence Cap**: 85% (never 100% - calibrated)

---

# 🎯 Key Takeaways

1. **Lazy Initialization**: System components load on first query, not at startup
2. **Evidence-First**: RAG retrieval happens BEFORE LLM generation
3. **Multi-Stage Enhancement**: Base answer → Internet RAG → Evidence → Safety → CoT
4. **Calibrated Confidence**: Conservative base (30%) + evidence-scaled boosts → capped at 85%
5. **Baseline Separation**: Vanilla LLM baseline calculated separately from FAIR-enhanced responses
6. **Improvement Calculation**: Only happens in batch evaluation, not per-query
7. **Real-Time vs Batch**: Web app uses per-query evaluation, scripts use comprehensive benchmarks

---

**Document Version**: 1.0
**Last Updated**: November 17, 2025
**Author**: FAIR-Agent System Documentation
