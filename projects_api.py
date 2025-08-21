"""
API endpoints for project management
"""
from flask import Blueprint, jsonify, request
from database_models import db, Project, Schedule, KeywordQueue, Article
from datetime import datetime
import traceback

# Create a Blueprint for project management
projects_api_bp = Blueprint('projects-api', __name__)

@projects_api_bp.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects with statistics"""
    try:
        projects = Project.query.all()
        projects_data = []
        
        for project in projects:
            project_dict = project.to_dict()
            
            # Add additional statistics
            project_dict['stats'] = {
                'total_keywords': len(project.keywords),
                'pending_keywords': len([k for k in project.keywords if k.status == 'pending']),
                'processing_keywords': len([k for k in project.keywords if k.status == 'processing']),
                'completed_keywords': len([k for k in project.keywords if k.status == 'completed']),
                'failed_keywords': len([k for k in project.keywords if k.status == 'failed']),
                'total_articles': len(project.articles),
                'active_schedules': len([s for s in project.schedules if s.is_active])
            }
            
            projects_data.append(project_dict)
        
        return jsonify({
            'success': True,
            'projects': projects_data,
            'total': len(projects_data)
        })
        
    except Exception as e:
        print(f"Error in get_projects: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@projects_api_bp.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'Project name is required'}), 400
        if not data.get('website_url'):
            return jsonify({'success': False, 'error': 'Website URL is required'}), 400
        
        # Check if project name already exists
        existing_project = Project.query.filter_by(name=data['name']).first()
        if existing_project:
            return jsonify({'success': False, 'error': 'Project name already exists'}), 400
        
        # Create new project
        project = Project(
            name=data['name'],
            website_url=data['website_url'],
            wordpress_user=data.get('wordpress_user'),
            wordpress_password=data.get('wordpress_password'),
            neuron_project_id=data.get('neuron_project_id'),
            default_language=data.get('default_language', 'en'),
            default_engine=data.get('default_engine', 'google'),
            daily_keywords_limit=data.get('daily_keywords_limit', 5),
            status=data.get('status', 'active')
        )
        
        db.session.add(project)
        db.session.commit()
        
        # Create default schedule
        default_schedule = Schedule(
            project_id=project.id,
            name=f"{project.name} - Default Schedule",
            daily_limit=project.daily_keywords_limit,
            days_of_week=[1, 2, 3, 4, 5]  # Weekdays
        )
        
        db.session.add(default_schedule)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project created successfully',
            'project': project.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in create_project: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@projects_api_bp.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project with detailed information"""
    try:
        project = Project.query.get_or_404(project_id)
        project_data = project.to_dict()
        
        # Add detailed information
        project_data['schedules'] = [schedule.to_dict() for schedule in project.schedules]
        project_data['recent_keywords'] = [
            kw.to_dict() for kw in 
            KeywordQueue.query.filter_by(project_id=project_id)
            .order_by(KeywordQueue.created_at.desc())
            .limit(10).all()
        ]
        project_data['recent_articles'] = [
            article.to_dict() for article in
            Article.query.filter_by(project_id=project_id)
            .order_by(Article.created_at.desc())
            .limit(10).all()
        ]
        
        return jsonify({
            'success': True,
            'project': project_data
        })
        
    except Exception as e:
        print(f"Error in get_project: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@projects_api_bp.route('/api/projects/<int:project_id>/keywords', methods=['POST'])
def add_keywords_to_project(project_id):
    """Add keywords to a project"""
    try:
        project = Project.query.get_or_404(project_id)
        data = request.get_json()
        
        # Validate input
        if not data.get('keywords'):
            return jsonify({'success': False, 'error': 'Keywords list is required'}), 400
        
        keywords_list = data['keywords']
        if not isinstance(keywords_list, list):
            return jsonify({'success': False, 'error': 'Keywords must be a list'}), 400
        
        # Get default schedule for the project
        default_schedule = Schedule.query.filter_by(
            project_id=project_id, 
            is_active=True
        ).first()
        
        added_keywords = []
        skipped_keywords = []
        
        for keyword_data in keywords_list:
            if isinstance(keyword_data, str):
                keyword_text = keyword_data
                priority = 1
                tags = []
                category_id = None
            elif isinstance(keyword_data, dict):
                keyword_text = keyword_data.get('keyword')
                priority = keyword_data.get('priority', 1)
                tags = keyword_data.get('tags', [])
                category_id = keyword_data.get('category_id')
            else:
                continue
            
            if not keyword_text:
                continue
            
            # Check if keyword already exists for this project
            existing_keyword = KeywordQueue.query.filter_by(
                project_id=project_id,
                keyword=keyword_text
            ).first()
            
            if existing_keyword:
                skipped_keywords.append(keyword_text)
                continue
            
            # Create new keyword
            keyword = KeywordQueue(
                project_id=project_id,
                schedule_id=default_schedule.id if default_schedule else None,
                keyword=keyword_text,
                priority=priority,
                category_id=category_id,
                tags_json=tags
            )
            
            db.session.add(keyword)
            added_keywords.append(keyword_text)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Added {len(added_keywords)} keywords, skipped {len(skipped_keywords)} duplicates',
            'added': len(added_keywords),
            'skipped': len(skipped_keywords),
            'skipped_keywords': skipped_keywords
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in add_keywords_to_project: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@projects_api_bp.route('/api/dashboard', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Overall statistics
        total_projects = Project.query.count()
        active_projects = Project.query.filter_by(status='active').count()
        
        total_keywords = KeywordQueue.query.count()
        pending_keywords = KeywordQueue.query.filter_by(status='pending').count()
        processing_keywords = KeywordQueue.query.filter_by(status='processing').count()
        completed_keywords = KeywordQueue.query.filter_by(status='completed').count()
        failed_keywords = KeywordQueue.query.filter_by(status='failed').count()
        
        total_articles = Article.query.count()
        
        # Recent activity
        recent_articles = Article.query.order_by(Article.created_at.desc()).limit(5).all()
        recent_keywords = KeywordQueue.query.order_by(KeywordQueue.created_at.desc()).limit(10).all()
        
        return jsonify({
            'success': True,
            'stats': {
                'projects': {
                    'total': total_projects,
                    'active': active_projects,
                    'inactive': total_projects - active_projects
                },
                'keywords': {
                    'total': total_keywords,
                    'pending': pending_keywords,
                    'processing': processing_keywords,
                    'completed': completed_keywords,
                    'failed': failed_keywords
                },
                'articles': {
                    'total': total_articles
                }
            },
            'recent_activity': {
                'articles': [article.to_dict() for article in recent_articles],
                'keywords': [keyword.to_dict() for keyword in recent_keywords]
            }
        })
        
    except Exception as e:
        print(f"Error in get_dashboard_stats: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500