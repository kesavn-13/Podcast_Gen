"""
Conversation Engine
Manages host interactions, role assignments, and natural conversation flow
"""

import random
import re
from typing import Dict, List, Any, Tuple, Optional
from .style_definitions import get_style_config


class ConversationEngine:
    """Manages natural conversation patterns between podcast hosts"""
    
    def __init__(self, style_name: str):
        self.style_name = style_name
        self.style_config = get_style_config(style_name)
        self.host_configs = self.style_config["host_dynamics"]
        self.flow_config = self.style_config["conversation_flow"]
        
        # Track conversation state
        self.conversation_history = []
        self.last_speaker = None
        self.segment_count = 0
        
        # Cache host roles for quick lookup
        self.host_roles = {
            speaker: config["role"] 
            for speaker, config in self.host_configs.items()
        }
    
    def get_host_config(self, speaker: str) -> Dict[str, Any]:
        """Get configuration for a specific host"""
        return self.host_configs.get(speaker, self.host_configs.get("host1", {}))
    
    def should_add_interruption(self) -> bool:
        """Determine if an interruption should occur based on style"""
        return random.random() < self.flow_config["interruptions"]
    
    def should_add_follow_up(self) -> bool:
        """Determine if a follow-up question should be added"""
        return random.random() < self.flow_config["follow_up_questions"]
    
    def should_add_reaction(self) -> bool:
        """Determine if a reaction should be added"""
        return random.random() < self.flow_config["personal_reactions"]
    
    def should_add_agreement(self) -> bool:
        """Determine if agreement sounds should be added"""
        return random.random() < self.flow_config["agreement_sounds"]
    
    def get_interruption_phrase(self, speaker: str, content_emotion: str = "neutral") -> str:
        """Get an appropriate interruption phrase for the speaker"""
        host_config = self.get_host_config(speaker)
        reactions = host_config.get("typical_reactions", [])
        
        if content_emotion == "exciting" and reactions:
            # Filter for excited interruptions
            excited = [r for r in reactions if any(word in r.lower() 
                      for word in ["cool", "amazing", "incredible", "wow", "wait"])]
            if excited:
                return random.choice(excited)
        
        if reactions:
            return random.choice(reactions)
        return "Wait, let me jump in here..."
    
    def get_follow_up_question(self, speaker: str, content_type: str = "general") -> str:
        """Generate a follow-up question appropriate to the speaker and content"""
        host_config = self.get_host_config(speaker)
        questions = host_config.get("question_patterns", [])
        
        if questions:
            return random.choice(questions)
        return "Can you tell us more about that?"
    
    def get_reaction_phrase(self, speaker: str, content_emotion: str = "neutral") -> str:
        """Get an appropriate reaction phrase"""
        host_config = self.get_host_config(speaker)
        reactions = host_config.get("typical_reactions", [])
        
        if content_emotion == "exciting" and reactions:
            excited_reactions = [r for r in reactions if any(word in r.lower() 
                               for word in ["cool", "amazing", "incredible", "wow"])]
            if excited_reactions:
                return random.choice(excited_reactions)
        
        if reactions:
            return random.choice(reactions)
        return "That's really interesting."
    
    def get_agreement_sound(self) -> str:
        """Get natural agreement sounds"""
        sounds = ["mm-hmm", "exactly", "right", "yes", "absolutely", "I see"]
        return random.choice(sounds)
    
    def get_transition_phrase(self, speaker: str) -> str:
        """Get a natural transition phrase"""
        host_config = self.get_host_config(speaker)
        transitions = host_config.get("transitions", [])
        
        if transitions:
            return random.choice(transitions)
        
        # Fallback transitions based on conversation flow style
        transition_style = self.flow_config.get("transition_style", "smooth")
        if transition_style == "smooth":
            return random.choice(["And building on that...", "Speaking of which...", "This connects to..."])
        elif transition_style == "investigative":
            return random.choice(["Now here's what I want to know...", "But let's dig deeper...", "Hold on, that raises a question..."])
        elif transition_style == "contrastive":
            return random.choice(["However...", "On the other hand...", "But consider this..."])
        else:
            return random.choice(["Moving on...", "Additionally...", "Furthermore..."])
    
    def assign_speaker_for_content(self, content: str, preferred_speaker: str = None) -> str:
        """Assign the most appropriate speaker based on content and style"""
        if preferred_speaker and preferred_speaker in self.host_configs:
            return preferred_speaker
        
        # For better alternation, prioritize switching speakers
        if self.last_speaker:
            next_speaker = "host2" if self.last_speaker == "host1" else "host1"
            
            # Only override alternation for very specific content types
            if self._is_question_content(content):
                return self._get_questioner_speaker()
            elif self._is_strong_explanation_content(content):
                return self._get_explainer_speaker()
            else:
                # Use alternating pattern for balanced conversation
                return next_speaker
        
        # Content analysis for first speaker assignment
        if self._is_question_content(content):
            return self._get_questioner_speaker()
        elif self._is_explanation_content(content):
            return self._get_explainer_speaker()
        elif self._is_critical_content(content):
            return self._get_critical_speaker()
        else:
            return "host1"  # Default start
    
    def _is_question_content(self, content: str) -> bool:
        """Check if content is question-like"""
        question_indicators = ["what", "how", "why", "when", "where", "?", "can you explain", "tell me"]
        return any(indicator in content.lower() for indicator in question_indicators)
    
    def _is_explanation_content(self, content: str) -> bool:
        """Check if content is explanation-like"""
        explanation_indicators = ["because", "therefore", "the result", "the study shows", "we found", "the data", "analysis reveals"]
        return any(indicator in content.lower() for indicator in explanation_indicators)
    
    def _is_strong_explanation_content(self, content: str) -> bool:
        """Check if content is a strong technical explanation that should go to expert"""
        strong_indicators = ["algorithm", "methodology", "architecture", "implementation", "results show", "we demonstrate", "our approach"]
        return any(indicator in content.lower() for indicator in strong_indicators)
    
    def _is_critical_content(self, content: str) -> bool:
        """Check if content requires critical analysis"""
        critical_indicators = ["limitation", "concern", "problem", "issue", "bias", "however", "but", "despite"]
        return any(indicator in content.lower() for indicator in critical_indicators)
    
    def _get_questioner_speaker(self) -> str:
        """Get the speaker who typically asks questions"""
        for speaker, role in self.host_roles.items():
            if any(keyword in role.lower() for keyword in ["interviewer", "curious", "investigator"]):
                return speaker
        return "host1"
    
    def _get_explainer_speaker(self) -> str:
        """Get the speaker who typically explains"""
        for speaker, role in self.host_roles.items():
            if any(keyword in role.lower() for keyword in ["expert", "knowledgeable", "interpreter", "presenter"]):
                return speaker
        return "host2"
    
    def _get_critical_speaker(self) -> str:
        """Get the speaker who typically provides critical analysis"""
        for speaker, role in self.host_roles.items():
            if any(keyword in role.lower() for keyword in ["critical", "analyst", "examiner", "skeptical"]):
                return speaker
        return "host1"
    
    def _get_alternate_speaker(self) -> str:
        """Get alternating speaker for variety"""
        if self.last_speaker == "host1":
            return "host2"
        elif self.last_speaker == "host2":
            return "host1"
        else:
            return "host1"
    
    def enhance_text_with_conversation(self, text: str, speaker: str, content_type: str = "general") -> str:
        """Add conversational elements to text based on style and speaker"""
        enhanced_text = text
        host_config = self.get_host_config(speaker)
        
        # Add natural conversation starters
        if self.segment_count == 0 or random.random() < 0.3:
            if content_type == "introduction":
                starter_phrases = [
                    "So let's dive into this...",
                    "Here's what caught my attention...",
                    "This is really interesting because...",
                ]
                enhanced_text = f"{random.choice(starter_phrases)} {enhanced_text}"
            elif content_type == "technical":
                explanation_patterns = host_config.get("explanation_patterns", [])
                if explanation_patterns:
                    enhanced_text = f"{random.choice(explanation_patterns)} {enhanced_text}"
        
        # Add thinking pauses for complex content
        if content_type in ["complex", "technical"] or len(enhanced_text.split()) > 30:
            if random.random() < 0.2:
                thinking_pauses = ["... let me think about this ...", "... this is interesting ...", "... hmm ..."]
                enhanced_text = f"{random.choice(thinking_pauses)} {enhanced_text}"
        
        # Update conversation state
        self.last_speaker = speaker
        self.segment_count += 1
        self.conversation_history.append({
            "speaker": speaker,
            "content": enhanced_text,
            "content_type": content_type
        })
        
        return enhanced_text
    
    def generate_speaker_interaction(self, primary_text: str, primary_speaker: str, content_type: str = "general") -> List[Dict[str, str]]:
        """Generate a natural interaction between hosts with better speaker balance"""
        interactions = []
        
        # Primary speaker's enhanced text
        enhanced_primary = self.enhance_text_with_conversation(primary_text, primary_speaker, content_type)
        interactions.append({
            "speaker": primary_speaker,
            "text": enhanced_primary,
            "type": "primary"
        })
        
        # Determine secondary speaker
        other_speaker = "host2" if primary_speaker == "host1" else "host1"
        
        # For tech_interview style, ensure both speakers get substantial content
        if self.style_name == "tech_interview":
            if len(enhanced_primary.split()) > 50:  # Long content needs response
                if primary_speaker == "host1":  # Interviewer asked/commented
                    # Expert should provide detailed response
                    expert_response = self._generate_expert_response(enhanced_primary, content_type)
                    interactions.append({
                        "speaker": other_speaker,
                        "text": expert_response,
                        "type": "expert_response"
                    })
                else:  # Expert explained something
                    # Interviewer should ask follow-up
                    follow_up = self.get_follow_up_question(other_speaker, content_type)
                    interactions.append({
                        "speaker": other_speaker,
                        "text": follow_up,
                        "type": "follow_up"
                    })
        else:
            # For debate_format, create adversarial interactions
            if self.style_name == "debate_format":
                if self.should_add_follow_up() or content_type in ["controversial", "technical", "general"]:
                    opposition = self._generate_adversarial_response(other_speaker, enhanced_primary, content_type)
                    interactions.append({
                        "speaker": other_speaker,
                        "text": opposition,
                        "type": "opposition"
                    })
            else:
                # Original logic for other styles
                # Add interruption if appropriate
                if self.should_add_interruption() and content_type in ["exciting", "controversial"]:
                    interruption = self.get_interruption_phrase(other_speaker, content_type)
                    interactions.append({
                        "speaker": other_speaker,
                        "text": interruption,
                        "type": "interruption"
                    })
                
                # Add follow-up question if appropriate
                elif self.should_add_follow_up() and content_type in ["complex", "technical", "general"]:
                    follow_up = self.get_follow_up_question(other_speaker, content_type)
                    interactions.append({
                        "speaker": other_speaker,
                        "text": follow_up,
                        "type": "follow_up"
                    })
                
                # Add agreement if appropriate
                elif self.should_add_agreement():
                    agreement = self.get_agreement_sound()
                    interactions.append({
                        "speaker": other_speaker,
                        "text": agreement,
                        "type": "agreement"
                    })
        
        return interactions
    
    def _generate_expert_response(self, interviewer_text: str, content_type: str) -> str:
        """Generate appropriate expert response based on interviewer's input"""
        if content_type == "technical":
            responses = [
                "From a technical standpoint, this involves a sophisticated approach where...",
                "The key insight here is that the algorithm leverages...",
                "What makes this particularly interesting is the implementation of...",
                "The methodology demonstrates significant improvements in..."
            ]
        elif content_type == "complex":
            responses = [
                "Let me break this down into key components...",
                "The experimental setup reveals several important findings...",
                "What we're seeing in the data is a clear pattern where...",
                "The results demonstrate that..."
            ]
        else:
            responses = [
                "That's an excellent question. The research shows...",
                "What's particularly noteworthy about this work is...",
                "The authors' approach addresses this by...",
                "The implications of this research are..."
            ]
        
        import random
        return random.choice(responses)
    
    def _generate_adversarial_response(self, current_text: str, speaker: str, style_config: Dict) -> str:
        """Generate adversarial response for debate format with natural balance"""
        import random
        
        # Get host dynamics for current speaker
        host_key = "host1" if speaker == "host1" else "host2"
        host_config = style_config["host_dynamics"][host_key]
        flow_config = style_config["conversation_flow"]
        
        # Determine if this should be agreement or opposition
        agreement_rate = flow_config.get("agreement_rate", 0.3)
        should_agree = random.random() < agreement_rate
        
        if should_agree:
            # Generate natural agreement
            agreement_patterns = host_config.get("agreement_patterns", [
                "You know what, you're absolutely right about that.",
                "That's actually a good point.",
                "I have to agree with you there.",
                "That's pretty convincing.",
                "You've got me there."
            ])
            agreement = random.choice(agreement_patterns)
            
            # Add follow-up thought
            typical_reactions = host_config.get("typical_reactions", [])
            if typical_reactions:
                follow_up = random.choice(typical_reactions)
                return f"{agreement} {follow_up}"
            return agreement
        else:
            # Generate natural opposition
            opposition_patterns = host_config.get("opposition_patterns", [
                "But here's where I disagree...",
                "I just don't buy that argument because...",
                "That's where you lose me...",
                "I think you're being too harsh here...",
                "That sounds great in theory, but..."
            ])
            opposition = random.choice(opposition_patterns)
            
            # Add reasoning
            typical_reactions = host_config.get("typical_reactions", [])
            if typical_reactions:
                reasoning = random.choice(typical_reactions)
                return f"{opposition} {reasoning}"
            return opposition
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of conversation patterns used"""
        return {
            "style": self.style_name,
            "total_segments": self.segment_count,
            "speakers_used": list(set(item["speaker"] for item in self.conversation_history)),
            "content_types": list(set(item["content_type"] for item in self.conversation_history)),
            "host_roles": self.host_roles
        }
