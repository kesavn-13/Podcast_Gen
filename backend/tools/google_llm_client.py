"""
Google Gemini LLM Client
Primary LLM provider for Paper→Podcast generation
"""

import google.generativeai as genai
import os
import json
import logging
from typing import List, Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class GoogleGeminiClient:
    """
    Google Gemini client for reasoning and content generation
    Primary LLM provider replacing NVIDIA NIM for cost efficiency
    """
    
    def __init__(self, 
                 api_key: str = None,
                 model: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model_name = model or os.getenv("GOOGLE_MODEL", "gemini-pro")
        
        if not self.api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY environment variable.")
        
        # Configure the API
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel(self.model_name)
        
        # Generation config for consistent outputs
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            top_p=0.8,
            top_k=40,
            max_output_tokens=4000,
            candidate_count=1
        )
        
        # Safety settings to allow educational content
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        logger.info(f"✅ Google Gemini client initialized with model: {self.model_name}")
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Generate response using Google Gemini
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
            
            # Generate response in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                response = await loop.run_in_executor(
                    executor, 
                    self._generate_sync, 
                    prompt
                )
            
            # Extract response text
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Parse response based on type
            parsed_content = self._parse_response_by_type(response_text, response_type)
            
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(parsed_content) if isinstance(parsed_content, dict) else parsed_content
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": len(prompt.split()) * 1.3,  # Rough estimate
                    "completion_tokens": len(response_text.split()) * 1.3,
                    "total_tokens": len((prompt + response_text).split()) * 1.3
                },
                "model": self.model_name,
                "provider": "google-gemini"
            }
            
        except Exception as e:
            logger.error(f"❌ Google Gemini generation failed: {e}")
            return {
                "error": str(e),
                "choices": [{"message": {"role": "assistant", "content": "{\"error\": \"Generation failed\"}"}}],
                "model": self.model_name,
                "provider": "google-gemini"
            }
    
    def _generate_sync(self, prompt: str):
        """Synchronous generation for thread pool execution"""
        return self.model.generate_content(
            prompt,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
    
    def _create_structured_prompt(self, messages: List[Dict[str, str]], response_type: str) -> str:
        """
        Create structured prompts for different response types
        
        Args:
            messages: List of message dictionaries
            response_type: Type of response expected
            
        Returns:
            Structured prompt for the specific response type
        """
        # Extract system and user messages
        system_msg = next((msg['content'] for msg in messages if msg['role'] == 'system'), '')
        user_msg = next((msg['content'] for msg in messages if msg['role'] == 'user'), '')
        
        if response_type == 'outline':
            return f"""
{system_msg}

PAPER CONTENT:
{user_msg}

Generate a detailed podcast episode outline as a JSON object with this exact structure:
{{
    "title": "Episode title",
    "summary": "Brief episode summary",
    "segments": [
        {{
            "type": "intro",
            "title": "Segment title",
            "duration_target": 60,
            "key_points": ["point1", "point2", "point3"]
        }},
        {{
            "type": "core",
            "title": "Main content segment",
            "duration_target": 300,
            "key_points": ["technical details", "methodology", "results"]
        }},
        {{
            "type": "takeaways",
            "title": "Conclusions and impact", 
            "duration_target": 120,
            "key_points": ["summary", "implications", "future work"]
        }}
    ],
    "complexity_score": 0.7,
    "total_duration_estimate": 480
}}

Return only the JSON object, no additional text.
"""
        
        elif response_type == 'segment':
            return f"""
{system_msg}

SEGMENT CONTEXT:
{user_msg}

Generate a detailed podcast segment script as a JSON object:
{{
    "script_lines": [
        {{
            "speaker": "host_1",
            "text": "Natural dialogue here...",
            "duration_estimate": 6.5
        }},
        {{
            "speaker": "host_2",
            "text": "Response from second host...",
            "duration_estimate": 7.2
        }}
    ]
}}

Make the dialogue natural, engaging, and technically accurate. Return only the JSON object.
"""
        
        elif response_type == 'factcheck':
            return f"""
{system_msg}

CONTENT TO VERIFY:
{user_msg}

Generate fact-check results as a JSON object:
{{
    "verification_results": [
        {{
            "line_index": 0,
            "is_verified": true,
            "confidence": 0.95,
            "citations": [
                {{
                    "page": 1,
                    "text": "Supporting text from paper",
                    "relevance": 0.95
                }}
            ],
            "notes": "Verification notes"
        }}
    ]
}}

Return only the JSON object.
"""
        
        else:
            return self._convert_messages_to_prompt(messages)
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert OpenAI-style messages to a single prompt for Gemini
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Single prompt string
        """
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"SYSTEM INSTRUCTIONS:\n{content}\n")
            elif role == "user":
                prompt_parts.append(f"USER:\n{content}\n")
            elif role == "assistant":
                prompt_parts.append(f"ASSISTANT:\n{content}\n")
        
        return "\n".join(prompt_parts)
    
    def _parse_response_by_type(self, response_text: str, response_type: str):
        """
        Parse response based on expected type
        
        Args:
            response_text: Raw response from Gemini
            response_type: Expected response type
            
        Returns:
            Parsed response content
        """
        # Try to extract JSON from response
        try:
            # Look for JSON block in markdown
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                json_str = response_text[json_start:json_end].strip()
                return json.loads(json_str)
            
            # Look for direct JSON
            elif response_text.strip().startswith('{'):
                # Find the complete JSON object
                brace_count = 0
                json_end = 0
                for i, char in enumerate(response_text):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                
                if json_end > 0:
                    json_str = response_text[:json_end]
                    return json.loads(json_str)
            
            # Fallback for different response types
            if response_type == 'outline':
                return {
                    "title": "Generated Episode",
                    "segments": [
                        {"title": "Introduction", "duration_target": 60},
                        {"title": "Main Content", "duration_target": 300},
                        {"title": "Conclusion", "duration_target": 60}
                    ]
                }
            elif response_type == 'segment':
                return {
                    "script_lines": [
                        {
                            "speaker": "host_1",
                            "text": response_text[:200] + "...",
                            "duration_estimate": 10.0
                        }
                    ]
                }
            else:
                return {"content": response_text}
                
        except json.JSONDecodeError:
            # Return raw text if JSON parsing fails
            return {"content": response_text}
    
    async def generate_podcast_outline(self, paper_content: str, style: str = "tech_energetic") -> Dict[str, Any]:
        """
        Generate a detailed podcast outline from research paper
        
        Args:
            paper_content: Extracted text from research paper
            style: Podcast style (tech_energetic, npr_calm, etc.)
            
        Returns:
            Structured podcast outline
        """
        prompt = f"""
You are an expert podcast producer creating engaging audio content from research papers.

PAPER CONTENT:
{paper_content[:4000]}  # Truncate for token limits

STYLE: {style}

Generate a detailed podcast outline with the following structure:

{{
    "title": "Engaging podcast episode title",
    "duration_estimate": 1500,
    "hosts": {{
        "host1": {{
            "name": "Dr. Sarah Chen",
            "role": "Research expert",
            "personality": "Curious and analytical"
        }},
        "host2": {{
            "name": "Prof. Mike Rodriguez", 
            "role": "Practical applications expert",
            "personality": "Enthusiastic and accessible"
        }}
    }},
    "segments": [
        {{
            "type": "intro",
            "duration": 120,
            "speakers": ["host1", "host2"],
            "content": "Engaging introduction to the topic",
            "key_points": ["What we'll cover", "Why it matters", "What listeners will learn"]
        }},
        {{
            "type": "main_discussion",
            "duration": 300,
            "speakers": ["host1", "host2"],
            "content": "Deep dive into the research methodology",
            "key_points": ["Research question", "Methodology", "Novel approach"]
        }},
        {{
            "type": "technical_deep_dive",
            "duration": 400,
            "speakers": ["host1", "host2"],
            "content": "Technical details explained accessibly",
            "key_points": ["Core innovation", "Technical challenges", "Solutions"]
        }},
        {{
            "type": "results_analysis",
            "duration": 300,
            "speakers": ["host1", "host2"],
            "content": "Discussion of results and implications",
            "key_points": ["Key findings", "Performance metrics", "Comparisons"]
        }},
        {{
            "type": "real_world_applications",
            "duration": 250,
            "speakers": ["host1", "host2"],
            "content": "Practical applications and future impact",
            "key_points": ["Current applications", "Future potential", "Industry impact"]
        }},
        {{
            "type": "outro",
            "duration": 125,
            "speakers": ["host1", "host2"],
            "content": "Summary and next steps for listeners",
            "key_points": ["Key takeaways", "Further reading", "Thank you"]
        }}
    ],
    "total_segments": 6,
    "estimated_words": 2400,
    "target_audience": "Technical professionals and curious learners"
}}

Make the content engaging, educational, and conversational. Focus on making complex topics accessible while maintaining technical accuracy.
"""
        
        messages = [{"role": "user", "content": prompt}]
        return await self.generate(messages)
    
    async def generate_segment_script(self, 
                                    outline_segment: Dict[str, Any], 
                                    paper_context: str,
                                    previous_segments: List[str] = None) -> Dict[str, Any]:
        """
        Generate detailed script for a specific podcast segment
        
        Args:
            outline_segment: Segment from the podcast outline
            paper_context: Relevant paper content for this segment
            previous_segments: Previous segment scripts for continuity
            
        Returns:
            Detailed segment script with speaker assignments
        """
        previous_context = ""
        if previous_segments:
            previous_context = f"\nPREVIOUS SEGMENTS SUMMARY:\n{' '.join(previous_segments[-2:])}\n"
        
        prompt = f"""
You are writing a detailed podcast script for a specific segment.

SEGMENT INFO:
- Type: {outline_segment.get('type', 'discussion')}
- Duration: {outline_segment.get('duration', 300)} seconds
- Speakers: {outline_segment.get('speakers', ['host1', 'host2'])}
- Content Focus: {outline_segment.get('content', '')}
- Key Points: {outline_segment.get('key_points', [])}

PAPER CONTEXT:
{paper_context[:2000]}

{previous_context}

Generate a detailed script with natural conversation flow:

{{
    "segment_type": "{outline_segment.get('type', 'discussion')}",
    "estimated_duration": {outline_segment.get('duration', 300)},
    "word_count": 480,
    "dialogue": [
        {{
            "speaker": "host1",
            "text": "Natural opening statement or question that flows from previous content...",
            "duration": 8.5,
            "emotion": "curious"
        }},
        {{
            "speaker": "host2", 
            "text": "Engaging response that builds on the topic...",
            "duration": 12.0,
            "emotion": "enthusiastic"
        }},
        {{
            "speaker": "host1",
            "text": "Follow-up that dives deeper into technical details...",
            "duration": 15.5,
            "emotion": "analytical"
        }}
    ],
    "technical_terms_explained": ["term1", "term2"],
    "key_takeaways": ["takeaway1", "takeaway2"],
    "transitions": {{
        "intro": "How this segment connects from previous",
        "outro": "How this leads to next segment"
    }}
}}

Requirements:
- Natural, conversational dialogue
- Technical accuracy with accessible explanations
- Smooth transitions between speakers
- Engaging and educational content
- Target ~160 words per minute speaking rate
- Include brief pauses and natural speech patterns
"""
        
        messages = [{"role": "user", "content": prompt}]
        return await self.generate(messages)


class GoogleEmbeddingClient:
    """
    Google embedding client for RAG and semantic search
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError("Google API key is required for embeddings")
        
        genai.configure(api_key=self.api_key)
        logger.info("✅ Google Embedding client initialized")
    
    async def embed(self, texts: List[str]) -> Dict[str, Any]:
        """
        Generate embeddings for a list of texts
        Compatible with existing Paper→Podcast system interface
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Dictionary with embeddings in NIM-compatible format
        """
        try:
            embeddings = []
            
            # Process in batches to avoid rate limits
            batch_size = 100
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # Generate embeddings for batch
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    batch_embeddings = await loop.run_in_executor(
                        executor,
                        self._embed_batch,
                        batch
                    )
                    embeddings.extend(batch_embeddings)
            
            # Format response to match existing system expectations
            return {
                "data": [
                    {
                        "embedding": embedding,
                        "index": i,
                        "object": "embedding"
                    }
                    for i, embedding in enumerate(embeddings)
                ],
                "model": "models/embedding-001",
                "object": "list",
                "usage": {
                    "prompt_tokens": sum(len(text.split()) for text in texts),
                    "total_tokens": sum(len(text.split()) for text in texts)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {e}")
            # Return empty embeddings with proper format
            return {
                "data": [],
                "error": str(e),
                "model": "models/embedding-001"
            }
    
    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Synchronous embedding generation for thread pool"""
        embeddings = []
        for text in texts:
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            embeddings.append(result['embedding'])
        return embeddings


# Factory function for creating clients
def create_google_clients(api_key: str = None) -> tuple:
    """
    Create Google Gemini and Embedding clients
    
    Args:
        api_key: Google API key
        
    Returns:
        Tuple of (gemini_client, embedding_client)
    """
    gemini_client = GoogleGeminiClient(api_key=api_key)
    embedding_client = GoogleEmbeddingClient(api_key=api_key)
    
    return gemini_client, embedding_client