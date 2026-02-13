"""
Standalone Scheduler Daemon
Runs scheduled tasks independently from the web API
"""
import sys
import signal
import time
import logging
from datetime import datetime

from app.config import settings
from app.services.scheduler import get_scheduler_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/proxmox-cronjob-scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SchedulerDaemon:
    """Standalone scheduler daemon"""
    
    def __init__(self):
        self.scheduler_service = None
        self.running = False
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """Start the scheduler daemon"""
        logger.info("=" * 60)
        logger.info("Proxmox Cronjob Scheduler Daemon Starting")
        logger.info("=" * 60)
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Start scheduler service
        self.scheduler_service = get_scheduler_service()
        self.scheduler_service.start()
        
        self.running = True
        logger.info("Scheduler daemon started successfully")
        logger.info(f"Monitoring schedules and executing tasks...")
        
        # Keep daemon running
        try:
            while self.running:
                time.sleep(60)  # Sleep for 1 minute
                
                # Periodic health check log
                if datetime.now().minute == 0:  # Log once per hour
                    logger.info("Scheduler daemon is running...")
        
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.stop()
    
    def stop(self):
        """Stop the scheduler daemon"""
        logger.info("Stopping scheduler daemon...")
        
        if self.scheduler_service:
            self.scheduler_service.stop()
        
        self.running = False
        logger.info("Scheduler daemon stopped")


def main():
    """Main entry point"""
    daemon = SchedulerDaemon()
    
    try:
        daemon.start()
    except Exception as e:
        logger.error(f"Fatal error in scheduler daemon: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
