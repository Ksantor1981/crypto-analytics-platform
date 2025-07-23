"""
Channel Metrics Service - Real channel performance calculation
Part of Task 3.1.3: Расчет реальных метрик каналов
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
import numpy as np

from ..models.signal import Signal, SignalStatus
from ..models.channel import Channel
from ..models.user import User

logger = logging.getLogger(__name__)

class ChannelMetricsService:
    """
    Service for calculating real channel performance metrics
    Core business logic: Accurate channel ratings based on actual signal performance
    """
    
    def __init__(self):
        self.metric_weights = {
            'accuracy': 0.35,      # Signal success rate
            'avg_roi': 0.25,       # Average return on investment
            'consistency': 0.20,   # Performance consistency over time
            'frequency': 0.10,     # Signal frequency (not too many, not too few)
            'risk_management': 0.10  # Stop loss usage and risk control
        }
        
        self.time_periods = {
            'week': 7,
            'month': 30,
            'quarter': 90,
            'year': 365
        }
    
    async def calculate_channel_metrics(
        self,
        channel: Channel,
        db: Session,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics for a channel
        
        Args:
            channel: Channel to analyze
            db: Database session
            period_days: Analysis period in days
        
        Returns:
            Dict with calculated metrics
        """
        try:
            # Get signals for the period
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)
            signals = db.query(Signal).filter(
                and_(
                    Signal.channel_id == channel.id,
                    Signal.created_at >= cutoff_date
                )
            ).all()
            
            if not signals:
                return self._empty_metrics()
            
            # Calculate individual metrics
            accuracy_metrics = await self._calculate_accuracy_metrics(signals)
            roi_metrics = await self._calculate_roi_metrics(signals)
            consistency_metrics = await self._calculate_consistency_metrics(signals, period_days)
            frequency_metrics = await self._calculate_frequency_metrics(signals, period_days)
            risk_metrics = await self._calculate_risk_metrics(signals)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                accuracy_metrics, roi_metrics, consistency_metrics,
                frequency_metrics, risk_metrics
            )
            
            # Calculate additional insights
            symbol_performance = await self._calculate_symbol_performance(signals)
            time_analysis = await self._calculate_time_analysis(signals)
            trend_analysis = await self._calculate_trend_analysis(signals, db)
            
            metrics = {
                'channel_id': channel.id,
                'channel_name': channel.name,
                'analysis_period_days': period_days,
                'total_signals': len(signals),
                'calculation_date': datetime.utcnow().isoformat(),
                
                # Core metrics
                'overall_score': overall_score,
                'accuracy': accuracy_metrics,
                'roi': roi_metrics,
                'consistency': consistency_metrics,
                'frequency': frequency_metrics,
                'risk_management': risk_metrics,
                
                # Additional insights
                'symbol_performance': symbol_performance,
                'time_analysis': time_analysis,
                'trend_analysis': trend_analysis,
                
                # Rating and category
                'rating': self._calculate_rating(overall_score),
                'category': self._determine_category(channel, signals),
                'recommendation': self._generate_recommendation(overall_score, accuracy_metrics, roi_metrics)
            }
            
            logger.info(f"Metrics calculated for channel {channel.name}: score {overall_score:.3f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics for channel {channel.id}: {e}")
            return self._empty_metrics()
    
    async def calculate_all_channels_metrics(
        self,
        user: User,
        db: Session,
        period_days: int = 30
    ) -> List[Dict[str, Any]]:
        """Calculate metrics for all user's channels"""
        try:
            channels = db.query(Channel).filter(Channel.owner_id == user.id).all()
            
            all_metrics = []
            for channel in channels:
                metrics = await self.calculate_channel_metrics(channel, db, period_days)
                all_metrics.append(metrics)
            
            # Sort by overall score
            all_metrics.sort(key=lambda x: x['overall_score'], reverse=True)
            
            return all_metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics for user {user.id}: {e}")
            return []
    
    async def get_channel_ranking(
        self,
        db: Session,
        period_days: int = 30,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get global channel ranking based on performance
        """
        try:
            # Get all channels with recent activity
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)
            
            channels_with_signals = db.query(Channel).join(Signal).filter(
                Signal.created_at >= cutoff_date
            ).distinct().all()
            
            rankings = []
            for channel in channels_with_signals:
                metrics = await self.calculate_channel_metrics(channel, db, period_days)
                
                if metrics['total_signals'] >= 5:  # Minimum signals for ranking
                    rankings.append({
                        'rank': 0,  # Will be set after sorting
                        'channel_id': channel.id,
                        'channel_name': channel.name,
                        'channel_type': channel.type,
                        'overall_score': metrics['overall_score'],
                        'accuracy': metrics['accuracy']['success_rate'],
                        'avg_roi': metrics['roi']['average_roi'],
                        'total_signals': metrics['total_signals'],
                        'rating': metrics['rating']
                    })
            
            # Sort by overall score and assign ranks
            rankings.sort(key=lambda x: x['overall_score'], reverse=True)
            for i, ranking in enumerate(rankings[:limit]):
                ranking['rank'] = i + 1
            
            return rankings[:limit]
            
        except Exception as e:
            logger.error(f"Error calculating channel ranking: {e}")
            return []
    
    async def _calculate_accuracy_metrics(self, signals: List[Signal]) -> Dict[str, Any]:
        """Calculate accuracy-related metrics"""
        completed_signals = [s for s in signals if s.status in [SignalStatus.COMPLETED, SignalStatus.STOPPED]]
        
        if not completed_signals:
            return {
                'success_rate': 0.0,
                'total_completed': 0,
                'successful_signals': 0,
                'failed_signals': 0,
                'pending_signals': len([s for s in signals if s.status == SignalStatus.PENDING])
            }
        
        successful_signals = [s for s in completed_signals if s.roi_percentage and s.roi_percentage > 0]
        failed_signals = [s for s in completed_signals if s.roi_percentage and s.roi_percentage <= 0]
        
        success_rate = len(successful_signals) / len(completed_signals) * 100
        
        return {
            'success_rate': round(success_rate, 2),
            'total_completed': len(completed_signals),
            'successful_signals': len(successful_signals),
            'failed_signals': len(failed_signals),
            'pending_signals': len([s for s in signals if s.status == SignalStatus.PENDING]),
            'completion_rate': round(len(completed_signals) / len(signals) * 100, 2)
        }
    
    async def _calculate_roi_metrics(self, signals: List[Signal]) -> Dict[str, Any]:
        """Calculate ROI-related metrics"""
        completed_signals = [s for s in signals if s.status in [SignalStatus.COMPLETED, SignalStatus.STOPPED] and s.roi_percentage is not None]
        
        if not completed_signals:
            return {
                'average_roi': 0.0,
                'median_roi': 0.0,
                'best_roi': 0.0,
                'worst_roi': 0.0,
                'total_roi': 0.0,
                'positive_roi_count': 0,
                'negative_roi_count': 0
            }
        
        roi_values = [s.roi_percentage for s in completed_signals]
        positive_rois = [roi for roi in roi_values if roi > 0]
        negative_rois = [roi for roi in roi_values if roi <= 0]
        
        return {
            'average_roi': round(np.mean(roi_values), 2),
            'median_roi': round(np.median(roi_values), 2),
            'best_roi': round(max(roi_values), 2),
            'worst_roi': round(min(roi_values), 2),
            'total_roi': round(sum(roi_values), 2),
            'positive_roi_count': len(positive_rois),
            'negative_roi_count': len(negative_rois),
            'roi_std': round(np.std(roi_values), 2),
            'sharpe_ratio': self._calculate_sharpe_ratio(roi_values)
        }
    
    async def _calculate_consistency_metrics(self, signals: List[Signal], period_days: int) -> Dict[str, Any]:
        """Calculate consistency metrics over time"""
        if len(signals) < 10:  # Need minimum signals for consistency analysis
            return {
                'consistency_score': 0.5,
                'performance_variance': 0.0,
                'weekly_performance': [],
                'trend': 'insufficient_data'
            }
        
        # Group signals by week
        weekly_performance = {}
        for signal in signals:
            if signal.roi_percentage is not None:
                week_key = signal.created_at.strftime('%Y-W%U')
                if week_key not in weekly_performance:
                    weekly_performance[week_key] = []
                weekly_performance[week_key].append(signal.roi_percentage)
        
        # Calculate weekly averages
        weekly_averages = []
        for week, rois in weekly_performance.items():
            if rois:
                weekly_averages.append(np.mean(rois))
        
        if len(weekly_averages) < 2:
            return {
                'consistency_score': 0.5,
                'performance_variance': 0.0,
                'weekly_performance': weekly_averages,
                'trend': 'insufficient_data'
            }
        
        # Calculate consistency score (inverse of variance)
        variance = np.var(weekly_averages)
        consistency_score = max(0, 1 - (variance / 100))  # Normalize to 0-1
        
        # Determine trend
        if len(weekly_averages) >= 3:
            recent_avg = np.mean(weekly_averages[-3:])
            older_avg = np.mean(weekly_averages[:-3]) if len(weekly_averages) > 3 else weekly_averages[0]
            
            if recent_avg > older_avg * 1.1:
                trend = 'improving'
            elif recent_avg < older_avg * 0.9:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return {
            'consistency_score': round(consistency_score, 3),
            'performance_variance': round(variance, 2),
            'weekly_performance': [round(avg, 2) for avg in weekly_averages],
            'trend': trend,
            'weeks_analyzed': len(weekly_averages)
        }
    
    async def _calculate_frequency_metrics(self, signals: List[Signal], period_days: int) -> Dict[str, Any]:
        """Calculate signal frequency metrics"""
        signals_per_day = len(signals) / period_days
        
        # Optimal frequency is around 1-3 signals per day
        if 1 <= signals_per_day <= 3:
            frequency_score = 1.0
        elif 0.5 <= signals_per_day < 1:
            frequency_score = 0.8
        elif 3 < signals_per_day <= 5:
            frequency_score = 0.7
        elif signals_per_day < 0.5:
            frequency_score = 0.5
        else:  # Too many signals (>5 per day)
            frequency_score = 0.3
        
        # Calculate signal distribution
        daily_counts = {}
        for signal in signals:
            day_key = signal.created_at.strftime('%Y-%m-%d')
            daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
        
        return {
            'signals_per_day': round(signals_per_day, 2),
            'frequency_score': round(frequency_score, 3),
            'most_active_day': max(daily_counts.values()) if daily_counts else 0,
            'days_with_signals': len(daily_counts),
            'total_days_analyzed': period_days,
            'activity_rate': round(len(daily_counts) / period_days * 100, 2)
        }
    
    async def _calculate_risk_metrics(self, signals: List[Signal]) -> Dict[str, Any]:
        """Calculate risk management metrics"""
        signals_with_sl = [s for s in signals if s.stop_loss is not None]
        completed_signals = [s for s in signals if s.status in [SignalStatus.COMPLETED, SignalStatus.STOPPED]]
        
        # Stop loss usage rate
        sl_usage_rate = len(signals_with_sl) / len(signals) * 100 if signals else 0
        
        # Risk-reward ratios
        risk_reward_ratios = []
        for signal in signals_with_sl:
            if signal.entry_price and signal.target_price and signal.stop_loss:
                if signal.signal_type == 'buy':
                    potential_profit = signal.target_price - signal.entry_price
                    potential_loss = signal.entry_price - signal.stop_loss
                else:  # sell
                    potential_profit = signal.entry_price - signal.target_price
                    potential_loss = signal.stop_loss - signal.entry_price
                
                if potential_loss > 0:
                    risk_reward_ratios.append(potential_profit / potential_loss)
        
        avg_risk_reward = np.mean(risk_reward_ratios) if risk_reward_ratios else 0
        
        # Calculate risk score
        risk_score = 0.0
        if sl_usage_rate > 80:
            risk_score += 0.4
        elif sl_usage_rate > 50:
            risk_score += 0.2
        
        if avg_risk_reward > 2:
            risk_score += 0.3
        elif avg_risk_reward > 1:
            risk_score += 0.2
        
        if completed_signals:
            stopped_signals = [s for s in completed_signals if s.status == SignalStatus.STOPPED]
            stop_loss_hit_rate = len(stopped_signals) / len(completed_signals) * 100
            
            if stop_loss_hit_rate < 30:  # Good risk management
                risk_score += 0.3
            elif stop_loss_hit_rate < 50:
                risk_score += 0.1
        
        return {
            'risk_score': round(min(risk_score, 1.0), 3),
            'stop_loss_usage_rate': round(sl_usage_rate, 2),
            'average_risk_reward_ratio': round(avg_risk_reward, 2),
            'signals_with_stop_loss': len(signals_with_sl),
            'risk_reward_ratios': [round(rr, 2) for rr in risk_reward_ratios[:10]]  # Show first 10
        }
    
    def _calculate_overall_score(
        self,
        accuracy: Dict[str, Any],
        roi: Dict[str, Any],
        consistency: Dict[str, Any],
        frequency: Dict[str, Any],
        risk: Dict[str, Any]
    ) -> float:
        """Calculate weighted overall score"""
        
        # Normalize accuracy (0-100% -> 0-1)
        accuracy_score = accuracy['success_rate'] / 100
        
        # Normalize ROI (assume good performance is 5-20% average ROI)
        roi_score = min(max(roi['average_roi'] / 20, 0), 1) if roi['average_roi'] > 0 else 0
        
        # Consistency score is already 0-1
        consistency_score = consistency['consistency_score']
        
        # Frequency score is already 0-1
        frequency_score = frequency['frequency_score']
        
        # Risk score is already 0-1
        risk_score = risk['risk_score']
        
        # Calculate weighted score
        overall_score = (
            accuracy_score * self.metric_weights['accuracy'] +
            roi_score * self.metric_weights['avg_roi'] +
            consistency_score * self.metric_weights['consistency'] +
            frequency_score * self.metric_weights['frequency'] +
            risk_score * self.metric_weights['risk_management']
        )
        
        return round(overall_score, 3)
    
    def _calculate_sharpe_ratio(self, roi_values: List[float]) -> float:
        """Calculate Sharpe ratio for risk-adjusted returns"""
        if not roi_values or len(roi_values) < 2:
            return 0.0
        
        mean_return = np.mean(roi_values)
        std_return = np.std(roi_values)
        
        if std_return == 0:
            return 0.0
        
        # Assume risk-free rate of 2% annually (simplified)
        risk_free_rate = 0.02 / 365  # Daily rate
        sharpe_ratio = (mean_return - risk_free_rate) / std_return
        
        return round(sharpe_ratio, 3)
    
    def _calculate_rating(self, overall_score: float) -> str:
        """Convert overall score to rating"""
        if overall_score >= 0.8:
            return 'S'  # Superior
        elif overall_score >= 0.7:
            return 'A'  # Excellent
        elif overall_score >= 0.6:
            return 'B'  # Good
        elif overall_score >= 0.5:
            return 'C'  # Average
        elif overall_score >= 0.4:
            return 'D'  # Below Average
        else:
            return 'F'  # Poor
    
    def _determine_category(self, channel: Channel, signals: List[Signal]) -> str:
        """Determine channel category based on behavior"""
        if not signals:
            return 'inactive'
        
        # Analyze signal patterns
        buy_signals = len([s for s in signals if s.signal_type == 'buy'])
        sell_signals = len([s for s in signals if s.signal_type == 'sell'])
        
        if buy_signals > sell_signals * 2:
            return 'bullish_focused'
        elif sell_signals > buy_signals * 2:
            return 'bearish_focused'
        else:
            return 'balanced'
    
    def _generate_recommendation(self, overall_score: float, accuracy: Dict[str, Any], roi: Dict[str, Any]) -> str:
        """Generate recommendation based on metrics"""
        if overall_score >= 0.8:
            return "Highly recommended - Excellent performance across all metrics"
        elif overall_score >= 0.7:
            return "Recommended - Strong performance with good consistency"
        elif overall_score >= 0.6:
            return "Consider with caution - Good performance but monitor closely"
        elif overall_score >= 0.5:
            return "Average performance - Suitable for diversification"
        elif overall_score >= 0.4:
            return "Below average - Consider only with other strong channels"
        else:
            return "Not recommended - Poor performance metrics"
    
    async def _calculate_symbol_performance(self, signals: List[Signal]) -> Dict[str, Any]:
        """Calculate performance by symbol"""
        symbol_stats = {}
        
        for signal in signals:
            if signal.symbol not in symbol_stats:
                symbol_stats[signal.symbol] = {
                    'total_signals': 0,
                    'completed_signals': 0,
                    'successful_signals': 0,
                    'total_roi': 0.0
                }
            
            stats = symbol_stats[signal.symbol]
            stats['total_signals'] += 1
            
            if signal.status in [SignalStatus.COMPLETED, SignalStatus.STOPPED] and signal.roi_percentage is not None:
                stats['completed_signals'] += 1
                stats['total_roi'] += signal.roi_percentage
                
                if signal.roi_percentage > 0:
                    stats['successful_signals'] += 1
        
        # Calculate success rates and average ROI
        for symbol, stats in symbol_stats.items():
            if stats['completed_signals'] > 0:
                stats['success_rate'] = round(stats['successful_signals'] / stats['completed_signals'] * 100, 2)
                stats['average_roi'] = round(stats['total_roi'] / stats['completed_signals'], 2)
            else:
                stats['success_rate'] = 0.0
                stats['average_roi'] = 0.0
        
        # Sort by total signals and return top 10
        sorted_symbols = sorted(symbol_stats.items(), key=lambda x: x[1]['total_signals'], reverse=True)
        
        return {symbol: stats for symbol, stats in sorted_symbols[:10]}
    
    async def _calculate_time_analysis(self, signals: List[Signal]) -> Dict[str, Any]:
        """Analyze signal timing patterns"""
        if not signals:
            return {}
        
        # Analyze by hour of day
        hourly_distribution = {}
        for signal in signals:
            hour = signal.created_at.hour
            hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1
        
        # Find most active hours
        most_active_hour = max(hourly_distribution, key=hourly_distribution.get) if hourly_distribution else 0
        
        return {
            'most_active_hour': most_active_hour,
            'hourly_distribution': hourly_distribution,
            'signals_last_24h': len([s for s in signals if s.created_at >= datetime.utcnow() - timedelta(hours=24)]),
            'signals_last_week': len([s for s in signals if s.created_at >= datetime.utcnow() - timedelta(days=7)])
        }
    
    async def _calculate_trend_analysis(self, signals: List[Signal], db: Session) -> Dict[str, Any]:
        """Analyze performance trends"""
        if len(signals) < 10:
            return {'trend': 'insufficient_data'}
        
        # Sort signals by date
        sorted_signals = sorted(signals, key=lambda x: x.created_at)
        
        # Split into first and second half
        mid_point = len(sorted_signals) // 2
        first_half = sorted_signals[:mid_point]
        second_half = sorted_signals[mid_point:]
        
        # Calculate performance for each half
        first_half_completed = [s for s in first_half if s.roi_percentage is not None]
        second_half_completed = [s for s in second_half if s.roi_percentage is not None]
        
        if not first_half_completed or not second_half_completed:
            return {'trend': 'insufficient_data'}
        
        first_half_roi = np.mean([s.roi_percentage for s in first_half_completed])
        second_half_roi = np.mean([s.roi_percentage for s in second_half_completed])
        
        # Determine trend
        if second_half_roi > first_half_roi * 1.2:
            trend = 'strongly_improving'
        elif second_half_roi > first_half_roi * 1.05:
            trend = 'improving'
        elif second_half_roi < first_half_roi * 0.8:
            trend = 'declining'
        elif second_half_roi < first_half_roi * 0.95:
            trend = 'slightly_declining'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'first_half_roi': round(first_half_roi, 2),
            'second_half_roi': round(second_half_roi, 2),
            'improvement': round(((second_half_roi - first_half_roi) / abs(first_half_roi)) * 100, 2)
        }
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            'channel_id': None,
            'channel_name': 'Unknown',
            'analysis_period_days': 0,
            'total_signals': 0,
            'overall_score': 0.0,
            'accuracy': {'success_rate': 0.0, 'total_completed': 0},
            'roi': {'average_roi': 0.0, 'total_roi': 0.0},
            'consistency': {'consistency_score': 0.0, 'trend': 'no_data'},
            'frequency': {'signals_per_day': 0.0, 'frequency_score': 0.0},
            'risk_management': {'risk_score': 0.0, 'stop_loss_usage_rate': 0.0},
            'rating': 'N/A',
            'category': 'inactive',
            'recommendation': 'No data available'
        }


# Global channel metrics service instance
channel_metrics_service = ChannelMetricsService()
