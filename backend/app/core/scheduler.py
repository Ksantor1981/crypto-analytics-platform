"""
Scheduler for automated email notifications
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from app.tasks.email_tasks import (
    send_daily_payment_reminders,
    send_expired_subscription_notifications,
    send_weekly_payment_summary
)

logger = logging.getLogger(__name__)

class EmailScheduler:
    """Scheduler for email notifications"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._setup_jobs()
    
    def _setup_jobs(self):
        """Setup scheduled jobs"""
        
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
        
        logger.info("Email scheduler jobs configured")
    
    def start(self):
        """Start the scheduler"""
        try:
            self.scheduler.start()
            logger.info("Email scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start email scheduler: {e}")
    
    def stop(self):
        """Stop the scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("Email scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping email scheduler: {e}")
    
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
email_scheduler = EmailScheduler() 