import os
from dotenv import load_dotenv
import json
import yaml
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate



load_dotenv()

####################################
# app
####################################

# init flask app
app = Flask(__name__)

# Database configuration
database_url = os.getenv('DATABASE_URL', 'sqlite:///content_maker.db')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize database
from database_models import db
db.init_app(app)
migrate = Migrate(app, db)

app_port = os.getenv('APP_PORT')

article_maker_main_api_key = os.getenv('ARTICLE_MAKER_MAIN_API_KEY')

wordpress_article_maker_api_key = os.getenv('WORDPRESS_ARTICLE_MAKER_MAIN_API_KEY')

prompts_file_path = os.getenv('PROMPTS_FILE_PATH')
'''
# Load the prompts from the JSON file
with open(prompts_file_path, 'r', encoding='utf-8') as file:
    prompts = json.load(file)
'''

# Load the prompts from the YAML file
with open(prompts_file_path, 'r', encoding='utf-8') as file:
    prompts = yaml.safe_load(file)

anchors_config_path = os.getenv('ANCHORS_CONFIG_PATH')

# test
#print(prompts['title_creation_prompt'].format(terms='test123'))


# a mapping of neuron languages to stopdelay blog language codes
stopdelay_language_code_mapper = {
    'Russian' : "ru",
    'French' : "fr",
    'German' : "de",
    'Polish' : "pl",
    'Turkish' : "tr",
    'Italian' : "it",
    'Spanish' : "es",
    'Arabic' : "ar",
    'Ukrainian': "uk",
    'English': "en"

}


####################################
# neuron
####################################

neuron_api_key = os.getenv('NEURON_API_KEY')
neuron_api_endpoint = os.getenv('NEURON_API_ENDPOINT')
neuron_stopdelay_project_id = os.getenv('NEURON_STOPDELAY_PROJECT_ID')

####################################
# openai
####################################

openai_model = os.getenv('OPENAI_MODEL')
openai_image_model = os.getenv('OPENAI_IMAGE_MODEL')
openai_key = os.getenv('OPENAI_KEY')

openai_image_prompt_pattern = os.getenv('OPENAI_IMAGE_PROMPT_PATTERN')

#################################
# stopdelay
#################################

stopdelay_blog_api_key = os.getenv('STOPDELAY_BLOG_API_KEY')
stopdelay_blog_upload_route = os.getenv('STOPDELAY_BLOG_UPLOAD_ROUTE')

s3_bucket_name = os.getenv('S3_BUCKET_NAME')
s3_bucket_domain = os.getenv('S3_BUCKET_DOMAIN')
s3_bucket_domain_no_zone = os.getenv('S3_BUCKET_DOMAIN_NO_ZONE')
s3_bucket_path = os.getenv('S3_BUCKET_PATH')

######################################
# rapid - midjourney - best experience
######################################

rapid_api_key = os.getenv('RAPID_API_KEY')

midjourney_generate_fast_url = os.getenv('RAPID_MIDJOURNEY_GENERATE_FAST_URL')
midjourney_get_job_url = os.getenv('RAPID_MIDJOURNEY_GET_JOB_URL')
midjourney_action_fast_url = os.getenv('RAPID_MIDJOURNEY_ACTION_FAST_URL')


######################################
# imagineapi.dev - midjourney API
######################################

imagine_api_dev_key = os.getenv('IMAGINE_API_DEV_KEY')
midjourney_prompt_pattern = os.getenv('MIDJOURNEY_PROMPT_PATTERN')


######################################
# Airtable API
######################################

airtable_api_key = os.getenv('AIRTABLE_API_KEY')

stopdelay_airtable_base = os.getenv('STOPDELAY_AIRTABLE_BASE')
stopdelay_airtable_table_name = os.getenv('STOPDELAY_AIRTABLE_TABLE_NAME')


##################################
# APScheduler
##################################

# Flag to control run-on-startup
keywords_env_val = os.getenv('RUN_KEYWORDS_ON_STARTUP', '0')  # default to "0"
run_keywords_on_startup = (keywords_env_val == '1')

# maximum keywords per day
max_keywords_per_day = int(os.getenv('MAX_KEYWORDS_PER_DAY'))

google_sheets_keyword_lease_minutes = int(os.getenv('GOOGLE_SHEETS_KEYWORD_LEASE_MINUTES'))

##################################
# wordpress
##################################

#wordpress_user = os.getenv('KOREAN_WORDPRESS_USER') #os.getenv('WORDPRESS_USER')
#wordpress_password = os.getenv('KOREAN_WORDPRESS_PASSWORD') #os.getenv('WORDPRESS_PASSWORD')
#wordpress_site = os.getenv('KOREAN_WORDPRESS_SITE') #os.getenv('WORDPRESS_SITE')

wordpress_user = os.getenv('ISRAELI_WORDPRESS_USER') #os.getenv('WORDPRESS_USER')
wordpress_password = os.getenv('ISRAELI_WORDPRESS_PASSWORD') #os.getenv('WORDPRESS_PASSWORD')
#wordpress_site = os.getenv('') #os.getenv('WORDPRESS_SITE')


###################################
# google
###################################

google_sheets_key_path = os.getenv('GOOGLE_SHEETS_SERVICE_ACCOUNT_KEY_PATH')
google_spreadsheet_id = os.getenv('GOOGLE_SPREADSHEETS_ID')
google_spreadsheet_name = os.getenv('GOOGLE_SPREADSHEETS_NAME')

def tests():

    value = stopdelay_language_code_mapper['English']

    print(value)

#tests()
