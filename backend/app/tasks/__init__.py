"""
Автоматические задачи Celery для обновления данных
"""
from .scheduled_tasks import (
    collect_all_signals_hourly,
    recalculate_statistics_hourly,
    analyze_channels_quality_hourly,
    deep_historical_analysis,
    update_channel_ratings_daily,
    cleanup_old_signals,
    system_health_check
)

__all__ = [
    'collect_all_signals_hourly',
    'recalculate_statistics_hourly', 
    'analyze_channels_quality_hourly',
    'deep_historical_analysis',
    'update_channel_ratings_daily',
    'cleanup_old_signals',
    'system_health_check'
]
