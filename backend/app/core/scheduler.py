"""
Scheduler for automated email notifications and trading tasks
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from app.tasks.email_tasks import (
    send_daily_payment_reminders,
    send_expired_subscription_notifications,
    send_weekly_payment_summary
)

from app.tasks.trading_tasks import (
    update_all_positions,
    check_stop_losses,
    check_take_profits,
    update_trailing_stops,
    execute_pending_signals,
    sync_account_balances,
    generate_trading_report
)

logger = logging.getLogger(__name__)

class TradingScheduler:
    """Scheduler for trading and email notifications"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._setup_jobs()
    
    def _setup_jobs(self):
        """Setup scheduled jobs"""
        
        # Email notifications
        # Daily payment reminders at 9:00 AM UTC
        self.scheduler.add_job(
            send_daily_payment_reminders,
            CronTrigger(hour=9, minute=0),
            id='daily_payment_reminders',
            name='Send daily payment reminders',
            replace_existing=True
        )
        
        # Expired subscription notifications at 10:00 AM UTC
        self.scheduler.add_job(
            send_expired_subscription_notifications,
            CronTrigger(hour=10, minute=0),
            id='expired_subscription_notifications',
            name='Send expired subscription notifications',
            replace_existing=True
        )
        
        # Weekly payment summary every Monday at 8:00 AM UTC
        self.scheduler.add_job(
            send_weekly_payment_summary,
            CronTrigger(day_of_week='mon', hour=8, minute=0),
            id='weekly_payment_summary',
            name='Send weekly payment summary',
            replace_existing=True
        )
        
        # Trading tasks
        # Update positions every 30 seconds
        self.scheduler.add_job(
            update_all_positions,
            CronTrigger(second='*/30'),
            id='update_all_positions',
            name='Update all position prices and PnL',
            replace_existing=True
        )
        
        # Check stop losses every 10 seconds
        self.scheduler.add_job(
            check_stop_losses,
            CronTrigger(second='*/10'),
            id='check_stop_losses',
            name='Check and execute stop losses',
            replace_existing=True
        )
        
        # Check take profits every 10 seconds
        self.scheduler.add_job(
            check_take_profits,
            CronTrigger(second='*/10'),
            id='check_take_profits',
            name='Check and execute take profits',
            replace_existing=True
        )
        
        # Update trailing stops every minute
        self.scheduler.add_job(
            update_trailing_stops,
            CronTrigger(minute='*/1'),
            id='update_trailing_stops',
            name='Update trailing stops',
            replace_existing=True
        )
        
        # Execute pending signals every 2 minutes
        self.scheduler.add_job(
            execute_pending_signals,
            CronTrigger(minute='*/2'),
            id='execute_pending_signals',
            name='Execute pending trading signals',
            replace_existing=True
        )
        
        # Sync account balances every 5 minutes
        self.scheduler.add_job(
            sync_account_balances,
            CronTrigger(minute='*/5'),
            id='sync_account_balances',
            name='Sync account balances with exchanges',
            replace_existing=True
        )
        
        # Generate trading report daily at 6:00 AM UTC
        self.scheduler.add_job(
            generate_trading_report,
            CronTrigger(hour=6, minute=0),
            id='generate_trading_report',
            name='Generate daily trading report',
            replace_existing=True
        )
        
        logger.info("Trading scheduler jobs configured")
    
    def start(self):
        """Start the scheduler"""
        try:
            self.scheduler.start()
            logger.info("Trading scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start trading scheduler: {e}")
    
    def stop(self):
        """Stop the scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("Trading scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping trading scheduler: {e}")
    
    def get_jobs(self):
        """Get list of scheduled jobs"""
        return self.scheduler.get_jobs()
    
    def add_manual_job(self, func, trigger, **trigger_args):
        """Add a manual job to the scheduler"""
        try:
            job = self.scheduler.add_job(func, trigger, **trigger_args)
            logger.info(f"Manual job added: {job.id}")
            return job
        except Exception as e:
            logger.error(f"Failed to add manual job: {e}")
            return None

# Global scheduler instance
trading_scheduler = TradingScheduler() 