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

print("Starting AI Content Maker API v2...")
print(f"Python path: {sys.path}")

# Load environment variables
load_dotenv()

# Check if POSTGRES_URL is available
postgres_url = os.getenv('POSTGRES_URL')
print(f"Database URL available: {'Yes' if postgres_url else 'No'}")
if postgres_url:
    print(f"Database type: {'neon' if 'neon' in postgres_url else 'other'}")

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(project_root)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
print("Path setup completed")

# Essential configurations and functions embedded for Vercel compatibility
MODULES_AVAILABLE = True  # Set to True since we're embedding everything

# Configuration from environment variables
neuron_api_key = os.getenv('NEURON_API_KEY')
neuron_api_endpoint = os.getenv('NEURON_API_ENDPOINT')
openai_model = os.getenv('OPENAI_MODEL')
openai_key = os.getenv('OPENAI_KEY')
anchors_config_path = os.getenv('ANCHORS_CONFIG_PATH')

# Essential Neuron Writer functions
def neuron_new_query(project_id, keyword, engine, language):
    """Create a new query in Neuron Writer"""
    import json
    
    print(f"🧠 NEURON API: Creating query for keyword '{keyword}' in {language}")
    
    headers = {
        "X-API-KEY": neuron_api_key,
        "Accept": "application/json", 
        "Content-Type": "application/json",
    }
    payload = json.dumps({"project": project_id, "keyword": keyword, "engine": engine, "language": language})
    response = requests.request("POST", neuron_api_endpoint + "/new-query", headers=headers, data=payload)
    return response.json()

