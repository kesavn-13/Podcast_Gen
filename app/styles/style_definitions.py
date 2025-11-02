"""
Podcast Style Definitions
Defines 5 core authentic podcast conversation styles with host dynamics
"""

from typing import Dict, List, Any

PODCAST_STYLES: Dict[str, Dict[str, Any]] = {
    "layperson": {
        "name": "Layperson-Friendly",
        "description": "Friendly, accessible discussion making complex topics approachable for everyone",
        "use_case": "General audience, avoiding jargon, everyday analogies, personal relevance",
        "host_dynamics": {
            "host1": {
                "role": "curious_everyman",
                "personality": "asks the questions regular people would ask, seeks clarity",
                "speech_rate": 130,
                "voice_energy": "warm-curious",
                "typical_reactions": [
                    "Okay, but what does that actually mean?",
                    "So basically...",
                    "Wait, let me make sure I understand...",
                    "How does this affect regular people?",
                    "That's pretty cool, but..."
                ],
                "question_patterns": [
                    "Can you put that in everyday terms?",
                    "What would this look like in real life?",
                    "Why should I care about this?",
                    "How is this different from what we have now?"
                ],
                "transitions": [
                    "You know what I'm wondering...",
                    "That reminds me of...",
                    "Speaking of everyday life..."
                ]
            },
            "host2": {
                "role": "friendly_explainer",
                "personality": "patient teacher, uses analogies, makes complex simple",
                "speech_rate": 125,
                "voice_energy": "warm-encouraging",
                "typical_reactions": [
                    "Good question! Let me put it this way...",
                    "Think about it like this...",
                    "Here's why that's exciting...",
                    "What they discovered was...",
                    "In everyday terms..."
                ],
                "explanation_patterns": [
                    "The researchers found...",
                    "Studies show...",
                    "What this means for you is...",
                    "Imagine if..."
                ],
                "transitions": [
                    "Now, I know that sounds complicated, but...",
                    "Here's why this matters to you...",
                    "Think about it like this..."
                ]
            }
        },
        "conversation_flow": {
            "interruptions": 0.1,
            "agreement_sounds": 0.35,
            "follow_up_questions": 0.5,
            "personal_reactions": 0.3,
            "pace": "relaxed",
            "transition_style": "gentle"
        }
    },
    
    "classroom": {
        "name": "Classroom Teaching",
        "description": "Patient, pedagogical discussion building understanding step-by-step",
        "use_case": "Educational content, learning objectives, concept building, student-friendly",
        "host_dynamics": {
            "host1": {
                "role": "curious_student",
                "personality": "asks for clarification, checks understanding, seeks examples",
                "speech_rate": 135,
                "voice_energy": "engaged-learning",
                "typical_reactions": [
                    "Can you explain that in simpler terms?",
                    "So if I understand correctly...",
                    "Can you give us a concrete example?",
                    "How does this connect to what we learned earlier?",
                    "Let me see if I've got this right..."
                ],
                "question_patterns": [
                    "What does that mean exactly?",
                    "How does this work in practice?",
                    "Can you walk us through that step-by-step?",
                    "Why is this important to understand?"
                ],
                "transitions": [
                    "Building on that...",
                    "Now I'm curious about...",
                    "That makes me think..."
                ]
            },
            "host2": {
                "role": "patient_teacher",
                "personality": "systematic explainer, uses examples, checks for understanding",
                "speech_rate": 140,
                "voice_energy": "steady-supportive",
                "typical_reactions": [
                    "Of course! Imagine you have...",
                    "That's right, and here's why that matters...",
                    "Great question. Let me break it down...",
                    "Think of it this way...",
                    "Exactly! And according to the paper..."
                ],
                "explanation_patterns": [
                    "The authors explain on page X...",
                    "Looking at Figure 3, we can see...",
                    "The research demonstrates...",
                    "Step by step, here's what happens..."
                ],
                "transitions": [
                    "Now that we understand X, let's move to Y...",
                    "This connects to what we learned earlier...",
                    "Building on that concept..."
                ]
            }
        },
        "conversation_flow": {
            "interruptions": 0.05,
            "agreement_sounds": 0.25,
            "follow_up_questions": 0.6,
            "personal_reactions": 0.15,
            "pace": "measured",
            "transition_style": "pedagogical"
        }
    },
    
    "tech_interview": {
        "name": "Tech Deep Dive",
        "description": "In-depth technical discussion with expert insights",
        "use_case": "Technical audience, detailed analysis, expert knowledge",
        "host_dynamics": {
            "host1": {
                "role": "technical_interviewer",
                "personality": "probing questioner, seeks technical depth",
                "speech_rate": 145,
                "voice_energy": "focused",
                "typical_reactions": [
                    "Let's dig deeper into that...",
                    "What's the technical implementation here?",
                    "How does this compare to existing approaches?",
                    "What are the limitations?",
                    "Walk me through the methodology..."
                ],
                "question_patterns": [
                    "Can you explain the algorithm behind this?",
                    "What's the computational complexity?",
                    "How did you validate these results?",
                    "What assumptions are you making?"
                ],
                "transitions": [
                    "From a technical standpoint...",
                    "Looking at the implementation...",
                    "In terms of performance..."
                ]
            },
            "host2": {
                "role": "technical_expert",
                "personality": "detailed explainer, methodology-focused",
                "speech_rate": 140,
                "voice_energy": "measured",
                "typical_reactions": [
                    "The key insight here is...",
                    "From a technical standpoint...",
                    "What we're seeing in the data is...",
                    "The breakthrough comes from...",
                    "If you look at the architecture..."
                ],
                "explanation_patterns": [
                    "The paper demonstrates that...",
                    "The experimental setup involves...",
                    "What's novel about their approach is...",
                    "The results show a significant improvement..."
                ],
                "transitions": [
                    "The technical details show...",
                    "From the data we can see...",
                    "The methodology reveals..."
                ]
            }
        },
        "conversation_flow": {
            "interruptions": 0.08,
            "agreement_sounds": 0.2,
            "follow_up_questions": 0.6,
            "personal_reactions": 0.1,
            "pace": "measured",
            "transition_style": "structured"
        }
    },
    "journal_club": {
        "name": "Journal Club Academic",
        "description": "Scholarly examination with critical methodology focus and literature context",
        "use_case": "Academic audience, peer review style, methodological analysis, clinical implications",
        "host_dynamics": {
            "host1": {
                "role": "methodological_critic",
                "personality": "scrutinizes methodology, asks about validity and limitations",
                "speech_rate": 145,
                "voice_energy": "analytically-focused",
                "typical_reactions": [
                    "What's your assessment of their methodology?",
                    "How do these results compare to previous work?",
                    "One limitation to consider...",
                    "I'm curious about the exclusion criteria...",
                    "That raises questions about external validity..."
                ],
                "question_patterns": [
                    "What's the sample size and power analysis?",
                    "How does this fit with existing literature?",
                    "What are the study limitations?",
                    "Can these results be generalized?",
                    "How robust is the statistical approach?"
                ],
                "transitions": [
                    "From a methodological perspective...",
                    "Considering the literature...",
                    "In terms of validity..."
                ]
            },
            "host2": {
                "role": "literature_synthesizer",
                "personality": "contextualizes findings, discusses clinical implications",
                "speech_rate": 140,
                "voice_energy": "scholarly-measured",
                "typical_reactions": [
                    "The experimental design is solid, however...",
                    "That's an excellent question. The literature shows...",
                    "This builds on previous work by...",
                    "The authors acknowledge that...",
                    "The broader implications suggest..."
                ],
                "explanation_patterns": [
                    "As reported in Table 2...",
                    "The statistical analysis on page X reveals...",
                    "Consistent with findings from previous studies...",
                    "The authors' interpretation is..."
                ],
                "transitions": [
                    "Moving to the results section...",
                    "The literature suggests...",
                    "From a clinical perspective..."
                ]
            }
        },
        "conversation_flow": {
            "interruptions": 0.03,
            "agreement_sounds": 0.15,
            "follow_up_questions": 0.7,
            "personal_reactions": 0.05,
            "pace": "deliberate",
            "transition_style": "scholarly"
        }
    },
    
    "npr_calm": {
        "name": "NPR-Style Thoughtful",
        "description": "Measured, warm discussion building interest through content depth",
        "use_case": "Thoughtful analysis, authoritative but approachable, reflective insights",
        "host_dynamics": {
            "host1": {
                "role": "thoughtful_questioner",
                "personality": "builds understanding gently, no rush, strategic questioning",
                "speech_rate": 130,
                "voice_energy": "calm-curious",
                "typical_reactions": [
                    "So help me understand this...",
                    "And how does that change things?",
                    "What caught my attention about this research...",
                    "Walk us through that discovery...",
                    "If you're following along..."
                ],
                "question_patterns": [
                    "What's particularly interesting here is...",
                    "How should we think about this?",
                    "What does this tell us about...?",
                    "Help me understand why this matters..."
                ],
                "transitions": [
                    "Today we're exploring...",
                    "This builds on something we discussed earlier...",
                    "Let's dig into..."
                ]
            },
            "host2": {
                "role": "measured_expert",
                "personality": "thoughtful explainer, uses strategic pauses, builds to revelations",
                "speech_rate": 125,
                "voice_energy": "calm-authoritative",
                "typical_reactions": [
                    "Well, let me walk through that...",
                    "That's exactly the breakthrough here...",
                    "The authors make a compelling case that...",
                    "What's particularly noteworthy...",
                    "The data shows..."
                ],
                "explanation_patterns": [
                    "According to the authors on page X...",
                    "The paper notes that...",
                    "As they put it in their conclusion...",
                    "For years, we've thought... but this shows..."
                ],
                "transitions": [
                    "Now, what's particularly interesting here is...",
                    "This challenges the conventional wisdom...",
                    "The discovery here is..."
                ]
            }
        },
        "conversation_flow": {
            "interruptions": 0.02,
            "agreement_sounds": 0.2,
            "follow_up_questions": 0.4,
            "personal_reactions": 0.1,
            "pace": "thoughtful",
            "transition_style": "reflective"
        }
    },
    
    "news_flash": {
        "name": "Breaking News Alert",
        "description": "Rapid, urgent coverage of breakthrough research with immediate significance",
        "use_case": "Breaking discoveries, industry disruption, time-sensitive findings, major breakthroughs",
        "host_dynamics": {
            "host1": {
                "role": "breaking_news_anchor",
                "personality": "urgent reporter, focuses on immediate impact and significance",
                "speech_rate": 180,
                "voice_energy": "high-urgent",
                "typical_reactions": [
                    "What does this mean for the industry?",
                    "How quickly will we see impact?",
                    "This is not incremental improvement...",
                    "We're talking months, not years...",
                    "Industry experts are calling this..."
                ],
                "question_patterns": [
                    "What are the immediate implications?",
                    "Who does this disrupt?",
                    "How significant is this breakthrough?",
                    "What should companies do right now?"
                ],
                "transitions": [
                    "Breaking: New research reveals...",
                    "This just in from the world of AI...",
                    "Alert: Breakthrough study shows..."
                ]
            },
            "host2": {
                "role": "rapid_analyst",
                "personality": "fast-paced technical interpreter, focuses on market impact",
                "speech_rate": 175,
                "voice_energy": "high-analytical",
                "typical_reactions": [
                    "This could completely disrupt...",
                    "The numbers don't lie...",
                    "They actually proved that...",
                    "This changes everything about...",
                    "We're looking at a paradigm shift..."
                ],
                "explanation_patterns": [
                    "The study, published today, shows...",
                    "Key findings include...",
                    "Data from the research indicates...",
                    "Benchmark results are mind-blowing..."
                ],
                "transitions": [
                    "And here's what makes this critical...",
                    "But the story gets more significant...",
                    "The implications are staggering..."
                ]
            }
        },
        "conversation_flow": {
            "interruptions": 0.25,
            "agreement_sounds": 0.1,
            "follow_up_questions": 0.5,
            "personal_reactions": 0.2,
            "pace": "rapid",
            "transition_style": "urgent"
        }
    },
    
    "tech_energetic": {
        "name": "Tech Enthusiast",
        "description": "High-energy, excited discussion about cutting-edge technical breakthroughs",
        "use_case": "Technical audience, breakthrough excitement, deep technical enthusiasm, rapid insights",
        "host_dynamics": {
            "host1": {
                "role": "excited_techie",
                "personality": "infectious enthusiasm for technical breakthroughs, rapid-fire excitement",
                "speech_rate": 170,
                "voice_energy": "high-excited",
                "typical_reactions": [
                    "Okay, break this down for me...",
                    "No way, really?",
                    "This is absolutely wild...",
                    "I'm geeking out over this paper...",
                    "You're not going to believe this..."
                ],
                "question_patterns": [
                    "How insane are these benchmarks?",
                    "What's the secret sauce here?",
                    "This changes everything, right?",
                    "Show me the numbers!"
                ],
                "transitions": [
                    "Alright, buckle up because...",
                    "But here's where it gets crazy...",
                    "Wait, wait, wait - there's more..."
                ]
            },
            "host2": {
                "role": "technical_enthusiast",
                "personality": "deep technical knowledge with infectious excitement",
                "speech_rate": 165,
                "voice_energy": "high-technical",
                "typical_reactions": [
                    "Dude, this is insane...",
                    "I'm telling you, this is revolutionary...",
                    "The benchmark results are mind-blowing...",
                    "Check this out - page X literally says...",
                    "This is going to change everything..."
                ],
                "explanation_patterns": [
                    "They actually proved that...",
                    "The numbers don't lie...",
                    "Look at those FLOPS reductions...",
                    "This completely changes the game because..."
                ],
                "transitions": [
                    "And then - plot twist...",
                    "This is huge!",
                    "The implications are staggering..."
                ]
            }
        },
        "conversation_flow": {
            "interruptions": 0.3,
            "agreement_sounds": 0.15,
            "follow_up_questions": 0.4,
            "personal_reactions": 0.4,
            "pace": "rapid",
            "transition_style": "energetic"
        }
    },
    
    "investigative": {
        "name": "Investigative Analysis",
        "description": "Probing examination with healthy skepticism",
        "use_case": "Critical analysis, controversial topics, fact-checking",
        "host_dynamics": {
            "host1": {
                "role": "skeptical_investigator",
                "personality": "questions assumptions, seeks evidence",
                "speech_rate": 150,
                "voice_energy": "probing",
                "typical_reactions": [
                    "But wait, let's question that assumption...",
                    "How do we know this is actually true?",
                    "What evidence supports this claim?",
                    "I'm seeing some red flags here...",
                    "Let's dig into the data..."
                ],
                "question_patterns": [
                    "Who funded this research?",
                    "What conflicts of interest exist?",
                    "How was the data collected?",
                    "What aren't they telling us?"
                ],
                "transitions": [
                    "But here's what concerns me...",
                    "Let's investigate further...",
                    "We need to question..."
                ]
            },
            "host2": {
                "role": "evidence_presenter",
                "personality": "fact-focused, presents multiple perspectives",
                "speech_rate": 145,
                "voice_energy": "analytical",
                "typical_reactions": [
                    "The data shows...",
                    "From another perspective...",
                    "Here's what we know for certain...",
                    "The evidence is mixed on this...",
                    "Multiple studies indicate..."
                ],
                "explanation_patterns": [
                    "According to the research...",
                    "Independent verification shows...",
                    "Cross-referencing with other studies...",
                    "The peer review process revealed..."
                ],
                "transitions": [
                    "The evidence shows...",
                    "Independent sources confirm...",
                    "Cross-checking reveals..."
                ]
            }
        },
        "conversation_flow": {
            "interruptions": 0.12,
            "agreement_sounds": 0.1,
            "follow_up_questions": 0.7,
            "personal_reactions": 0.15,
            "pace": "dynamic",
            "transition_style": "investigative"
        }
    },
    
    "debate_format": {
        "name": "Balanced Debate",
        "description": "Natural debate with opposition and agreement, like real human conversation",
        "use_case": "Controversial topics, balanced viewpoints, realistic debates with natural flow",
        "host_dynamics": {
            "host1": {
                "role": "research_advocate", 
                "personality": "supports research but acknowledges valid criticism, natural conversational style",
                "speech_rate": 150,
                "voice_energy": "engaged-natural",
                "typical_reactions": [
                    "Look, I get what you're saying, but...",
                    "Okay, fair point, though I think...",
                    "I hear you, but here's the thing...",
                    "You're right about that part, but...",
                    "That's actually a good question..."
                ],
                "agreement_patterns": [
                    "You know what, you're absolutely right about that.",
                    "I'll give you that one.",
                    "That's a fair criticism.",
                    "Good point, I hadn't thought of it that way.",
                    "You've got me there."
                ],
                "opposition_patterns": [
                    "But here's where I disagree...",
                    "I just don't buy that argument because...",
                    "Come on, that's not really fair...",
                    "I think you're being too harsh here...",
                    "That's where you lose me...",
                    "Hold on, that's not accurate...",
                    "Actually, I think you're wrong about that...",
                    "No, that's missing the real issue...",
                    "That's not what the data shows..."
                ],
                "question_patterns": [
                    "But don't you think the benefits outweigh that?",
                    "How do you explain these results then?",
                    "Isn't that being a bit pessimistic?",
                    "What would convince you otherwise?"
                ],
                "transitions": [
                    "Here's what I think...",
                    "The way I see it...",
                    "Look at it this way..."
                ]
            },
            "host2": {
                "role": "research_skeptic",
                "personality": "questions research but gives credit where due, natural conversational style",
                "speech_rate": 148,
                "voice_energy": "analytical-natural",
                "typical_reactions": [
                    "I'll admit, that's pretty impressive, but...",
                    "Okay, sure, but what about...",
                    "That's interesting, though I'm still concerned about...",
                    "Right, but the real question is...",
                    "I see what they're trying to do here..."
                ],
                "agreement_patterns": [
                    "Actually, that's a really good point.",
                    "I have to agree with you there.",
                    "You're right, that is significant.",
                    "That's actually pretty convincing.",
                    "Okay, I'll concede that."
                ],
                "opposition_patterns": [
                    "But that's exactly my concern...",
                    "I just don't see how that's realistic...",
                    "That sounds great in theory, but...",
                    "I'm just not convinced because...",
                    "That's where I think you're wrong...",
                    "Wait, that's not right...",
                    "Actually, you're overlooking something important...",
                    "No, I disagree with that interpretation...",
                    "That's actually backwards..."
                ],
                "explanation_patterns": [
                    "The thing is...",
                    "What worries me is...",
                    "The problem I see is...",
                    "My concern is that..."
                ],
                "transitions": [
                    "But here's my issue...",
                    "The reality is...",
                    "What I'm seeing is..."
                ]
            }
        },
        "conversation_flow": {
            "interruptions": 0.25,
            "agreement_sounds": 0.15,
            "follow_up_questions": 0.5,
            "personal_reactions": 0.3,
            "pace": "natural",
            "transition_style": "conversational",
            "agreement_rate": 0.15,
            "opposition_rate": 0.85
        }
    }
}


def get_available_styles() -> List[str]:
    """Get list of available podcast style names"""
    return list(PODCAST_STYLES.keys())


def get_style_config(style_name: str) -> Dict[str, Any]:
    """Get configuration for a specific style"""
    if style_name not in PODCAST_STYLES:
        available = ', '.join(get_available_styles())
        raise ValueError(f"Style '{style_name}' not found. Available styles: {available}")
    
    return PODCAST_STYLES[style_name]


def get_style_description(style_name: str) -> str:
    """Get human-readable description of a style"""
    style = get_style_config(style_name)
    return f"{style['name']}: {style['description']} - {style['use_case']}"


def list_all_styles() -> Dict[str, str]:
    """Get all styles with their descriptions"""
    return {
        name: f"{config['name']}: {config['description']}"
        for name, config in PODCAST_STYLES.items()
    }


def get_style_summary() -> str:
    """Get a formatted summary of all available styles"""
    summary = "🎭 Available Podcast Styles:\n\n"
    for name, config in PODCAST_STYLES.items():
        summary += f"• **{config['name']}** (`{name}`)\n"
        summary += f"  {config['description']}\n"
        summary += f"  Best for: {config['use_case']}\n\n"
    return summary
