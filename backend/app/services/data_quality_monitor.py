"""
Data Quality Monitor - Real-time data pipeline monitoring
Part of Task 2.1: Data Quality Monitoring
"""
import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import statistics
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class DataQualityMetric:
    """Data quality metric structure"""
    timestamp: datetime
    source: str
    metric_type: str
    value: float
    threshold: float
    status: str  # 'healthy', 'warning', 'critical'
    details: Dict[str, Any]

@dataclass
class AnomalyAlert:
    """Anomaly alert structure"""
    timestamp: datetime
    source: str
    alert_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    details: Dict[str, Any]
    resolved: bool = False

class DataQualityMonitor:
    """
    Real-time data quality monitoring system
    Detects anomalies and degradation in data pipeline
    """
    
    def __init__(self):
        # Monitoring configuration
        self.monitoring_interval = 60  # seconds
        self.alert_cooldown = 300  # 5 minutes between alerts
        
        # Quality thresholds
        self.thresholds = {
            'signal_parsing_accuracy': 0.8,      # 80% parsing success rate
            'data_freshness': 300,               # 5 minutes max age
            'source_availability': 0.9,          # 90% uptime
            'data_volume': 0.5,                  # 50% of expected volume
            'error_rate': 0.1,                   # 10% max error rate
            'duplicate_rate': 0.05,              # 5% max duplicates
            'format_consistency': 0.9,           # 90% format consistency
            'price_accuracy': 0.95,              # 95% price accuracy
            'confidence_distribution': 0.3       # 30% min confidence spread
        }
        
        # Metrics storage
        self.metrics_history: List[DataQualityMetric] = []
        self.active_alerts: List[AnomalyAlert] = []
        self.source_stats: Dict[str, Dict[str, Any]] = {}
        
        # Monitoring state
        self.is_monitoring = False
        self.last_check = None
        
        # Alert handlers
        self.alert_handlers: List[callable] = []
        
        # Data sources to monitor
        self.data_sources = {
            'telegram': {
                'channels': [],
                'expected_volume': 100,  # signals per hour
                'parsing_patterns': ['BTCUSDT', 'ETHUSDT', 'ADAUSDT'],
                'last_activity': None
            },
            'reddit': {
                'subreddits': ['cryptocurrency', 'cryptomarkets', 'bitcoin'],
                'expected_volume': 50,   # signals per hour
                'parsing_patterns': ['BTCUSDT', 'ETHUSDT', 'ADAUSDT'],
                'last_activity': None
            },
            'ml_service': {
                'endpoints': ['/api/v1/predictions/predict'],
                'expected_response_time': 2.0,  # seconds
                'last_activity': None
            },
            'database': {
                'tables': ['signals', 'channels', 'users'],
                'expected_queries_per_minute': 100,
                'last_activity': None
            }
        }
    
    async def start_monitoring(self):
        """Start continuous data quality monitoring"""
        logger.info("🚀 Starting Data Quality Monitor")
        self.is_monitoring = True
        
        while self.is_monitoring:
            try:
                await self.run_quality_check()
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in data quality monitoring: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds on error
    
    async def stop_monitoring(self):
        """Stop data quality monitoring"""
        logger.info("🛑 Stopping Data Quality Monitor")
        self.is_monitoring = False
    
    async def run_quality_check(self):
        """Run comprehensive quality check"""
        logger.debug("🔍 Running data quality check")
        
        # Check each data source
        for source_name, source_config in self.data_sources.items():
            try:
                await self._check_source_quality(source_name, source_config)
            except Exception as e:
                logger.error(f"Error checking {source_name}: {e}")
        
        # Check overall system health
        await self._check_system_health()
        
        # Process alerts
        await self._process_alerts()
        
        # Clean up old metrics
        self._cleanup_old_metrics()
        
        self.last_check = datetime.now()
    
    async def _check_source_quality(self, source_name: str, source_config: Dict[str, Any]):
        """Check quality metrics for specific data source"""
        
        # 1. Check data freshness
        freshness_metric = await self._check_data_freshness(source_name, source_config)
        self._record_metric(freshness_metric)
        
        # 2. Check data volume
        volume_metric = await self._check_data_volume(source_name, source_config)
        self._record_metric(volume_metric)
        
        # 3. Check parsing accuracy
        accuracy_metric = await self._check_parsing_accuracy(source_name, source_config)
        self._record_metric(accuracy_metric)
        
        # 4. Check error rate
        error_metric = await self._check_error_rate(source_name, source_config)
        self._record_metric(error_metric)
        
        # 5. Check format consistency
        consistency_metric = await self._check_format_consistency(source_name, source_config)
        self._record_metric(consistency_metric)
        
        # Update source statistics
        self._update_source_stats(source_name, source_config)
    
    async def _check_data_freshness(self, source_name: str, source_config: Dict[str, Any]) -> DataQualityMetric:
        """Check if data is fresh (recently updated)"""
        last_activity = source_config.get('last_activity')
        
        if last_activity is None:
            freshness_age = float('inf')
        else:
            freshness_age = (datetime.now() - last_activity).total_seconds()
        
        threshold = self.thresholds['data_freshness']
        status = 'healthy' if freshness_age <= threshold else 'critical'
        
        return DataQualityMetric(
            timestamp=datetime.now(),
            source=source_name,
            metric_type='data_freshness',
            value=freshness_age,
            threshold=threshold,
            status=status,
            details={
                'last_activity': last_activity.isoformat() if last_activity else None,
                'age_seconds': freshness_age
            }
        )
    
    async def _check_data_volume(self, source_name: str, source_config: Dict[str, Any]) -> DataQualityMetric:
        """Check if data volume is within expected range"""
        expected_volume = source_config.get('expected_volume', 100)
        
        # Get recent data volume (last hour)
        recent_volume = await self._get_recent_data_volume(source_name)
        
        volume_ratio = recent_volume / expected_volume if expected_volume > 0 else 0
        threshold = self.thresholds['data_volume']
        status = 'healthy' if volume_ratio >= threshold else 'warning'
        
        return DataQualityMetric(
            timestamp=datetime.now(),
            source=source_name,
            metric_type='data_volume',
            value=volume_ratio,
            threshold=threshold,
            status=status,
            details={
                'expected_volume': expected_volume,
                'actual_volume': recent_volume,
                'volume_ratio': volume_ratio
            }
        )
    
    async def _check_parsing_accuracy(self, source_name: str, source_config: Dict[str, Any]) -> DataQualityMetric:
        """Check signal parsing accuracy"""
        # Get recent parsing results
        parsing_results = await self._get_parsing_results(source_name)
        
        if not parsing_results:
            accuracy = 0.0
        else:
            successful_parses = sum(1 for result in parsing_results if result['success'])
            accuracy = successful_parses / len(parsing_results)
        
        threshold = self.thresholds['signal_parsing_accuracy']
        status = 'healthy' if accuracy >= threshold else 'critical'
        
        return DataQualityMetric(
            timestamp=datetime.now(),
            source=source_name,
            metric_type='parsing_accuracy',
            value=accuracy,
            threshold=threshold,
            status=status,
            details={
                'total_attempts': len(parsing_results),
                'successful_parses': sum(1 for result in parsing_results if result['success']),
                'failed_parses': sum(1 for result in parsing_results if not result['success'])
            }
        )
    
    async def _check_error_rate(self, source_name: str, source_config: Dict[str, Any]) -> DataQualityMetric:
        """Check error rate for data source"""
        # Get recent errors
        recent_errors = await self._get_recent_errors(source_name)
        total_operations = await self._get_total_operations(source_name)
        
        if total_operations == 0:
            error_rate = 0.0
        else:
            error_rate = recent_errors / total_operations
        
        threshold = self.thresholds['error_rate']
        status = 'healthy' if error_rate <= threshold else 'critical'
        
        return DataQualityMetric(
            timestamp=datetime.now(),
            source=source_name,
            metric_type='error_rate',
            value=error_rate,
            threshold=threshold,
            status=status,
            details={
                'total_operations': total_operations,
                'error_count': recent_errors,
                'error_rate': error_rate
            }
        )
    
    async def _check_format_consistency(self, source_name: str, source_config: Dict[str, Any]) -> DataQualityMetric:
        """Check format consistency of parsed data"""
        # Get recent parsed signals
        recent_signals = await self._get_recent_signals(source_name)
        
        if not recent_signals:
            consistency = 1.0  # No data means no inconsistency
        else:
            # Check for required fields
            required_fields = ['symbol', 'signal_type', 'entry_price']
            consistent_signals = 0
            
            for signal in recent_signals:
                if all(field in signal and signal[field] is not None for field in required_fields):
                    consistent_signals += 1
            
            consistency = consistent_signals / len(recent_signals)
        
        threshold = self.thresholds['format_consistency']
        status = 'healthy' if consistency >= threshold else 'warning'
        
        return DataQualityMetric(
            timestamp=datetime.now(),
            source=source_name,
            metric_type='format_consistency',
            value=consistency,
            threshold=threshold,
            status=status,
            details={
                'total_signals': len(recent_signals),
                'consistent_signals': int(consistency * len(recent_signals)),
                'inconsistent_signals': int((1 - consistency) * len(recent_signals))
            }
        )
    
    async def _check_system_health(self):
        """Check overall system health"""
        # Calculate aggregate metrics
        recent_metrics = self._get_recent_metrics(minutes=5)
        
        if not recent_metrics:
            return
        
        # Check for critical issues
        critical_metrics = [m for m in recent_metrics if m.status == 'critical']
        warning_metrics = [m for m in recent_metrics if m.status == 'warning']
        
        # Create system health alert if needed
        if critical_metrics:
            await self._create_alert(
                source='system',
                alert_type='critical_quality_degradation',
                severity='critical',
                message=f"Critical data quality issues detected: {len(critical_metrics)} critical metrics",
                details={
                    'critical_metrics': [m.metric_type for m in critical_metrics],
                    'warning_metrics': [m.metric_type for m in warning_metrics],
                    'total_metrics': len(recent_metrics)
                }
            )
        elif warning_metrics:
            await self._create_alert(
                source='system',
                alert_type='quality_warning',
                severity='medium',
                message=f"Data quality warnings: {len(warning_metrics)} warning metrics",
                details={
                    'warning_metrics': [m.metric_type for m in warning_metrics],
                    'total_metrics': len(recent_metrics)
                }
            )
    
    async def _get_recent_data_volume(self, source_name: str) -> int:
        """Get recent data volume for source (last hour)"""
        # This would typically query the database
        # For now, return mock data
        mock_volumes = {
            'telegram': 85,
            'reddit': 42,
            'ml_service': 120,
            'database': 95
        }
        return mock_volumes.get(source_name, 0)
    
    async def _get_parsing_results(self, source_name: str) -> List[Dict[str, Any]]:
        """Get recent parsing results for source"""
        # This would typically query the database
        # For now, return mock data
        mock_results = {
            'telegram': [
                {'success': True, 'timestamp': datetime.now()},
                {'success': True, 'timestamp': datetime.now()},
                {'success': False, 'timestamp': datetime.now()},
                {'success': True, 'timestamp': datetime.now()}
            ],
            'reddit': [
                {'success': True, 'timestamp': datetime.now()},
                {'success': True, 'timestamp': datetime.now()},
                {'success': True, 'timestamp': datetime.now()}
            ]
        }
        return mock_results.get(source_name, [])
    
    async def _get_recent_errors(self, source_name: str) -> int:
        """Get recent error count for source"""
        # This would typically query the database
        # For now, return mock data
        mock_errors = {
            'telegram': 2,
            'reddit': 1,
            'ml_service': 0,
            'database': 3
        }
        return mock_errors.get(source_name, 0)
    
    async def _get_total_operations(self, source_name: str) -> int:
        """Get total operation count for source"""
        # This would typically query the database
        # For now, return mock data
        mock_operations = {
            'telegram': 100,
            'reddit': 50,
            'ml_service': 150,
            'database': 200
        }
        return mock_operations.get(source_name, 0)
    
    async def _get_recent_signals(self, source_name: str) -> List[Dict[str, Any]]:
        """Get recent signals from source"""
        # This would typically query the database
        # For now, return mock data
        mock_signals = {
            'telegram': [
                {'symbol': 'BTCUSDT', 'signal_type': 'LONG', 'entry_price': 45000},
                {'symbol': 'ETHUSDT', 'signal_type': 'SHORT', 'entry_price': 3000},
                {'symbol': 'ADAUSDT', 'signal_type': 'LONG', 'entry_price': 0.5}
            ],
            'reddit': [
                {'symbol': 'BTCUSDT', 'signal_type': 'LONG', 'entry_price': 45000},
                {'symbol': 'SOLUSDT', 'signal_type': 'LONG', 'entry_price': 100}
            ]
        }
        return mock_signals.get(source_name, [])
    
    def _record_metric(self, metric: DataQualityMetric):
        """Record a quality metric"""
        self.metrics_history.append(metric)
        
        # Check if metric indicates an anomaly
        if metric.status in ['warning', 'critical']:
            asyncio.create_task(self._check_for_anomaly(metric))
    
    async def _check_for_anomaly(self, metric: DataQualityMetric):
        """Check if metric indicates an anomaly that requires alerting"""
        # Check if we already have a recent alert for this source and metric type
        recent_alerts = [
            alert for alert in self.active_alerts
            if (alert.source == metric.source and 
                alert.alert_type == f"{metric.metric_type}_anomaly" and
                not alert.resolved and
                (datetime.now() - alert.timestamp).total_seconds() < self.alert_cooldown)
        ]
        
        if recent_alerts:
            return  # Don't create duplicate alerts
        
        # Create anomaly alert
        severity = 'critical' if metric.status == 'critical' else 'medium'
        
        await self._create_alert(
            source=metric.source,
            alert_type=f"{metric.metric_type}_anomaly",
            severity=severity,
            message=f"Data quality anomaly detected: {metric.metric_type} = {metric.value:.2f} (threshold: {metric.threshold:.2f})",
            details={
                'metric_type': metric.metric_type,
                'value': metric.value,
                'threshold': metric.threshold,
                'status': metric.status,
                'details': metric.details
            }
        )
    
    async def _create_alert(self, source: str, alert_type: str, severity: str, message: str, details: Dict[str, Any]):
        """Create a new alert"""
        alert = AnomalyAlert(
            timestamp=datetime.now(),
            source=source,
            alert_type=alert_type,
            severity=severity,
            message=message,
            details=details
        )
        
        self.active_alerts.append(alert)
        
        # Log the alert
        logger.warning(f"🚨 ALERT [{severity.upper()}] {source}: {message}")
        
        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
    
    async def _process_alerts(self):
        """Process and resolve alerts"""
        current_time = datetime.now()
        
        for alert in self.active_alerts:
            if alert.resolved:
                continue
            
            # Check if alert should be auto-resolved
            if (current_time - alert.timestamp).total_seconds() > 3600:  # 1 hour
                # Check if the issue is resolved
                if await self._is_issue_resolved(alert):
                    alert.resolved = True
                    logger.info(f"✅ Alert resolved: {alert.message}")
    
    async def _is_issue_resolved(self, alert: AnomalyAlert) -> bool:
        """Check if an alert issue is resolved"""
        # Get recent metrics for the alert source
        recent_metrics = [
            m for m in self._get_recent_metrics(minutes=5)
            if m.source == alert.source and m.metric_type in alert.alert_type
        ]
        
        if not recent_metrics:
            return False
        
        # Check if all recent metrics are healthy
        return all(m.status == 'healthy' for m in recent_metrics)
    
    def _get_recent_metrics(self, minutes: int = 5) -> List[DataQualityMetric]:
        """Get metrics from the last N minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            metric for metric in self.metrics_history
            if metric.timestamp >= cutoff_time
        ]
    
    def _update_source_stats(self, source_name: str, source_config: Dict[str, Any]):
        """Update source statistics"""
        if source_name not in self.source_stats:
            self.source_stats[source_name] = {}
        
        # Update last activity
        self.source_stats[source_name]['last_activity'] = datetime.now()
        self.source_stats[source_name]['last_check'] = datetime.now()
        
        # Update configuration
        self.source_stats[source_name]['config'] = source_config
    
    def _cleanup_old_metrics(self):
        """Clean up old metrics to prevent memory bloat"""
        cutoff_time = datetime.now() - timedelta(hours=24)  # Keep 24 hours
        self.metrics_history = [
            metric for metric in self.metrics_history
            if metric.timestamp >= cutoff_time
        ]
        
        # Clean up resolved alerts older than 1 day
        cutoff_time = datetime.now() - timedelta(days=1)
        self.active_alerts = [
            alert for alert in self.active_alerts
            if not alert.resolved or alert.timestamp >= cutoff_time
        ]
    
    def add_alert_handler(self, handler: callable):
        """Add an alert handler function"""
        self.alert_handlers.append(handler)
    
    def get_quality_report(self) -> Dict[str, Any]:
        """Get comprehensive quality report"""
        recent_metrics = self._get_recent_metrics(minutes=30)
        
        # Calculate aggregate statistics
        total_metrics = len(recent_metrics)
        healthy_metrics = len([m for m in recent_metrics if m.status == 'healthy'])
        warning_metrics = len([m for m in recent_metrics if m.status == 'warning'])
        critical_metrics = len([m for m in recent_metrics if m.status == 'critical'])
        
        # Calculate health score
        health_score = healthy_metrics / total_metrics if total_metrics > 0 else 1.0
        
        # Group metrics by source
        source_metrics = {}
        for metric in recent_metrics:
            if metric.source not in source_metrics:
                source_metrics[metric.source] = []
            source_metrics[metric.source].append(metric)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_health_score': health_score,
            'total_metrics': total_metrics,
            'healthy_metrics': healthy_metrics,
            'warning_metrics': warning_metrics,
            'critical_metrics': critical_metrics,
            'active_alerts': len([a for a in self.active_alerts if not a.resolved]),
            'source_metrics': {
                source: {
                    'total': len(metrics),
                    'healthy': len([m for m in metrics if m.status == 'healthy']),
                    'warning': len([m for m in metrics if m.status == 'warning']),
                    'critical': len([m for m in metrics if m.status == 'critical'])
                }
                for source, metrics in source_metrics.items()
            },
            'recent_alerts': [
                {
                    'timestamp': alert.timestamp.isoformat(),
                    'source': alert.source,
                    'severity': alert.severity,
                    'message': alert.message,
                    'resolved': alert.resolved
                }
                for alert in self.active_alerts[-10:]  # Last 10 alerts
            ]
        }

# Global monitor instance
data_quality_monitor = DataQualityMonitor()

# Test function
async def test_data_quality_monitor():
    """Test the data quality monitor"""
    monitor = DataQualityMonitor()
    
    print("🧪 Testing Data Quality Monitor")
    print("=" * 50)
    
    # Start monitoring for a short period
    monitor_task = asyncio.create_task(monitor.start_monitoring())
    
    # Wait for some metrics to be collected
    await asyncio.sleep(5)
    
    # Stop monitoring
    await monitor.stop_monitoring()
    
    # Get quality report
    report = monitor.get_quality_report()
    
    print(f"📊 Quality Report:")
    print(f"Health Score: {report['overall_health_score']:.2%}")
    print(f"Total Metrics: {report['total_metrics']}")
    print(f"Healthy: {report['healthy_metrics']}")
    print(f"Warnings: {report['warning_metrics']}")
    print(f"Critical: {report['critical_metrics']}")
    print(f"Active Alerts: {report['active_alerts']}")
    
    print(f"\n📈 Source Metrics:")
    for source, stats in report['source_metrics'].items():
        print(f"  {source}: {stats['healthy']}/{stats['total']} healthy")
    
    if report['recent_alerts']:
        print(f"\n🚨 Recent Alerts:")
        for alert in report['recent_alerts']:
            print(f"  [{alert['severity']}] {alert['source']}: {alert['message']}")

if __name__ == "__main__":
    asyncio.run(test_data_quality_monitor())
