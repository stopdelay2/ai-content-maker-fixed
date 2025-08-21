
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

from configs import *

from routes.create_article import create_article_bp
from routes.publish_to_stopdelay_blog import publish_to_stopdelay_blog_bp
from routes.publish_to_wordpress import publish_to_wordpress_blog_bp

#from modules.scheduler.apscheduler.apscheduler_general import *
from modules.scheduler.apscheduler.sheets_keyword_queue_job import *

app.register_blueprint(create_article_bp)
app.register_blueprint(publish_to_stopdelay_blog_bp)
app.register_blueprint(publish_to_wordpress_blog_bp)

####################################################
# Setup APScheduler
####################################################
# I disabled the scheduler for development purposes.

scheduler = BackgroundScheduler(timezone="Asia/Jerusalem")  # or your TZ

# Add the job to run at midnight every day
scheduler.add_job(
    func=keyword_scheduled_job,
    trigger='cron',
    id="daily-keyword-queue",
    hour=0, minute=0,
    replace_existing=True,
    coalesce=True,       # if the server was down at midnight, run once on startup
    max_instances=1,     # don’t overlap if a previous run is still going
    misfire_grace_time=None  # don’t run if we missed midnight OR (you can change to: 1h grace if the server wakes up late)
)

# Start the scheduler only in the main process (avoid Flask reloader double-start)
if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    scheduler.start()

# Optionally run the job once at startup (based on your flag)
if run_keywords_on_startup:
    keyword_scheduled_job()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown(wait=False))


##################################
# run app
##################################
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=app_port)