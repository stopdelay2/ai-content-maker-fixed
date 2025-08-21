"""
Vercel serverless function entry point with PostgreSQL
"""
import os
import sys
import base64
import json
import requests
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

app = Flask(__name__)

# Database configuration for Neon Postgres
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
# Use Neon Postgres connection string (pooled version is recommended)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('POSTGRES_URL', 'sqlite:///fallback.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_timeout': 20,
    'pool_recycle': -1,
    'pool_pre_ping': True
}

# Initialize database
from models import db, Project, Keyword
db.init_app(app)

# Create tables when app starts
def init_database():
    """Initialize database tables"""
    try:
        with app.app_context():
            db.create_all()
            print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")

# Initialize database on startup
init_database()

# Add database health check
def check_database_connection():
    """Check if database connection is working"""
    try:
        with app.app_context():
            # Try to execute a simple query
            result = db.session.execute(db.text('SELECT 1')).fetchone()
            print(f"Database connection successful: {result}")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

# Check connection on startup
print("Checking database connection...")
check_database_connection()

def get_dashboard_stats():
    """Calculate dashboard statistics from database"""
    try:
        projects = Project.query.all()
        total_projects = len(projects)
        active_projects = len([p for p in projects if p.status == 'active'])
        
        all_keywords = Keyword.query.all()
        total_keywords = len(all_keywords)
        pending_keywords = len([k for k in all_keywords if k.status == 'pending'])
        processing_keywords = len([k for k in all_keywords if k.status == 'processing'])
        completed_keywords = len([k for k in all_keywords if k.status == 'completed'])
        failed_keywords = len([k for k in all_keywords if k.status == 'failed'])
        
        return {
            'projects': {'total': total_projects, 'active': active_projects, 'inactive': total_projects - active_projects},
            'keywords': {'total': total_keywords, 'pending': pending_keywords, 'processing': processing_keywords, 'completed': completed_keywords, 'failed': failed_keywords},
            'articles': {'total': completed_keywords}
        }
    except Exception as e:
        print(f"Error calculating stats: {e}")
        return {
            'projects': {'total': 0, 'active': 0, 'inactive': 0},
            'keywords': {'total': 0, 'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0},
            'articles': {'total': 0}
        }

def test_wordpress_connection(site_url, username, app_password):
    """Test WordPress connection and return categories"""
    try:
        # Clean up site URL
        site_url = site_url.rstrip('/')
        if not site_url.startswith(('http://', 'https://')):
            site_url = 'https://' + site_url
        
        # Create auth header
        auth = base64.b64encode(f"{username}:{app_password}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json"
        }
        
        # Test connection with categories endpoint
        categories_url = f"{site_url}/wp-json/wp/v2/categories"
        response = requests.get(categories_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            categories = response.json()
            return {
                'success': True,
                'connected': True,
                'categories': categories,
                'site_info': {
                    'url': site_url,
                    'categories_count': len(categories)
                }
            }
        elif response.status_code == 401:
            return {
                'success': False,
                'connected': False,
                'error': 'אימות נכשל - בדוק את שם המשתמש וסיסמת האפליקציה'
            }
        else:
            return {
                'success': False,
                'connected': False,
                'error': f'שגיאה בחיבור: {response.status_code} - {response.text}'
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'connected': False,
            'error': 'פסק זמן - האתר לא מגיב'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'connected': False,
            'error': 'לא ניתן להתחבר לאתר - בדוק את כתובת האתר'
        }
    except Exception as e:
        return {
            'success': False,
            'connected': False,
            'error': f'שגיאה כללית: {str(e)}'
        }

@app.route('/')
def dashboard():
    """Render the full dashboard"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Content Maker - Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
</head>
<body class="bg-gray-100">
    <div x-data="dashboard()" x-init="loadDashboard()" class="min-h-screen">
        <!-- Header -->
        <header class="bg-white shadow">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between h-16">
                    <div class="flex items-center">
                        <h1 class="text-2xl font-bold text-gray-900">🤖 AI Content Maker</h1>
                    </div>
                    <div class="flex items-center space-x-4">
                        <button @click="showCreateProject = true" 
                                class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium">
                            + New Project
                        </button>
                    </div>
                </div>
            </div>
        </header>

        <!-- Navigation -->
        <nav class="bg-white border-b border-gray-200">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex space-x-8">
                    <a href="#" @click.prevent="currentView = 'dashboard'" 
                       :class="currentView === 'dashboard' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
                       class="border-b-2 py-4 px-1 text-sm font-medium">
                        Dashboard
                    </a>
                    <a href="#" @click.prevent="currentView = 'projects'" 
                       :class="currentView === 'projects' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
                       class="border-b-2 py-4 px-1 text-sm font-medium">
                        Projects
                    </a>
                </div>
            </div>
        </nav>

        <!-- Main Content -->
        <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            <!-- Loading -->
            <div x-show="loading" class="flex justify-center items-center py-12">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>

            <!-- Dashboard View -->
            <div x-show="!loading && currentView === 'dashboard'">
                <!-- Stats Cards -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                                        <span class="text-white text-sm font-bold">P</span>
                                    </div>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Active Projects</dt>
                                        <dd class="text-lg font-medium text-gray-900" x-text="stats.projects?.active || 0"></dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <div class="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                                        <span class="text-white text-sm font-bold">K</span>
                                    </div>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Total Keywords</dt>
                                        <dd class="text-lg font-medium text-gray-900" x-text="stats.keywords?.total || 0"></dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                                        <span class="text-white text-sm font-bold">A</span>
                                    </div>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Total Articles</dt>
                                        <dd class="text-lg font-medium text-gray-900" x-text="stats.articles?.total || 0"></dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <div class="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                                        <span class="text-white text-sm font-bold">🚀</span>
                                    </div>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Status</dt>
                                        <dd class="text-lg font-medium text-green-600">Active</dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- System Info -->
                <div class="bg-white shadow rounded-lg p-6 mb-6">
                    <h3 class="text-lg font-medium text-gray-900 mb-4">🎯 How to Get Started</h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div class="text-center p-4 bg-blue-50 rounded-lg">
                            <div class="text-2xl mb-2">1️⃣</div>
                            <h4 class="font-medium text-gray-900">Create Project</h4>
                            <p class="text-sm text-gray-600 mt-1">Click "+ New Project" to add your WordPress site</p>
                        </div>
                        <div class="text-center p-4 bg-green-50 rounded-lg">
                            <div class="text-2xl mb-2">2️⃣</div>
                            <h4 class="font-medium text-gray-900">Add Keywords</h4>
                            <p class="text-sm text-gray-600 mt-1">Upload your target keywords for article generation</p>
                        </div>
                        <div class="text-center p-4 bg-purple-50 rounded-lg">
                            <div class="text-2xl mb-2">3️⃣</div>
                            <h4 class="font-medium text-gray-900">Generate Content</h4>
                            <p class="text-sm text-gray-600 mt-1">AI will create and publish SEO articles automatically</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Projects View -->
            <div x-show="!loading && currentView === 'projects'">
                <div class="mb-6 flex justify-between items-center">
                    <h2 class="text-2xl font-bold text-gray-900">Projects</h2>
                    <button @click="showCreateProject = true" 
                            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium">
                        + Add Project
                    </button>
                </div>
                
                <!-- Keywords Modal -->
                <div x-show="showKeywords" x-cloak 
                     class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                    <div class="relative top-10 mx-auto p-5 border w-4/5 max-w-4xl shadow-lg rounded-md bg-white">
                        <div class="mt-3">
                            <div class="flex justify-between items-center mb-4">
                                <h3 class="text-lg font-medium text-gray-900" x-text="`Keywords for ${selectedProject?.name || 'Project'}`"></h3>
                                <button @click="closeKeywords()" class="text-gray-400 hover:text-gray-600">
                                    <span class="text-2xl">&times;</span>
                                </button>
                            </div>
                            
                            <!-- Keywords Table -->
                            <div class="overflow-x-auto">
                                <div x-show="projectKeywords.length === 0" class="text-center py-8 text-gray-500">
                                    אין מילות מפתח עדיין. הוסף מילות מפתח תחילה.
                                </div>
                                
                                <table x-show="projectKeywords.length > 0" class="min-w-full bg-white">
                                    <thead class="bg-gray-50">
                                        <tr>
                                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">מילת מפתח</th>
                                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">סטטוס</th>
                                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ציון</th>
                                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">תאריך</th>
                                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">פעולות</th>
                                        </tr>
                                    </thead>
                                    <tbody class="bg-white divide-y divide-gray-200">
                                        <template x-for="keyword in projectKeywords" :key="keyword.id">
                                            <tr>
                                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900" x-text="keyword.keyword"></td>
                                                <td class="px-6 py-4 whitespace-nowrap">
                                                    <span :class="{
                                                        'bg-yellow-100 text-yellow-800': keyword.status === 'pending',
                                                        'bg-blue-100 text-blue-800': keyword.status === 'processing', 
                                                        'bg-green-100 text-green-800': keyword.status === 'completed',
                                                        'bg-red-100 text-red-800': keyword.status === 'failed'
                                                    }" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" x-text="keyword.status"></span>
                                                </td>
                                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900" x-text="keyword.content_score || '-'"></td>
                                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500" x-text="keyword.created_at"></td>
                                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                                    <button x-show="keyword.status === 'pending'" 
                                                            @click="createArticle(keyword)" 
                                                            class="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-xs">
                                                        צור מאמר
                                                    </button>
                                                    <span x-show="keyword.status === 'processing'" class="text-blue-600 text-xs">מעבד...</span>
                                                    <span x-show="keyword.status === 'completed'" class="text-green-600 text-xs">הושלם ✓</span>
                                                    <span x-show="keyword.status === 'failed'" class="text-red-600 text-xs">נכשל</span>
                                                </td>
                                            </tr>
                                        </template>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Projects Grid -->
                <div x-show="projects.length === 0" class="text-center py-12">
                    <div class="text-gray-400 text-6xl mb-4">📁</div>
                    <h3 class="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
                    <p class="text-gray-500 mb-4">Create your first project to get started with AI content generation</p>
                    <button @click="showCreateProject = true" 
                            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium">
                        Create First Project
                    </button>
                </div>

                <div x-show="projects.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <template x-for="project in projects" :key="project.id">
                        <div class="bg-white overflow-hidden shadow rounded-lg">
                            <div class="px-4 py-5 sm:p-6">
                                <div class="flex items-center justify-between mb-4">
                                    <h3 class="text-lg font-medium text-gray-900" x-text="project.name"></h3>
                                    <div class="flex items-center space-x-2">
                                        <span x-show="project.wordpress_status?.connected" 
                                              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                            ✅ WordPress
                                        </span>
                                        <span x-show="project.wordpress_status && !project.wordpress_status.connected" 
                                              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
                                              :title="project.wordpress_status?.error">
                                            ❌ WordPress
                                        </span>
                                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                            Active
                                        </span>
                                    </div>
                                </div>
                                
                                <div class="text-sm text-gray-600 mb-4">
                                    <p x-text="project.website_url"></p>
                                    <p>Daily limit: <span x-text="project.daily_keywords_limit"></span> keywords</p>
                                    <p x-show="project.wordpress_status?.categories" class="text-xs text-blue-600">
                                        <span x-text="project.wordpress_status.categories.length"></span> קטגוריות באתר
                                    </p>
                                    <div x-show="project.neuron_settings" class="mt-2 p-2 bg-purple-50 rounded text-xs">
                                        <p class="text-purple-700 font-medium">🔍 SecretSEOApp Settings:</p>
                                        <p class="text-purple-600">Project: <span x-text="project.neuron_settings?.project_id"></span></p>
                                        <p class="text-purple-600">Engine: <span x-text="project.neuron_settings?.search_engine"></span></p>
                                        <p class="text-purple-600">Language: <span x-text="project.neuron_settings?.language"></span></p>
                                    </div>
                                </div>

                                <div class="grid grid-cols-2 gap-4 text-center">
                                    <div>
                                        <p class="text-2xl font-bold text-blue-600" x-text="project.stats?.total_keywords || 0"></p>
                                        <p class="text-xs text-gray-500">Keywords</p>
                                    </div>
                                    <div>
                                        <p class="text-2xl font-bold text-green-600" x-text="project.stats?.total_articles || 0"></p>
                                        <p class="text-xs text-gray-500">Articles</p>
                                    </div>
                                </div>

                                <div class="mt-4 flex space-x-2">
                                    <button @click="addKeywords(project.id)" 
                                            class="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-md text-sm">
                                        Add Keywords
                                    </button>
                                    <button @click="viewKeywords(project.id)" 
                                            class="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded-md text-sm">
                                        View Keywords
                                    </button>
                                </div>
                            </div>
                        </div>
                    </template>
                </div>
            </div>
        </main>

        <!-- Create Project Modal -->
        <div x-show="showCreateProject" x-cloak 
             class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                <div class="mt-3">
                    <h3 class="text-lg font-medium text-gray-900 mb-4">Create New Project</h3>
                    <form @submit.prevent="createProject()">
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-1">Project Name *</label>
                            <input x-model="newProject.name" type="text" required 
                                   class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-1">Website URL *</label>
                            <input x-model="newProject.website_url" type="url" required 
                                   class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-1">WordPress Username</label>
                            <input x-model="newProject.wordpress_user" type="text" 
                                   class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-1">WordPress App Password *</label>
                            <input x-model="newProject.wordpress_password" type="password" 
                                   class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                   placeholder="qp5R 8WET vkD6 YDwl Rlc3 oL7h">
                            <p class="text-xs text-gray-500 mt-1">סיסמת אפליקציה מהגדרות המשתמש בוורדפרס</p>
                        </div>
                        <div class="mb-4">
                            <button type="button" @click="testWordPressConnection()" 
                                    :disabled="!newProject.website_url || !newProject.wordpress_user || !newProject.wordpress_password || testingConnection"
                                    class="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-3 py-2 rounded-md text-sm mb-2">
                                <span x-show="!testingConnection">🔗 Test WordPress Connection</span>
                                <span x-show="testingConnection">בודק חיבור...</span>
                            </button>
                            
                            <!-- Connection Status -->
                            <div x-show="connectionStatus" class="mb-2">
                                <div x-show="connectionStatus?.success" class="p-3 bg-green-50 border border-green-200 rounded-lg">
                                    <div class="flex items-center">
                                        <span class="text-green-600 text-lg mr-2">✅</span>
                                        <span class="text-green-700 font-medium">חיבור תקין!</span>
                                    </div>
                                    <div x-show="connectionStatus?.categories" class="mt-2">
                                        <p class="text-sm text-green-600 mb-1">
                                            נמצאו <span x-text="connectionStatus?.categories?.length || 0"></span> קטגוריות:
                                        </p>
                                        <div class="max-h-20 overflow-y-auto text-xs text-green-600">
                                            <template x-for="category in connectionStatus?.categories?.slice(0, 5)" :key="category.id">
                                                <span x-text="category.name" class="inline-block bg-green-100 px-2 py-1 rounded mr-1 mb-1"></span>
                                            </template>
                                        </div>
                                    </div>
                                </div>
                                
                                <div x-show="!connectionStatus?.success" class="p-3 bg-red-50 border border-red-200 rounded-lg">
                                    <div class="flex items-center">
                                        <span class="text-red-600 text-lg mr-2">❌</span>
                                        <span class="text-red-700 font-medium">שגיאת חיבור</span>
                                    </div>
                                    <p class="text-sm text-red-600 mt-1" x-text="connectionStatus?.error"></p>
                                </div>
                            </div>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-1">Daily Keywords Limit</label>
                            <input x-model="newProject.daily_keywords_limit" type="number" min="1" max="50" value="5" 
                                   class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                        </div>
                        
                        <!-- SecretSEOApp Settings Section -->
                        <div class="mb-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
                            <h4 class="text-md font-semibold text-purple-900 mb-3 flex items-center">
                                🔍 SecretSEOApp Settings
                            </h4>
                            
                            <div class="mb-4">
                                <label class="block text-sm font-medium text-gray-700 mb-1">SEO Project ID *</label>
                                <input x-model="newProject.neuron_project_id" type="text" required 
                                       placeholder="16597e77d2635516"
                                       class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500">
                                <p class="text-xs text-gray-500 mt-1">מזהה הפרויקט ב-SecretSEOApp (16 תווים)</p>
                            </div>
                            
                            <div class="mb-4">
                                <label class="block text-sm font-medium text-gray-700 mb-1">Search Engine *</label>
                                <select x-model="newProject.neuron_search_engine" required 
                                        class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500">
                                    <option value="">בחר מנוע חיפוש</option>
                                    <option value="google.com">Google.com (Global)</option>
                                    <option value="google.co.uk">Google.co.uk (UK)</option>
                                    <option value="google.de">Google.de (Germany)</option>
                                    <option value="google.fr">Google.fr (France)</option>
                                    <option value="google.es">Google.es (Spain)</option>
                                    <option value="google.it">Google.it (Italy)</option>
                                    <option value="google.com.au">Google.com.au (Australia)</option>
                                    <option value="google.ca">Google.ca (Canada)</option>
                                </select>
                                <p class="text-xs text-gray-500 mt-1">מנוע החיפוש לאנליזה (לדוגמא: google.co.uk)</p>
                            </div>
                            
                            <div class="mb-4">
                                <label class="block text-sm font-medium text-gray-700 mb-1">Language *</label>
                                <select x-model="newProject.neuron_language" required 
                                        class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500">
                                    <option value="">בחר שפה</option>
                                    <option value="English">English</option>
                                    <option value="Hebrew">Hebrew</option>
                                    <option value="Spanish">Spanish</option>
                                    <option value="French">French</option>
                                    <option value="German">German</option>
                                    <option value="Italian">Italian</option>
                                    <option value="Portuguese">Portuguese</option>
                                    <option value="Russian">Russian</option>
                                    <option value="Chinese">Chinese</option>
                                    <option value="Japanese">Japanese</option>
                                </select>
                                <p class="text-xs text-gray-500 mt-1">שפת התוכן שייווצר (לדוגמא: English)</p>
                            </div>
                        </div>
                        <div class="flex justify-end space-x-3">
                            <button type="button" @click="showCreateProject = false; resetNewProject()" 
                                    class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md">
                                Cancel
                            </button>
                            <button type="submit" :disabled="creating"
                                    class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50">
                                <span x-show="!creating">Create</span>
                                <span x-show="creating">Creating...</span>
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <script>
        function dashboard() {
            return {
                loading: true,
                currentView: 'dashboard',
                projects: [],
                stats: {},
                recentActivity: { articles: [], keywords: [] },
                showCreateProject: false,
                creating: false,
                newProject: {
                    name: '',
                    website_url: '',
                    wordpress_user: '',
                    wordpress_password: '',
                    daily_keywords_limit: 5,
                    neuron_project_id: '',
                    neuron_search_engine: '',
                    neuron_language: ''
                },
                testingConnection: false,
                connectionStatus: null,
                showKeywords: false,
                selectedProject: null,
                projectKeywords: [],

                async loadDashboard() {
                    this.loading = true;
                    try {
                        const [dashboardResponse, projectsResponse] = await Promise.all([
                            fetch('/api/dashboard'),
                            fetch('/api/projects')
                        ]);
                        
                        const dashboardData = await dashboardResponse.json();
                        const projectsData = await projectsResponse.json();
                        
                        if (dashboardData.success) {
                            this.stats = dashboardData.stats;
                            this.recentActivity = dashboardData.recent_activity;
                        }
                        
                        if (projectsData.success) {
                            this.projects = projectsData.projects;
                        }
                    } catch (error) {
                        console.error('Error loading dashboard:', error);
                    } finally {
                        this.loading = false;
                    }
                },

                async createProject() {
                    this.creating = true;
                    try {
                        const response = await fetch('/api/projects', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify(this.newProject)
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            this.projects.push(data.project);
                            this.showCreateProject = false;
                            this.resetNewProject();
                            alert('Project created successfully!');
                            this.stats.projects.total++;
                            this.stats.projects.active++;
                        } else {
                            alert('Error: ' + data.error);
                        }
                    } catch (error) {
                        console.error('Error creating project:', error);
                        alert('Error creating project');
                    } finally {
                        this.creating = false;
                    }
                },

                resetNewProject() {
                    this.newProject = {
                        name: '',
                        website_url: '',
                        wordpress_user: '',
                        wordpress_password: '',
                        daily_keywords_limit: 5,
                        neuron_project_id: '',
                        neuron_search_engine: '',
                        neuron_language: ''
                    };
                    this.connectionStatus = null;
                    this.testingConnection = false;
                },
                
                async testWordPressConnection() {
                    this.testingConnection = true;
                    this.connectionStatus = null;
                    
                    try {
                        const response = await fetch('/api/test-wordpress', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                website_url: this.newProject.website_url,
                                wordpress_user: this.newProject.wordpress_user,
                                wordpress_password: this.newProject.wordpress_password
                            })
                        });
                        
                        const data = await response.json();
                        this.connectionStatus = data;
                        
                    } catch (error) {
                        console.error('Error testing connection:', error);
                        this.connectionStatus = {
                            success: false,
                            error: 'שגיאה בבדיקת חיבור'
                        };
                    } finally {
                        this.testingConnection = false;
                    }
                },

                addKeywords(projectId) {
                    const keywords = prompt('Enter keywords separated by commas:');
                    if (keywords) {
                        const keywordList = keywords.split(',').map(k => k.trim()).filter(k => k);
                        this.submitKeywords(projectId, keywordList);
                    }
                },

                async submitKeywords(projectId, keywords) {
                    try {
                        const response = await fetch(`/api/projects/${projectId}/keywords`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ keywords })
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            alert(data.message);
                            await this.loadDashboard(); // Refresh data
                        } else {
                            alert('Error: ' + data.error);
                        }
                    } catch (error) {
                        console.error('Error adding keywords:', error);
                        alert('Error adding keywords');
                    }
                },

                async viewKeywords(projectId) {
                    this.selectedProject = this.projects.find(p => p.id === projectId);
                    this.showKeywords = true;
                    
                    try {
                        const response = await fetch(`/api/projects/${projectId}/keywords`);
                        const data = await response.json();
                        
                        if (data.success) {
                            this.projectKeywords = data.keywords;
                        } else {
                            console.error('Error loading keywords:', data.error);
                            this.projectKeywords = [];
                        }
                    } catch (error) {
                        console.error('Error loading keywords:', error);
                        this.projectKeywords = [];
                    }
                },

                closeKeywords() {
                    this.showKeywords = false;
                    this.selectedProject = null;
                    this.projectKeywords = [];
                },

                async createArticle(keyword) {
                    if (confirm(`האם לייצר מאמר עבור המילה "${keyword.keyword}"?`)) {
                        alert('פיצר יצירת מאמר יבוא בקרוב! המערכת תפנה ל-SecretSEOApp ותיצור תוכן מותאם SEO עם תמונות.');
                        // TODO: Implement article creation
                        // This will call the SecretSEOApp API and WordPress publishing
                    }
                }
            }
        }
    </script>

    <style>
        [x-cloak] { display: none !important; }
    </style>
</body>
</html>'''

@app.route('/api/dashboard', methods=['GET'])
def api_dashboard_stats():
    """Get dashboard statistics"""
    return jsonify({
        'success': True,
        'stats': get_dashboard_stats(),
        'recent_activity': {
            'articles': [],
            'keywords': []
        }
    })

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    try:
        projects = Project.query.all()
        projects_data = [project.to_dict() for project in projects]
        return jsonify({
            'success': True,
            'projects': projects_data,
            'total': len(projects_data)
        })
    except Exception as e:
        print(f"Error getting projects: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('website_url'):
            return jsonify({'success': False, 'error': 'Name and website URL are required'}), 400
        
        if not data.get('neuron_project_id') or not data.get('neuron_search_engine') or not data.get('neuron_language'):
            return jsonify({'success': False, 'error': 'SecretSEOApp settings are required (Project ID, Search Engine, Language)'}), 400
        
        # Test WordPress connection if credentials provided
        wordpress_status = {'connected': False, 'categories': []}
        if data.get('wordpress_user') and data.get('wordpress_password'):
            test_result = test_wordpress_connection(
                data['website_url'],
                data['wordpress_user'],
                data['wordpress_password']
            )
            wordpress_status = {
                'connected': test_result['connected'],
                'categories': test_result.get('categories', []),
                'error': test_result.get('error')
            }
        
        # Create new project in database
        project = Project(
            name=data['name'],
            website_url=data['website_url'],
            wordpress_user=data.get('wordpress_user', ''),
            wordpress_password=data.get('wordpress_password', ''),  # In production: encrypt!
            daily_keywords_limit=data.get('daily_keywords_limit', 5),
            neuron_project_id=data['neuron_project_id'],
            neuron_search_engine=data['neuron_search_engine'],
            neuron_language=data['neuron_language'],
            status='active'
        )
        
        db.session.add(project)
        db.session.commit()
        
        project_dict = project.to_dict()
        # Add WordPress status from test
        project_dict['wordpress_status'] = wordpress_status
        
        return jsonify({
            'success': True,
            'message': 'Project created successfully',
            'project': project_dict
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating project: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/projects/<int:project_id>/keywords', methods=['POST'])
def add_keywords_to_project(project_id):
    """Add keywords to a project"""
    try:
        data = request.get_json()
        keywords = data.get('keywords', [])
        
        if not keywords:
            return jsonify({'success': False, 'error': 'No keywords provided'}), 400
        
        # Find the project
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Add keywords to database
        added_keywords = []
        for keyword_text in keywords:
            keyword_obj = Keyword(
                project_id=project_id,
                keyword=keyword_text.strip(),
                status='pending'
            )
            db.session.add(keyword_obj)
            added_keywords.append(keyword_obj)
        
        db.session.commit()
        
        # Convert to dict for response
        added_keywords_data = [k.to_dict() for k in added_keywords]
        
        return jsonify({
            'success': True,
            'message': f'Added {len(added_keywords)} keywords successfully',
            'keywords': added_keywords_data
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding keywords: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/projects/<int:project_id>/keywords', methods=['GET'])
def get_project_keywords(project_id):
    """Get keywords for a project"""
    try:
        # Find the project
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Get keywords for this project
        keywords = Keyword.query.filter_by(project_id=project_id).all()
        keywords_data = [k.to_dict() for k in keywords]
        
        return jsonify({
            'success': True,
            'keywords': keywords_data,
            'total': len(keywords_data)
        })
        
    except Exception as e:
        print(f"Error getting project keywords: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test-wordpress', methods=['POST'])
def test_wordpress():
    """Test WordPress connection"""
    try:
        data = request.get_json()
        
        if not data.get('website_url') or not data.get('wordpress_user') or not data.get('wordpress_password'):
            return jsonify({
                'success': False, 
                'error': 'Website URL, username and password are required'
            }), 400
        
        result = test_wordpress_connection(
            data['website_url'],
            data['wordpress_user'],
            data['wordpress_password']
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

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
    try:
        # Test database connection
        with app.app_context():
            db.session.execute(db.text('SELECT 1')).fetchone()
            db_status = 'connected'
        
        # Get basic stats
        stats = get_dashboard_stats()
        
        return jsonify({
            'status': 'healthy',
            'environment': 'vercel-serverless',
            'database': db_status,
            'database_url': 'neon-postgres' if 'neon' in (os.getenv('POSTGRES_URL', '') or '') else 'fallback',
            'stats': stats,
            'message': 'AI Content Maker API is running with Neon Postgres'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'database': 'disconnected', 
            'error': str(e),
            'message': 'Database connection failed'
        }), 500

# Vercel expects the Flask app to be available at module level
application = app

if __name__ == '__main__':
    app.run(debug=True)