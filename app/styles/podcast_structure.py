"""
Podcast Structure Elements
Defines intros, outros, and ad breaks for different podcast styles
"""

from typing import Dict, List, Any

PODCAST_STRUCTURE: Dict[str, Dict[str, Any]] = {
    "layperson": {
        "intro": {
            "greeting": "Hey there, curious minds! Welcome back to Making Sense of Science.",
            "host_introduction": "I'm Sarah, and as always, I'm joined by my co-host Alex.",
            "episode_setup": "Today we're diving into some fascinating research that might just change how we think about {topic}.",
            "audience_hook": "Whether you're a science newbie or just love learning cool stuff, we're going to break this down in a way that actually makes sense.",
            "transition": "So grab your favorite drink, get comfortable, and let's explore this together!"
        },
        "ad_break": {
            "lead_in": "Alright folks, we're going to take a quick breather here.",
            "break_message": "This is the perfect time to grab a snack, stretch those legs, or maybe share this episode with a friend who loves learning new things.",
            "return_tease": "When we come back, we'll dive into the really exciting part - what this means for you and me in everyday life.",
            "closing": "We'll be right back in just a moment!"
        },
        "outro": {
            "summary": "So there you have it - {topic} explained in a way that hopefully made sense to all of us!",
            "key_takeaway": "The big picture here is that science keeps finding ways to make our lives better, even in ways we might not expect.",
            "engagement": "What did you think? Did this blow your mind as much as it did ours? Drop us a comment and let us know!",
            "next_episode": "Next week, we're exploring another mind-bending discovery, so make sure to subscribe so you don't miss it.",
            "farewell": "Until then, keep being curious, keep asking questions, and remember - science is for everyone. Thanks for listening!"
        }
    },
    
    "classroom": {
        "intro": {
            "greeting": "Good morning, students! Welcome to today's Science Learning Session.",
            "host_introduction": "I'm Dr. Sarah, your instructor, and I'm joined by Dr. Alex, our teaching assistant.",
            "episode_setup": "In today's lesson, we'll be examining a groundbreaking study on {topic}.",
            "audience_hook": "By the end of this session, you'll have a solid understanding of the methodology, results, and implications of this research.",
            "transition": "Let's begin with our learning objectives and dive right into the material."
        },
        "ad_break": {
            "lead_in": "Let's pause here for a moment to review what we've covered so far.",
            "break_message": "This is a good time to take notes, review the key concepts we've discussed, or ask yourself if you have any questions about the material.",
            "return_tease": "When we resume, we'll move on to the experimental results section - make sure you understand the methodology we just covered.",
            "closing": "Take a few minutes to process this information, and we'll continue shortly."
        },
        "outro": {
            "summary": "To summarize today's lesson on {topic}, we've covered the background, methodology, results, and implications.",
            "key_takeaway": "The most important concept to remember is how this research advances our understanding in this field.",
            "engagement": "For homework, I want you to think about how you might apply these findings or what questions you'd ask if you were peer-reviewing this paper.",
            "next_episode": "Next week, we'll build on today's concepts as we examine related research in this area.",
            "farewell": "Class dismissed! Keep studying, keep questioning, and remember that every expert was once a beginner."
        }
    },
    
    "tech_interview": {
        "intro": {
            "greeting": "Welcome to Deep Tech Analysis, the podcast where we dissect cutting-edge research.",
            "host_introduction": "I'm Sarah, your host, and I'm here with Alex, our technical expert.",
            "episode_setup": "Today we're doing a deep dive into a fascinating paper on {topic}.",
            "audience_hook": "If you're a developer, researcher, or just love getting into the technical weeds, this episode is for you.",
            "transition": "Let's jump straight into the architecture and see what makes this research tick."
        },
        "ad_break": {
            "lead_in": "Alright, let's take a quick technical timeout here.",
            "break_message": "Perfect time to check out the paper yourself, pull up those GitHub repos we mentioned, or maybe start thinking about how you'd implement this.",
            "return_tease": "Coming up, we'll dive into the performance benchmarks and discuss the real-world implications.",
            "closing": "Back in just a moment with more technical insights."
        },
        "outro": {
            "summary": "That wraps up our technical analysis of {topic} - from architecture to implementation details.",
            "key_takeaway": "The key innovation here is how they solved the performance bottleneck while maintaining accuracy.",
            "engagement": "What's your take on their approach? Hit us up on Twitter or LinkedIn with your thoughts on the technical trade-offs.",
            "next_episode": "Next week, we're analyzing another breakthrough in machine learning optimization.",
            "farewell": "Keep building, keep innovating, and remember - the best code is code that solves real problems. Until next time!"
        }
    },
    
    "journal_club": {
        "intro": {
            "greeting": "Welcome to Academic Journal Club, where we critically examine the latest research.",
            "host_introduction": "I'm Dr. Sarah, and I'm joined by Dr. Alex for today's peer review discussion.",
            "episode_setup": "Today we're reviewing a recent publication on {topic}.",
            "audience_hook": "Whether you're a clinician, researcher, or academic, we'll examine this paper with the rigor it deserves.",
            "transition": "Let's begin with our methodological assessment and work through the paper systematically."
        },
        "ad_break": {
            "lead_in": "Let's pause our analysis here for a moment.",
            "break_message": "This would be an excellent time to access the paper yourself and review the figures we've discussed so far.",
            "return_tease": "When we return, we'll examine the statistical analysis and discuss the clinical implications.",
            "closing": "We'll resume our peer review discussion shortly."
        },
        "outro": {
            "summary": "To conclude our journal club review of {topic}, we've assessed the methodology, results, and broader implications.",
            "key_takeaway": "The significance of this work lies in its potential to advance clinical practice, though several limitations warrant consideration.",
            "engagement": "We'd love to hear your peer review thoughts - what aspects would you have questioned during review?",
            "next_episode": "Next session, we'll be reviewing a meta-analysis that builds on today's topic.",
            "farewell": "Keep questioning, keep reviewing, and remember that good science thrives on healthy skepticism. Until next time."
        }
    },
    
    "npr_calm": {
        "intro": {
            "greeting": "You're listening to Science Discoveries. I'm Sarah Kowalski.",
            "host_introduction": "Today, I'm joined by researcher Alex Chen to explore a study that's been making waves in the scientific community.",
            "episode_setup": "It's about {topic}, and the implications are more far-reaching than you might expect.",
            "audience_hook": "This is one of those discoveries that might seem technical at first, but it touches on something much more fundamental about how we understand the world.",
            "transition": "Let's start from the beginning and see where this research takes us."
        },
        "ad_break": {
            "lead_in": "We'll be right back with more of our conversation about {topic}.",
            "break_message": "I'm Sarah Kowalski, and you're listening to Science Discoveries.",
            "return_tease": "",
            "closing": ""
        },
        "outro": {
            "summary": "That was researcher Alex Chen, discussing the breakthrough research on {topic}.",
            "key_takeaway": "What strikes me most about this work is how it challenges us to think differently about problems we thought we understood.",
            "engagement": "If this story resonated with you, we'd love to hear your thoughts.",
            "next_episode": "Next time on Science Discoveries, we'll explore how artificial intelligence is changing the way we approach climate science.",
            "farewell": "I'm Sarah Kowalski. Thanks for listening."
        }
    },
    
    "news_flash": {
        "intro": {
            "greeting": "BREAKING: This is Science Alert with your hosts Sarah and Alex.",
            "host_introduction": "I'm Sarah Martinez, and with me is tech analyst Alex Rodriguez.",
            "episode_setup": "We're bringing you urgent coverage of groundbreaking research on {topic} that just hit the scientific community.",
            "audience_hook": "This is the kind of breakthrough that's going to change everything, and we mean everything.",
            "transition": "Let's get straight to the details because this news is already making waves across the industry."
        },
        "ad_break": {
            "lead_in": "Hold that thought - we need to take a quick break, but don't go anywhere!",
            "break_message": "This is developing news, and we're tracking reactions from industry leaders as we speak.",
            "return_tease": "Coming up next: What this means for companies, investors, and everyone using this technology.",
            "closing": "Stay with us - the biggest implications are still coming!"
        },
        "outro": {
            "summary": "That's our breaking coverage of the {topic} breakthrough that's reshaping the industry as we speak.",
            "key_takeaway": "Bottom line: we're witnessing a paradigm shift that will ripple through multiple sectors.",
            "engagement": "How do you think this will impact your work? Let us know - we're monitoring social media for your reactions.",
            "next_episode": "We'll have more breaking science news tomorrow, plus follow-up coverage on today's story.",
            "farewell": "This has been Science Alert. Stay informed, stay ahead of the curve!"
        }
    },
    
    "tech_energetic": {
        "intro": {
            "greeting": "What's up, tech enthusiasts! Welcome to another episode of Code & Coffee!",
            "host_introduction": "I'm Sarah, your resident AI geek, and I'm here with Alex, our machine learning wizard.",
            "episode_setup": "Today we're absolutely geeking out over this insane research paper on {topic}.",
            "audience_hook": "If you love bleeding-edge tech and mind-blowing algorithms, you're going to lose your mind over this episode!",
            "transition": "So grab your energy drink, fire up your IDE, and let's dive into some seriously cool tech!"
        },
        "ad_break": {
            "lead_in": "Okay, okay, we need to pause for a second because our brains are literally melting from all this awesome tech!",
            "break_message": "Perfect time to star that GitHub repo, share this episode with your dev friends, or maybe start sketching out your own implementation.",
            "return_tease": "When we come back, we're diving into the performance numbers that are going to blow your mind!",
            "closing": "BRB - more incredible tech coming your way!"
        },
        "outro": {
            "summary": "Dude, that was {topic} and it was absolutely incredible! My brain is still processing all those performance gains!",
            "key_takeaway": "The main thing here is that we're literally watching the future of technology unfold before our eyes.",
            "engagement": "Drop us a comment, tweet at us, slide into our DMs - we want to hear what you're building with this tech!",
            "next_episode": "Next week, we're covering another mind-bending paper that's going to make your jaw drop.",
            "farewell": "Keep coding, keep innovating, and remember - the future is written in code! Peace out, tech fam!"
        }
    },
    
    "investigative": {
        "intro": {
            "greeting": "Welcome to Research Under the Microscope, where we investigate the science behind the headlines.",
            "host_introduction": "I'm investigative journalist Sarah Kim, and I'm joined by fact-checker Alex Thompson.",
            "episode_setup": "Today we're examining claims made in a recent study about {topic}.",
            "audience_hook": "We're going to dig deep, ask tough questions, and separate the facts from the hype.",
            "transition": "Let's start by looking at who funded this research and what they might have to gain."
        },
        "ad_break": {
            "lead_in": "We're going to pause our investigation here, but we're just getting started.",
            "break_message": "This is the perfect time to fact-check what we've discussed so far - don't take our word for it, verify it yourself.",
            "return_tease": "Coming up: we'll examine the data that doesn't make it into the headlines and ask the questions others won't.",
            "closing": "More investigative analysis coming right up."
        },
        "outro": {
            "summary": "That concludes our investigation into {topic} - we've examined the evidence, questioned the claims, and verified the facts.",
            "key_takeaway": "The truth, as always, is more nuanced than the headlines suggest.",
            "engagement": "If you've found inconsistencies or have additional evidence, we want to hear from you.",
            "next_episode": "Next week, we're investigating claims about breakthrough battery technology that seems too good to be true.",
            "farewell": "Keep questioning, keep investigating, and remember - the truth matters. Until next time."
        }
    },
    
    "debate_format": {
        "intro": {
            "greeting": "Welcome to Science Showdown, where great minds don't always think alike!",
            "host_introduction": "I'm Sarah, and I'm here with Alex, and as usual, we probably won't agree on everything.",
            "episode_setup": "Today we're debating the merits and limitations of groundbreaking research on {topic}.",
            "audience_hook": "Buckle up, because we're about to dive deep into a topic that's got scientists talking, arguing, and everything in between.",
            "transition": "Let's jump right into the controversy and see where this heated discussion takes us!"
        },
        "ad_break": {
            "lead_in": "Alright, timeout! We need to take a breather before we completely tear each other apart over this research!",
            "break_message": "While we're cooling down, this is your chance to pick a side - are you team Sarah or team Alex?",
            "return_tease": "When we come back, we're settling this once and for all with the experimental evidence.",
            "closing": "Don't touch that dial - the debate is about to get even more intense!"
        },
        "outro": {
            "summary": "Well, that was {topic}, and as you heard, Sarah and I still can't agree on everything!",
            "key_takeaway": "But that's the beauty of science - healthy debate and disagreement drive us toward better understanding.",
            "engagement": "So what's your take? Who won this debate? Let us know in the comments - we love a good argument!",
            "next_episode": "Next week, we're tackling another controversial topic that's sure to get us fired up again.",
            "farewell": "Keep debating, keep questioning, and remember - the best ideas survive the toughest challenges!"
        }
    }
}

