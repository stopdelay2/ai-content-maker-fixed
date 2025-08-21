
from flask import Blueprint,jsonify,request
import traceback

from configs import *

from routes.create_article import *

from routes.create_article import create_article
from modules.stopdelay.stopdelay_blog import publish_article_to_stopdelay_blog
from modules.utils.general_utils import *
from modules.third_party_modules.midjourney.imagine_api_dev import *
from modules.utils.blog_utils import *
from modules.third_party_modules.aws.s3.s3_general import *

# Create a Blueprint
publish_to_stopdelay_blog_bp = Blueprint('publish-to-stopdelay-blog', __name__)


# the internal function (of this route),
# this is for the purpose of calling this function from other modules, outside this route.
def create_article_and_publish_internal(
        keyword,
        category_id,
        tags_list,
        project_id,
        engine,
        language
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
    )

    # If create_article() encountered an error, just return it immediately
    if status_code != 200:
        # If an error occurred, just return that data
        return response_data, status_code

    # 2. Now do your extra “publishing” step
    data = response_data

    # transform the google keyword into a url slug format
    url_slug = keyword_to_slug(keyword)

    ############################################
    # midjourney picture
    ############################################

    # create an article picture with midjourney
    midjourney_prompt = midjourney_prompt_pattern.format(
        article_topic=keyword
    )

    picture = generate_image_from_prompt(
        midjourney_prompt
    )

    # upload picture to aws s3 bucket of stopdelay, and return its URL
    picture_name = url_slug.replace('-', '_')

    object_key = f'{s3_bucket_path}{picture_name}.jpeg'

    upload_image_bytesio(
        picture,
        s3_bucket_name,
        object_key)

    picture_url = s3_bucket_domain + object_key
    print(f'The picture URL that have been constructed - \n'
          f'{picture_url}')

    picture_url_no_zone = s3_bucket_domain_no_zone + object_key

    ############################################
    # publish article to stopdelay blog
    ############################################

    stopdelay_langauge_code = stopdelay_language_code_mapper[language]

    # transform the articles HTML format (used by neuron writer API),
    # to editor.js format (or something that resembles it)
    data['article_content'] = html_to_editorjs(
        data['article_content'],
        picture_url_no_zone,
        keyword
    )

    # 3. Call some external blog API with article_content
    #    e.g. publish_article_to_stopdelay_blog(article_content)
    #    (You'll have to implement that.)
    stopdelay_response = publish_article_to_stopdelay_blog(
        data['title'],
        url_slug,
        data['meta_description'],
        data['article_content'],
        picture_url,
        category_id,
        tags_list,
        stopdelay_blog_upload_route,
        stopdelay_blog_api_key,
        stopdelay_langauge_code
    )

    # 4. Craft a final response that includes the original data + new info
    #    or just replace the original response JSON with more fields:
    data['published_to_stopdelay_blog'] = stopdelay_response
    print(f'data - \n{data}')

    return {
        'success': True,
        'message': 'Article created & published successfully.',
        'data': data
    }


@publish_to_stopdelay_blog_bp.route('/seo/create-article/publish-to-stopdelay-blog', methods=['POST'])
def create_article_and_publish():
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

        if api_key != article_maker_main_api_key:
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
        category_id = int(request.form.get('category_id'))
        tags_list = list(request.form.get('tags_list'))
        project_id = request.form.get('project_id')
        engine = request.form.get('engine')
        language = request.form.get('language')

        # Call the internal function
        result = create_article_and_publish_internal(
            keyword,
            category_id,
            tags_list,
            project_id,
            engine,
            language
        )
        return jsonify(result), 200 if result['success'] else 500

    except Exception as e:
        # Prints the type of exception, the exception message, and the traceback
        print(f"Error in /seo/create-article/publish-to-stopdelay-blog: {type(e).__name__}: {str(e)}")
        traceback.print_exc()

        # Return a generic error message
        return jsonify(error="An error occurred"), 500
