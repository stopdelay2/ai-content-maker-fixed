
import time
import atexit
import os
from apscheduler.schedulers.background import BackgroundScheduler
from flask import render_template

from configs import *
from database_models import db

from routes.create_article import create_article_bp
from routes.publish_to_stopdelay_blog import publish_to_stopdelay_blog_bp
from routes.publish_to_wordpress import publish_to_wordpress_blog_bp

# Import new project management API
from projects_api import projects_api_bp

# Import both old and new schedulers for backward compatibility
from modules.scheduler.apscheduler.sheets_keyword_queue_job import keyword_scheduled_job as sheets_scheduler
from database_scheduler import database_scheduled_job

# Register existing blueprints
app.register_blueprint(create_article_bp)
app.register_blueprint(publish_to_stopdelay_blog_bp)
app.register_blueprint(publish_to_wordpress_blog_bp)

# Register new project management API
app.register_blueprint(projects_api_bp)

# Create database tables
with app.app_context():
    db.create_all()

# Dashboard route
@app.route('/')
def dashboard():
    """Render the main dashboard"""
    return render_template('dashboard.html')

####################################################
# Setup APScheduler
####################################################
# I disabled the scheduler for development purposes.

scheduler = BackgroundScheduler(timezone="Asia/Jerusalem")  # or your TZ

# Add the database-based scheduler job to run at midnight every day
scheduler.add_job(
    func=database_scheduled_job,
    trigger='cron',
    id="daily-database-scheduler",
    hour=0, minute=0,
    replace_existing=True,
    coalesce=True,       # if the server was down at midnight, run once on startup
    max_instances=1,     # don't overlap if a previous run is still going
    misfire_grace_time=None  # don't run if we missed midnight
)

# Optional: Keep Google Sheets scheduler for backward compatibility
# Uncomment if you want to run both schedulers
# scheduler.add_job(
#     func=sheets_scheduler,
#     trigger='cron',
#     id="daily-sheets-scheduler",
#     hour=0, minute=30,  # Run 30 minutes after database scheduler
#     replace_existing=True,
#     coalesce=True,
#     max_instances=1,
#     misfire_grace_time=None
# )

# Start the scheduler only in the main process (avoid Flask reloader double-start)
if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    scheduler.start()

# Optionally run the job once at startup (based on your flag)
if run_keywords_on_startup:
    database_scheduled_job()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown(wait=False))


##################################
# run app
##################################
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=app_port)