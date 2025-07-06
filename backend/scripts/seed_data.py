#!/usr/bin/env python3
"""
Database seeding script for development and testing
"""
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set environment
os.environ['ENVIRONMENT'] = 'development'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.hash import bcrypt

from app.core.config import get_settings
from app.core.database import get_db
from app.models import (
    Base, User, Channel, Signal, Subscription, APIKey, Payment, 
    PerformanceMetric, UserRole, SignalDirection, SignalStatus,
    SubscriptionPlan, SubscriptionStatus, PaymentStatus, PaymentMethod
)
from app.schemas.user import UserCreate
from app.schemas.channel import ChannelCreate
from app.services.user_service import UserService
from app.services.channel_service import ChannelService

def create_test_users(session):
    """Create test users"""
    print("Creating test users...")
    
    # Admin user
    admin = User(
        email="admin@cryptoanalytics.com",
        username="admin",
        full_name="System Administrator",
        hashed_password=bcrypt.hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        timezone="UTC",
        language="en"
    )
    session.add(admin)
    
    # Premium user
    premium_user = User(
        email="premium@example.com",
        username="premium_user",
        full_name="Premium User",
        hashed_password=bcrypt.hash("premium123"),
        role=UserRole.PREMIUM_USER,
        is_active=True,
        is_verified=True,
        current_subscription_expires=datetime.utcnow() + timedelta(days=30),
        timezone="UTC",
        language="en"
    )
    session.add(premium_user)
    
    # Free user
    free_user = User(
        email="free@example.com",
        username="free_user",
        full_name="Free User",
        hashed_password=bcrypt.hash("free123"),
        role=UserRole.FREE_USER,
        is_active=True,
        is_verified=True,
        timezone="UTC",
        language="en"
    )
    session.add(free_user)
    
    session.commit()
    return admin, premium_user, free_user

def create_test_channels(session):
    """Create test channels"""
    print("Creating test channels...")
    
    channels = [
        Channel(
            name="Crypto Signals Pro",
            platform="telegram",
            url="https://t.me/cryptosignalspro",
            category="premium",
            description="Premium crypto trading signals with high accuracy",
            accuracy=75.5,
            signals_count=150,
            successful_signals=113,
            average_roi=12.5,
            max_drawdown=8.2,
            is_active=True,
            is_verified=True
        ),
        Channel(
            name="Bitcoin Alerts",
            platform="telegram",
            url="https://t.me/bitcoinalerts",
            category="bitcoin",
            description="Focused on Bitcoin trading signals",
            accuracy=68.3,
            signals_count=98,
            successful_signals=67,
            average_roi=9.8,
            max_drawdown=12.1,
            is_active=True,
            is_verified=True
        ),
        Channel(
            name="Altcoin Gems",
            platform="telegram", 
            url="https://t.me/altcoingems",
            category="altcoins",
            description="Hidden gems in altcoin market",
            accuracy=82.1,
            signals_count=76,
            successful_signals=62,
            average_roi=18.7,
            max_drawdown=15.3,
            is_active=True,
            is_verified=False
        ),
        Channel(
            name="DeFi Signals",
            platform="telegram",
            url="https://t.me/defisignals",
            category="defi",
            description="DeFi protocol trading signals",
            accuracy=71.2,
            signals_count=124,
            successful_signals=88,
            average_roi=14.2,
            max_drawdown=10.7,
            is_active=True,
            is_verified=True
        ),
        Channel(
            name="Quick Scalps",
            platform="telegram",
            url="https://t.me/quickscalps",
            category="scalping",
            description="Fast scalping signals for day traders",
            accuracy=65.8,
            signals_count=203,
            successful_signals=134,
            average_roi=6.3,
            max_drawdown=7.8,
            is_active=True,
            is_verified=False
        )
    ]
    
    for channel in channels:
        session.add(channel)
    
    session.commit()
    return channels

