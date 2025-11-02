"""
Text Processor
Analyzes content and enhances text with style-appropriate conversation patterns
"""

import re
from typing import Dict, List, Any, Tuple
from .conversation_engine import ConversationEngine


class TextProcessor:
    """Processes and enhances text for natural podcast conversation"""
    
    def __init__(self, style_name: str):
        self.style_name = style_name
        self.conversation_engine = ConversationEngine(style_name)
        
        # Content analysis patterns
        self.excitement_keywords = [
            "breakthrough", "revolutionary", "unprecedented", "remarkable", "extraordinary",
            "amazing", "incredible", "stunning", "groundbreaking", "game-changing"
        ]
        
        self.technical_keywords = [
            "algorithm", "methodology", "implementation", "architecture", "framework",
            "analysis", "computation", "optimization", "neural", "statistical"
        ]
        
        self.controversial_keywords = [
            "concern", "risk", "limitation", "bias", "ethical", "problematic",
            "controversial", "debate", "criticism", "question"
        ]
        
        self.complex_indicators = [
            "multi-step", "complex", "sophisticated", "intricate", "comprehensive",
            "detailed", "extensive", "in-depth", "thorough"
        ]
    
    def analyze_content_type(self, text: str) -> str:
        """Analyze text to determine its primary content type"""
        text_lower = text.lower()
        
        # Count keyword matches
        excitement_score = sum(1 for keyword in self.excitement_keywords if keyword in text_lower)
        technical_score = sum(1 for keyword in self.technical_keywords if keyword in text_lower)
        controversial_score = sum(1 for keyword in self.controversial_keywords if keyword in text_lower)
        complex_score = sum(1 for keyword in self.complex_indicators if keyword in text_lower)
        
        # Determine primary type based on highest score
        scores = {
            "exciting": excitement_score,
            "technical": technical_score,
            "controversial": controversial_score,
            "complex": complex_score
        }
        
        max_score = max(scores.values())
        if max_score == 0:
            return "general"
        
        # Return the type with highest score
        for content_type, score in scores.items():
            if score == max_score:
                return content_type
        
        return "general"
    
    def analyze_content_emotion(self, text: str) -> str:
        """Analyze the emotional tone of the content"""
        text_lower = text.lower()
        
        positive_indicators = ["success", "improvement", "effective", "better", "positive", "breakthrough"]
        negative_indicators = ["failure", "worse", "negative", "problem", "concern", "limitation"]
        neutral_indicators = ["analysis", "study", "research", "data", "method", "approach"]
        
        positive_score = sum(1 for word in positive_indicators if word in text_lower)
        negative_score = sum(1 for word in negative_indicators if word in text_lower)
        neutral_score = sum(1 for word in neutral_indicators if word in text_lower)
        
        if positive_score > negative_score and positive_score > neutral_score:
            return "positive"
        elif negative_score > positive_score and negative_score > neutral_score:
            return "negative"
        else:
            return "neutral"
    
    def clean_text_for_speech(self, text: str) -> str:
        """Clean and prepare text for natural speech"""
        # Remove markdown and special formatting
        clean_text = text.replace('**', '').replace('*', '')
        clean_text = clean_text.replace('[Source', '. Source')
        clean_text = clean_text.replace(']', '.')
        
        # Handle citations and references
        clean_text = re.sub(r'\[(\d+)\]', r'', clean_text)  # Remove citation numbers
        clean_text = re.sub(r'\(.*?et al\..*?\)', '', clean_text)  # Remove author citations
        
        # Add natural pauses
        clean_text = clean_text.replace('. ', '. ... ')
        clean_text = clean_text.replace('? ', '? ... ')
        clean_text = clean_text.replace('! ', '! ... ')
        clean_text = clean_text.replace(', ', ', .. ')
        
        # Handle common abbreviations for better pronunciation
        abbreviations = {
            'AI': 'A.I.',
            'ML': 'M.L.',
            'NLP': 'N.L.P.',
            'CNN': 'C.N.N.',
            'RNN': 'R.N.N.',
            'GPU': 'G.P.U.',
            'CPU': 'C.P.U.',
            'API': 'A.P.I.',
            'URL': 'U.R.L.',
            'HTTP': 'H.T.T.P.',
            'JSON': 'J.S.O.N.',
            'XML': 'X.M.L.',
            'SQL': 'S.Q.L.'
        }
        
        for abbrev, pronunciation in abbreviations.items():
            clean_text = clean_text.replace(abbrev, pronunciation)
        
        # Handle numbers for better speech
        clean_text = re.sub(r'\b(\d+)%', r'\1 percent', clean_text)
        clean_text = re.sub(r'\b(\d+)\s*x\b', r'\1 times', clean_text)
        
        return clean_text.strip()
    
    def add_emphasis_pauses(self, text: str, content_type: str) -> str:
        """Add strategic pauses for emphasis based on content type"""
        if content_type == "exciting":
            # Add dramatic pauses before exciting revelations
            emphasis_terms = ["breakthrough", "revolutionary", "unprecedented", "remarkable"]
            for term in emphasis_terms:
                text = text.replace(f' {term}', f' ..... {term}')
        
        elif content_type == "technical":
            # Add thinking pauses before technical explanations
            technical_terms = ["algorithm", "methodology", "implementation", "analysis"]
            for term in technical_terms:
                text = text.replace(f' {term}', f' ... {term}')
        
        elif content_type == "controversial":
            # Add cautious pauses before sensitive topics
            caution_terms = ["concern", "limitation", "risk", "problem"]
            for term in caution_terms:
                text = text.replace(f' {term}', f' .... {term}')
        
        return text
    
    def process_text_segment(self, text: str, preferred_speaker: str = None) -> List[Dict[str, Any]]:
        """Process a text segment into conversational podcast segments with balanced speakers"""
        # Analyze content
        content_type = self.analyze_content_type(text)
        content_emotion = self.analyze_content_emotion(text)
        
        # For longer content, split between speakers for better balance
        if len(text.split()) > 100 and not preferred_speaker:
            return self._process_long_content_with_balance(text, content_type, content_emotion)
        
        # Determine best speaker with alternation priority
        speaker = self.conversation_engine.assign_speaker_for_content(text, preferred_speaker)
        
        # Clean and enhance text
        clean_text = self.clean_text_for_speech(text)
        emphasized_text = self.add_emphasis_pauses(clean_text, content_type)
        
        # Generate speaker interactions
        interactions = self.conversation_engine.generate_speaker_interaction(
            emphasized_text, speaker, content_type
        )
        
        # Add metadata to each interaction
        for interaction in interactions:
            interaction.update({
                "content_type": content_type,
                "content_emotion": content_emotion,
                "voice_config": self._get_voice_config_for_speaker(interaction["speaker"])
            })
        
        return interactions
    
    def _process_long_content_with_balance(self, text: str, content_type: str, content_emotion: str) -> List[Dict[str, Any]]:
        """Split long content between speakers for better conversation balance"""
        # Split text into sentences
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        if len(sentences) < 2:
            # Fall back to single speaker
            speaker = self.conversation_engine.assign_speaker_for_content(text)
            return self._create_single_interaction(text, speaker, content_type, content_emotion)
        
        interactions = []
        current_speaker = self.conversation_engine.assign_speaker_for_content(sentences[0])
        
        # Group sentences and alternate speakers
        mid_point = len(sentences) // 2
        
        # First half
        first_part = '. '.join(sentences[:mid_point]) + '.'
        first_interactions = self._create_single_interaction(first_part, current_speaker, content_type, content_emotion)
        interactions.extend(first_interactions)
        
        # Second half with other speaker
        other_speaker = "host2" if current_speaker == "host1" else "host1"
        second_part = '. '.join(sentences[mid_point:]) + '.'
        
        # Add transition for the second speaker
        if self.style_name == "tech_interview":
            if current_speaker == "host1":  # Interviewer spoke first
                transition = "That's fascinating. Can you elaborate on the technical details?"
            else:  # Expert spoke first
                transition = "Let me ask about the implications of what you just described."
            
            interactions.append({
                "speaker": other_speaker,
                "text": transition,
                "type": "transition",
                "content_type": "transition",
                "content_emotion": "neutral",
                "voice_config": self._get_voice_config_for_speaker(other_speaker)
            })
        
        second_interactions = self._create_single_interaction(second_part, other_speaker, content_type, content_emotion)
        interactions.extend(second_interactions)
        
        return interactions
    
    def _create_single_interaction(self, text: str, speaker: str, content_type: str, content_emotion: str) -> List[Dict[str, Any]]:
        """Create a single interaction with proper processing"""
        clean_text = self.clean_text_for_speech(text)
        emphasized_text = self.add_emphasis_pauses(clean_text, content_type)
        
        interactions = self.conversation_engine.generate_speaker_interaction(
            emphasized_text, speaker, content_type
        )
        
        for interaction in interactions:
            interaction.update({
                "content_type": content_type,
                "content_emotion": content_emotion,
                "voice_config": self._get_voice_config_for_speaker(interaction["speaker"])
            })
        
        return interactions
    
    def _get_voice_config_for_speaker(self, speaker: str) -> Dict[str, Any]:
        """Get voice configuration for a speaker based on current style"""
        host_config = self.conversation_engine.get_host_config(speaker)
        
        return {
            "speech_rate": host_config.get("speech_rate", 140),
            "voice_energy": host_config.get("voice_energy", "medium"),
            "personality": host_config.get("personality", "neutral")
        }
    
    def process_full_content(self, content_segments: List[str]) -> List[Dict[str, Any]]:
        """Process multiple content segments into a full podcast conversation"""
        all_interactions = []
        
        for i, segment in enumerate(content_segments):
            # Add introduction for first segment
            if i == 0:
                intro_interactions = self._generate_introduction()
                all_interactions.extend(intro_interactions)
            
            # Process main content
            segment_interactions = self.process_text_segment(segment)
            all_interactions.extend(segment_interactions)
            
            # Add transitions between segments
            if i < len(content_segments) - 1:
                transition = self._generate_transition()
                if transition:
                    all_interactions.append(transition)
        
        # Add conclusion
        conclusion_interactions = self._generate_conclusion()
        all_interactions.extend(conclusion_interactions)
        
        return all_interactions
    
    def _generate_introduction(self) -> List[Dict[str, Any]]:
        """Generate podcast introduction based on style"""
        style_config = self.conversation_engine.style_config
        
        intro_templates = {
            "friendly_chat": [
                "Hey everyone! We've got a really fascinating research paper to dive into today.",
                "I know, right? I was reading through this and I couldn't wait to discuss it with you."
            ],
            "tech_interview": [
                "Welcome to our technical deep dive. Today we're examining some cutting-edge research.",
                "The methodology here is particularly interesting. Let's break down what the researchers accomplished."
            ],
            "academic_discussion": [
                "Good day, colleagues. We're here to conduct a scholarly examination of recent research.",
                "Indeed. The paper presents several findings worthy of rigorous analysis."
            ],
            "investigative": [
                "We're here to take a critical look at some new research that's been making waves.",
                "That's right. And we're going to dig deep into the claims and examine the evidence."
            ],
            "debate_format": [
                "Today we're discussing research that's sure to spark some interesting debate.",
                "Absolutely. I think we're going to have some different perspectives on this one."
            ]
        }
        
        templates = intro_templates.get(self.style_name, intro_templates["friendly_chat"])
        
        return [
            {
                "speaker": "host1",
                "text": templates[0],
                "type": "introduction",
                "content_type": "introduction",
                "content_emotion": "neutral",
                "voice_config": self._get_voice_config_for_speaker("host1")
            },
            {
                "speaker": "host2", 
                "text": templates[1],
                "type": "introduction",
                "content_type": "introduction",
                "content_emotion": "neutral",
                "voice_config": self._get_voice_config_for_speaker("host2")
            }
        ]
    
    def _generate_transition(self) -> Dict[str, Any]:
        """Generate transition between segments"""
        current_speaker = self.conversation_engine.last_speaker
        next_speaker = "host2" if current_speaker == "host1" else "host1"
        
        transition_phrase = self.conversation_engine.get_transition_phrase(next_speaker)
        
        return {
            "speaker": next_speaker,
            "text": transition_phrase,
            "type": "transition",
            "content_type": "transition",
            "content_emotion": "neutral",
            "voice_config": self._get_voice_config_for_speaker(next_speaker)
        }
    
    def _generate_conclusion(self) -> List[Dict[str, Any]]:
        """Generate podcast conclusion based on style"""
        conclusion_templates = {
            "friendly_chat": [
                "This was such an interesting discussion! Thanks for breaking that down with me.",
                "Absolutely! It's amazing what researchers are discovering these days."
            ],
            "tech_interview": [
                "That's a comprehensive analysis of the technical implementation.",
                "The implications for the field are certainly significant."
            ],
            "academic_discussion": [
                "This concludes our scholarly examination of the research.",
                "The findings certainly contribute valuable insights to the literature."
            ],
            "investigative": [
                "We've examined the evidence from multiple angles.",
                "It's important to maintain healthy skepticism while acknowledging valid research."
            ],
            "debate_format": [
                "Well, we've certainly covered multiple perspectives on this research.",
                "That's the beauty of scientific discourse - examining all angles."
            ]
        }
        
        templates = conclusion_templates.get(self.style_name, conclusion_templates["friendly_chat"])
        
        return [
            {
                "speaker": "host1",
                "text": templates[0],
                "type": "conclusion",
                "content_type": "conclusion",
                "content_emotion": "positive",
                "voice_config": self._get_voice_config_for_speaker("host1")
            },
            {
                "speaker": "host2",
                "text": templates[1], 
                "type": "conclusion",
                "content_type": "conclusion",
                "content_emotion": "positive",
                "voice_config": self._get_voice_config_for_speaker("host2")
            }
        ]
