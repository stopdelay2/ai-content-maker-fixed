"""
Database-based scheduler for processing keywords from projects
"""
import logging
import traceback
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from configs import app
from database_models import db, Project, Schedule, KeywordQueue, Article
from routes.publish_to_wordpress import create_article_and_publish_internal

WORKER_ID = "database-scheduler"

def get_eligible_projects() -> List[Project]:
    """Get all active projects that should be processed"""
    with app.app_context():
        return Project.query.filter_by(status='active').all()


def get_project_schedules(project_id: int) -> List[Schedule]:
    """Get active schedules for a project"""
    with app.app_context():
        return Schedule.query.filter_by(
            project_id=project_id,
            is_active=True
        ).all()


def should_schedule_run_today(schedule: Schedule) -> bool:
    """Check if schedule should run today based on days_of_week"""
    today = datetime.now().weekday()  # 0=Monday, 6=Sunday
    
    # Convert Python weekday to our format (1=Sunday, 7=Saturday)
    our_weekday = 1 if today == 6 else today + 2
    
    days_of_week = schedule.get_days_of_week()
    return our_weekday in days_of_week


def claim_keywords_for_schedule(schedule: Schedule, limit: int) -> List[KeywordQueue]:
    """Claim pending keywords for processing"""
    with app.app_context():
        # Get current time
        now = datetime.now(timezone.utc)
        lease_until = now + timedelta(hours=2)  # 2-hour lease
        
        # Find pending keywords or keywords with expired leases
        keywords = KeywordQueue.query.filter(
            KeywordQueue.project_id == schedule.project_id,
            KeywordQueue.schedule_id == schedule.id,
            db.or_(
                KeywordQueue.status == 'pending',
                db.and_(
                    KeywordQueue.status == 'processing',
                    KeywordQueue.lease_until < now
                )
            )
        ).order_by(
            KeywordQueue.priority.desc(),
            KeywordQueue.created_at.asc()
        ).limit(limit).all()
        
        # Claim the keywords
        claimed_keywords = []
        for keyword in keywords:
            keyword.status = 'processing'
            keyword.processing_by = WORKER_ID
            keyword.lease_until = lease_until
            claimed_keywords.append(keyword)
        
        db.session.commit()
        return claimed_keywords


def process_keyword(keyword: KeywordQueue, project: Project) -> bool:
    """Process a single keyword"""
    with app.app_context():
        try:
            logging.info(f"Processing keyword: {keyword.keyword} for project: {project.name}")
            
            # Increment attempts
            keyword.attempts += 1
            db.session.commit()
            
            # Call the existing article creation function
            result = create_article_and_publish_internal(
                keyword=keyword.keyword,
                project_id=project.neuron_project_id or "default",  # Use project's neuron ID
                engine=project.default_engine,
                language=project.default_language,
                site=project.website_url
            )
            
            success = bool(result.get("success"))
            
            if success:
                # Mark as completed and create article record
                keyword.status = 'completed'
                keyword.processed_at = datetime.now(timezone.utc)
                keyword.error_message = None
                
                # Create article record
                article = Article(
                    project_id=keyword.project_id,
                    keyword_id=keyword.id,
                    title=result.get('title', 'Generated Article'),
                    content_score=result.get('content_score'),
                    published_at=datetime.now(timezone.utc)
                )
                db.session.add(article)
                
                logging.info(f"Successfully processed keyword: {keyword.keyword}")
                
            else:
                # Mark as failed
                keyword.status = 'failed'
                keyword.error_message = result.get('message') or result.get('error') or 'Unknown error'
                logging.warning(f"Failed to process keyword: {keyword.keyword} - {keyword.error_message}")
            
            db.session.commit()
            return success
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            logging.exception(f"Exception processing keyword {keyword.keyword}: {error_msg}")
            
            # Mark as failed
            keyword.status = 'failed'
            keyword.error_message = error_msg[:500]  # Truncate long error messages
            db.session.commit()
            
            return False


def run_database_scheduler():
    """Main scheduler function to process keywords from database"""
    logging.info("Starting database scheduler run")
    
    try:
        with app.app_context():
            # Get all active projects
            projects = get_eligible_projects()
            
            if not projects:
                logging.info("No active projects found")
                return
            
            total_processed = 0
            total_succeeded = 0
            total_failed = 0
            
            for project in projects:
                logging.info(f"Processing project: {project.name}")
                
                # Get active schedules for this project
                schedules = get_project_schedules(project.id)
                
                if not schedules:
                    logging.info(f"No active schedules for project: {project.name}")
                    continue
                
                for schedule in schedules:
                    # Check if schedule should run today
                    if not should_schedule_run_today(schedule):
                        logging.info(f"Schedule {schedule.name} not scheduled for today")
                        continue
                    
                    logging.info(f"Processing schedule: {schedule.name} (limit: {schedule.daily_limit})")
                    
                    # Claim keywords for processing
                    keywords = claim_keywords_for_schedule(schedule, schedule.daily_limit)
                    
                    if not keywords:
                        logging.info(f"No eligible keywords for schedule: {schedule.name}")
                        continue
                    
                    logging.info(f"Claimed {len(keywords)} keywords for processing")
                    
                    # Process each keyword
                    for keyword in keywords:
                        success = process_keyword(keyword, project)
                        total_processed += 1
                        
                        if success:
                            total_succeeded += 1
                        else:
                            total_failed += 1
            
            logging.info(f"Scheduler run completed. Processed: {total_processed}, "
                        f"Succeeded: {total_succeeded}, Failed: {total_failed}")
    
    except Exception as e:
        logging.exception(f"Error in database scheduler: {e}")


def get_queue_stats() -> dict:
    """Get current queue statistics"""
    with app.app_context():
        stats = {
            'total_projects': Project.query.count(),
            'active_projects': Project.query.filter_by(status='active').count(),
            'total_keywords': KeywordQueue.query.count(),
            'pending_keywords': KeywordQueue.query.filter_by(status='pending').count(),
            'processing_keywords': KeywordQueue.query.filter_by(status='processing').count(),
            'completed_keywords': KeywordQueue.query.filter_by(status='completed').count(),
            'failed_keywords': KeywordQueue.query.filter_by(status='failed').count(),
            'total_articles': Article.query.count()
        }
        
        # Check for expired processing keywords
        now = datetime.now(timezone.utc)
        expired_keywords = KeywordQueue.query.filter(
            KeywordQueue.status == 'processing',
            KeywordQueue.lease_until < now
        ).count()
        stats['expired_keywords'] = expired_keywords
        
        return stats


def cleanup_expired_keywords():
    """Reset expired processing keywords to pending"""
    with app.app_context():
        now = datetime.now(timezone.utc)
        
        expired_keywords = KeywordQueue.query.filter(
            KeywordQueue.status == 'processing',
            KeywordQueue.lease_until < now
        ).all()
        
        for keyword in expired_keywords:
            keyword.status = 'pending'
            keyword.processing_by = None
            keyword.lease_until = None
            logging.info(f"Reset expired keyword: {keyword.keyword}")
        
        if expired_keywords:
            db.session.commit()
            logging.info(f"Reset {len(expired_keywords)} expired keywords")


# Wrapper function for APScheduler compatibility
def database_scheduled_job():
    """Entry point for APScheduler - runs the database-based scheduler"""
    try:
        cleanup_expired_keywords()
        run_database_scheduler()
        
        # Print stats
        stats = get_queue_stats()
        logging.info(f"Queue stats: {stats}")
        
    except Exception as e:
        logging.exception(f"Error in database_scheduled_job: {e}")


if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)
    database_scheduled_job()