def create_test_signals(session, channels):
    """Create test signals"""
    print("Creating test signals...")
    
    signals_data = [
        # Successful signals
        {
            "channel": channels[0],
            "asset": "BTC/USDT",
            "direction": SignalDirection.LONG,
            "entry_price": Decimal("45000.00"),
            "tp1_price": Decimal("46500.00"),
            "tp2_price": Decimal("47800.00"),
            "stop_loss": Decimal("43500.00"),
            "status": SignalStatus.TP1_HIT,
            "is_successful": True,
            "reached_tp1": True,
            "profit_loss_percentage": Decimal("3.33")
        },
        {
            "channel": channels[1],
            "asset": "ETH/USDT", 
            "direction": SignalDirection.LONG,
            "entry_price": Decimal("3200.00"),
            "tp1_price": Decimal("3350.00"),
            "tp2_price": Decimal("3500.00"),
            "stop_loss": Decimal("3050.00"),
            "status": SignalStatus.TP2_HIT,
            "is_successful": True,
            "reached_tp1": True,
            "reached_tp2": True,
            "profit_loss_percentage": Decimal("9.38")
        },
        {
            "channel": channels[2],
            "asset": "SOL/USDT",
            "direction": SignalDirection.SHORT,
            "entry_price": Decimal("95.00"),
            "tp1_price": Decimal("88.00"),
            "tp2_price": Decimal("82.00"),
            "stop_loss": Decimal("98.50"),
            "status": SignalStatus.TP1_HIT,
            "is_successful": True,
            "reached_tp1": True,
            "profit_loss_percentage": Decimal("7.37")
        },
        # Failed signals
        {
            "channel": channels[0],
            "asset": "BNB/USDT",
            "direction": SignalDirection.LONG,
            "entry_price": Decimal("310.00"),
            "tp1_price": Decimal("325.00"),
            "stop_loss": Decimal("295.00"),
            "status": SignalStatus.SL_HIT,
            "is_successful": False,
            "hit_stop_loss": True,
            "profit_loss_percentage": Decimal("-4.84")
        },
        # Pending signals
        {
            "channel": channels[3],
            "asset": "ADA/USDT",
            "direction": SignalDirection.LONG,
            "entry_price": Decimal("0.45"),
            "tp1_price": Decimal("0.48"),
            "tp2_price": Decimal("0.52"),
            "stop_loss": Decimal("0.42"),
            "status": SignalStatus.PENDING,
            "is_successful": None
        }
    ]
    
    for signal_data in signals_data:
        signal = Signal(
            channel=signal_data["channel"],
            asset=signal_data["asset"],
            direction=signal_data["direction"],
            entry_price=signal_data["entry_price"],
            tp1_price=signal_data.get("tp1_price"),
            tp2_price=signal_data.get("tp2_price"),
            stop_loss=signal_data.get("stop_loss"),
            status=signal_data["status"],
            is_successful=signal_data.get("is_successful"),
            reached_tp1=signal_data.get("reached_tp1", False),
            reached_tp2=signal_data.get("reached_tp2", False),
            hit_stop_loss=signal_data.get("hit_stop_loss", False),
            profit_loss_percentage=signal_data.get("profit_loss_percentage"),
            original_text=f"🚀 {signal_data['asset']} {signal_data['direction'].value}\nEntry: {signal_data['entry_price']}\nTP1: {signal_data.get('tp1_price', 'N/A')}\nSL: {signal_data.get('stop_loss', 'N/A')}",
            message_timestamp=datetime.utcnow() - timedelta(hours=24),
            confidence_score=Decimal("85.5"),
            ml_success_probability=Decimal("0.73")
        )
        session.add(signal)
    
    session.commit()

def create_test_subscriptions(session, users):
    """Create test subscriptions"""
    print("Creating test subscriptions...")
    
    admin, premium_user, free_user = users
    
    # Premium subscription
    premium_sub = Subscription(
        user=premium_user,
        plan=SubscriptionPlan.PREMIUM_MONTHLY,
        status=SubscriptionStatus.ACTIVE,
        price=Decimal("29.99"),
        currency="USD",
        started_at=datetime.utcnow() - timedelta(days=5),
        current_period_start=datetime.utcnow() - timedelta(days=5),
        current_period_end=datetime.utcnow() + timedelta(days=25),
        api_requests_limit=1000,
        can_access_all_channels=True,
        can_export_data=True,
        can_use_api=True,
        auto_renew=True
    )
    session.add(premium_sub)
    
    # Free subscription
    free_sub = Subscription(
        user=free_user,
        plan=SubscriptionPlan.FREE,
        status=SubscriptionStatus.ACTIVE,
        price=Decimal("0.00"),
        currency="USD",
        started_at=datetime.utcnow() - timedelta(days=10),
        current_period_start=datetime.utcnow() - timedelta(days=10),
        current_period_end=datetime.utcnow() + timedelta(days=355),
        max_channels_access=5,
        can_access_all_channels=False,
        can_export_data=False,
        can_use_api=False,
        auto_renew=False
    )
    session.add(free_sub)
    
    session.commit()

