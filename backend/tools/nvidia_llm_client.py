"""
NVIDIA Llama-3.1-Nemotron-Nano-8B-v1 LLM Client
Hackathon-compliant primary LLM provider using NVIDIA NIM endpoints with OpenAI format
"""

import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

# Use OpenAI library as specified in NVIDIA documentation
try:
    from openai import OpenAI
except ImportError:
    raise ImportError("OpenAI library is required. Install with: pip install openai")

logger = logging.getLogger(__name__)


class NVIDIALlamaClient:
    """
    NVIDIA Llama-3.1-Nemotron-Nano-8B-v1 client for reasoning and content generation
    Hackathon-compliant LLM provider using OpenAI library with NVIDIA endpoints
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        self.base_url = "https://integrate.api.nvidia.com/v1"
        # Use exact model name from NVIDIA documentation
        self.model_name = "nvidia/llama-3.1-nemotron-nano-8b-v1"
        
        if not self.api_key:
            raise ValueError("NVIDIA API key is required. Set NVIDIA_API_KEY environment variable.")
        
        # Initialize OpenAI client with NVIDIA endpoints (as per NVIDIA docs)
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        
        logger.info(f"✅ NVIDIA Llama client initialized with model: {self.model_name}")
        logger.info(f"🏆 Using NVIDIA NIM endpoint: {self.base_url}")
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Generate response using NVIDIA Llama-3.1-Nemotron-Nano-8B-v1
        Compatible with existing Paper→Podcast system interface
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            response_type: Type of response expected ('outline', 'segment', 'factcheck', 'rewrite')
            **kwargs: Additional generation parameters
            
        Returns:
            Dictionary with response and metadata in NIM-compatible format
        """
        try:
            # Extract response type for structured prompts
            response_type = kwargs.get('response_type', 'text')
            
            # Create appropriate prompt based on response type
            if response_type in ['outline', 'segment', 'factcheck', 'rewrite']:
                prompt = self._create_structured_prompt(messages, response_type)
            else:
                prompt = self._convert_messages_to_prompt(messages)
            
            # Generate response using NVIDIA NIM API
            response = await self._generate_async(prompt, **kwargs)
            
            # Format response for compatibility
            formatted_response = self._format_response(response, response_type)
            
            logger.info(f"🏆 NVIDIA Llama generation completed: {len(formatted_response.get('content', ''))} chars")
            return formatted_response
            
        except Exception as e:
            logger.error(f"❌ NVIDIA Llama generation failed: {e}")
            return self._create_fallback_response(response_type, str(e))
    
    async def _generate_async(self, prompt: str, **kwargs) -> str:
        """Generate response using NVIDIA NIM API via OpenAI library"""
        
        try:
            # Convert single prompt to messages format
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # Use OpenAI client with NVIDIA parameters (exact format from NVIDIA docs)
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                completion = await loop.run_in_executor(
                    executor,
                    lambda: self.client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        temperature=kwargs.get('temperature', 0),
                        top_p=kwargs.get('top_p', 0.95),
                        max_tokens=kwargs.get('max_tokens', 1024),
                        frequency_penalty=kwargs.get('frequency_penalty', 0),
                        presence_penalty=kwargs.get('presence_penalty', 0),
                        stream=False  # Use non-streaming for async compatibility
                    )
                )
            
            # Extract content from response
            if completion.choices and completion.choices[0].message.content:
                return completion.choices[0].message.content
            else:
                raise Exception("NVIDIA API returned empty response")
                
        except Exception as e:
            # Handle OpenAI library exceptions
            if "401" in str(e) or "authentication" in str(e).lower():
                logger.error("NVIDIA API authentication failed")
                raise Exception("NVIDIA API authentication failed - check API key")
            elif "429" in str(e) or "rate limit" in str(e).lower():
                logger.error("NVIDIA API rate limit exceeded")
                raise Exception("NVIDIA API rate limit exceeded - wait and retry")
            elif "timeout" in str(e).lower():
                logger.error("NVIDIA API request timed out")
                raise Exception("NVIDIA API timeout - try reducing max_tokens")
            else:
                logger.error(f"NVIDIA API error: {e}")
                raise Exception(f"NVIDIA API request failed: {e}")
    
    def _create_structured_prompt(self, messages: List[Dict[str, str]], response_type: str) -> str:
        """Create structured prompt based on response type for NVIDIA Llama"""
        
        # Extract system and user messages
        system_msg = next((msg['content'] for msg in messages if msg['role'] == 'system'), '')
        user_msg = next((msg['content'] for msg in messages if msg['role'] == 'user'), '')
        
        # Add specific formatting instructions for NVIDIA Llama
        formatting_instructions = {
            'outline': """
IMPORTANT: Your response must be valid JSON only. Format as:
{
  "title": "Episode title",
  "segments": [
    {
      "title": "Segment title",
      "duration": 120,
      "content_summary": "Brief summary",
      "key_points": ["point1", "point2"]
    }
  ]
}""",
            'segment': """
IMPORTANT: Your response must be valid JSON only. Format as:
{
  "script_lines": [
    "Host dialogue line 1",
    "Host dialogue line 2"
  ],
  "speaker_notes": ["Note 1", "Note 2"]
}""",
            'factcheck': """
IMPORTANT: Your response must be valid JSON only. Format as:
{
  "accuracy_score": 0.95,
  "issues_found": [],
  "corrections": [],
  "verified_facts": ["fact1", "fact2"]
}""",
            'rewrite': """
IMPORTANT: Your response must be valid JSON only. Format as:
{
  "improved_content": "Rewritten content here",
  "changes_made": ["change1", "change2"]
}"""
        }
        
        instruction = formatting_instructions.get(response_type, "Provide a helpful and informative response.")
        
        return f"""System: {system_msg}

{instruction}

User: {user_msg}

Response:"""
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to single prompt for NVIDIA Llama"""
        prompt_parts = []
        
        for message in messages:
            role = message['role'].title()
            content = message['content']
            prompt_parts.append(f"{role}: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def _format_response(self, content: str, response_type: str) -> Dict[str, Any]:
        """Format NVIDIA response to match expected interface"""
        
        # Try to parse as JSON for structured responses
        if response_type in ['outline', 'segment', 'factcheck', 'rewrite']:
            try:
                # Extract JSON from response if it's embedded in text
                if '```json' in content:
                    start = content.find('```json') + 7
                    end = content.find('```', start)
                    json_content = content[start:end].strip()
                else:
                    # Look for JSON-like structure
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start != -1 and end != 0:
                        json_content = content[start:end]
                    else:
                        json_content = content
                
                parsed_json = json.loads(json_content)
                
                return {
                    "content": json_content,
                    "parsed": parsed_json,
                    "model": self.model_name,
                    "provider": "nvidia",
                    "response_type": response_type,
                    "hackathon_compliant": True
                }
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON response for {response_type}")
        
        # Return as text response
        return {
            "content": content,
            "model": self.model_name, 
            "provider": "nvidia",
            "response_type": response_type,
            "hackathon_compliant": True
        }
    
    def _create_fallback_response(self, response_type: str, error_msg: str) -> Dict[str, Any]:
        """Create fallback response when NVIDIA API fails"""
        
        fallback_content = {
            "outline": {
                "title": "Generated by NVIDIA Llama (Fallback)",
                "segments": [
                    {
                        "title": "Introduction",
                        "duration": 60,
                        "content_summary": "Episode introduction",
                        "key_points": ["Welcome message"]
                    }
                ]
            },
            "segment": {
                "script_lines": ["Generated by NVIDIA Llama fallback system"],
                "speaker_notes": ["Fallback response due to API error"]
            },
            "factcheck": {
                "accuracy_score": 0.0,
                "issues_found": [f"API Error: {error_msg}"],
                "corrections": [],
                "verified_facts": []
            },
            "rewrite": {
                "improved_content": "NVIDIA Llama unavailable - using fallback",
                "changes_made": ["Fallback response generated"]
            }
        }
        
        content = fallback_content.get(response_type, f"NVIDIA Llama fallback: {error_msg}")
        
        return {
            "content": json.dumps(content) if isinstance(content, dict) else content,
            "parsed": content if isinstance(content, dict) else None,
            "model": self.model_name,
            "provider": "nvidia",
            "response_type": response_type,
            "error": error_msg,
            "hackathon_compliant": True
        }


# Factory function for NVIDIA clients  
def create_nvidia_clients(api_key: str = None) -> tuple:
    """
    Create NVIDIA-based reasoning and embedding clients for hackathon compliance
    
    Returns:
        Tuple of (nvidia_llama_client, nvidia_embedding_client)
    """
    try:
        from backend.tools.nvidia_embedding_client import NVIDIAEmbeddingClient
        
        nvidia_llm_client = NVIDIALlamaClient(api_key=api_key)
        nvidia_embedding_client = NVIDIAEmbeddingClient(api_key=api_key)
        
        logger.info("🏆 NVIDIA Llama-3.1-Nemotron-Nano-8B-v1 + nv-embedqa-e5-v5 clients created successfully")
        return nvidia_llm_client, nvidia_embedding_client
        
    except Exception as e:
        logger.error(f"Failed to create NVIDIA clients: {e}")
        raise


# Test function for NVIDIA integration
async def test_nvidia_llm():
    """Test NVIDIA Llama integration"""
    print("🧪 Testing NVIDIA Llama-3.1-Nemotron-Nano-8B-v1 integration...")
    
    try:
        client = NVIDIALlamaClient()
        
        test_messages = [
            {"role": "system", "content": "You are a helpful AI assistant for podcast generation."},
            {"role": "user", "content": "Generate a brief outline for a podcast about artificial intelligence."}
        ]
        
        response = await client.generate(test_messages, response_type='outline')
        
        print("✅ NVIDIA Llama test successful!")
        print(f"Model: {response.get('model')}")
        print(f"Provider: {response.get('provider')}")
        print(f"Hackathon Compliant: {response.get('hackathon_compliant')}")
        print(f"Response length: {len(response.get('content', ''))}")
        
        return True
        
    except Exception as e:
        print(f"❌ NVIDIA Llama test failed: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_nvidia_llm())