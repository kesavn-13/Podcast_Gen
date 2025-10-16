"""
Mock SageMaker NIM Clients for Development
These have identical interfaces to the real clients but return deterministic responses
"""

import json
import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime


class MockReasonerClient:
    """Mock NVIDIA NIM Llama Nemotron client for development"""
    
    def __init__(self, mock_data_path: str = "samples/mocks/"):
        self.mock_data_path = mock_data_path
        self.call_count = 0
        
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Mock generation that returns deterministic responses based on message type
        
        Args:
            messages: List of chat messages
            **kwargs: Additional parameters (ignored in mock)
            
        Returns:
            Mock response matching real NIM format
        """
        self.call_count += 1
        
        # Simulate API latency
        await asyncio.sleep(float(os.getenv('MOCK_RESPONSE_DELAY', '1.0')))
        
        # Determine response type based on system message
        system_message = next((msg['content'] for msg in messages if msg['role'] == 'system'), '')
        
        if 'outline' in system_message.lower():
            response_file = 'outline_response.json'
        elif 'segment' in system_message.lower():
            response_file = 'segment_response.json'
        elif 'factcheck' in system_message.lower():
            response_file = 'factcheck_response.json'
        elif 'rewrite' in system_message.lower():
            response_file = 'rewrite_response.json'
        else:
            response_file = 'default_response.json'
            
        # Load mock response
        mock_response = self._load_mock_response(response_file)
        
        return {
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'content': mock_response
                },
                'finish_reason': 'stop'
            }],
            'usage': {
                'prompt_tokens': sum(len(msg['content'].split()) for msg in messages),
                'completion_tokens': len(mock_response.split()),
                'total_tokens': sum(len(msg['content'].split()) for msg in messages) + len(mock_response.split())
            },
            'model': 'llama-3.1-nemotron-nano-8b-v1',
            'mock': True,
            'call_count': self.call_count
        }
    
    def _load_mock_response(self, filename: str) -> str:
        """Load mock response from file"""
        filepath = os.path.join(self.mock_data_path, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('content', 'Mock response not found')
        
        # Fallback responses if files don't exist
        fallback_responses = {
            'outline_response.json': self._get_outline_response(),
            'segment_response.json': self._get_segment_response(),
            'factcheck_response.json': self._get_factcheck_response(),
            'rewrite_response.json': self._get_rewrite_response(),
            'default_response.json': "I understand your request and will provide a helpful response."
        }
        
        return fallback_responses.get(filename, "Mock response available")
    
    def _get_outline_response(self) -> str:
        """Generate a deterministic outline response"""
        return json.dumps({
            "title": "Understanding Transformer Architectures in Modern AI",
            "summary": "An exploration of how attention mechanisms revolutionized natural language processing and machine learning.",
            "segments": [
                {
                    "type": "intro",
                    "title": "Introduction to Transformers",
                    "duration_target": 60,
                    "key_points": [
                        "Historical context of sequence modeling",
                        "Problems with RNN architectures",
                        "The breakthrough of attention mechanisms"
                    ]
                },
                {
                    "type": "core",
                    "title": "Deep Dive: Attention is All You Need",
                    "duration_target": 300,
                    "key_points": [
                        "Self-attention mechanism explained",
                        "Multi-head attention architecture",
                        "Positional encoding innovations",
                        "Encoder-decoder structure",
                        "Training efficiency improvements"
                    ]
                },
                {
                    "type": "takeaways",
                    "title": "Impact and Future Directions",
                    "duration_target": 60,
                    "key_points": [
                        "Real-world applications",
                        "Performance benchmarks",
                        "Future research directions",
                        "Industry adoption"
                    ]
                }
            ],
            "complexity_score": 0.7,
            "total_duration_estimate": 420
        }, indent=2)
    
    def _get_segment_response(self) -> str:
        """Generate a deterministic segment script response"""
        return json.dumps({
            "script_lines": [
                {
                    "speaker": "host_1",
                    "text": "Welcome to today's deep dive into transformer architectures. I'm excited to explore this groundbreaking paper that changed everything we know about natural language processing.",
                    "duration_estimate": 6.5
                },
                {
                    "speaker": "host_2", 
                    "text": "Absolutely! The 'Attention is All You Need' paper by Vaswani and colleagues really was a watershed moment. Before transformers, we were stuck with the sequential limitations of RNNs and LSTMs.",
                    "duration_estimate": 7.2
                },
                {
                    "speaker": "host_1",
                    "text": "Right, and what makes this so fascinating is how they completely reimagined sequence modeling. Instead of processing words one by one, transformers can look at all positions simultaneously.",
                    "duration_estimate": 6.8
                },
                {
                    "speaker": "host_2",
                    "text": "The key insight, as they explain on page 3, is that attention mechanisms allow the model to focus on different parts of the input sequence based on their relevance to the current position being processed.",
                    "duration_estimate": 7.5
                }
            ]
        }, indent=2)
    
    def _get_factcheck_response(self) -> str:
        """Generate a deterministic fact-check response"""
        return json.dumps({
            "verification_results": [
                {
                    "line_index": 0,
                    "is_verified": True,
                    "confidence": 0.95,
                    "citations": [],
                    "notes": "General introduction, no specific claims to verify"
                },
                {
                    "line_index": 1,
                    "is_verified": True, 
                    "confidence": 0.92,
                    "citations": [
                        {
                            "page": 1,
                            "text": "Attention Is All You Need, Vaswani et al., 2017",
                            "relevance": 0.95
                        }
                    ],
                    "notes": "Correctly attributes the paper and main insight"
                },
                {
                    "line_index": 2,
                    "is_verified": True,
                    "confidence": 0.88,
                    "citations": [
                        {
                            "page": 2,
                            "text": "The Transformer allows for significantly more parallelization",
                            "relevance": 0.87
                        }
                    ],
                    "notes": "Accurate description of parallel processing capability"
                },
                {
                    "line_index": 3,
                    "is_verified": False,
                    "confidence": 0.45,
                    "citations": [],
                    "needs_rewrite": True,
                    "notes": "Page 3 reference needs verification - attention mechanism description may be oversimplified"
                }
            ],
            "overall_verification_rate": 0.75
        }, indent=2)
    
    def _get_rewrite_response(self) -> str:
        """Generate a deterministic rewrite response"""
        return json.dumps({
            "rewritten_lines": [
                {
                    "original_index": 3,
                    "speaker": "host_2",
                    "text": "According to the authors on page 1, the attention function can be described as mapping a query and a set of key-value pairs to an output, allowing the model to weigh the importance of different input positions when processing each element.",
                    "duration_estimate": 8.2,
                    "improvement_notes": "More accurate description with proper citation"
                }
            ]
        }, indent=2)


class MockEmbeddingClient:
    """Mock NVIDIA Retrieval NIM client for development"""
    
    def __init__(self, local_model: str = "sentence-transformers/all-mpnet-base-v2"):
        self.local_model = local_model
        self.call_count = 0
        
        # Try to load local embeddings model
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(local_model)
            self.use_local_model = True
        except ImportError:
            print("Warning: sentence-transformers not installed. Using random embeddings.")
            self.use_local_model = False
    
    async def embed(self, texts: List[str], **kwargs) -> Dict[str, Any]:
        """
        Generate embeddings for texts
        
        Args:
            texts: List of texts to embed
            **kwargs: Additional parameters
            
        Returns:
            Embeddings response
        """
        self.call_count += 1
        
        # Simulate API latency
        await asyncio.sleep(0.5)
        
        if self.use_local_model:
            embeddings = self.model.encode(texts).tolist()
        else:
            # Generate random embeddings as fallback
            import random
            dimension = 768  # Standard dimension
            embeddings = [[random.random() for _ in range(dimension)] for _ in texts]
        
        return {
            'data': [
                {
                    'embedding': emb,
                    'index': i,
                    'object': 'embedding'
                }
                for i, emb in enumerate(embeddings)
            ],
            'model': self.local_model,
            'usage': {
                'prompt_tokens': sum(len(text.split()) for text in texts),
                'total_tokens': sum(len(text.split()) for text in texts)
            },
            'mock': True,
            'call_count': self.call_count
        }


# Factory function to create clients based on environment
def create_clients(use_mock: bool = None) -> tuple[MockReasonerClient, MockEmbeddingClient]:
    """
    Create mock or real clients based on configuration
    
    Args:
        use_mock: Override for mock usage (defaults to env setting)
        
    Returns:
        Tuple of (reasoner_client, embedding_client)
    """
    if use_mock is None:
        use_mock = os.getenv('USE_MOCK_SERVICES', 'true').lower() == 'true'
    
    if use_mock:
        reasoner = MockReasonerClient()
        embedding = MockEmbeddingClient()
        print("🎭 Using mock clients for development")
    else:
        # Import real clients when not using mocks
        try:
            from .sagemaker_client import SageMakerReasonerClient, SageMakerEmbeddingClient
            reasoner = SageMakerReasonerClient()
            embedding = SageMakerEmbeddingClient()
            print("🚀 Using real SageMaker NIM clients")
        except ImportError:
            print("⚠️  Real clients not available, falling back to mocks")
            reasoner = MockReasonerClient()
            embedding = MockEmbeddingClient()
    
    return reasoner, embedding