def create_test_api_keys(session, users):
    """Create test API keys"""
    print("Creating test API keys...")
    
    admin, premium_user, free_user = users
    
    # API key for premium user
    api_key = APIKey(
        user=premium_user,
        name="Production API Key",
        key_hash="hash_premium_user_key_12345",
        key_prefix="cap_premium",
        requests_per_day=1000,
        requests_per_hour=100,
        can_read_channels=True,
        can_read_signals=True,
        can_read_analytics=True,
        can_export_data=True
    )
    session.add(api_key)
    
    session.commit()

def create_test_payments(session, users):
    """Create test payment records"""
    print("Creating test payments...")
    
    admin, premium_user, free_user = users
    
    # Successful payment
    payment = Payment(
        user=premium_user,
        amount=Decimal("29.99"),
        currency="USD",
        description="Monthly Premium Subscription",
        status=PaymentStatus.SUCCEEDED,
        payment_method=PaymentMethod.STRIPE_CARD,
        processed_at=datetime.utcnow() - timedelta(days=5),
        billing_name="Premium User",
        billing_email="premium@example.com"
    )
    session.add(payment)
    
    session.commit()

def create_test_performance_metrics(session, channels):
    """Create test performance metrics"""
    print("Creating test performance metrics...")
    
    # Monthly metrics for first channel
    metric = PerformanceMetric(
        channel=channels[0],
        period_start=datetime.utcnow() - timedelta(days=30),
        period_end=datetime.utcnow(),
        period_type="monthly",
        total_signals=150,
        successful_signals=113,
        failed_signals=37,
        win_rate=Decimal("75.33"),
        average_roi=Decimal("12.50"),
        total_roi=Decimal("1875.00"),
        best_signal_roi=Decimal("45.20"),
        worst_signal_roi=Decimal("-8.30"),
        max_drawdown=Decimal("8.20"),
        quality_score=Decimal("82.50"),
        rank_in_period=1,
        percentile=Decimal("95.50"),
        has_sufficient_data=True,
        is_verified=True,
        asset_breakdown={"BTC/USDT": 45, "ETH/USDT": 30, "SOL/USDT": 15, "Others": 10},
        direction_breakdown={"LONG": 75, "SHORT": 25}
    )
    session.add(metric)
    
    session.commit()

def seed_database():
    """Seed database with initial data."""
    settings = get_settings()
    print("🌱 Starting database seeding...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create admin user
        admin_data = UserCreate(
            email="admin@crypto-analytics.com",
            username="admin",
            password="admin123",
            full_name="System Administrator",
            is_active=True,
            is_admin=True
        )
        
        user_service = UserService(db)
        admin_user = user_service.create_user(admin_data)
        print(f"✅ Created admin user: {admin_user.email}")
        
        # Create test channels
        channel_service = ChannelService(db)
        
        test_channels = [
            {
                "name": "Binance Killers",
                "description": "Premium crypto trading signals",
                "telegram_channel_id": "binancekillers",
                "is_active": True,
                "subscription_price": Decimal("49.99")
            },
            {
                "name": "Crypto Signals Pro",
                "description": "Professional trading signals",
                "telegram_channel_id": "cryptosignalspro",
                "is_active": True,
                "subscription_price": Decimal("29.99")
            },
            {
                "name": "Altcoin Alerts",
                "description": "Altcoin trading opportunities",
                "telegram_channel_id": "altcoinalerts",
                "is_active": True,
                "subscription_price": Decimal("19.99")
            }
        ]
        
        for channel_data in test_channels:
            channel_create = ChannelCreate(**channel_data)
            channel = channel_service.create_channel(channel_create)
            print(f"✅ Created channel: {channel.name}")
        
        # Create test signals
        channels = db.query(Channel).all()
        
        for channel in channels:
            for i in range(5):
                signal = Signal(
                    channel_id=channel.id,
                    coin_symbol=f"BTC{i}" if i == 0 else f"ETH{i}",
                    signal_type="BUY",
                    entry_price=Decimal("50000.00") + (i * 1000),
                    target_price=Decimal("55000.00") + (i * 1000),
                    stop_loss=Decimal("48000.00") + (i * 1000),
                    leverage=10,
                    confidence_score=0.85,
                    message_text=f"🚀 {channel.name} Signal #{i+1}",
                    created_at=datetime.utcnow() - timedelta(hours=i)
                )
                db.add(signal)
        
        db.commit()
        print("✅ Created test signals")
        
        print("🎉 Database seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    success = seed_database()
    sys.exit(0 if success else 1) 