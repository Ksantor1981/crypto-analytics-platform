"""
Backend Integration Client
Client for communicating with the main backend service
"""

import httpx
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..config import settings

logger = logging.getLogger(__name__)

class BackendClient:
    """
    Client for integrating with the main backend service
    """
    
    def __init__(self):
        self.base_url = settings.backend_url
        self.api_key = settings.backend_api_key
        self.timeout = settings.prediction_timeout
        
    async def get_channel_info(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """
        Get channel information from backend
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = self._get_headers()
                response = await client.get(
                    f"{self.base_url}/api/v1/channels/{channel_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to get channel {channel_id}: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting channel info: {str(e)}")
            return None
    
    async def get_channel_accuracy(self, channel_id: int) -> Optional[float]:
        """
        Get channel accuracy from backend
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = self._get_headers()
                response = await client.get(
                    f"{self.base_url}/api/v1/channels/{channel_id}/stats",
                    headers=headers
                )
                
                if response.status_code == 200:
                    stats = response.json()
                    return stats.get('accuracy', 0.5)
                else:
                    logger.warning(f"Failed to get channel accuracy {channel_id}: {response.status_code}")
                    return 0.5
                    
        except Exception as e:
            logger.error(f"Error getting channel accuracy: {str(e)}")
            return 0.5
    
    async def get_asset_info(self, asset: str) -> Optional[Dict[str, Any]]:
        """
        Get asset information from backend
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = self._get_headers()
                response = await client.get(
                    f"{self.base_url}/api/v1/assets/{asset}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to get asset {asset}: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting asset info: {str(e)}")
            return None
    
    async def get_market_data(self, asset: str) -> Optional[Dict[str, Any]]:
        """
        Get current market data for asset
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = self._get_headers()
                response = await client.get(
                    f"{self.base_url}/api/v1/market/{asset}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to get market data {asset}: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting market data: {str(e)}")
            return None
    
    async def save_prediction(self, prediction_data: Dict[str, Any]) -> bool:
        """
        Save ML prediction to backend
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = self._get_headers()
                response = await client.post(
                    f"{self.base_url}/api/v1/predictions",
                    json=prediction_data,
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Prediction saved successfully")
                    return True
                else:
                    logger.warning(f"Failed to save prediction: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error saving prediction: {str(e)}")
            return False
    
    async def get_recent_signals(self, channel_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent signals from a channel
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = self._get_headers()
                response = await client.get(
                    f"{self.base_url}/api/v1/signals",
                    params={"channel_id": channel_id, "limit": limit},
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json().get('signals', [])
                else:
                    logger.warning(f"Failed to get recent signals: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting recent signals: {str(e)}")
            return []
    
    async def health_check(self) -> bool:
        """
        Check if backend is healthy
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Backend health check failed: {str(e)}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for requests
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"ml-service/{settings.service_version}"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        return headers

# Global client instance
backend_client = BackendClient() 