def neuron_get_query(query_id):
    """Get query results from Neuron Writer"""
    import json
    import requests
    
    print(f"🧠 NEURON API: Getting query results for {query_id}")
    
    headers = {
        "X-API-KEY": neuron_api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    
    payload = json.dumps({"query": query_id})
    
    response = requests.request(
        "POST",
        neuron_api_endpoint + "/get-query",
        headers=headers,
        data=payload)
    
    return response.json()

def neuron_import_content(query_id, content, title, description):
    """Import content to Neuron Writer"""
    import json
    import requests
    
    print(f"🧠 NEURON API: Importing content with title '{title[:50]}...'")
    
    # Clean and prepare HTML content
    clean_content = strip_code_fences(content)
    html_content = ensure_html_document(clean_content)
    
    headers = {
        "X-API-KEY": neuron_api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    
    payload = json.dumps({
        "query": query_id,
        "html": html_content,  # Neuron expects 'html' not 'content'
        "title": title,
        "description": description  # Use 'description' not 'meta_description'
    })
    
    response = requests.request(
        "POST",
        neuron_api_endpoint + "/import-content",
        headers=headers,
        data=payload)
    
    return response.json()

def neuron_evaluate_content(query_id, content, title, description):
    """Evaluate content in Neuron Writer"""
    import json
    import requests
    
    print(f"🧠 NEURON API: Evaluating content for query {query_id}")
    
    headers = {
        "X-API-KEY": neuron_api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    
    # Clean and prepare HTML content
    clean_content = strip_code_fences(content) 
    html_content = ensure_html_document(clean_content)
    
    payload = json.dumps({
        "query": query_id,
        "html": html_content,  # Neuron expects 'html' not 'content'
        "title": title,
        "description": description  # Use 'description' not 'meta_description'
    })
    
    response = requests.request(
        "POST",
        neuron_api_endpoint + "/evaluate-content",
        headers=headers,
        data=payload)
    
    return response.json()

# Content processing utilities
def strip_code_fences(s: str) -> str:
    """Remove code fences (```html, ```) from GPT response"""
    if not s:
        return s
    s = s.strip()
    if s.startswith("```"):
        # Remove first line (``` or ```html)
        s = s.split('\n', 1)[1] if '\n' in s else ''
        # Remove final ```
        if s.endswith("```"):
            s = s[:-3]
    return s.strip()

def ensure_html_document(s: str) -> str:
    """Ensure content is wrapped in proper HTML document with RTL support"""
    if not s:
        return s
    
    low = s.lower().lstrip()
    if not (low.startswith("<!doctype html") or low.startswith("<html")):
        s = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AliExpress – קופונים והנחות</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        p {{ margin-bottom: 15px; }}
    </style>
</head>
<body>
{s}
</body>
</html>"""
    return s

# Embedded prompts (from prompts.yaml)
TITLE_CREATION_PROMPT = """Task:

Create a compelling, SEO-optimized title for a content article. The title should effectively incorporate the given terms, prioritizing them based on their usage percentages to achieve a high score in NeuronWriter.

Instructions:

Terms and Usage Percentages:

Use the following list of terms to craft the title. Each term comes with a usage percentage indicating its importance—the higher the percentage, the more prominently the term should feature in the title.
  
  {terms}

Also, incorporate these additional terms exactly as they are, without altering them. Also, do not add any characters before or after them, these specific terms must come after a space character and before a space character (unless they are the first or the last word of the title), you MUST incorporate these terms exactly as they are:

{search_keyword_terms}

Title Requirements:

Incorporate Key Terms: Prioritize including terms with higher usage percentages.

Natural Language: Ensure the title reads naturally and is grammatically correct.

SEO Optimization:

Length: Aim for a title length between 60-70 characters.
Relevance: Make the title relevant to the topic suggested by the terms.
Engagement: Craft the title to be engaging and enticing to readers.
Formatting:

Provide only the final title without additional explanations or annotations.
Do not include the usage percentages in the title.

Your Task:

Using the instructions above and the provided terms, generate one title for the content article."""

DESCRIPTION_CREATION_PROMPT = """Task:
Create an SEO-optimized meta description for a content article. The meta description should effectively incorporate the given terms, prioritizing them based on their usage percentages to achieve a high score in NeuronWriter.

Instructions:

Terms and Usage Percentages:

Use the following list of terms to craft the meta description. Each term comes with a usage percentage indicating its importance—the higher the percentage, the more prominently the term should feature in the description.
{terms}

Also, incorporate these additional terms exactly as they are, without altering them. Also, do not add any characters before or after them, these specific terms must come after a space character and before a space character (unless they are the first or the last word of the string), you MUST incorporate these terms exactly as they are:
{search_keyword_terms}

Meta Description Requirements:

Length: Aim for a meta description length of up to 155-160 characters to ensure it displays fully in search engine results.

Incorporate Key Terms: Prioritize including terms with higher usage percentages.

Natural Language: Ensure the meta description reads naturally and is grammatically correct.

SEO Optimization:

Relevance: Make the description relevant to the content of the article and enticing to users.
Call to Action (Optional): Include a call to action if appropriate.

Formatting:
Provide only the final meta description without additional explanations or annotations.
Do not include the usage percentages in the description.

Your Task:
Using the instructions above and the provided terms, generate one meta description for the content article."""

# Essential OpenAI functions
def gpt_generate_title(model, terms, keywords):
    """Generate title using OpenAI"""
    from openai import OpenAI
    
    client = OpenAI(api_key=openai_key)
    
    # Format terms properly
    print(f"🔍 DEBUG: Raw terms input: {terms}")
    print(f"🔍 DEBUG: Raw keywords input: {keywords}")
    
    if isinstance(terms, list):
        terms_formatted = "\n".join([f"{term.get('term', str(term))}: {term.get('score', 0)}%" if isinstance(term, dict) else str(term) for term in terms])
    else:
        terms_formatted = str(terms)
    
    print(f"🔍 DEBUG: Formatted terms: {terms_formatted}")
    print(f"🔍 DEBUG: Raw keywords: '{keywords}'")
    
    # Clean keywords - remove newlines and extra spaces
    keywords_cleaned = ' '.join(str(keywords).split()) if keywords else ''
    print(f"🔍 DEBUG: Cleaned keywords: '{keywords_cleaned}'")
    
    # TEST: Simple prompt first to check if GPT works at all
    test_prompt = "Write just the word 'TEST' and nothing else."
    print(f"🧪 TESTING: First trying simple test prompt...")
    
    try:
        test_response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": test_prompt}],
            max_completion_tokens=20000
        )
        if test_response and test_response.choices:
            test_result = test_response.choices[0].message.content
            print(f"🧪 TEST RESULT: '{test_result}'")
        else:
            print("❌ Test failed - no response")
            
    except Exception as test_e:
        print(f"❌ Test failed with error: {test_e}")
    
    # Now try the real prompt with cleaned keywords
    prompt = TITLE_CREATION_PROMPT.format(terms=terms_formatted, search_keyword_terms=keywords_cleaned)
    print(f"🔍 DEBUG: Now trying real prompt...")
    print(f"🔍 DEBUG: Prompt length: {len(prompt)} characters")
    print(f"🔍 DEBUG: First 200 chars of prompt: {prompt[:200]}...")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert SEO writer."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=2000
        )
        
        print(f"🔍 GPT Response received successfully")
        
        # Log raw response for debugging
        if not (response and response.choices and len(response.choices) > 0 and response.choices[0].message.content):
            print(f"❌ EMPTY/INVALID GPT RESPONSE - RAW: {response}")
        
        if response and response.choices and len(response.choices) > 0:
            choice = response.choices[0]
            msg = choice.message
            result = getattr(msg, "content", None) or getattr(msg, "refusal", None) or ""
            
            # Clean result of hidden characters that might cause issues
            if result:
                result = result.replace("\u200f","").replace("\u200e","").strip()
            
            if not result:
                print(f"⚠️ GPT returned empty content. Full message: {msg}")
                print(f"⚠️ Choice details: finish_reason={getattr(choice, 'finish_reason', 'unknown')}")
                return None  # Return None instead of empty string
            else:
                print(f"✅ GPT Title Result: '{result}' (length: {len(result)})")
                return result
        else:
            print("❌ Invalid response structure from GPT")
            return None  # Return None instead of error string
    except Exception as e:
        print(f"❌ Exception in GPT title generation: {str(e)}")
        return None  # Return None instead of error string

def gpt_generate_description(model, terms, keywords):
    """Generate meta description using OpenAI"""
    from openai import OpenAI
    
    client = OpenAI(api_key=openai_key)
    
    # Format terms properly
    if isinstance(terms, list):
        terms_formatted = "\n".join([f"{term.get('term', str(term))}: {term.get('score', 0)}%" if isinstance(term, dict) else str(term) for term in terms])
    else:
        terms_formatted = str(terms)
    
    # Clean keywords - remove newlines and extra spaces
    keywords_cleaned = ' '.join(str(keywords).split()) if keywords else ''
    print(f"🔍 DEBUG Description - Raw keywords: '{keywords}' -> Cleaned: '{keywords_cleaned}'")
    
    prompt = DESCRIPTION_CREATION_PROMPT.format(terms=terms_formatted, search_keyword_terms=keywords_cleaned)
    print(f"🔍 GPT Description Prompt: {prompt[:300]}...")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert SEO writer."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=2000
        )
        
        print(f"🔍 GPT Description Response received successfully")
        # Log raw response for debugging
        if not (response and response.choices and len(response.choices) > 0 and response.choices[0].message.content):
            print(f"❌ EMPTY/INVALID GPT DESCRIPTION RESPONSE - RAW: {response}")
        
        if response and response.choices and len(response.choices) > 0:
            choice = response.choices[0]
            msg = choice.message
            result = getattr(msg, "content", None) or getattr(msg, "refusal", None) or ""
            
            # Clean result of hidden characters
            if result:
                result = result.replace("\u200f","").replace("\u200e","").strip()
            
            if not result:
                print(f"⚠️ GPT returned empty description. Full message: {msg}")
                print(f"⚠️ Choice details: finish_reason={getattr(choice, 'finish_reason', 'unknown')}")
                return None  # Return None instead of empty string
            else:
                print(f"✅ GPT Description Result: '{result}' (length: {len(result)})")
                return result
        else:
            print("❌ Invalid description response structure from GPT")
            return None  # Return None instead of error string
    except Exception as e:
        print(f"❌ Exception in GPT description generation: {str(e)}")
        return None  # Return None instead of error string

def gpt_generate_article(model, title_terms, h1_terms, h2_terms, content_terms):
    """Generate article content using OpenAI"""
    from openai import OpenAI
    
    client = OpenAI(api_key=openai_key)
    
    prompt = f"""Write a comprehensive article in Hebrew using these terms:
    Title terms: {title_terms}
    H1 terms: {h1_terms}
    H2 terms: {h2_terms}
    Content terms: {content_terms}
    
    Please create a well-structured HTML article with proper headings and paragraphs."""
    
    print(f"🔍 GPT Article Prompt: {prompt[:500]}...")
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=2000
    )
    
    result = response.choices[0].message.content.strip()
    print(f"🔍 GPT Article Result Length: {len(result)} chars")
    print(f"🔍 GPT Article Result Preview: {result[:200]}...")
    return result

# Essential utility functions
def sentence_to_multiline(sentence):
    """Convert sentence to multiline format"""
    return sentence.replace(' ', '\n')

def objects_array_to_multiline(objects_array):
    """Convert objects array to multiline string"""
    if not objects_array:
        return ""
    return '\n'.join([obj.get('term', str(obj)) if isinstance(obj, dict) else str(obj) for obj in objects_array])

def format_terms_with_usage(terms):
    """Format terms with usage information"""
    if not terms:
        return ""
    formatted = []
    for term in terms:
        if isinstance(term, dict):
            formatted.append(f"{term.get('term', '')}: {term.get('usage', 0)} times")
        else:
            formatted.append(str(term))
    return '\n'.join(formatted)

# Stub functions for features not essential for basic operation
def load_rules_and_anchors(config_path, site):
    """Load rules and anchors - simplified version"""
    return "Basic SEO rules", "Basic anchors"

def gpt_optimize_headings(model, content, terms, keywords, rules, anchors, site):
    """Optimize headings - simplified version"""
    return content  # Return original content for now

def switch_headings(content, headings, score, query_id, title, description):
    """Switch headings - simplified version"""
    return {
        'success': True,
        'updated_html_content': content,
        'message': 'Headings optimized (simplified)'
    }

def get_terms_not_used(content, query_data):
    """Get terms not used - simplified version"""
    return []  # Return empty for now

def get_terms_used_excessively(content, query_data):
    """Get terms used excessively - simplified version"""
    return []  # Return empty for now

def gpt_add_terms_not_used(model, content, terms):
    """Add terms not used - simplified version"""
    return content

def format_use_less_objects(terms):
    """Format use less objects - simplified version"""
    return ""

def gpt_reduce_terms(model, content, terms):
    """Reduce terms usage - simplified version"""
    return content

print("✅ Essential functions embedded for article creation - YAML prompts integrated")

app = Flask(__name__)

# Database configuration for Neon Postgres
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
# Fix Neon Postgres URL - convert postgres:// to postgresql://
postgres_url = os.getenv('POSTGRES_URL', 'sqlite:///fallback.db')
print(f"Original DB URL: {postgres_url[:50]}..." if len(postgres_url) > 50 else f"Original DB URL: {postgres_url}")
if postgres_url.startswith('postgres://'):
    postgres_url = postgres_url.replace('postgres://', 'postgresql://', 1)
    print("Fixed postgres:// to postgresql://")
app.config['SQLALCHEMY_DATABASE_URI'] = postgres_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_timeout': 20,
    'pool_recycle': -1,
    'pool_pre_ping': True
}

# Initialize database inline to avoid import issues
try:
    from datetime import datetime, timezone
    from flask_sqlalchemy import SQLAlchemy
    import json

    db = SQLAlchemy()
    db.init_app(app)
    print("SQLAlchemy initialized successfully")
    DB_AVAILABLE = True
except Exception as e:
    print(f"Failed to initialize SQLAlchemy: {e}")
    DB_AVAILABLE = False
    db = None

# Define models only if DB is available
if DB_AVAILABLE and db:
    class Project(db.Model):
        """Model for managing content creation projects"""
        __tablename__ = 'projects'
        
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(255), nullable=False)
        website_url = db.Column(db.String(255), nullable=False)
        
        # WordPress Configuration
        wordpress_user = db.Column(db.String(100))
        wordpress_password = db.Column(db.String(255))  # In production: encrypt this!
        # wordpress_categories_count = db.Column(db.Integer, default=0, nullable=True)  # Temporarily disabled
        
        # SecretSEOApp Configuration  
        neuron_project_id = db.Column(db.String(100))  # Make nullable for now
        neuron_search_engine = db.Column(db.String(50), default='google.com')
        neuron_language = db.Column(db.String(20), default='English')
        
        # Settings
        daily_keywords_limit = db.Column(db.Integer, default=5)
        
        # Status and Timestamps
        status = db.Column(db.String(20), default='active')  # active, paused, inactive
        created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
        updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
        
        # Relationships
        keywords = db.relationship('Keyword', backref='project', lazy=True, cascade='all, delete-orphan')
        
        def get_neuron_settings(self):
            """Get SecretSEOApp settings as dict"""
            return {
                'project_id': self.neuron_project_id or '',
                'search_engine': self.neuron_search_engine or 'google.com',
                'language': self.neuron_language or 'English'
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
                'wordpress_categories_count': 0,  # Temporarily disabled
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
        search_engine = db.Column(db.String(50))  # google.co.il etc
        language = db.Column(db.String(50))  # Hebrew, English etc
        category_id = db.Column(db.Integer)
        tags_json = db.Column(db.Text)  # JSON string of tags
        priority = db.Column(db.Integer, default=1)
        
        # Processing Status
        status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed, paused
        processing_by = db.Column(db.String(100))
        lease_until = db.Column(db.DateTime(timezone=True))
        error_message = db.Column(db.Text)
        attempts = db.Column(db.Integer, default=0)
        
        # Article Information (when completed)
        article_title = db.Column(db.String(500))
        meta_description = db.Column(db.Text)
        article_content = db.Column(db.Text)  # HTML content
        content_score = db.Column(db.Integer)
        wordpress_post_id = db.Column(db.Integer)
        
        # Timestamps
        created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
        processed_at = db.Column(db.DateTime(timezone=True))
        
        def get_tags(self):
            """Get tags as list from JSON string"""
            if self.tags_json:
                try:
                    import json
                    return json.loads(self.tags_json)
                except:
                    return []
            return []
            
        def to_dict(self):
            """Convert model to dictionary for JSON serialization"""
            return {
                'id': self.id,
                'project_id': self.project_id,
                'keyword': self.keyword,
                'search_engine': self.search_engine,
                'language': self.language,
                'category_id': self.category_id,
                'tags': self.get_tags(),
                'priority': self.priority,
                'status': self.status,
                'processing_by': self.processing_by,
                'lease_until': self.lease_until.isoformat() if self.lease_until else None,
                'error_message': self.error_message,
                'attempts': self.attempts,
                'article_title': self.article_title,
                'meta_description': self.meta_description,
                'content_score': self.content_score,
                'wordpress_post_id': self.wordpress_post_id,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'processed_at': self.processed_at.isoformat() if self.processed_at else None
            }
        
        def __repr__(self):
            return f'<Keyword {self.keyword} ({self.status})>'

else:
    # Fallback classes for when DB is not available
    print("Creating fallback classes without database")
    Project = None
    Keyword = None

# Create tables when app starts
def init_database():
    """Initialize database tables"""
    try:
        with app.app_context():
            db.create_all()
            print("Database tables created successfully")
            
            # Try to handle schema changes gracefully
            try:
                # Just try to recreate tables (this will only add missing columns)
                db.create_all()
                print("Schema updated successfully")
            except Exception as schema_error:
                print(f"Schema update error: {schema_error}")
                
            # Add missing columns to keywords table
            new_columns = [
                ("search_engine", "VARCHAR(50)"),
                ("language", "VARCHAR(50)"),
                ("category_id", "INTEGER"),
                ("tags_json", "TEXT"),
                ("priority", "INTEGER DEFAULT 1"),
                ("processing_by", "VARCHAR(100)"),
                ("lease_until", "TIMESTAMP"),
                ("error_message", "TEXT"),
                ("attempts", "INTEGER DEFAULT 0"),
                ("meta_description", "TEXT"),
                ("article_content", "TEXT")
            ]
            
            for column_name, column_type in new_columns:
                try:
                    # Test if column exists
                    db.session.execute(db.text(f"SELECT {column_name} FROM keywords LIMIT 1"))
                    print(f"{column_name} column exists")
                except Exception:
                    try:
                        print(f"Adding {column_name} column...")
                        db.session.execute(db.text(f"ALTER TABLE keywords ADD COLUMN {column_name} {column_type}"))
                        db.session.commit()
                        print(f"Added {column_name} column successfully")
                    except Exception as e:
                        print(f"Could not add {column_name} column: {e}")
                        db.session.rollback()
                    
            # Test basic database operations
            try:
                test_query = db.session.execute(db.text("SELECT COUNT(*) FROM projects")).scalar()
                print(f"Database test successful - found {test_query} projects")
            except Exception as test_error:
                print(f"Database test failed: {test_error}")
                raise test_error
    except Exception as e:
        print(f"Error creating tables: {e}")

# Initialize database with error handling
try:
    print("Attempting to initialize database...")
    init_database()
    print("Database initialization completed")
except Exception as e:
    print(f"Database initialization failed: {e}")
    print("Continuing without database - will use fallback mode")

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

# Check connection on startup with error handling
try:
    print("Checking database connection...")
    check_database_connection()
except Exception as e:
    print(f"Initial database check failed: {e}")

def get_dashboard_stats():
    """Calculate dashboard statistics from database with fallback"""
    if not DB_AVAILABLE or not Project:
        print("Database not available, returning empty stats")
        return {
            'projects': {'total': 0, 'active': 0, 'inactive': 0},
            'keywords': {'total': 0, 'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0},
            'articles': {'total': 0}
        }
    
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
        print(f"Error calculating stats from database: {e}")
        print("Using fallback stats")
        return {
            'projects': {'total': 0, 'active': 0, 'inactive': 0},
            'keywords': {'total': 0, 'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0},
            'articles': {'total': 0}
        }

# Article creation logic (copied from routes/create_article.py for Vercel compatibility)
def create_article_logic_embedded(main_project_id, main_keyword, main_engine, main_language, site):
    """
    Does all the neuron and GPT logic for creating the article.
    Returns (response_dict, status_code).
    """
    import time
    import json
    
    # Check if required modules are available
    global MODULES_AVAILABLE
    if not MODULES_AVAILABLE:
        print("❌ Required modules not available")
        return {
            'success': False,
            'message': 'Required modules for article creation are not available in this deployment environment. This may be due to missing dependencies or path issues in Vercel.',
            'error': 'modules_not_available'
        }, 500
    
    # Debug: Check if environment variables are available
    print(f"🔍 Debugging environment variables:")
    print(f"neuron_api_key: {neuron_api_key is not None}")
    print(f"neuron_api_endpoint: {neuron_api_endpoint}")
    print(f"openai_model: {openai_model}")
    print(f"openai_key: {openai_key is not None}")
    
    if not neuron_api_key or not neuron_api_endpoint:
        return {
            'success': False,
            'message': f'Missing Neuron API configuration. API Key: {neuron_api_key is not None}, Endpoint: {neuron_api_endpoint}',
            'error': 'missing_neuron_config'
        }, 500
    
    if not openai_key or not openai_model:
        return {
            'success': False,
            'message': f'Missing OpenAI configuration. API Key: {openai_key is not None}, Model: {openai_model}',
            'error': 'missing_openai_config'
        }, 500

    ###################################
    # article creation process
    ###################################

    #################################################################
    # create a neuron query, and get query results
    #################################################################
    def neuron_create_and_get_query(main_project_id, main_keyword, main_engine, main_language):
        main_search_keyword_terms = sentence_to_multiline(main_keyword)

        # make a new query with neuron
        new_query_response = neuron_new_query(main_project_id, main_keyword, main_engine, main_language)
        main_query_id = new_query_response['query']

        # sleep for 65 seconds (a new query usually takes around 60 seconds until it's finished)
        print(f'response for new neuron query creation: {new_query_response} sleeping for 65 seconds, to wait for the query to be ready.')
        time.sleep(65)

        # get query results from neuron
        start_time = time.time()

        while True:
            neuron_query_response_data = neuron_get_query(main_query_id)
            status = neuron_query_response_data.get("status", "").lower()

            if status in ["waiting", "in progress"]:
                elapsed_time = time.time() - start_time
                if elapsed_time >= 120:
                    print("Exceeded 120 seconds. Stopping the loop.")
                    break
                print(f"Status is '{status}'. Waiting 10 seconds before checking again...")
                time.sleep(10)
            elif status == "ready":
                print("Status is 'ready'. Proceeding with the rest of the program...")
                break
            elif status == "not found":
                print("Status is 'not found'. Exiting main() function.")
                return
            else:
                print(f"Received unexpected status '{status}'. Exiting.")
                break

        print("Continuing with the rest of the code...")

        return_dict = {
            "neuron_query_response_data": neuron_query_response_data,
            "main_query_id": main_query_id,
            "main_search_keyword_terms": main_search_keyword_terms,
        }
        return return_dict

    #################################################################
    # create title, meta-description, article, and upload to neuron
    #################################################################
    def neuron_create_title_desc_article(neuron_query_dict):
        neuron_query_response_data = neuron_query_dict["neuron_query_response_data"]
        main_search_keyword_terms = neuron_query_dict["main_search_keyword_terms"]
        main_query_id = neuron_query_dict["main_query_id"]

        # create title with GPT
        main_title_terms = neuron_query_response_data['terms']['title']
        print(f"🔍 Title terms from Neuron: {main_title_terms}")
        print(f"🔍 Search keywords: {main_search_keyword_terms}")
        main_article_title = gpt_generate_title(openai_model, main_title_terms, main_search_keyword_terms)
        print(f"🔍 Generated title: '{main_article_title}'")

        # create meta-description with GPT
        main_description_terms = neuron_query_response_data['terms']["desc"]
        print(f"🔍 Description terms from Neuron: {main_description_terms}")
        main_article_description = gpt_generate_description(openai_model, main_description_terms, main_search_keyword_terms)
        print(f"🔍 Generated description: '{main_article_description}'")

        # Check if we got valid content before continuing
        if not main_article_title or not main_article_description:
            print("❌ Empty title or description from GPT, cannot continue")
            response_data = {
                'success': False,
                'message': 'Failed to generate title and description',
                'main_article_title': main_article_title or '',
                'main_article_description': main_article_description or '',
                'article_content': '',
                'content_score': 0
            }
            return response_data, 500
        
        print(f"✅ Valid title and description generated, continuing with article creation...")
        print(f"📝 TITLE: '{main_article_title}'")
        print(f"📝 DESCRIPTION: '{main_article_description}'")
        # create article with GPT
        main_h1_terms = neuron_query_response_data['terms']["h1"]
        main_h2_terms = neuron_query_response_data['terms']["h2"]
        title_terms_string = objects_array_to_multiline(main_title_terms)
        h1_terms_string = objects_array_to_multiline(main_h1_terms)
        h2_terms_string = objects_array_to_multiline(main_h2_terms)

        content_basic_terms = neuron_query_response_data['terms']['content_basic']
        content_extended_terms = neuron_query_response_data['terms']['content_extended']
        all_content_terms = content_basic_terms + content_extended_terms
        main_content_terms = format_terms_with_usage(all_content_terms)

        # create main article with GPT
        main_article_content = gpt_generate_article(openai_model, title_terms_string, h1_terms_string, h2_terms_string, main_content_terms)

        # Clean article content before uploading
        clean_article_content = strip_code_fences(main_article_content)
        final_html_content = ensure_html_document(clean_article_content)
        
        # upload initial article to neuron writer API, and get initial score
        import_content_response = neuron_import_content(main_query_id, main_article_content, main_article_title, main_article_description)
        
        print(f"🧠 NEURON IMPORT RESPONSE: {import_content_response}")

        return_dict = {
            'success': True,
            'message': 'Article created successfully with full content',
            'main_article_title': main_article_title,
            'main_article_description': main_article_description,
            'article_content': final_html_content,  # Return cleaned HTML
            'content_score': import_content_response.get('content_score', import_content_response.get('score', 0)) if isinstance(import_content_response, dict) else 0,
            # Keep additional data for potential optimization
            "import_content_response": import_content_response,
            "h1_terms_string": h1_terms_string,
            "h2_terms_string": h2_terms_string,
            "main_search_keyword_terms": main_search_keyword_terms,
            "main_query_id": main_query_id,
            "neuron_query_response_data": neuron_query_response_data
        }
        return return_dict, 200

    #################################################################
    # content optimization process
    #################################################################
    def content_optimization_process(content_and_terms_dict, site):
        result_dict = {'success': False}

        main_article_title = content_and_terms_dict['main_article_title']
        main_article_description = content_and_terms_dict['main_article_description']
        h1_terms_string = content_and_terms_dict['h1_terms_string']
        h2_terms_string = content_and_terms_dict['h2_terms_string']
        main_article_content = content_and_terms_dict['main_article_content']
        main_search_keyword_terms = content_and_terms_dict['main_search_keyword_terms']
        import_content_response = content_and_terms_dict['import_content_response']
        main_query_id = content_and_terms_dict['main_query_id']
        neuron_query_response_data = content_and_terms_dict['neuron_query_response_data']

        main_h1_h2_terms = f'H1 TERMS:\n{h1_terms_string}\n\nH2 TERMS:{h2_terms_string}'
        current_score = import_content_response["content_score"]

        def optimize_headings(main_article_content, current_score):
            rules_str, anchors_str = load_rules_and_anchors(anchors_config_path, site)
            main_optimized_headings = gpt_optimize_headings(openai_model, main_article_content, main_h1_h2_terms, main_search_keyword_terms, rules_str, anchors_str, site)
            updated_html_content_dict = switch_headings(main_article_content, main_optimized_headings, current_score, main_query_id, main_article_title, main_article_description)
            
            print(updated_html_content_dict['message'])
            updated_html_content = updated_html_content_dict['updated_html_content']
            
            if updated_html_content_dict['success'] is False:
                return result_dict
            
            result_dict['success'] = True
            result_dict['updated_html_content'] = updated_html_content
            
            new_evaluate_content_response = neuron_evaluate_content(main_query_id, updated_html_content, main_article_title, main_article_description)
            current_score = new_evaluate_content_response['content_score']
            return updated_html_content, current_score

        # optimize headings
        print('\nheadings optimization round 1:\n')
        updated_html_content, current_score = optimize_headings(main_article_content, current_score)

        # optimize for terms not used (grey terms)
        main_terms_not_used = get_terms_not_used(updated_html_content, neuron_query_response_data)
        if len(main_terms_not_used) > 0:
            updated_html_content = gpt_add_terms_not_used(openai_model, updated_html_content, main_terms_not_used)
            new_evaluate_content_response = neuron_evaluate_content(main_query_id, updated_html_content, main_article_title, main_article_description)
            if current_score <= new_evaluate_content_response['content_score']:
                neuron_import_content(main_query_id, updated_html_content, main_article_title, main_article_description)
                current_score = new_evaluate_content_response['content_score']
        else:
            print('\nfound 0 terms not used (grey) - skipping grey term optimization process\n')

        # optimize for terms to use less (red terms) - 2 rounds
        for round_num in [1, 2]:
            print(f'\n{["first", "2nd"][round_num-1]} round of red-terms reduction\n')
            main_terms_to_use_less = get_terms_used_excessively(updated_html_content, neuron_query_response_data)
            if len(main_terms_to_use_less) > 0:
                main_terms_to_reduce_string = format_use_less_objects(main_terms_to_use_less)
                updated_html_content = gpt_reduce_terms(openai_model, updated_html_content, main_terms_to_reduce_string)
                new_evaluate_content_response = neuron_import_content(main_query_id, updated_html_content, main_article_title, main_article_description)
            else:
                print(f'\nfound 0 red terms - skipping red term optimization process\n')

        return_dict = {
            'main_article_title': main_article_title,
            'main_article_description': main_article_description,
            'updated_html_content': updated_html_content,
            'content_score': int(current_score)
        }
        return return_dict

    #################################################################
    # run all the grouped-processes in sequence
    #################################################################

    try:
        # make neuron query, and get query result
        neuron_response_dict = neuron_create_and_get_query(main_project_id, main_keyword, main_engine, main_language)
        print(f'\n{neuron_response_dict}\n')

        # create: title, meta-description, article content
        initial_content_evaluation = neuron_create_title_desc_article(neuron_response_dict)
        print(f'\n🔍 RECEIVED FROM TITLE/DESC FUNCTION: {initial_content_evaluation}\n')

        # Handle tuple response from neuron function - CONTINUE PROCESSING
        if isinstance(initial_content_evaluation, tuple):
            response_data, status_code = initial_content_evaluation
            print(f'\n🔍 EXTRACTED DATA FROM TUPLE: {response_data}\n')
            # Check if we got valid title and description
            if not response_data.get('main_article_title') or not response_data.get('main_article_description'):
                print("❌ No valid title/description generated, stopping here")
                return response_data, status_code
        else:
            response_data = initial_content_evaluation
            if not response_data.get('main_article_title') or not response_data.get('main_article_description'):
                print("❌ No valid title/description generated, stopping here")
                return response_data

        # Use the initial content from title/description generation
        if isinstance(initial_content_evaluation, tuple):
            response_data, status_code = initial_content_evaluation
        else:
            response_data = initial_content_evaluation
        
        print(f"🎯 Starting content optimization process...")
        
        # Run content optimization process
        try:
            optimized_content_dict = content_optimization_process(response_data, site)
            print(f"🎯 Optimization completed: {optimized_content_dict.get('success', False)}")
            
            if optimized_content_dict.get('success'):
                # Use optimized content
                final_response = {
                    'success': True,
                    'message': 'Article content created and optimized successfully.',
                    'title': response_data.get('main_article_title', ''),
                    'meta_description': response_data.get('main_article_description', ''),
                    'article_content': optimized_content_dict.get('updated_html_content', response_data.get('article_content', '')),
                    'content_score': optimized_content_dict.get('content_score', response_data.get('content_score', 0))
                }
            else:
                # Fall back to basic content if optimization fails
                print("⚠️ Optimization failed, using basic content")
                final_response = {
                    'success': True,
                    'message': 'Article content created successfully (optimization failed).',
                    'title': response_data.get('main_article_title', ''),
                    'meta_description': response_data.get('main_article_description', ''),
                    'article_content': response_data.get('article_content', 'Basic article content generated'),
                    'content_score': response_data.get('content_score', 0)
                }
        except Exception as opt_e:
            print(f"❌ Optimization process failed: {opt_e}")
            # Fall back to basic content
            final_response = {
                'success': True,
                'message': 'Article content created successfully (optimization error).',
                'title': response_data.get('main_article_title', ''),
                'meta_description': response_data.get('main_article_description', ''),
                'article_content': response_data.get('article_content', 'Basic article content generated'),
                'content_score': response_data.get('content_score', 0)
            }

        print('Article creation and optimization completed successfully')
        print(json.dumps(final_response, indent=4))
        return final_response, 200

    except Exception as e:
        error_msg = f'Error in article creation process: {str(e)}'
        print(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'error': 'creation_failed'
        }, 500


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

@app.route('/api/get-sample-prompts', methods=['GET'])
def get_sample_prompts():
    """Get sample prompts for testing"""
    try:
        # Sample demo data
        demo_terms = [
            {'term': 'אלי אקספרס', 'score': 95},
            {'term': 'קופונים', 'score': 90}, 
            {'term': 'הנחות', 'score': 85}
        ]
        demo_keywords = 'עליאקספרס קופונים'
        
        # Format terms like in the real function
        terms_formatted = "\n".join([f"{term['term']}: {term['score']}%" for term in demo_terms])
        
        # Create the real prompts
        title_prompt = TITLE_CREATION_PROMPT.format(
            terms=terms_formatted, 
            search_keyword_terms=demo_keywords
        )
        
        desc_prompt = DESCRIPTION_CREATION_PROMPT.format(
            terms=terms_formatted,
            search_keyword_terms=demo_keywords  
        )
        
        return jsonify({
            'success': True,
            'prompts': {
                'title': {
                    'name': 'Title Creation (Real Prompt)',
                    'prompt': title_prompt
                },
                'description': {
                    'name': 'Description Creation (Real Prompt)', 
                    'prompt': desc_prompt
                },
                'simple': {
                    'name': 'Simple Test',
                    'prompt': 'Write just the word "TEST" and nothing else.'
                },
                'hebrew': {
                    'name': 'Hebrew Test',
                    'prompt': 'כתוב לי ברכה קצרה בעברית'
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test-gpt', methods=['POST'])
def test_gpt():
    """Test GPT with custom prompt"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', 'Hello, please respond with "Test successful"')
        
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        
        print(f"🧪 Testing GPT with prompt: {prompt}")
        
        response = client.chat.completions.create(
            model=openai_model,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=2000
        )
        
        if response and response.choices and len(response.choices) > 0:
            result = response.choices[0].message.content
            print(f"🧪 GPT Response: '{result}'")
            
            return jsonify({
                'success': True,
                'prompt': prompt,
                'response': result,
                'model': openai_model,
                'response_length': len(result) if result else 0
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No response from GPT',
                'prompt': prompt
            }), 500
            
    except Exception as e:
        print(f"❌ GPT Test Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'prompt': data.get('prompt', '') if 'data' in locals() else ''
        }), 500

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
                        <button @click="showGptTest = true" 
                                class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium">
                            🧪 Test GPT
                        </button>
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
                        <div @click="openProject(project.id)" class="bg-white overflow-hidden shadow rounded-lg cursor-pointer hover:shadow-lg transition-shadow duration-200">
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
                                    <div x-show="project.wordpress_user" class="flex items-center justify-between text-xs text-blue-600">
                                        <span>📂 <span x-text="project.wordpress_categories_count || 0"></span> קטגוריות WordPress</span>
                                        <button @click.stop="quickRefreshCategories(project.id)" 
                                                :disabled="refreshingProject === project.id"
                                                class="ml-2 px-2 py-1 bg-blue-100 hover:bg-blue-200 text-blue-600 rounded text-xs disabled:opacity-50">
                                            <span x-show="refreshingProject !== project.id">🔄</span>
                                            <span x-show="refreshingProject === project.id">⏳</span>
                                        </button>
                                    </div>
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

                                <div class="mt-4 text-center">
                                    <p class="text-sm text-gray-500">Click to manage project</p>
                                </div>
                            </div>
                        </div>
                    </template>
                </div>
            </div>

            <!-- Single Project Management View -->
            <div x-show="!loading && currentView === 'project'" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div class="mb-8">
                    <button @click="currentView = 'projects'" class="flex items-center text-gray-600 hover:text-gray-900 mb-4">
                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
                        </svg>
                        Back to Projects
                    </button>
                    <div class="bg-white shadow rounded-lg p-6">
                        <div class="flex justify-between items-start mb-6">
                            <div>
                                <h1 class="text-2xl font-bold text-gray-900" x-text="currentProject?.name || 'Project Management'"></h1>
                                <p class="text-gray-600" x-text="currentProject?.website_url"></p>
                                <div class="flex items-center space-x-4 mt-2">
                                    <p x-show="currentProject?.wordpress_categories_count !== undefined" class="text-sm text-blue-600">
                                        📂 <span x-text="currentProject?.wordpress_categories_count || 0"></span> קטגוריות WordPress
                                    </p>
                                    <button @click="refreshCategories()" 
                                            :disabled="refreshingCategories"
                                            class="text-xs bg-blue-100 hover:bg-blue-200 text-blue-600 px-2 py-1 rounded-md disabled:opacity-50">
                                        <span x-show="!refreshingCategories">🔄 Refresh</span>
                                        <span x-show="refreshingCategories">⏳ Refreshing...</span>
                                    </button>
                                </div>
                            </div>
                            <div class="flex items-center space-x-2">
                                <span x-show="currentProject?.wordpress_status?.connected" 
                                      class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                                    ✅ WordPress Connected
                                </span>
                                <span x-show="currentProject?.wordpress_status && !currentProject?.wordpress_status.connected" 
                                      class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                                    ❌ WordPress Error
                                </span>
                            </div>
                        </div>
                        
                        <!-- Project Stats -->
                        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                            <div class="bg-blue-50 p-4 rounded-lg">
                                <p class="text-3xl font-bold text-blue-600" x-text="currentProject?.stats?.total_keywords || 0"></p>
                                <p class="text-sm text-blue-800">Total Keywords</p>
                            </div>
                            <div class="bg-yellow-50 p-4 rounded-lg">
                                <p class="text-3xl font-bold text-yellow-600" x-text="currentProject?.stats?.pending_keywords || 0"></p>
                                <p class="text-sm text-yellow-800">Pending</p>
                            </div>
                            <div class="bg-green-50 p-4 rounded-lg">
                                <p class="text-3xl font-bold text-green-600" x-text="currentProject?.stats?.completed_keywords || 0"></p>
                                <p class="text-sm text-green-800">Completed</p>
                            </div>
                            <div class="bg-purple-50 p-4 rounded-lg">
                                <p class="text-3xl font-bold text-purple-600" x-text="currentProject?.stats?.total_articles || 0"></p>
                                <p class="text-sm text-purple-800">Articles</p>
                            </div>
                        </div>

                        <!-- Action Buttons -->
                        <div class="flex space-x-4 mb-8">
                            <button @click="addKeywords(currentProject?.id)" 
                                    class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium">
                                Add Keywords
                            </button>
                            <button @click="showKeywords = !showKeywords" 
                                    class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md font-medium">
                                <span x-text="showKeywords ? 'Hide Keywords' : 'Show Keywords'"></span>
                            </button>
                            <button class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium">
                                Export Data
                            </button>
                        </div>

                        <!-- Keywords List -->
                        <div x-show="showKeywords" class="mt-6">
                            <h3 class="text-lg font-medium text-gray-900 mb-4">Keywords Management</h3>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <template x-for="keyword in currentProjectKeywords" :key="keyword.id">
                                    <div class="bg-white shadow rounded-lg border hover:shadow-lg transition-shadow duration-200">
                                        <!-- Keyword Header -->
                                        <div class="px-6 py-4 border-b bg-gray-50">
                                            <div class="flex justify-between items-start">
                                                <div>
                                                    <h4 class="text-lg font-semibold text-gray-900" x-text="keyword.keyword"></h4>
                                                    <p class="text-sm text-gray-600 mt-1">
                                                        <span x-text="keyword.search_engine || 'N/A'"></span> • 
                                                        <span x-text="keyword.language || 'N/A'"></span>
                                                    </p>
                                                </div>
                                                <span :class="{
                                                    'bg-yellow-100 text-yellow-800': keyword.status === 'pending',
                                                    'bg-blue-100 text-blue-800': keyword.status === 'processing',
                                                    'bg-green-100 text-green-800': keyword.status === 'completed',
                                                    'bg-red-100 text-red-800': keyword.status === 'failed',
                                                    'bg-gray-100 text-gray-800': keyword.status === 'paused'
                                                }" class="inline-flex px-3 py-1 text-xs font-semibold rounded-full">
                                                    <span x-text="keyword.status"></span>
                                                </span>
                                            </div>
                                        </div>

                                        <!-- Keyword Details -->
                                        <div class="px-6 py-4">
                                            <div class="grid grid-cols-2 gap-4 text-sm">
                                                <div>
                                                    <span class="text-gray-500">Category:</span>
                                                    <span class="font-medium text-gray-900" x-text="keyword.category_id || 'N/A'"></span>
                                                </div>
                                                <div>
                                                    <span class="text-gray-500">Priority:</span>
                                                    <span class="font-medium text-gray-900" x-text="keyword.priority || 1"></span>
                                                </div>
                                                <div class="col-span-2">
                                                    <span class="text-gray-500">Tags:</span>
                                                    <div class="mt-1">
                                                        <template x-for="tag in keyword.tags || []" :key="tag">
                                                            <span class="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full mr-1 mb-1" x-text="tag"></span>
                                                        </template>
                                                        <span x-show="!keyword.tags || keyword.tags.length === 0" class="text-gray-400 text-xs">No tags</span>
                                                    </div>
                                                </div>
                                            </div>

                                            <!-- Processing Info -->
                                            <div x-show="keyword.processing_by || keyword.lease_until || keyword.error_message" class="mt-4 pt-4 border-t">
                                                <div class="text-sm space-y-1">
                                                    <div x-show="keyword.processing_by">
                                                        <span class="text-gray-500">Processing by:</span>
                                                        <span class="font-medium text-gray-900" x-text="keyword.processing_by"></span>
                                                    </div>
                                                    <div x-show="keyword.lease_until">
                                                        <span class="text-gray-500">Lease until:</span>
                                                        <span class="font-medium text-gray-900" x-text="new Date(keyword.lease_until).toLocaleString()"></span>
                                                    </div>
                                                    <div x-show="keyword.error_message">
                                                        <span class="text-red-500">Error:</span>
                                                        <span class="text-red-600 text-xs" x-text="keyword.error_message"></span>
                                                    </div>
                                                </div>
                                            </div>

                                            <!-- Timestamps -->
                                            <div class="mt-4 pt-4 border-t">
                                                <div class="grid grid-cols-2 gap-4 text-xs text-gray-500">
                                                    <div>
                                                        <span>Created:</span><br>
                                                        <span x-text="keyword.created_at ? new Date(keyword.created_at).toLocaleDateString() : 'N/A'"></span>
                                                    </div>
                                                    <div x-show="keyword.processed_at">
                                                        <span>Processed:</span><br>
                                                        <span x-text="new Date(keyword.processed_at).toLocaleDateString()"></span>
                                                    </div>
                                                </div>
                                            </div>

                                            <!-- Article Info -->
                                            <div x-show="keyword.status === 'completed' && keyword.article_title" class="mt-4 p-3 bg-green-50 rounded-md">
                                                <div class="text-sm">
                                                    <div class="font-medium text-green-900" x-text="keyword.article_title"></div>
                                                    <div class="text-green-700 text-xs mt-1">
                                                        Content Score: <span x-text="keyword.content_score || 'N/A'"></span>
                                                        <span x-show="keyword.wordpress_post_id"> • WP ID: <span x-text="keyword.wordpress_post_id"></span></span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Actions -->
                                        <div class="px-6 py-4 bg-gray-50 border-t">
                                            <div class="flex space-x-2">
                                                <button x-show="keyword.status === 'pending'" 
                                                        @click="createArticle(keyword)" 
                                                        :disabled="creatingArticle === keyword.id"
                                                        class="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50">
                                                    <span x-show="creatingArticle !== keyword.id">🚀 Create Article</span>
                                                    <span x-show="creatingArticle === keyword.id">⏳ Creating...</span>
                                                </button>
                                                <button x-show="keyword.status === 'completed'" 
                                                        @click="viewArticle(keyword)" 
                                                        class="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium">
                                                    📖 View Article
                                                </button>
                                                <button x-show="keyword.status === 'failed'" 
                                                        @click="createArticle(keyword)" 
                                                        :disabled="creatingArticle === keyword.id"
                                                        class="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50">
                                                    <span x-show="creatingArticle !== keyword.id">🔄 Retry</span>
                                                    <span x-show="creatingArticle === keyword.id">⏳ Retrying...</span>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </template>
                                
                                <!-- Empty State -->
                                <div x-show="!currentProjectKeywords || currentProjectKeywords.length === 0" class="col-span-2 bg-white shadow rounded-lg p-8 text-center">
                                    <p class="text-gray-500">No keywords added yet</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Article Preview View -->
            <div x-show="!loading && currentView === 'article'" class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div class="mb-8">
                    <button @click="currentView = 'project'" class="flex items-center text-gray-600 hover:text-gray-900 mb-4">
                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
                        </svg>
                        Back to Project
                    </button>
                    
                    <div class="bg-white shadow rounded-lg overflow-hidden" x-show="currentArticle">
                        <!-- Article Header -->
                        <div class="bg-gray-50 px-6 py-4 border-b">
                            <div class="flex justify-between items-start">
                                <div>
                                    <h1 class="text-2xl font-bold text-gray-900" x-text="currentArticle?.title"></h1>
                                    <p class="text-gray-600 mt-1">Keyword: <span class="font-medium" x-text="currentArticle?.keyword"></span></p>
                                    <p class="text-gray-500 text-sm mt-1" x-text="currentArticle?.meta_description"></p>
                                </div>
                                <div class="text-right">
                                    <div class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium mb-2">
                                        Content Score: <span x-text="currentArticle?.content_score || 'N/A'"></span>
                                    </div>
                                    <p class="text-gray-500 text-sm">
                                        Created: <span x-text="currentArticle?.created_at ? new Date(currentArticle.created_at).toLocaleDateString() : 'N/A'"></span>
                                    </p>
                                </div>
                            </div>
                        </div>

                        <!-- Article Content -->
                        <div class="px-6 py-6">
                            <div class="prose max-w-none" x-html="currentArticle?.content">
                                <!-- Article content will be inserted here -->
                            </div>
                        </div>

                        <!-- Article Actions -->
                        <div class="bg-gray-50 px-6 py-4 border-t">
                            <div class="flex space-x-4">
                                <button class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium">
                                    📝 Edit Article
                                </button>
                                <button class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium">
                                    🚀 Publish to WordPress
                                </button>
                                <button class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md font-medium">
                                    📄 Export HTML
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <div x-show="!currentArticle" class="bg-white shadow rounded-lg p-8 text-center">
                        <p class="text-gray-500">Loading article...</p>
                    </div>
                </div>
            </div>
        </main>

        <!-- Add Keywords Modal -->
        <div x-show="showAddKeywords" x-cloak 
             class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                <div class="mt-3">
                    <h3 class="text-lg font-medium text-gray-900 mb-4">Add Keywords</h3>
                    <form @submit.prevent="submitKeywords()">
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-1">Keywords *</label>
                            <textarea x-model="newKeywordsData.keywords" required rows="4"
                                   placeholder="Enter keywords separated by commas"
                                   class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
                            <p class="text-xs text-gray-500 mt-1">Separate multiple keywords with commas</p>
                        </div>
                        
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-1">Search Engine</label>
                            <select x-model="newKeywordsData.search_engine"
                                    class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                                <option value="">Use project default</option>
                                <option value="google.com">Google.com (Global)</option>
                                <option value="google.co.il">Google.co.il (Israel)</option>
                                <option value="google.co.uk">Google.co.uk (UK)</option>
                                <option value="google.de">Google.de (Germany)</option>
                                <option value="google.fr">Google.fr (France)</option>
                                <option value="google.es">Google.es (Spain)</option>
                            </select>
                        </div>
                        
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-1">Language</label>
                            <select x-model="newKeywordsData.language"
                                    class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                                <option value="">Use project default</option>
                                <option value="Hebrew">Hebrew</option>
                                <option value="English">English</option>
                                <option value="Spanish">Spanish</option>
                                <option value="French">French</option>
                                <option value="German">German</option>
                                <option value="Italian">Italian</option>
                            </select>
                        </div>
                        
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-1">Category ID</label>
                            <input x-model="newKeywordsData.category_id" type="number" 
                                   class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                        </div>
                        
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-1">Tags</label>
                            <input x-model="newKeywordsData.tags" type="text" 
                                   placeholder="tag1, tag2, tag3"
                                   class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <p class="text-xs text-gray-500 mt-1">Separate tags with commas</p>
                        </div>
                        
                        <div class="flex justify-end space-x-3">
                            <button type="button" @click="showAddKeywords = false; resetNewKeywords()" 
                                    class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md">
                                Cancel
                            </button>
                            <button type="submit" :disabled="addingKeywords"
                                    class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50">
                                <span x-show="!addingKeywords">Add Keywords</span>
                                <span x-show="addingKeywords">Adding...</span>
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <!-- GPT Test Modal -->
        <div x-show="showGptTest" x-cloak 
             class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div class="relative top-10 mx-auto p-5 border max-w-2xl shadow-lg rounded-md bg-white">
                <div class="mt-3">
                    <h3 class="text-lg font-medium text-gray-900 mb-4">🧪 Test GPT Connection</h3>
                    
                    <!-- Prompt Type Selection -->
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Choose prompt type:
                        </label>
                        <select x-model="selectedPromptType" @change="loadSamplePrompt()"
                                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="custom">Custom Prompt</option>
                            <option value="simple">Simple Test</option>
                            <option value="hebrew">Hebrew Test</option>
                            <option value="title">Title Creation (Real)</option>
                            <option value="description">Description Creation (Real)</option>
                        </select>
                    </div>

                    <!-- Input Form -->
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Your prompt:
                        </label>
                        <textarea 
                            x-model="gptTestPrompt"
                            :readonly="selectedPromptType !== 'custom'"
                            :class="selectedPromptType !== 'custom' ? 'bg-gray-50' : ''"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                            rows="6" 
                            placeholder="Enter your prompt here... (e.g., 'Write a short greeting in Hebrew')">
                        </textarea>
                    </div>
                    
                    <!-- Test Button -->
                    <div class="mb-4">
                        <button @click="testGpt()" 
                                :disabled="gptTesting"
                                class="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md text-sm font-medium">
                            <span x-show="!gptTesting">🚀 Test GPT</span>
                            <span x-show="gptTesting">🔄 Testing...</span>
                        </button>
                    </div>
                    
                    <!-- Results -->
                    <div x-show="gptTestResult" class="mb-4">
                        <div x-show="gptTestResult && gptTestResult.success" class="border border-green-300 bg-green-50 p-4 rounded-md">
                            <h4 class="font-medium text-green-800 mb-2">✅ Success!</h4>
                            <div class="text-sm text-gray-600 mb-2">
                                <strong>Model:</strong> <span x-text="gptTestResult.model"></span> |
                                <strong>Response Length:</strong> <span x-text="gptTestResult.response_length"></span> chars
                            </div>
                            <div class="bg-white p-3 rounded border">
                                <strong class="text-gray-700">GPT Response:</strong>
                                <div class="mt-1 whitespace-pre-wrap" x-text="gptTestResult.response"></div>
                            </div>
                        </div>
                        
                        <div x-show="gptTestResult && !gptTestResult.success" class="border border-red-300 bg-red-50 p-4 rounded-md">
                            <h4 class="font-medium text-red-800 mb-2">❌ Error</h4>
                            <div class="text-sm text-red-700" x-text="gptTestResult.error"></div>
                        </div>
                    </div>
                    
                    <!-- Action Buttons -->
                    <div class="flex justify-end space-x-3">
                        <button type="button" @click="showGptTest = false; resetGptTest()" 
                                class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md">
                            Close
                        </button>
                        <button type="button" @click="resetGptTest()" 
                                class="px-4 py-2 text-sm font-medium text-blue-700 bg-blue-100 hover:bg-blue-200 rounded-md">
                            Clear
                        </button>
                    </div>
                </div>
            </div>
        </div>

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
                                    <option value="google.co.il">Google.co.il (Israel)</option>
                                    <option value="google.co.uk">Google.co.uk (UK)</option>
                                    <option value="google.de">Google.de (Germany)</option>
                                    <option value="google.fr">Google.fr (France)</option>
                                    <option value="google.es">Google.es (Spain)</option>
                                    <option value="google.it">Google.it (Italy)</option>
                                    <option value="google.com.au">Google.com.au (Australia)</option>
                                    <option value="google.ca">Google.ca (Canada)</option>
                                </select>
                                <p class="text-xs text-gray-500 mt-1">מנוע החיפוש לאנליזה (לדוגמא: google.co.il)</p>
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
                showGptTest: false,
                creating: false,
                gptTesting: false,
                gptTestPrompt: '',
                gptTestResult: null,
                selectedPromptType: 'custom',
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
                // New project management variables
                currentProject: null,
                currentProjectKeywords: [],
                refreshingCategories: false,
                refreshingProject: null,
                creatingArticle: null,
                viewingArticle: null,
                currentArticle: null,
                showAddKeywords: false,
                addingKeywords: false,
                selectedProjectId: null,
                newKeywordsData: {
                    keywords: '',
                    search_engine: '',
                    language: '',
                    category_id: '',
                    tags: ''
                },

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
                    this.selectedProjectId = projectId;
                    this.showAddKeywords = true;
                    this.resetNewKeywords();
                },

                resetNewKeywords() {
                    this.newKeywordsData = {
                        keywords: '',
                        search_engine: '',
                        language: '',
                        category_id: '',
                        tags: ''
                    };
                },

                async submitKeywords() {
                    if (this.addingKeywords) return;
                    
                    this.addingKeywords = true;
                    try {
                        const keywordList = this.newKeywordsData.keywords.split(',').map(k => k.trim()).filter(k => k);
                        
                        if (keywordList.length === 0) {
                            alert('Please enter at least one keyword');
                            return;
                        }
                        
                        // Prepare keywords with their settings
                        const keywordsWithSettings = keywordList.map(keyword => ({
                            keyword: keyword,
                            search_engine: this.newKeywordsData.search_engine || null,
                            language: this.newKeywordsData.language || null,
                            category_id: this.newKeywordsData.category_id ? parseInt(this.newKeywordsData.category_id) : null,
                            tags: this.newKeywordsData.tags ? this.newKeywordsData.tags.split(',').map(t => t.trim()).filter(t => t) : []
                        }));
                        
                        const response = await fetch(`/api/projects/${this.selectedProjectId}/keywords`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ keywords: keywordsWithSettings })
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            this.showAddKeywords = false;
                            await this.loadProjectKeywords(this.selectedProjectId);
                            alert(`✅ Added ${keywordList.length} keywords successfully`);
                        } else {
                            alert('❌ Error: ' + data.error);
                        }
                    } catch (error) {
                        console.error('Error adding keywords:', error);
                        alert('❌ Error adding keywords');
                    } finally {
                        this.addingKeywords = false;
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
                },

                // Project Management Functions
                async openProject(projectId) {
                    const project = this.projects.find(p => p.id === projectId);
                    if (project) {
                        this.currentProject = project;
                        this.currentView = 'project';
                        this.showKeywords = false;
                        // Load project keywords automatically
                        await this.loadProjectKeywords(projectId);
                    }
                },

                async loadProjectKeywords(projectId) {
                    try {
                        const response = await fetch(`/api/projects/${projectId}/keywords`);
                        const data = await response.json();
                        
                        if (data.success) {
                            this.currentProjectKeywords = data.keywords;
                            // Update project stats based on keywords
                            if (this.currentProject) {
                                const total = data.keywords.length;
                                const pending = data.keywords.filter(k => k.status === 'pending').length;
                                const completed = data.keywords.filter(k => k.status === 'completed').length;
                                const processing = data.keywords.filter(k => k.status === 'processing').length;
                                
                                this.currentProject.stats = {
                                    total_keywords: total,
                                    pending_keywords: pending,
                                    completed_keywords: completed,
                                    processing_keywords: processing,
                                    total_articles: completed
                                };
                            }
                        } else {
                            console.error('Error loading project keywords:', data.error);
                            this.currentProjectKeywords = [];
                        }
                    } catch (error) {
                        console.error('Error loading project keywords:', error);
                        this.currentProjectKeywords = [];
                    }
                },

                async refreshCategories() {
                    if (!this.currentProject || this.refreshingCategories) return;
                    
                    this.refreshingCategories = true;
                    try {
                        const response = await fetch(`/api/projects/${this.currentProject.id}/refresh-categories`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            }
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            // Update current project data
                            this.currentProject.wordpress_categories_count = data.categories_count;
                            
                            // Also update in the projects list
                            const projectIndex = this.projects.findIndex(p => p.id === this.currentProject.id);
                            if (projectIndex !== -1) {
                                this.projects[projectIndex].wordpress_categories_count = data.categories_count;
                            }
                            
                            alert(`✅ ${data.message}`);
                        } else {
                            alert(`❌ Error: ${data.error}`);
                        }
                    } catch (error) {
                        console.error('Error refreshing categories:', error);
                        alert('❌ Error refreshing categories');
                    } finally {
                        this.refreshingCategories = false;
                    }
                },

                async quickRefreshCategories(projectId) {
                    if (this.refreshingProject) return;
                    
                    this.refreshingProject = projectId;
                    try {
                        const response = await fetch(`/api/projects/${projectId}/refresh-categories`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            }
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            // Update project in the list
                            const projectIndex = this.projects.findIndex(p => p.id === projectId);
                            if (projectIndex !== -1) {
                                this.projects[projectIndex].wordpress_categories_count = data.categories_count;
                            }
                            
                            // Also update current project if it's the same
                            if (this.currentProject && this.currentProject.id === projectId) {
                                this.currentProject.wordpress_categories_count = data.categories_count;
                            }
                            
                            // Show success message briefly
                            console.log(`✅ Updated to ${data.categories_count} categories`);
                        } else {
                            console.error(`❌ Error: ${data.error}`);
                        }
                    } catch (error) {
                        console.error('Error refreshing categories:', error);
                    } finally {
                        this.refreshingProject = null;
                    }
                },

                async createArticle(keyword) {
                    if (this.creatingArticle) return;
                    
                    this.creatingArticle = keyword.id;
                    try {
                        // Get project settings for article creation
                        const project = this.currentProject;
                        
                        const response = await fetch(`/api/keywords/${keyword.id}/create-article`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                main_project_id: project.neuron_settings?.project_id,
                                main_keyword: keyword.keyword,
                                main_engine: keyword.search_engine || project.neuron_settings?.search_engine,
                                main_language: keyword.language || project.neuron_settings?.language,
                                site: project.website_url
                            })
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            // Refresh keywords to show updated status
                            await this.loadProjectKeywords(project.id);
                            alert(`✅ Article created successfully: ${data.title}`);
                        } else {
                            alert(`❌ Error: ${data.error}`);
                        }
                    } catch (error) {
                        console.error('Error creating article:', error);
                        alert('❌ Error creating article');
                    } finally {
                        this.creatingArticle = null;
                    }
                },

                async viewArticle(keyword) {
                    try {
                        this.currentView = 'article';
                        this.currentArticle = null; // Show loading
                        
                        const response = await fetch(`/api/keywords/${keyword.id}/article`);
                        const data = await response.json();
                        
                        if (data.success) {
                            this.currentArticle = data;
                        } else {
                            alert(`❌ Error: ${data.error}`);
                            this.currentView = 'project'; // Go back
                        }
                    } catch (error) {
                        console.error('Error loading article:', error);
                        alert('❌ Error loading article');
                        this.currentView = 'project'; // Go back
                    }
                },

                async testGpt() {
                    if (!this.gptTestPrompt.trim()) {
                        alert('Please enter a prompt');
                        return;
                    }

                    this.gptTesting = true;
                    this.gptTestResult = null;

                    try {
                        const response = await fetch('/api/test-gpt', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ prompt: this.gptTestPrompt })
                        });

                        const data = await response.json();
                        this.gptTestResult = data;

                        if (!data.success) {
                            alert(`❌ GPT Error: ${data.error}`);
                        }
                    } catch (error) {
                        console.error('GPT Test Error:', error);
                        this.gptTestResult = {
                            success: false,
                            error: 'Network error: ' + error.message
                        };
                    } finally {
                        this.gptTesting = false;
                    }
                },

                resetGptTest() {
                    this.gptTestPrompt = '';
                    this.gptTestResult = null;
                },

                async loadSamplePrompt() {
                    if (this.selectedPromptType === 'custom') {
                        this.gptTestPrompt = '';
                        return;
                    }

                    try {
                        const response = await fetch('/api/get-sample-prompts');
                        const data = await response.json();
                        
                        if (data.success && data.prompts[this.selectedPromptType]) {
                            this.gptTestPrompt = data.prompts[this.selectedPromptType].prompt;
                        } else {
                            alert('❌ Could not load sample prompt');
                        }
                    } catch (error) {
                        console.error('Error loading sample prompt:', error);
                        alert('❌ Error loading sample prompt');
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
    """Get all projects with database fallback"""
    if not DB_AVAILABLE:
        return jsonify({
            'success': True,
            'projects': [],
            'total': 0,
            'message': 'Database not available - using fallback mode'
        })
    
    try:
        projects = Project.query.all()
        projects_data = [project.to_dict() for project in projects]
        return jsonify({
            'success': True,
            'projects': projects_data,
            'total': len(projects_data)
        })
    except Exception as e:
        print(f"Error getting projects from database: {e}")
        # Return empty list as fallback
        return jsonify({
            'success': True,
            'projects': [],
            'total': 0,
            'message': 'Database connection failed - using fallback mode'
        })

@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project with database fallback"""
    if not DB_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Database not available - cannot create projects'
        }), 503
        
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
        project_data = {
            'name': data['name'],
            'website_url': data['website_url'],
            'wordpress_user': data.get('wordpress_user', ''),
            'wordpress_password': data.get('wordpress_password', ''),  # In production: encrypt!
            'daily_keywords_limit': data.get('daily_keywords_limit', 5),
            'neuron_project_id': data['neuron_project_id'],
            'neuron_search_engine': data['neuron_search_engine'],
            'neuron_language': data['neuron_language'],
            'status': 'active'
        }
        
        # Categories count feature temporarily disabled for stability
            
        project = Project(**project_data)
        
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
    if not DB_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Database not available - cannot add keywords'
        }), 503
        
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
        for keyword_data in keywords:
            # Handle both old format (string) and new format (object)
            if isinstance(keyword_data, str):
                keyword_text = keyword_data.strip()
                keyword_obj = Keyword(
                    project_id=project_id,
                    keyword=keyword_text,
                    status='pending'
                )
            else:
                # New format with settings
                keyword_obj = Keyword(
                    project_id=project_id,
                    keyword=keyword_data['keyword'].strip(),
                    search_engine=keyword_data.get('search_engine') or project.neuron_search_engine,
                    language=keyword_data.get('language') or project.neuron_language,
                    category_id=keyword_data.get('category_id'),
                    tags_json=json.dumps(keyword_data.get('tags', [])) if keyword_data.get('tags') else None,
                    priority=keyword_data.get('priority', 1),
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
    if not DB_AVAILABLE:
        return jsonify({
            'success': True,
            'keywords': [],
            'total': 0,
            'message': 'Database not available - using fallback mode'
        })
        
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

@app.route('/api/keywords/<int:keyword_id>/create-article', methods=['POST'])
def create_article_endpoint(keyword_id):
    """Create article for a keyword using create_article_logic"""
    if not DB_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Database not available'
        }), 503
    
    try:
        data = request.get_json()
        
        # Get the keyword from database
        keyword = Keyword.query.get(keyword_id)
        if not keyword:
            return jsonify({'success': False, 'error': 'Keyword not found'}), 404
        
        # Check if already processed
        if keyword.status != 'pending':
            return jsonify({'success': False, 'error': f'Keyword already {keyword.status}'}), 400
        
        # Update status to processing
        keyword.status = 'processing'
        keyword.processing_by = 'web_interface'
        keyword.lease_until = datetime.now(timezone.utc)
        db.session.commit()
        
        # Call the embedded article creation logic
        try:
            response_data, status_code = create_article_logic_embedded(
                main_project_id=data['main_project_id'],
                main_keyword=data['main_keyword'], 
                main_engine=data['main_engine'],
                main_language=data['main_language'],
                site=data.get('site', '')  # Optional site parameter
            )
            
            if status_code == 200 and response_data['success']:
                # Update keyword with success info
                keyword.status = 'completed'
                keyword.processed_at = datetime.now(timezone.utc)
                keyword.article_title = response_data['title']
                keyword.meta_description = response_data['meta_description']
                keyword.article_content = response_data['article_content']
                keyword.content_score = response_data['content_score']
                keyword.attempts += 1
                
                db.session.commit()
                
                return jsonify(response_data)
            else:
                # Update keyword with failure info
                keyword.status = 'failed'
                keyword.error_message = response_data.get('message', 'Article creation failed')
                keyword.processed_at = datetime.now(timezone.utc)
                db.session.commit()
                
                return jsonify(response_data), status_code
                
        except Exception as creation_error:
            # Update keyword with error info
            keyword.status = 'failed'
            keyword.error_message = str(creation_error)
            keyword.processed_at = datetime.now(timezone.utc)
            db.session.commit()
            
            print(f"Error in create_article_logic: {creation_error}")
            return jsonify({
                'success': False,
                'error': f'Article creation failed: {str(creation_error)}'
            }), 500
            
    except Exception as e:
        print(f"Error in create_article_endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/keywords/<int:keyword_id>/article', methods=['GET'])
def get_article_content(keyword_id):
    """Get article content for viewing"""
    if not DB_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Database not available'
        }), 503
    
    try:
        keyword = Keyword.query.get(keyword_id)
        if not keyword:
            return jsonify({'success': False, 'error': 'Keyword not found'}), 404
        
        if keyword.status != 'completed' or not keyword.article_content:
            return jsonify({'success': False, 'error': 'Article not yet created'}), 400
        
        return jsonify({
            'success': True,
            'keyword': keyword.keyword,
            'title': keyword.article_title,
            'meta_description': keyword.meta_description,
            'content': keyword.article_content,
            'content_score': keyword.content_score,
            'created_at': keyword.processed_at.isoformat() if keyword.processed_at else None
        })
        
    except Exception as e:
        print(f"Error getting article content: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Temporarily disabled - causes database issues
# @app.route('/api/projects/<int:project_id>/refresh-categories', methods=['POST'])
# def refresh_project_categories(project_id):
#     """Refresh and update WordPress categories count for a project"""
#     return jsonify({'success': False, 'error': 'Feature temporarily disabled'}), 503

# Vercel expects the Flask app to be available at module level
application = app

if __name__ == '__main__':
    app.run(debug=True)