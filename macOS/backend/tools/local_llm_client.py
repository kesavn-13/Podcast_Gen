"""
Local LLM Clients using Ollama
Alternative to NVIDIA NIM for development without credits
"""

import requests
import os
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class LocalReasonerClient:
    """
    Local LLM client using Ollama for reasoning tasks
    Drop-in replacement for NVIDIA NIM reasoning client
    """
    
    def __init__(self, 
                 base_url: str = None,
                 model: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = model or os.getenv("LOCAL_REASONER_MODEL", "llama3:8b-instruct")
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test if Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = [m['name'] for m in response.json().get('models', [])]
                if self.model not in models:
                    logger.warning(f"⚠️  Model {self.model} not found. Available: {models}")
                    logger.warning(f"   Run: ollama pull {self.model}")
                else:
                    logger.info(f"✅ Connected to Ollama with model: {self.model}")
            else:
                raise ConnectionError(f"Ollama not responding: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Ollama connection failed: {e}")
            logger.error(f"   Make sure Ollama is running: ollama serve")
            logger.error(f"   Install from: https://ollama.com")
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Generate response using local LLM via Ollama
        
        Args:
            messages: List of chat messages [{"role": "user", "content": "..."}]
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Response in NVIDIA NIM compatible format
        """
        try:
            # Extract parameters
            temperature = kwargs.get('temperature', 0.2)
            max_tokens = kwargs.get('max_tokens', 800)
            response_type = kwargs.get('response_type', 'text')
            
            # Call Ollama API
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "stop": ["</response>", "Human:", "Assistant:"]
                }
            }
            
            logger.info(f"🤖 Generating with {self.model}: {len(messages)} messages")
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["message"]["content"]
            
            # Format response to match NVIDIA NIM structure
            formatted_response = {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": self._parse_response(content, response_type)
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                    "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                },
                "model": self.model,
                "created": result.get("created_at", ""),
                "id": f"local-{hash(str(messages))}"
            }
            
            logger.info(f"✅ Generated {result.get('eval_count', 0)} tokens")
            return formatted_response
            
        except Exception as e:
            logger.error(f"❌ Local LLM generation failed: {e}")
            # Fallback to mock response
            return self._fallback_response(response_type)
    
    def _parse_response(self, content: str, response_type: str) -> Any:
        """Parse response based on expected type"""
        if response_type in ['outline', 'segment', 'factcheck', 'rewrite']:
            # Try to extract JSON from response
            try:
                # Look for JSON block
                if '```json' in content:
                    json_start = content.find('```json') + 7
                    json_end = content.find('```', json_start)
                    json_str = content[json_start:json_end].strip()
                    return json.loads(json_str)
                elif '{' in content and '}' in content:
                    # Try to extract JSON directly
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    json_str = content[start:end]
                    return json.loads(json_str)
                else:
                    # Return structured text
                    return {"generated_text": content.strip()}
            except json.JSONDecodeError:
                return {"generated_text": content.strip()}
        
        return content.strip()
    
    def _fallback_response(self, response_type: str) -> Dict[str, Any]:
        """Fallback to mock response if local LLM fails"""
        logger.warning("🔄 Falling back to mock response")
        
        fallback_content = {
            "outline": {"segments": [{"title": "Introduction", "duration": 60}]},
            "segment": {"script_lines": ["Generated by local LLM fallback"]},
            "factcheck": {"verification_status": "fallback_mode"},
            "rewrite": {"improved_content": "Local LLM unavailable"}
        }
        
        return {
            "choices": [{
                "message": {
                    "role": "assistant", 
                    "content": fallback_content.get(response_type, "Local LLM fallback response")
                },
                "finish_reason": "stop"
            }]
        }


class LocalEmbeddingClient:
    """
    Local embedding client using Ollama
    Drop-in replacement for NVIDIA Retrieval Embedding NIM
    """
    
    def __init__(self, 
                 base_url: str = None,
                 model: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = model or os.getenv("LOCAL_EMBED_MODEL", "nomic-embed-text")
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test if embedding model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = [m['name'] for m in response.json().get('models', [])]
                if self.model not in models:
                    logger.warning(f"⚠️  Embedding model {self.model} not found")
                    logger.warning(f"   Run: ollama pull {self.model}")
                else:
                    logger.info(f"✅ Embedding model ready: {self.model}")
        except Exception as e:
            logger.error(f"❌ Embedding model connection failed: {e}")
    
    async def embed(self, texts: List[str]) -> Dict[str, Any]:
        """
        Generate embeddings using local model
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Embeddings in NVIDIA NIM compatible format
        """
        try:
            embeddings = []
            
            for text in texts:
                payload = {
                    "model": self.model,
                    "input": text
                }
                
                response = requests.post(
                    f"{self.base_url}/api/embed",
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                
                result = response.json()
                embeddings.append(result["embeddings"][0])
            
            # Format response to match NVIDIA NIM structure
            formatted_response = {
                "data": [
                    {
                        "embedding": embedding,
                        "index": i,
                        "object": "embedding"
                    }
                    for i, embedding in enumerate(embeddings)
                ],
                "model": self.model,
                "object": "list",
                "usage": {
                    "prompt_tokens": sum(len(text.split()) for text in texts),
                    "total_tokens": sum(len(text.split()) for text in texts)
                }
            }
            
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            return formatted_response
            
        except Exception as e:
            logger.error(f"❌ Local embedding generation failed: {e}")
            # Fallback to random embeddings for development
            return self._fallback_embeddings(texts)
    
    def _fallback_embeddings(self, texts: List[str]) -> Dict[str, Any]:
        """Fallback to random embeddings"""
        import random
        
        logger.warning("🔄 Using random embeddings as fallback")
        
        embeddings = []
        for text in texts:
            # Generate consistent random embedding based on text hash
            random.seed(hash(text))
            embedding = [random.random() for _ in range(768)]
            embeddings.append(embedding)
        
        return {
            "data": [
                {
                    "embedding": embedding,
                    "index": i,
                    "object": "embedding"
                }
                for i, embedding in enumerate(embeddings)
            ],
            "model": "fallback-random",
            "object": "list"
        }


def create_local_clients():
    """Factory function to create local LLM clients"""
    reasoning_client = LocalReasonerClient()
    embedding_client = LocalEmbeddingClient()
    
    return reasoning_client, embedding_client


# Auto-setup check
def check_ollama_setup():
    """Check if Ollama is properly set up"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            print("🦙 Ollama Status:")
            print(f"   ✅ Server running on http://localhost:11434")
            print(f"   📚 Available models: {model_names}")
            
            # Check for recommended models
            recommended = ["llama3:8b-instruct", "nomic-embed-text"]
            for model in recommended:
                if model in model_names:
                    print(f"   ✅ {model}")
                else:
                    print(f"   ❌ {model} - run: ollama pull {model}")
            
            return True
        else:
            print("❌ Ollama server not responding")
            return False
    except:
        print("❌ Ollama not found. Install from: https://ollama.com")
        print("   Then run: ollama serve")
        return False


if __name__ == "__main__":
    # Test the setup
    check_ollama_setup()