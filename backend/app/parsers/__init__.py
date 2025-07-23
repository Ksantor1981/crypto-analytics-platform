"""
Parsers Module - Plugin-based channel parsers system
Part of Task 2.1.1: Рефакторинг системы парсеров
"""

from .base_parser import (
    BaseChannelParser,
    ChannelType,
    SignalType,
    ParsedSignal,
    ChannelConfig
)

from .parser_registry import (
    ParserRegistry,
    parser_registry,
    register_parser,
    create_parser,
    get_parser
)

# Import available parsers (they will auto-register)
try:
    from .telegram_parser import TelegramParser
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

try:
    from .reddit_parser import RedditParser
    REDDIT_AVAILABLE = True
except ImportError:
    REDDIT_AVAILABLE = False

try:
    from .rss_parser import RSSParser
    RSS_AVAILABLE = True
except ImportError:
    RSS_AVAILABLE = False

try:
    from .twitter_parser import TwitterParser
    TWITTER_AVAILABLE = True
except ImportError:
    TWITTER_AVAILABLE = False

try:
    from .tradingview_parser import TradingViewParser
    TRADINGVIEW_AVAILABLE = True
except ImportError:
    TRADINGVIEW_AVAILABLE = False

__all__ = [
    # Base classes
    'BaseChannelParser',
    'ChannelType',
    'SignalType', 
    'ParsedSignal',
    'ChannelConfig',
    
    # Registry
    'ParserRegistry',
    'parser_registry',
    'register_parser',
    'create_parser',
    'get_parser',
    
    # Parsers
    'TelegramParser' if TELEGRAM_AVAILABLE else None,
    'RedditParser' if REDDIT_AVAILABLE else None,
    'RSSParser' if RSS_AVAILABLE else None,
    'TwitterParser' if TWITTER_AVAILABLE else None,
    'TradingViewParser' if TRADINGVIEW_AVAILABLE else None,
]

# Remove None values
__all__ = [item for item in __all__ if item is not None]
