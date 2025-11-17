"""
Ollama Client for FAIR-Agent
Provides interface to Ollama models for faster local inference
"""

import requests
import json
import logging
from typing import Optional, Dict, Any

class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11435"):
        """
        Initialize Ollama client
        
        Args:
            base_url: Base URL for Ollama API (default: http://localhost:11435)
        """
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self.api_endpoint = f"{base_url}/api/generate"
        
    def generate(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stream: bool = False
    ) -> Optional[str]:
        """
        Generate text using Ollama model
        
        Args:
            model: Model name (e.g., 'llama3.2', 'llama3', 'codellama')
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            stream: Whether to stream response
            
        Returns:
            Generated text or None if error
        """
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "num_predict": max_tokens
                }
            }
            
            self.logger.info(f"Calling Ollama API with model: {model}")
            
            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                if stream:
                    # Handle streaming response
                    full_text = ""
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line)
                            if 'response' in data:
                                full_text += data['response']
                    return full_text
                else:
                    # Handle non-streaming response
                    data = response.json()
                    return data.get('response', '')
            else:
                self.logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            self.logger.error("Ollama API timeout")
            return None
        except requests.exceptions.ConnectionError:
            self.logger.error("Cannot connect to Ollama - is it running? (ollama serve)")
            return None
        except Exception as e:
            self.logger.error(f"Ollama generation error: {str(e)}")
            return None
    
    def is_available(self) -> bool:
        """
        Check if Ollama service is available
        
        Returns:
            True if Ollama is running and accessible
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> list:
        """
        List available Ollama models
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except:
            return []
