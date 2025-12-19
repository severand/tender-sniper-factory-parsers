"""Scheduler logic for managing task execution"""

from sqlalchemy.orm import Session
from factory_parsers.shared.logger import logger
from factory_parsers.admin_service.repositories import SearchRuleRepository
from factory_parsers.scheduler_service.celery_app import celery_app
from factory_parsers.scheduler_service.tasks import fetch_tenders_api, fetch_tenders_web


class TenderScheduler:
    """Scheduler for managing tender fetching tasks"""
    
    def __init__(self, db: Session):
        self.db = db
        self.rule_repo = SearchRuleRepository(db)
    
    def schedule_active_rules(self) -> dict:
        """Schedule all active search rules
        
        Returns:
            Dictionary with scheduling results
        """
        from factory_parsers.admin_service.repositories import PlatformRepository
        
        platform_repo = PlatformRepository(self.db)
        platforms = platform_repo.list_all(active_only=True)
        
        scheduled = 0
        failed = 0
        
        for platform in platforms:
            rules = self.rule_repo.get_by_platform(platform.id, active_only=True)
            for rule in rules:
                try:
                    self.schedule_rule(platform.id, rule.id)
                    scheduled += 1
                except Exception as e:
                    logger.error(f"Failed to schedule rule {rule.id}: {str(e)}")
                    failed += 1
        
        return {
            "scheduled": scheduled,
            "failed": failed,
            "total": scheduled + failed
        }
    
    def schedule_rule(self, platform_id: int, rule_id: int) -> str:
        """Schedule a specific search rule
        
        Args:
            platform_id: Platform ID
            rule_id: SearchRule ID
        
        Returns:
            Task ID
        """
        logger.info(f"Scheduling rule {rule_id} for platform {platform_id}")
        
        # Determine if API or web scraping
        from factory_parsers.admin_service.models import Platform
        
        platform = self.db.query(Platform).filter(Platform.id == platform_id).first()
        if not platform:
            raise ValueError(f"Platform {platform_id} not found")
        
        if platform.api_endpoint and platform.api_key:
            # Use API
            task = fetch_tenders_api.delay(platform_id, rule_id)
        else:
            # Use web scraping
            task = fetch_tenders_web.delay(platform_id, rule_id)
        
        logger.info(f"Scheduled task {task.id} for rule {rule_id}")
        return task.id
    
    def get_task_status(self, task_id: str) -> dict:
        """Get Celery task status
        
        Args:
            task_id: Celery task ID
        
        Returns:
            Task status information
        """
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id, app=celery_app)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.successful() else None,
            "error": str(result.info) if result.failed() else None
        }


def schedule_all_platforms(db: Session) -> dict:
    """Schedule all active platforms
    
    Args:
        db: Database session
    
    Returns:
        Scheduling results
    """
    scheduler = TenderScheduler(db)
    return scheduler.schedule_active_rules()
