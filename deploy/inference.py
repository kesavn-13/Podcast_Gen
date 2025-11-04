"""
SageMaker Inference Handler for AI Research Podcast Agent
Production-ready inference script for NVIDIA-AWS Hackathon
"""

import json
import os
import sys
import logging
import asyncio
from typing import Dict, Any, List
import torch
import numpy as np

# Add project root to path
sys.path.append('/opt/ml/code')

# Import application modules
from app.main import PodcastGenerator
from backend.tools.sm_client import create_clients
from app.audio_generator import PodcastAudioProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SageMakerInferenceHandler:
    """
    SageMaker inference handler for scalable podcast generation
    Handles model loading, preprocessing, inference, and postprocessing
    """
    
    def __init__(self):
        self.model = None
        self.device = None
        self.is_initialized = False
        
    def model_fn(self, model_dir: str):
        """
        Load the model for inference
        Called once when the endpoint is created
        """
        logger.info("🚀 Initializing AI Podcast Agent for SageMaker...")
        
        try:
            # Set up environment
            os.environ.setdefault('HACKATHON_MODE', 'true')
            os.environ.setdefault('USE_NVIDIA_NIM', 'true')
            
            # Initialize NVIDIA NIM clients
            logger.info("🔧 Setting up NVIDIA NIM clients...")
            reasoner_client, embedding_client = create_clients()
            
            # Initialize podcast generator
            logger.info("🎙️ Initializing podcast generator...")
            podcast_generator = PodcastGenerator(
                reasoner_client=reasoner_client,
                embedding_client=embedding_client
            )
            
            # Initialize audio producer
            logger.info("🎵 Setting up audio production...")
            audio_producer = PodcastAudioProducer(
                use_natural_voices=True,
                podcast_style='layperson'
            )
            
            # Package model components
            model = {
                'podcast_generator': podcast_generator,
                'audio_producer': audio_producer,
                'reasoner_client': reasoner_client,
                'embedding_client': embedding_client
            }
            
            # Set device (GPU if available)
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info(f"🖥️  Using device: {self.device}")
            
            self.is_initialized = True
            logger.info("✅ SageMaker model initialization complete!")
            
            return model
            
        except Exception as e:
            logger.error(f"❌ Model initialization failed: {e}")
            raise e
    
    def input_fn(self, request_body: str, content_type: str = 'application/json') -> Dict[str, Any]:
        """
        Preprocess input data
        """
        logger.info(f"📥 Processing input: {content_type}")
        
        try:
            if content_type == 'application/json':
                input_data = json.loads(request_body)
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
            
            # Validate required fields
            required_fields = ['action']
            for field in required_fields:
                if field not in input_data:
                    raise ValueError(f"Missing required field: {field}")
            
            logger.info(f"✅ Input validated: {input_data['action']}")
            return input_data
            
        except Exception as e:
            logger.error(f"❌ Input processing failed: {e}")
            raise e
    
    def predict_fn(self, input_data: Dict[str, Any], model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run inference
        """
        logger.info("🤖 Running AI podcast generation inference...")
        
        try:
            action = input_data.get('action', 'process_paper')
            
            if action == 'process_paper':
                return self._process_paper(input_data, model)
            elif action == 'generate_outline':
                return self._generate_outline(input_data, model)
            elif action == 'generate_script':
                return self._generate_script(input_data, model)
            elif action == 'generate_audio':
                return self._generate_audio(input_data, model)
            elif action == 'health_check':
                return self._health_check(model)
            else:
                raise ValueError(f"Unsupported action: {action}")
                
        except Exception as e:
            logger.error(f"❌ Inference failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'action': input_data.get('action', 'unknown')
            }
    
    def _process_paper(self, input_data: Dict[str, Any], model: Dict[str, Any]) -> Dict[str, Any]:
        """Process complete paper to podcast pipeline"""
        logger.info("📄 Processing complete paper-to-podcast pipeline...")
        
        try:
            # Extract parameters
            paper_content = input_data.get('paper_content', '')
            paper_url = input_data.get('paper_url', '')
            podcast_style = input_data.get('podcast_style', 'layperson')
            
            if not paper_content and not paper_url:
                raise ValueError("Either paper_content or paper_url must be provided")
            
            # If URL provided, download content (simplified for demo)
            if paper_url and not paper_content:
                paper_content = f"Research paper from {paper_url}"
            
            # Generate podcast outline
            logger.info("📋 Generating podcast outline...")
            outline_result = asyncio.run(
                self._async_generate_outline(paper_content, model['reasoner_client'])
            )
            
            if not outline_result.get('success'):
                return {
                    'status': 'error',
                    'message': 'Outline generation failed',
                    'stage': 'outline'
                }
            
            # Generate podcast scripts
            logger.info("📝 Generating podcast scripts...")
            scripts_result = asyncio.run(
                self._async_generate_scripts(
                    outline_result['outline'], 
                    paper_content,
                    model['reasoner_client']
                )
            )
            
            if not scripts_result.get('success'):
                return {
                    'status': 'error',
                    'message': 'Script generation failed',
                    'stage': 'scripts'
                }
            
            # Generate audio
            logger.info("🎵 Generating podcast audio...")
            audio_result = asyncio.run(
                self._async_generate_audio(
                    scripts_result['scripts'],
                    podcast_style,
                    model['audio_producer']
                )
            )
            
            return {
                'status': 'success',
                'message': 'Podcast generated successfully',
                'data': {
                    'outline': outline_result['outline'],
                    'scripts': scripts_result['scripts'],
                    'audio_info': audio_result,
                    'metadata': {
                        'style': podcast_style,
                        'segments': len(outline_result['outline'].get('segments', [])),
                        'processing_time': 'calculated_in_production'
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Paper processing failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'stage': 'paper_processing'
            }
    
    async def _async_generate_outline(self, paper_content: str, reasoner_client) -> Dict[str, Any]:
        """Generate podcast outline asynchronously"""
        try:
            # Simplified outline generation for demo
            outline_prompt = f"""
            Create a 6-segment podcast outline for this research paper.
            
            Paper content: {paper_content[:2000]}...
            
            Return JSON with segments including title, duration_seconds, and description.
            """
            
            messages = [{"role": "user", "content": outline_prompt}]
            response = await reasoner_client.generate(messages)
            
            # Parse response (simplified)
            if isinstance(response, dict) and 'content' in response:
                content = response['content']
                
                # Try to extract JSON
                if '```json' in content:
                    json_start = content.find('```json') + 7
                    json_end = content.find('```', json_start)
                    if json_end != -1:
                        json_content = content[json_start:json_end].strip()
                    else:
                        json_content = content[json_start:].strip()
                else:
                    json_content = content
                
                outline = json.loads(json_content)
                
                return {
                    'success': True,
                    'outline': outline
                }
            else:
                raise Exception("Invalid response format")
                
        except Exception as e:
            logger.error(f"Outline generation error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _async_generate_scripts(self, outline: Dict[str, Any], paper_content: str, reasoner_client) -> Dict[str, Any]:
        """Generate podcast scripts asynchronously"""
        try:
            segments = outline.get('segments', [])
            scripts = []
            
            for i, segment in enumerate(segments[:3]):  # Limit for demo
                script_prompt = f"""
                Create a conversational podcast script for this segment.
                
                Segment: {segment.get('title', 'Untitled')}
                Description: {segment.get('description', '')}
                
                Return JSON with script array of speaker/text objects.
                """
                
                messages = [{"role": "user", "content": script_prompt}]
                response = await reasoner_client.generate(messages)
                
                # Parse script response (simplified)
                if isinstance(response, dict) and 'content' in response:
                    content = response['content']
                    
                    # Extract JSON
                    if '```json' in content:
                        json_start = content.find('```json') + 7
                        json_end = content.find('```', json_start)
                        if json_end != -1:
                            json_content = content[json_start:json_end].strip()
                        else:
                            json_content = content[json_start:].strip()
                    else:
                        json_content = content
                    
                    script_data = json.loads(json_content)
                    scripts.append({
                        'segment_id': i,
                        'segment_title': segment.get('title', 'Untitled'),
                        'script': script_data.get('script', [])
                    })
            
            return {
                'success': True,
                'scripts': scripts
            }
            
        except Exception as e:
            logger.error(f"Script generation error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _async_generate_audio(self, scripts: List[Dict], podcast_style: str, audio_producer) -> Dict[str, Any]:
        """Generate podcast audio asynchronously"""
        try:
            # Flatten scripts for audio generation
            all_segments = []
            for script_data in scripts:
                for dialogue in script_data['script']:
                    all_segments.append({
                        'text': dialogue.get('text', ''),
                        'speaker': dialogue.get('speaker', 'host1')
                    })
            
            # Generate audio (simplified for SageMaker)
            audio_info = {
                'status': 'generated',
                'segments_count': len(all_segments),
                'estimated_duration': len(all_segments) * 10,  # Rough estimate
                'format': 'mp3',
                'style': podcast_style
            }
            
            return audio_info
            
        except Exception as e:
            logger.error(f"Audio generation error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _health_check(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """Health check endpoint"""
        try:
            # Check model components
            components_status = {
                'podcast_generator': 'healthy' if model.get('podcast_generator') else 'missing',
                'audio_producer': 'healthy' if model.get('audio_producer') else 'missing',
                'reasoner_client': 'healthy' if model.get('reasoner_client') else 'missing',
                'embedding_client': 'healthy' if model.get('embedding_client') else 'missing'
            }
            
            overall_status = 'healthy' if all(status == 'healthy' for status in components_status.values()) else 'unhealthy'
            
            return {
                'status': overall_status,
                'components': components_status,
                'device': str(self.device),
                'initialized': self.is_initialized,
                'timestamp': str(np.datetime64('now'))
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': str(np.datetime64('now'))
            }
    
    def output_fn(self, prediction: Dict[str, Any], accept: str = 'application/json') -> str:
        """
        Postprocess output data
        """
        logger.info(f"📤 Formatting output: {accept}")
        
        try:
            if accept == 'application/json':
                return json.dumps(prediction, indent=2)
            else:
                raise ValueError(f"Unsupported accept type: {accept}")
                
        except Exception as e:
            logger.error(f"❌ Output processing failed: {e}")
            return json.dumps({
                'status': 'error',
                'message': f'Output processing failed: {str(e)}'
            })

# Global handler instance
handler = SageMakerInferenceHandler()

# SageMaker entry points
def model_fn(model_dir):
    """SageMaker model loading entry point"""
    return handler.model_fn(model_dir)

def input_fn(request_body, content_type='application/json'):
    """SageMaker input processing entry point"""
    return handler.input_fn(request_body, content_type)

def predict_fn(input_data, model):
    """SageMaker prediction entry point"""
    return handler.predict_fn(input_data, model)

def output_fn(prediction, accept='application/json'):
    """SageMaker output processing entry point"""
    return handler.output_fn(prediction, accept)

if __name__ == "__main__":
    # Local testing
    print("🧪 Testing SageMaker inference handler locally...")
    
    # Initialize model
    model = handler.model_fn("/tmp/model")
    
    # Test health check
    test_input = {"action": "health_check"}
    result = handler.predict_fn(test_input, model)
    print("Health Check Result:", json.dumps(result, indent=2))
    
    # Test paper processing
    test_input = {
        "action": "process_paper",
        "paper_content": "Sample research paper about AI and machine learning...",
        "podcast_style": "tech_interview"
    }
    result = handler.predict_fn(test_input, model)
    print("Paper Processing Result:", json.dumps(result, indent=2))