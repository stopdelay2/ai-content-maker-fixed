"""
Vercel serverless function entry point
"""
import os
import sys
from flask import Flask, render_template, jsonify, request

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

app = Flask(__name__)

# Basic configuration for serverless
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Simple in-memory storage for demo (replace with external DB in production)
projects_data = []
dashboard_stats = {
    'projects': {'total': 0, 'active': 0, 'inactive': 0},
    'keywords': {'total': 0, 'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0},
    'articles': {'total': 0}
}

@app.route('/')
def dashboard():
    """Render the main dashboard"""
    # Simple HTML response since we can't use templates in serverless easily
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Content Maker - Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100">
        <div class="min-h-screen">
            <header class="bg-white shadow">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="flex justify-between h-16">
                        <div class="flex items-center">
                            <h1 class="text-2xl font-bold text-gray-900">🤖 AI Content Maker</h1>
                        </div>
                    </div>
                </div>
            </header>
            
            <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
                <div class="bg-white overflow-hidden shadow rounded-lg p-6">
                    <h2 class="text-xl font-semibold text-gray-900 mb-4">Welcome to AI Content Maker</h2>
                    <p class="text-gray-600 mb-4">
                        Your automated content creation system is running on Vercel serverless infrastructure.
                    </p>
                    
                    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <h3 class="font-medium text-blue-900">System Status</h3>
                        <p class="text-blue-700">✅ API endpoints are active</p>
                        <p class="text-blue-700">⚠️ Background scheduler disabled (serverless)</p>
                        <p class="text-blue-700">🔧 Use manual triggers for processing</p>
                    </div>
                    
                    <div class="mt-6">
                        <h3 class="font-medium text-gray-900 mb-2">Available Endpoints:</h3>
                        <ul class="text-sm text-gray-600 space-y-1">
                            <li>• GET /api/dashboard - Dashboard statistics</li>
                            <li>• GET /api/projects - List all projects</li>
                            <li>• POST /api/projects - Create new project</li>
                            <li>• POST /seo/create-article - Create article</li>
                            <li>• POST /api/trigger-scheduler - Manual trigger</li>
                        </ul>
                    </div>
                </div>
            </main>
        </div>
    </body>
    </html>
    '''

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    return jsonify({
        'success': True,
        'stats': dashboard_stats,
        'recent_activity': {
            'articles': [],
            'keywords': []
        }
    })

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    return jsonify({
        'success': True,
        'projects': projects_data,
        'total': len(projects_data)
    })

@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    try:
        data = request.get_json()
        
        if not data.get('name') or not data.get('website_url'):
            return jsonify({'success': False, 'error': 'Name and website URL are required'}), 400
        
        # Simple project creation (in production, use external database)
        project = {
            'id': len(projects_data) + 1,
            'name': data['name'],
            'website_url': data['website_url'],
            'wordpress_user': data.get('wordpress_user', ''),
            'daily_keywords_limit': data.get('daily_keywords_limit', 5),
            'status': 'active',
            'stats': {
                'total_keywords': 0,
                'total_articles': 0,
                'pending_keywords': 0,
                'completed_keywords': 0,
                'failed_keywords': 0
            }
        }
        
        projects_data.append(project)
        dashboard_stats['projects']['total'] += 1
        dashboard_stats['projects']['active'] += 1
        
        return jsonify({
            'success': True,
            'message': 'Project created successfully',
            'project': project
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trigger-scheduler', methods=['POST'])
def trigger_scheduler():
    """Manual scheduler trigger"""
    return jsonify({
        'success': True,
        'message': 'Scheduler functionality available in local development mode only'
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'environment': 'vercel-serverless',
        'message': 'AI Content Maker API is running'
    })

# Vercel expects the Flask app to be available at module level
application = app

if __name__ == '__main__':
    app.run(debug=True)