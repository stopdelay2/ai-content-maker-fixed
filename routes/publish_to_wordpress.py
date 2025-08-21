
from flask import Blueprint,jsonify,request
import traceback

from configs import *

from modules.utils.html_utils import *
from modules.tests.test_data.test_data_general import test_html

from routes.create_article import *


# Create a Blueprint
publish_to_wordpress_blog_bp = Blueprint('publish-to-wordpress-blog', __name__)


# the internal function (of this route),
# this is for the purpose of calling this function from other modules, outside this route.
def create_article_and_publish_internal(
        keyword,
        project_id,
        engine,
        language,
        site
):
    ##########################################################
    # pass request to a 'middle-route'
    # to handle creation of article, tite, and meta-description
    ###########################################################

    # 1. Call the existing create_article() route function
    #    This returns a tuple (Response, status_code).

    response_data, status_code = create_article_logic(
        project_id,
        keyword,
        engine,
        language,
        site
    )

    # If create_article() encountered an error, just return it immediately
    if status_code != 200:
        # If an error occurred, just return that data
        return response_data, status_code

    # 2. Now do your extra “publishing” step
    data = response_data

    ############################################
    # process article html
    # + AI images generation
    # (generation + upload + insert in article )
    ############################################

    # create 2 in-article images from a prompt,
    # upload them to WordPress,
    # and insert the image URLs into the article

    article_html = process_article_html(
        wordpress_site,
        wordpress_user,
        wordpress_password,
        data['article_content']
    )

    ############################################
    # create an article feature image (main image)
    # and upload the article to wordpress
    ############################################

    create_post_with_featured_image(
        wordpress_site,
        wordpress_user,
        wordpress_password,
        keyword,
        data['title'],
        article_html,
        status="publish",
        meta_description=data['meta_description'],  # <- your generated meta
        seo_plugin="yoast"  # or "rankmath"/"aioseo"/"none"
    )

    return {
        'success': True,
        'message': 'Article created & published successfully.',
    }


@publish_to_wordpress_blog_bp.route('/seo/create-article/publish-to-wordpress-blog', methods=['POST'])
def create_article_and_publish_wordpress():
    try:
        ###################################
        # Authorization
        ###################################

        # Check if an 'Authorization' header is present
        api_key = ""
        auth_header = request.headers.get('Authorization')

        if auth_header is None:
            app.logger.warning(f"Unauthorized access attempt.")
            return jsonify({'error': 'Unauthorized', 'message': 'Missing Authorization header'}), 401

        parts = auth_header.split()
        if len(parts) == 2 and parts[0] == 'Bearer':
            api_key = parts[1]

        if api_key != wordpress_article_maker_api_key:
            # Log the attempt, consider logging IP address and other relevant data
            app.logger.warning(f"Unauthorized access attempt.")
            # Return a generic error message
            response = jsonify({'error': 'Unauthorized', 'message': 'Access is denied due to invalid credentials.'})
            response.status_code = 401
            response.headers['WWW-Authenticate'] = 'Basic realm="Login Required"'
            return response

        ###################################
        # extract reqeust data
        ###################################

        keyword = request.form.get('keyword')
        #category_id = int(request.form.get('category_id'))
        #tags_list = list(request.form.get('tags_list'))
        project_id = request.form.get('project_id')
        engine = request.form.get('engine')
        language = request.form.get('language')
        site = request.form.get('site')

        # Call the internal function
        result = create_article_and_publish_internal(
            keyword,
            project_id,
            engine,
            language,
            site
        )

        return jsonify(result), 200 if result['success'] else 500

    except Exception as e:
        # Prints the type of exception, the exception message, and the traceback
        print(f"Error in /seo/create-article/publish-to-wordpress-blog: {type(e).__name__}: {str(e)}")
        traceback.print_exc()

        # Return a generic error message
        return jsonify(error="An error occurred"), 500