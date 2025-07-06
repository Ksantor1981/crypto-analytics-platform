"""
Telegram Configuration
"""
import os
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class TelegramChannel:
    """Configuration for a Telegram channel"""
    username: str
    channel_id: int
    name: str
    category: str = "crypto"
    active: bool = True
    last_message_id: int = 0

class TelegramConfig:
    """Telegram API configuration"""
    
    def __init__(self):
        # API credentials
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.session_name = os.getenv("TELEGRAM_SESSION_NAME", "crypto_analytics")
        
        # Bot token for bot API (optional)
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        # Channels to monitor (can be configured via database later)
        self.channels = self._load_channels()
        
        # Collection settings
        self.max_messages_per_channel = int(os.getenv("TELEGRAM_MAX_MESSAGES", "100"))
        self.collection_interval = int(os.getenv("TELEGRAM_COLLECTION_INTERVAL", "3600"))  # seconds
        
        # Signal processing settings
        self.min_signal_confidence = float(os.getenv("TELEGRAM_MIN_CONFIDENCE", "0.7"))
        self.enable_ocr = os.getenv("TELEGRAM_ENABLE_OCR", "false").lower() == "true"
        
    def _load_channels(self) -> List[TelegramChannel]:
        """Load channel configurations from environment or database"""
        # For now, load from environment variables
        # In production, this would come from the database
        
        channels = []
        
        # Example channels (replace with real ones)
        default_channels = [
            {
                "username": "cryptosignals_test",
                "channel_id": -1001234567890,  # Replace with real IDs
                "name": "Crypto Signals Test",
                "category": "crypto"
            },
            {
                "username": "btc_signals_test", 
                "channel_id": -1001234567891,
                "name": "BTC Signals Test",
                "category": "crypto"
            }
        ]
        
        # Load from environment if available
        channels_env = os.getenv("TELEGRAM_CHANNELS")
        if channels_env:
            try:
                import json
                channels_data = json.loads(channels_env)
                for ch_data in channels_data:
                    channels.append(TelegramChannel(**ch_data))
            except Exception as e:
                print(f"Error loading channels from env: {e}")
                # Fall back to defaults
                for ch_data in default_channels:
                    channels.append(TelegramChannel(**ch_data))
        else:
            # Use defaults
            for ch_data in default_channels:
                channels.append(TelegramChannel(**ch_data))
                
        return channels
    
    def get_active_channels(self) -> List[TelegramChannel]:
        """Get list of active channels"""
        return [ch for ch in self.channels if ch.active]
    
    def is_configured(self) -> bool:
        """Check if Telegram API is properly configured"""
        return bool(self.api_id and self.api_hash)

# Global config instance
telegram_config = TelegramConfig() 