def get_podcast_structure(style_name: str) -> Dict[str, Any]:
    """Get podcast structure elements for a specific style"""
    if style_name not in PODCAST_STRUCTURE:
        # Return a generic structure if style not found
        return {
            "intro": {
                "greeting": "Welcome to our podcast!",
                "host_introduction": "I'm Sarah, and I'm joined by Alex.",
                "episode_setup": "Today we're discussing {topic}.",
                "audience_hook": "Let's dive into this fascinating research.",
                "transition": "Let's get started!"
            },
            "ad_break": {
                "lead_in": "Let's take a quick break.",
                "break_message": "We'll be right back!",
                "return_tease": "More coming up next.",
                "closing": "Stay tuned!"
            },
            "outro": {
                "summary": "That's our discussion on {topic}.",
                "key_takeaway": "Thanks for listening.",
                "engagement": "Let us know what you think!",
                "next_episode": "Join us next time.",
                "farewell": "Until next time!"
            }
        }
    
    return PODCAST_STRUCTURE[style_name]

def format_podcast_segment(segment_type: str, style_name: str, topic: str = "") -> str:
    """Format a specific podcast segment with topic substitution"""
    structure = get_podcast_structure(style_name)
    
    if segment_type not in structure:
        return ""
    
    segment = structure[segment_type]
    formatted_lines = []
    
    for key, text in segment.items():
        if text:  # Only add non-empty text
            formatted_text = text.format(topic=topic) if "{topic}" in text else text
            formatted_lines.append(formatted_text)
    
    return " ".join(formatted_lines)

def should_add_ad_break(segment_number: int, total_segments: int) -> bool:
    """Determine if an ad break should be added after this segment"""
    # Add ad break roughly in the middle of longer episodes
    if total_segments >= 4:
        middle_point = total_segments // 2
        return segment_number == middle_point
    return False
