"""
Data Export Service - Excel/CSV export for Premium users
Part of Task 2.3.1: Premium функции
"""
import logging
import io
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..models.user import User, SubscriptionPlan
from ..models.channel import Channel
from ..models.signal import Signal
from ..middleware.rbac_middleware import check_subscription_limit

logger = logging.getLogger(__name__)

class DataExportService:
    """
    Service for exporting user data in various formats
    Premium feature: Excel/CSV export
    """
    
    def __init__(self):
        self.supported_formats = ['csv', 'excel', 'json']
    
    async def export_user_data(
        self,
        user: User,
        db: Session,
        export_type: str = 'signals',
        format: str = 'csv',
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        channel_ids: Optional[List[str]] = None
    ) -> StreamingResponse:
        """
        Export user data in specified format
        
        Args:
            user: User requesting export
            db: Database session
            export_type: Type of data to export ('signals', 'channels', 'analytics')
            format: Export format ('csv', 'excel', 'json')
            date_from: Start date filter
            date_to: End date filter
            channel_ids: Specific channel IDs to export
        
        Returns:
            StreamingResponse: File download response
        """
        # Check if user has export feature
        await check_subscription_limit(user, feature='export_data', api_call=False)
        
        if format not in self.supported_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format. Supported formats: {', '.join(self.supported_formats)}"
            )
        
        # Get data based on export type
        if export_type == 'signals':
            data = await self._get_signals_data(user, db, date_from, date_to, channel_ids)
            filename = f"crypto_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        elif export_type == 'channels':
            data = await self._get_channels_data(user, db)
            filename = f"crypto_channels_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        elif export_type == 'analytics':
            data = await self._get_analytics_data(user, db, date_from, date_to)
            filename = f"crypto_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid export type. Supported types: signals, channels, analytics"
            )
        
        # Generate file based on format
        if format == 'csv':
            return self._generate_csv_response(data, filename)
        elif format == 'excel':
            return self._generate_excel_response(data, filename, export_type)
        elif format == 'json':
            return self._generate_json_response(data, filename)
    
    async def _get_signals_data(
        self,
        user: User,
        db: Session,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        channel_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get signals data for export"""
        query = db.query(Signal).join(Channel).filter(Channel.owner_id == user.id)
        
        # Apply date filters
        if date_from:
            query = query.filter(Signal.created_at >= date_from)
        if date_to:
            query = query.filter(Signal.created_at <= date_to)
        
        # Apply channel filter
        if channel_ids:
            query = query.filter(Channel.id.in_(channel_ids))
        
        signals = query.order_by(Signal.created_at.desc()).all()
        
        # Convert to export format
        data = []
        for signal in signals:
            data.append({
                'Signal ID': signal.id,
                'Channel Name': signal.channel.name if signal.channel else 'Unknown',
                'Channel Type': signal.channel.type if signal.channel else 'Unknown',
                'Symbol': signal.symbol,
                'Signal Type': signal.signal_type,
                'Entry Price': signal.entry_price,
                'Target Price': signal.target_price,
                'Stop Loss': signal.stop_loss,
                'Confidence': signal.confidence,
                'Status': signal.status,
                'Created Date': signal.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Updated Date': signal.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Raw Message': signal.raw_message,
                'Source Channel': signal.source_channel,
                'Author': signal.author,
                'ROI %': signal.roi_percentage if hasattr(signal, 'roi_percentage') else None,
                'Duration (hours)': self._calculate_signal_duration(signal),
                'Performance': self._get_signal_performance(signal)
            })
        
        return data
    
    async def _get_channels_data(self, user: User, db: Session) -> List[Dict[str, Any]]:
        """Get channels data for export"""
        channels = db.query(Channel).filter(Channel.owner_id == user.id).all()
        
        data = []
        for channel in channels:
            # Calculate channel statistics
            total_signals = db.query(Signal).filter(Signal.channel_id == channel.id).count()
            successful_signals = db.query(Signal).filter(
                Signal.channel_id == channel.id,
                Signal.status == 'completed',
                Signal.roi_percentage > 0
            ).count() if hasattr(Signal, 'roi_percentage') else 0
            
            accuracy = (successful_signals / total_signals * 100) if total_signals > 0 else 0
            
            data.append({
                'Channel ID': channel.id,
                'Channel Name': channel.name,
                'Channel Type': channel.type,
                'URL': channel.url,
                'Description': channel.description,
                'Status': channel.status,
                'Created Date': channel.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Total Signals': total_signals,
                'Successful Signals': successful_signals,
                'Accuracy %': round(accuracy, 2),
                'Category': getattr(channel, 'category', 'General'),
                'Last Signal': self._get_last_signal_date(channel, db)
            })
        
        return data
    
    async def _get_analytics_data(
        self,
        user: User,
        db: Session,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get analytics data for export"""
        # Default to last 30 days if no dates provided
        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=30)
        if not date_to:
            date_to = datetime.utcnow()
        
        # Get user's channels
        channels = db.query(Channel).filter(Channel.owner_id == user.id).all()
        
        data = []
        for channel in channels:
            # Get signals for this channel in date range
            signals = db.query(Signal).filter(
                Signal.channel_id == channel.id,
                Signal.created_at >= date_from,
                Signal.created_at <= date_to
            ).all()
            
            if not signals:
                continue
            
            # Calculate analytics
            total_signals = len(signals)
            buy_signals = len([s for s in signals if s.signal_type == 'buy'])
            sell_signals = len([s for s in signals if s.signal_type == 'sell'])
            
            # Performance metrics (if available)
            completed_signals = [s for s in signals if s.status == 'completed']
            avg_confidence = sum(s.confidence for s in signals) / total_signals if total_signals > 0 else 0
            
            data.append({
                'Date': date_from.strftime('%Y-%m-%d'),
                'Channel Name': channel.name,
                'Channel Type': channel.type,
                'Total Signals': total_signals,
                'Buy Signals': buy_signals,
                'Sell Signals': sell_signals,
                'Completed Signals': len(completed_signals),
                'Average Confidence': round(avg_confidence, 3),
                'Success Rate %': self._calculate_success_rate(completed_signals),
                'Most Active Symbol': self._get_most_active_symbol(signals),
                'Signal Frequency': self._calculate_signal_frequency(signals, date_from, date_to)
            })
        
        return data
    
    def _generate_csv_response(self, data: List[Dict[str, Any]], filename: str) -> StreamingResponse:
        """Generate CSV file response"""
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No data available for export"
            )
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        response = StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type='text/csv',
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
        )
        
        return response
    
    def _generate_excel_response(
        self, 
        data: List[Dict[str, Any]], 
        filename: str, 
        export_type: str
    ) -> StreamingResponse:
        """Generate Excel file response with multiple sheets if needed"""
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No data available for export"
            )
        
        output = io.BytesIO()
        
        # Create Excel file with pandas
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df = pd.DataFrame(data)
            
            # Write main data sheet
            sheet_name = export_type.capitalize()
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Add summary sheet for signals export
            if export_type == 'signals' and len(data) > 0:
                summary_data = self._generate_summary_stats(data)
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        output.seek(0)
        
        response = StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
        
        return response
    
    def _generate_json_response(self, data: List[Dict[str, Any]], filename: str) -> StreamingResponse:
        """Generate JSON file response"""
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No data available for export"
            )
        
        import json
        
        output = io.BytesIO()
        json_data = json.dumps(data, indent=2, default=str)
        output.write(json_data.encode('utf-8'))
        output.seek(0)
        
        response = StreamingResponse(
            output,
            media_type='application/json',
            headers={"Content-Disposition": f"attachment; filename={filename}.json"}
        )
        
        return response
    
    def _calculate_signal_duration(self, signal: Signal) -> Optional[float]:
        """Calculate signal duration in hours"""
        if signal.status == 'completed' and signal.updated_at:
            duration = signal.updated_at - signal.created_at
            return round(duration.total_seconds() / 3600, 2)
        return None
    
    def _get_signal_performance(self, signal: Signal) -> str:
        """Get signal performance status"""
        if signal.status == 'completed':
            if hasattr(signal, 'roi_percentage') and signal.roi_percentage:
                if signal.roi_percentage > 0:
                    return 'Profitable'
                elif signal.roi_percentage < 0:
                    return 'Loss'
                else:
                    return 'Break Even'
        elif signal.status == 'active':
            return 'Active'
        elif signal.status == 'cancelled':
            return 'Cancelled'
        return 'Unknown'
    
    def _get_last_signal_date(self, channel: Channel, db: Session) -> Optional[str]:
        """Get the date of the last signal from channel"""
        last_signal = db.query(Signal).filter(
            Signal.channel_id == channel.id
        ).order_by(Signal.created_at.desc()).first()
        
        if last_signal:
            return last_signal.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return None
    
    def _calculate_success_rate(self, completed_signals: List[Signal]) -> float:
        """Calculate success rate for completed signals"""
        if not completed_signals:
            return 0.0
        
        successful = 0
        for signal in completed_signals:
            if hasattr(signal, 'roi_percentage') and signal.roi_percentage and signal.roi_percentage > 0:
                successful += 1
        
        return round((successful / len(completed_signals)) * 100, 2)
    
    def _get_most_active_symbol(self, signals: List[Signal]) -> str:
        """Get the most frequently traded symbol"""
        if not signals:
            return 'N/A'
        
        symbol_counts = {}
        for signal in signals:
            symbol = signal.symbol
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        return max(symbol_counts, key=symbol_counts.get) if symbol_counts else 'N/A'
    
    def _calculate_signal_frequency(
        self, 
        signals: List[Signal], 
        date_from: datetime, 
        date_to: datetime
    ) -> str:
        """Calculate average signals per day"""
        if not signals:
            return '0 signals/day'
        
        days = (date_to - date_from).days + 1
        avg_per_day = len(signals) / days if days > 0 else 0
        
        return f"{round(avg_per_day, 1)} signals/day"
    
    def _generate_summary_stats(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate summary statistics for export"""
        if not data:
            return []
        
        total_signals = len(data)
        buy_signals = len([d for d in data if d.get('Signal Type') == 'buy'])
        sell_signals = len([d for d in data if d.get('Signal Type') == 'sell'])
        
        # Calculate average confidence
        confidences = [d.get('Confidence', 0) for d in data if d.get('Confidence')]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Get unique symbols
        symbols = set(d.get('Symbol', '') for d in data if d.get('Symbol'))
        
        # Get unique channels
        channels = set(d.get('Channel Name', '') for d in data if d.get('Channel Name'))
        
        summary = [
            {'Metric': 'Total Signals', 'Value': total_signals},
            {'Metric': 'Buy Signals', 'Value': buy_signals},
            {'Metric': 'Sell Signals', 'Value': sell_signals},
            {'Metric': 'Average Confidence', 'Value': round(avg_confidence, 3)},
            {'Metric': 'Unique Symbols', 'Value': len(symbols)},
            {'Metric': 'Unique Channels', 'Value': len(channels)},
            {'Metric': 'Export Date', 'Value': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        ]
        
        return summary


# Global export service instance
export_service = DataExportService()
