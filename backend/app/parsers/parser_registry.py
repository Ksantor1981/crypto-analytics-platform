"""
Parser Registry - Central system for managing all channel parsers
Part of Task 2.1.1: Система регистрации и конфигурации парсеров
"""
from typing import Dict, List, Type, Optional, Any
from datetime import datetime
import logging
import asyncio

from .base_parser import BaseChannelParser, ChannelType, ChannelConfig, ParsedSignal

logger = logging.getLogger(__name__)

class ParserRegistry:
    """
    Central registry for all channel parsers
    
    Manages parser registration, configuration, and lifecycle
    """
    
    def __init__(self):
        self._parser_classes: Dict[ChannelType, Type[BaseChannelParser]] = {}
        self._active_parsers: Dict[str, BaseChannelParser] = {}
        self._parser_configs: Dict[str, ChannelConfig] = {}
        
    def register_parser(self, channel_type: ChannelType, parser_class: Type[BaseChannelParser]) -> None:
        """
        Register a parser class for a specific channel type
        
        Args:
            channel_type: Type of channel this parser handles
            parser_class: Parser class to register
        """
        if not issubclass(parser_class, BaseChannelParser):
            raise ValueError(f"Parser class must inherit from BaseChannelParser")
            
        self._parser_classes[channel_type] = parser_class
        logger.info(f"Registered parser {parser_class.__name__} for {channel_type.value}")
    
    def unregister_parser(self, channel_type: ChannelType) -> None:
        """
        Unregister a parser for a specific channel type
        
        Args:
            channel_type: Type of channel to unregister
        """
        if channel_type in self._parser_classes:
            del self._parser_classes[channel_type]
            logger.info(f"Unregistered parser for {channel_type.value}")
    
    def create_parser(self, config: ChannelConfig) -> BaseChannelParser:
        """
        Create a parser instance from configuration
        
        Args:
            config: Channel configuration
            
        Returns:
            Parser instance
            
        Raises:
            ValueError: If no parser registered for channel type
        """
        if config.channel_type not in self._parser_classes:
            raise ValueError(f"No parser registered for channel type: {config.channel_type.value}")
        
        parser_class = self._parser_classes[config.channel_type]
        parser = parser_class(config)
        
        # Validate configuration
        if not parser.validate_config():
            raise ValueError(f"Invalid configuration for parser {parser_class.__name__}")
        
        # Store parser and config
        parser_key = f"{config.channel_type.value}_{config.name}"
        self._active_parsers[parser_key] = parser
        self._parser_configs[parser_key] = config
        
        logger.info(f"Created parser {parser_class.__name__} for channel {config.name}")
        return parser
    
    def get_parser(self, channel_type: ChannelType, channel_name: str) -> Optional[BaseChannelParser]:
        """
        Get an active parser instance
        
        Args:
            channel_type: Type of channel
            channel_name: Name of the channel
            
        Returns:
            Parser instance if found, None otherwise
        """
        parser_key = f"{channel_type.value}_{channel_name}"
        return self._active_parsers.get(parser_key)
    
    def remove_parser(self, channel_type: ChannelType, channel_name: str) -> bool:
        """
        Remove and disconnect a parser
        
        Args:
            channel_type: Type of channel
            channel_name: Name of the channel
            
        Returns:
            True if parser was removed, False if not found
        """
        parser_key = f"{channel_type.value}_{channel_name}"
        
        if parser_key in self._active_parsers:
            parser = self._active_parsers[parser_key]
            
            # Disconnect parser if connected
            if parser.is_connected:
                try:
                    asyncio.create_task(parser.disconnect())
                except Exception as e:
                    logger.error(f"Error disconnecting parser {parser}: {e}")
            
            # Remove from registry
            del self._active_parsers[parser_key]
            del self._parser_configs[parser_key]
            
            logger.info(f"Removed parser for {channel_type.value}_{channel_name}")
            return True
        
        return False
    
    def list_registered_types(self) -> List[ChannelType]:
        """
        Get list of registered channel types
        
        Returns:
            List of registered channel types
        """
        return list(self._parser_classes.keys())
    
    def list_active_parsers(self) -> List[Dict[str, Any]]:
        """
        Get list of active parsers with their status
        
        Returns:
            List of parser information dictionaries
        """
        parsers_info = []
        
        for parser_key, parser in self._active_parsers.items():
            config = self._parser_configs[parser_key]
            
            parsers_info.append({
                "key": parser_key,
                "name": config.name,
                "channel_type": config.channel_type.value,
                "url": config.url,
                "enabled": config.enabled,
                "is_connected": parser.is_connected,
                "last_error": parser.last_error,
                "class_name": parser.__class__.__name__
            })
        
        return parsers_info
    
    async def connect_all_parsers(self) -> Dict[str, bool]:
        """
        Connect all active parsers
        
        Returns:
            Dictionary mapping parser keys to connection success status
        """
        results = {}
        
        for parser_key, parser in self._active_parsers.items():
            config = self._parser_configs[parser_key]
            
            if not config.enabled:
                results[parser_key] = False
                continue
            
            try:
                success = await parser.connect()
                results[parser_key] = success
                
                if success:
                    logger.info(f"Connected parser {parser_key}")
                else:
                    logger.warning(f"Failed to connect parser {parser_key}")
                    
            except Exception as e:
                logger.error(f"Error connecting parser {parser_key}: {e}")
                results[parser_key] = False
        
        return results
    
    async def disconnect_all_parsers(self) -> None:
        """Disconnect all active parsers"""
        for parser_key, parser in self._active_parsers.items():
            if parser.is_connected:
                try:
                    await parser.disconnect()
                    logger.info(f"Disconnected parser {parser_key}")
                except Exception as e:
                    logger.error(f"Error disconnecting parser {parser_key}: {e}")
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Perform health check on all active parsers
        
        Returns:
            Dictionary mapping parser keys to health status
        """
        health_results = {}
        
        for parser_key, parser in self._active_parsers.items():
            try:
                health_status = await parser.health_check()
                health_results[parser_key] = health_status
            except Exception as e:
                logger.error(f"Health check failed for parser {parser_key}: {e}")
                health_results[parser_key] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        return health_results
    
    async def collect_signals_from_all(self, limit_per_parser: int = 100) -> Dict[str, List[ParsedSignal]]:
        """
        Collect signals from all active and connected parsers
        
        Args:
            limit_per_parser: Maximum signals to collect from each parser
            
        Returns:
            Dictionary mapping parser keys to lists of signals
        """
        all_signals = {}
        
        for parser_key, parser in self._active_parsers.items():
            config = self._parser_configs[parser_key]
            
            if not config.enabled or not parser.is_connected:
                continue
            
            try:
                signals = await parser.parse_messages(limit=limit_per_parser)
                all_signals[parser_key] = signals
                
                logger.info(f"Collected {len(signals)} signals from {parser_key}")
                
            except Exception as e:
                logger.error(f"Error collecting signals from {parser_key}: {e}")
                all_signals[parser_key] = []
        
        return all_signals
    
    def get_parser_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the parser registry
        
        Returns:
            Dictionary with registry statistics
        """
        total_registered = len(self._parser_classes)
        total_active = len(self._active_parsers)
        connected_count = sum(1 for parser in self._active_parsers.values() if parser.is_connected)
        enabled_count = sum(1 for config in self._parser_configs.values() if config.enabled)
        
        return {
            "total_registered_types": total_registered,
            "total_active_parsers": total_active,
            "connected_parsers": connected_count,
            "enabled_parsers": enabled_count,
            "registered_types": [t.value for t in self._parser_classes.keys()],
            "timestamp": datetime.utcnow().isoformat()
        }


# Global parser registry instance
parser_registry = ParserRegistry()

# Convenience functions
def register_parser(channel_type: ChannelType, parser_class: Type[BaseChannelParser]) -> None:
    """Register a parser class globally"""
    parser_registry.register_parser(channel_type, parser_class)

def create_parser(config: ChannelConfig) -> BaseChannelParser:
    """Create a parser instance globally"""
    return parser_registry.create_parser(config)

def get_parser(channel_type: ChannelType, channel_name: str) -> Optional[BaseChannelParser]:
    """Get a parser instance globally"""
    return parser_registry.get_parser(channel_type, channel_name)
