"""
Database models for the AI Content Articles Maker project management system
"""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON
import json

db = SQLAlchemy()

class Project(db.Model):
    """Model for managing content creation projects (websites)"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    website_url = db.Column(db.String(255), nullable=False)
    
    # WordPress Configuration
    wordpress_user = db.Column(db.String(100))
    wordpress_password = db.Column(db.String(255))
    
    # Neuron Writer Configuration  
    neuron_project_id = db.Column(db.String(100))
    
    # Default Settings
    default_language = db.Column(db.String(10), default='en')
    default_engine = db.Column(db.String(50), default='google')
    daily_keywords_limit = db.Column(db.Integer, default=5)
    
    # Status and Timestamps
    status = db.Column(db.Enum('active', 'paused', 'inactive', name='project_status'), default='active')
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    schedules = db.relationship('Schedule', backref='project', lazy=True, cascade='all, delete-orphan')
    keywords = db.relationship('KeywordQueue', backref='project', lazy=True, cascade='all, delete-orphan')
    articles = db.relationship('Article', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'website_url': self.website_url,
            'wordpress_user': self.wordpress_user,
            'neuron_project_id': self.neuron_project_id,
            'default_language': self.default_language,
            'default_engine': self.default_engine,
            'daily_keywords_limit': self.daily_keywords_limit,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'total_keywords': len(self.keywords),
            'active_schedules': len([s for s in self.schedules if s.is_active])
        }
    
    def __repr__(self):
        return f'<Project {self.name}>'


class Schedule(db.Model):
    """Model for scheduling content creation"""
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    
    # Scheduling Configuration
    daily_limit = db.Column(db.Integer, default=5)
    start_time = db.Column(db.Time, default=lambda: datetime.min.time())
    timezone = db.Column(db.String(50), default='Asia/Jerusalem')
    days_of_week = db.Column(JSON)  # [1,2,3,4,5] = Sunday-Thursday
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    keywords = db.relationship('KeywordQueue', backref='schedule', lazy=True)
    
    def get_days_of_week(self):
        """Get days of week as list"""
        if isinstance(self.days_of_week, str):
            return json.loads(self.days_of_week)
        return self.days_of_week or [1, 2, 3, 4, 5]  # Default to weekdays
    
    def set_days_of_week(self, days):
        """Set days of week from list"""
        self.days_of_week = days
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'daily_limit': self.daily_limit,
            'start_time': self.start_time.strftime('%H:%M:%S') if self.start_time else None,
            'timezone': self.timezone,
            'days_of_week': self.get_days_of_week(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'pending_keywords': len([k for k in self.keywords if k.status == 'pending'])
        }
    
    def __repr__(self):
        return f'<Schedule {self.name}>'


class KeywordQueue(db.Model):
    """Model for managing keyword processing queue"""
    __tablename__ = 'keywords_queue'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=True)
    
    # Keyword Information
    keyword = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer)
    tags_json = db.Column(JSON)
    priority = db.Column(db.Integer, default=1)
    
    # Processing Status
    status = db.Column(db.Enum('pending', 'processing', 'completed', 'failed', 'paused', name='keyword_status'), default='pending')
    processing_by = db.Column(db.String(100))
    lease_until = db.Column(db.DateTime(timezone=True))
    scheduled_for = db.Column(db.DateTime(timezone=True))
    processed_at = db.Column(db.DateTime(timezone=True))
    
    # Error Handling
    error_message = db.Column(db.Text)
    attempts = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    articles = db.relationship('Article', backref='keyword', lazy=True, cascade='all, delete-orphan')
    
    def get_tags(self):
        """Get tags as list"""
        if isinstance(self.tags_json, str):
            return json.loads(self.tags_json)
        return self.tags_json or []
    
    def set_tags(self, tags):
        """Set tags from list"""
        self.tags_json = tags
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'schedule_id': self.schedule_id,
            'keyword': self.keyword,
            'category_id': self.category_id,
            'tags': self.get_tags(),
            'priority': self.priority,
            'status': self.status,
            'processing_by': self.processing_by,
            'lease_until': self.lease_until.isoformat() if self.lease_until else None,
            'scheduled_for': self.scheduled_for.isoformat() if self.scheduled_for else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'error_message': self.error_message,
            'attempts': self.attempts,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<KeywordQueue {self.keyword} ({self.status})>'


class Article(db.Model):
    """Model for tracking generated articles"""
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    keyword_id = db.Column(db.Integer, db.ForeignKey('keywords_queue.id'), nullable=False)
    
    # Article Information
    title = db.Column(db.String(500))
    content_score = db.Column(db.Integer)
    wordpress_post_id = db.Column(db.Integer)
    
    # Timestamps
    published_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'keyword_id': self.keyword_id,
            'title': self.title,
            'content_score': self.content_score,
            'wordpress_post_id': self.wordpress_post_id,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'keyword': self.keyword.keyword if self.keyword else None
        }
    
    def __repr__(self):
        return f'<Article {self.title}>'