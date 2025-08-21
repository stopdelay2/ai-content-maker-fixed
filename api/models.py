"""
Database models for AI Content Maker - Vercel optimized
"""
import os
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

class Project(db.Model):
    """Model for managing content creation projects"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    website_url = db.Column(db.String(255), nullable=False)
    
    # WordPress Configuration
    wordpress_user = db.Column(db.String(100))
    wordpress_password = db.Column(db.String(255))  # In production: encrypt this!
    
    # Neuron Writer Configuration  
    neuron_project_id = db.Column(db.String(100), nullable=False)
    neuron_search_engine = db.Column(db.String(50), nullable=False, default='google.com')
    neuron_language = db.Column(db.String(20), nullable=False, default='English')
    
    # Settings
    daily_keywords_limit = db.Column(db.Integer, default=5)
    
    # Status and Timestamps
    status = db.Column(db.String(20), default='active')  # active, paused, inactive
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    keywords = db.relationship('Keyword', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def get_neuron_settings(self):
        """Get Neuron Writer settings as dict"""
        return {
            'project_id': self.neuron_project_id,
            'search_engine': self.neuron_search_engine,
            'language': self.neuron_language
        }
    
    def get_wordpress_status(self):
        """Get WordPress connection status (will be updated later)"""
        return {
            'connected': bool(self.wordpress_user and self.wordpress_password),
            'categories': [],  # Will be populated by connection test
            'error': None
        }
    
    def get_stats(self):
        """Get project statistics"""
        return {
            'total_keywords': len(self.keywords),
            'pending_keywords': len([k for k in self.keywords if k.status == 'pending']),
            'processing_keywords': len([k for k in self.keywords if k.status == 'processing']),
            'completed_keywords': len([k for k in self.keywords if k.status == 'completed']),
            'failed_keywords': len([k for k in self.keywords if k.status == 'failed']),
            'total_articles': len([k for k in self.keywords if k.status == 'completed'])
        }
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'website_url': self.website_url,
            'wordpress_user': self.wordpress_user,
            'wordpress_password': self.wordpress_password,  # Remove in production UI
            'daily_keywords_limit': self.daily_keywords_limit,
            'neuron_settings': self.get_neuron_settings(),
            'status': self.status,
            'wordpress_status': self.get_wordpress_status(),
            'stats': self.get_stats(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Project {self.name}>'


class Keyword(db.Model):
    """Model for managing keyword processing queue"""
    __tablename__ = 'keywords'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    
    # Keyword Information
    keyword = db.Column(db.String(255), nullable=False)
    
    # Processing Status
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    
    # Article Information (when completed)
    article_title = db.Column(db.String(500))
    content_score = db.Column(db.Integer)
    wordpress_post_id = db.Column(db.Integer)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed_at = db.Column(db.DateTime(timezone=True))
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'keyword': self.keyword,
            'status': self.status,
            'article_title': self.article_title,
            'content_score': self.content_score,
            'wordpress_post_id': self.wordpress_post_id,
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
    
    def __repr__(self):
        return f'<Keyword {self.keyword} ({self.status})>'