"""
Podcast Styles Module
Provides authentic podcast conversation styles and host dynamics
"""

from .style_definitions import PODCAST_STYLES, get_available_styles, get_style_config, list_all_styles
from .conversation_engine import ConversationEngine
from .text_processor import TextProcessor

__all__ = [
    'PODCAST_STYLES',
    'get_available_styles', 
    'get_style_config',
    'list_all_styles',
    'ConversationEngine',
    'TextProcessor'
]