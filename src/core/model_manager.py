"""
Model Manager for FAIR-Agent System
CS668 Analytics Capstone - Fall 2025

Supports multiple LLM models including LLaMA, Mistral, and other Ollama models
for enhanced FAIR metrics evaluation and domain specialization.
"""

import logging
import torch
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    LlamaTokenizer, 
    LlamaForCausalLM,
    pipeline
)
import requests
import json

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Supported model types for FAIR-Agent (dynamically populated)"""
    # Static enum values for supported models
    LLAMA32_LATEST = "llama3.2:latest"
    MISTRAL_LATEST = "mistral:latest"
    PHI3_LATEST = "phi3:latest"
    CODELLAMA_LATEST = "codellama:latest"
    LLAMA_7B = "llama:7b"
    LLAMA_7B_CHAT = "llama:7b-chat"
    FLAN_T5_BASE = "flan-t5:base"

class ModelRegistry:
    """Dynamic model registry that discovers available models"""
    
    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get list of available Ollama models"""
        try:
            response = requests.get("http://localhost:11435/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
        except Exception as e:
            logger.warning(f"Could not fetch available models: {e}")
        
        # Fallback to common model names if API unavailable
        return ["llama3.2:latest", "mistral:latest", "phi3:latest"]
    
    @classmethod  
    def get_default_model(cls) -> str:
        """Get the best available default model"""
        available_models = cls.get_available_models()
        
        # Preference order for default model selection
        preferred_models = [
            "llama3.2:latest", "llama3.1:latest", "llama3:latest",
            "mistral:latest", "phi3:latest"
        ]
        
        for preferred in preferred_models:
            if preferred in available_models:
                return preferred
        
        # If none of the preferred models are available, use the first available
        return available_models[0] if available_models else "llama3.2:latest"
    
    @classmethod
    def get_domain_recommended_model(cls, domain: str) -> str:
        """Get recommended model for specific domain"""
        available_models = cls.get_available_models()
        
        domain_preferences = {
            'medical': ["llama3.2:latest", "mistral:latest"],  # Medical reasoning
            'finance': ["llama3.2:latest", "phi3:latest"],    # Financial analysis
            'general': ["llama3.2:latest", "mistral:latest"]  # General purpose
        }
        
        preferences = domain_preferences.get(domain.lower(), domain_preferences['general'])
        
        for preferred in preferences:
            if preferred in available_models:
                return preferred
        
        return cls.get_default_model()

@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    model_type: ModelType
    model_name: str
    tokenizer_name: Optional[str] = None
    requires_auth: bool = False
    memory_requirement_gb: float = 4.0
    recommended_max_length: int = 512
    supports_chat: bool = False
    domain_specialty: Optional[str] = None  # 'finance', 'medical', or None for general

class ModelCapabilities:
    """Model capabilities assessment for FAIR metrics"""
    
    @staticmethod
    def get_model_capabilities(model_type: ModelType) -> Dict[str, float]:
        """Get model capabilities scores for FAIR metrics"""
        capabilities = {
            ModelType.LLAMA32_LATEST: {
                'faithfulness': 0.85,
                'adaptability': 0.90,
                'interpretability': 0.80,
                'risk_awareness': 0.85,
                'domain_knowledge': 0.88
            },
            ModelType.MISTRAL_LATEST: {
                'faithfulness': 0.82,
                'adaptability': 0.88,
                'interpretability': 0.78,
                'risk_awareness': 0.80,
                'domain_knowledge': 0.85
            },
            ModelType.PHI3_LATEST: {
                'faithfulness': 0.80,
                'adaptability': 0.85,
                'interpretability': 0.75,
                'risk_awareness': 0.78,
                'domain_knowledge': 0.82
            },
            ModelType.LLAMA_7B: {
                'faithfulness': 0.75,
                'adaptability': 0.85,
                'interpretability': 0.7,
                'risk_awareness': 0.7,
                'domain_knowledge': 0.8
            },
            ModelType.LLAMA_7B_CHAT: {
                'faithfulness': 0.8,
                'adaptability': 0.9,
                'interpretability': 0.75,
                'risk_awareness': 0.75,
                'domain_knowledge': 0.8
            },
            ModelType.FLAN_T5_BASE: {
                'faithfulness': 0.85,
                'adaptability': 0.8,
                'interpretability': 0.85,
                'risk_awareness': 0.7,
                'domain_knowledge': 0.75
            }
        }
        return capabilities.get(model_type, {
            'faithfulness': 0.5,
            'adaptability': 0.5,
            'interpretability': 0.5,
            'risk_awareness': 0.5,
            'domain_knowledge': 0.5
        })

class InternetRAGSystem:
    """Internet-based Retrieval Augmented Generation for enhanced responses"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def search_and_enhance(self, query: str, domain: str) -> Dict[str, Any]:
        """Search internet for relevant information and enhance response"""
        try:
            # Simulate internet search for demo (in real implementation, use search APIs)
            if "finance" in domain.lower():
                return self._get_finance_context(query)
            elif "medical" in domain.lower():
                return self._get_medical_context(query)
            else:
                return {"sources": [], "context": "", "enhancement_score": 0.0}
        except Exception as e:
            self.logger.error(f"Internet RAG error: {e}")
            return {"sources": [], "context": "", "enhancement_score": 0.0}
    
    def _get_finance_context(self, query: str) -> Dict[str, Any]:
        """Get finance-specific context from internet sources"""
        # Mock implementation - in reality would use financial APIs
        finance_sources = [
            "SEC.gov financial regulations",
            "Federal Reserve economic data",
            "Yahoo Finance market data",
            "Bloomberg financial news"
        ]
        
        context = f"Current financial market conditions and regulatory guidelines for {query}"
        return {
            "sources": finance_sources[:2],
            "context": context,
            "enhancement_score": 0.3
        }
    
    def _get_medical_context(self, query: str) -> Dict[str, Any]:
        """Get medical-specific context from internet sources"""
        # Mock implementation - in reality would use medical APIs
        medical_sources = [
            "PubMed medical literature",
            "FDA drug information",
            "CDC health guidelines",
            "Mayo Clinic medical information"
        ]
        
        context = f"Current medical research and guidelines for {query}"
        return {
            "sources": medical_sources[:2],
            "context": context,
            "enhancement_score": 0.25
        }

class ModelManager:
    """Manages multiple LLM models for FAIR-Agent system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.available_models = self._initialize_model_configs()
        self.loaded_models = {}
        self.internet_rag = InternetRAGSystem()
        
    def _initialize_model_configs(self) -> Dict[ModelType, ModelConfig]:
        """Initialize configurations for all supported Ollama models"""
        return {
            ModelType.LLAMA32_LATEST: ModelConfig(
                model_type=ModelType.LLAMA32_LATEST,
                model_name="llama3.2:latest",
                memory_requirement_gb=8.0,
                recommended_max_length=2048,
                supports_chat=True
            ),
            ModelType.MISTRAL_LATEST: ModelConfig(
                model_type=ModelType.MISTRAL_LATEST,
                model_name="mistral:latest",
                memory_requirement_gb=6.0,
                recommended_max_length=1024,
                supports_chat=True
            ),
            ModelType.PHI3_LATEST: ModelConfig(
                model_type=ModelType.PHI3_LATEST,
                model_name="phi3:latest",
                memory_requirement_gb=4.0,
                recommended_max_length=1024,
                supports_chat=True
            ),
            ModelType.CODELLAMA_LATEST: ModelConfig(
                model_type=ModelType.CODELLAMA_LATEST,
                model_name="codellama:latest",
                memory_requirement_gb=10.0,
                recommended_max_length=2048,
                supports_chat=True
            )
        }
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models with their capabilities"""
        models = []
        for model_type, config in self.available_models.items():
            capabilities = ModelCapabilities.get_model_capabilities(model_type)
            models.append({
                'type': model_type.value,
                'name': config.model_name,
                'memory_gb': config.memory_requirement_gb,
                'max_length': config.recommended_max_length,
                'supports_chat': config.supports_chat,
                'requires_auth': config.requires_auth,
                'capabilities': capabilities,
                'loaded': model_type in self.loaded_models
            })
        return models
    
    def load_model(self, model_type: ModelType, device: str = "auto") -> bool:
        """Load a specific model"""
        if model_type in self.loaded_models:
            self.logger.info(f"Model {model_type.value} already loaded")
            return True
            
        config = self.available_models.get(model_type)
        if not config:
            self.logger.error(f"Model type {model_type.value} not supported")
            return False
            
        try:
            self.logger.info(f"Loading model {config.model_name}...")
            
            # Check if LLaMA model
            if "llama" in config.model_name.lower():
                tokenizer = AutoTokenizer.from_pretrained(config.model_name)
                model = AutoModelForCausalLM.from_pretrained(
                    config.model_name,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map=device if device != "auto" else None,
                    low_cpu_mem_usage=True
                )
            else:
                # Standard HuggingFace model loading
                tokenizer = AutoTokenizer.from_pretrained(config.model_name)
                model = AutoModelForCausalLM.from_pretrained(
                    config.model_name,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map=device if device != "auto" else None
                )
            
            # Handle pad token
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Create pipeline
            text_pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                device_map=device if device != "auto" else None
            )
            
            self.loaded_models[model_type] = {
                'config': config,
                'tokenizer': tokenizer,
                'model': model,
                'pipeline': text_pipeline,
                'capabilities': ModelCapabilities.get_model_capabilities(model_type)
            }
            
            self.logger.info(f"Successfully loaded {config.model_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load model {config.model_name}: {e}")
            return False
    
    def unload_model(self, model_type: ModelType):
        """Unload a specific model to free memory"""
        if model_type in self.loaded_models:
            del self.loaded_models[model_type]
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            self.logger.info(f"Unloaded model {model_type.value}")
    
    def generate_response(
        self, 
        model_type: ModelType, 
        prompt: str, 
        max_new_tokens: int = 1000,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response using specified model"""
        
        if model_type not in self.loaded_models:
            if not self.load_model(model_type):
                return {"error": f"Failed to load model {model_type.value}"}
        
        model_info = self.loaded_models[model_type]
        pipeline = model_info['pipeline']
        
        try:
            response = pipeline(
                prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=model_info['tokenizer'].eos_token_id,
                repetition_penalty=1.1,
                **kwargs
            )
            
            generated_text = response[0]['generated_text'][len(prompt):]
            
            return {
                'generated_text': generated_text,
                'model_type': model_type.value,
                'capabilities': model_info['capabilities'],
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Generation error with {model_type.value}: {e}")
            return {"error": str(e), "success": False}
    
    def get_best_model_for_domain(self, domain: str, metric: str = "overall") -> ModelType:
        """Get the best model for a specific domain and metric"""
        
        if not self.loaded_models:
            return ModelType.LLAMA32_LATEST  # Default Ollama model
        
        best_model = None
        best_score = 0.0
        
        for model_type, model_info in self.loaded_models.items():
            capabilities = model_info['capabilities']
            
            if metric == "faithfulness":
                score = capabilities.get('faithfulness', 0.0)
            elif metric == "risk_awareness":
                score = capabilities.get('risk_awareness', 0.0)
            elif metric == "interpretability":
                score = capabilities.get('interpretability', 0.0)
            else:  # overall
                score = sum(capabilities.values()) / len(capabilities)
            
            if score > best_score:
                best_score = score
                best_model = model_type
        
        return best_model or ModelType.LLAMA32_LATEST
    
    def benchmark_models(self, test_prompts: List[str]) -> Dict[str, Any]:
        """Benchmark all loaded models for FAIR metrics comparison"""
        results = {}
        
        for model_type in self.loaded_models:
            model_results = []
            for prompt in test_prompts:
                response = self.generate_response(model_type, prompt)
                if response.get('success'):
                    model_results.append({
                        'prompt': prompt,
                        'response': response['generated_text'],
                        'length': len(response['generated_text']),
                        'capabilities': response['capabilities']
                    })
            
            results[model_type.value] = {
                'responses': model_results,
                'avg_length': sum(r['length'] for r in model_results) / len(model_results) if model_results else 0,
                'capabilities': self.loaded_models[model_type]['capabilities']
            }
        
        return results

# Global model manager instance
model_manager = ModelManager()