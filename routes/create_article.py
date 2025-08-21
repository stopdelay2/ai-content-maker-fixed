
import time
from flask import Blueprint,jsonify,request
import traceback
import json

from configs import *

from modules.third_party_modules.neuron_writer.neuron_general import *
from modules.third_party_modules.openai.openai_general import *
from modules.utils.text_and_string_functions_general import *
from modules.anchors.anchors_genreral import *

# Create a Blueprint
create_article_bp = Blueprint('create-article', __name__)


def create_article_logic(main_project_id,
                         main_keyword,
                         main_engine,
                         main_language,
                         site
                         ):
    """
    Does all the neuron and GPT logic for creating the article.
    Returns (response_dict, status_code).
    """
    # The code that was in create_article() goes here,
    # except you replace 'request.form.get(...)' with direct parameters,
    # and remove any Flask references.

    ###################################
    # article creation process
    ###################################


    #################################################################
    #################################################################
    # create a neuron query, and get query results
    #################################################################
    #################################################################

    def neuron_create_and_get_query(
            main_project_id,
            main_keyword,
            main_engine,
            main_language
    ):

        main_search_keyword_terms = sentence_to_multiline(main_keyword)

        ##########################################
        # make a new query with neuron
        ##########################################

        # make a new query with neuron
        new_query_response = neuron_new_query(main_project_id, main_keyword, main_engine, main_language)

        main_query_id = new_query_response['query']

        # sleep for 65 seconds (a new query usually takes around 60 seconds until it's finished,
        # according to the neuron documentation)
        print(f'response for new neuron query creation: {new_query_response} '
              f'\nsleeping for 65 seconds, to wait for the query to be ready.')
        time.sleep(65)

        ##########################################
        # get query results from neuron
        ##########################################

        start_time = time.time()  # Track when the loop started

        while True:
            # 1. Call the function to get current status
            neuron_query_response_data = neuron_get_query(main_query_id)
            status = neuron_query_response_data.get("status", "").lower()  # Convert to lowercase for consistency

            # 2. Check the status
            if status in ["waiting", "in progress"]:
                elapsed_time = time.time() - start_time

                # If 120 seconds have passed, exit the loop
                if elapsed_time >= 120:
                    print("Exceeded 120 seconds. Stopping the loop.")
                    break

                print(f"Status is '{status}'. Waiting 10 seconds before checking again...")
                time.sleep(10)

            elif status == "ready":
                # Status is "ready" -> proceed with next steps
                print("Status is 'ready'. Proceeding with the rest of the program...")
                break  # Continue after the loop

            elif status == "not found":
                # Status is "not found" -> print a message and exit main()
                print("Status is 'not found'. Exiting main() function.")
                return  # or sys.exit(1), if preferred

            else:
                # Handle any unexpected status if needed
                print(f"Received unexpected status '{status}'. Exiting.")
                break

            # Continue next steps here (only if status was "ready" or we timed out).
        print("Continuing with the rest of the code...")

        return_dict = {
            "neuron_query_response_data": neuron_query_response_data,
            "main_query_id": main_query_id,
            "main_search_keyword_terms": main_search_keyword_terms,
        }

        return return_dict

    #################################################################
    #################################################################
    # create title, meta-description, article, and upload to neuron
    # - for initial content evaluation
    #################################################################
    #################################################################

    def neuron_create_title_desc_article(
            neuron_query_dict
    ):
        ##########################################
        # extract neuron_query_dict
        ##########################################

        neuron_query_response_data = neuron_query_dict["neuron_query_response_data"]
        main_search_keyword_terms = neuron_query_dict["main_search_keyword_terms"]
        main_query_id = neuron_query_dict["main_query_id"]

        ##########################################
        # create title with GPT
        ##########################################

        main_title_terms = neuron_query_response_data['terms']['title']

        main_article_title = gpt_generate_title(
            openai_model,
            main_title_terms,
            main_search_keyword_terms
        )

        ##########################################
        # create meta-description with GPT
        ##########################################

        main_description_terms = neuron_query_response_data['terms']["desc"]

        main_article_description = gpt_generate_description(
            openai_model,
            main_description_terms,
            main_search_keyword_terms
        )

        ##########################################
        # create article with GPT
        ##########################################

        # h1 h2 terms - objects array
        main_h1_terms = neuron_query_response_data['terms']["h1"]
        main_h2_terms = neuron_query_response_data['terms']["h2"]

        # terms - string formatted
        title_terms_string = objects_array_to_multiline(main_title_terms)
        # description_terms_string = objects_array_to_multiline(main_description_terms)
        h1_terms_string = objects_array_to_multiline(main_h1_terms)
        h2_terms_string = objects_array_to_multiline(main_h2_terms)

        # content terms
        content_basic_terms = neuron_query_response_data['terms']['content_basic']
        content_extended_terms = neuron_query_response_data['terms']['content_extended']

        all_content_terms = content_basic_terms + content_extended_terms

        main_content_terms = format_terms_with_usage(
            all_content_terms
        )

        # create main article with GPT
        main_article_content = gpt_generate_article(
            openai_model,
            title_terms_string,
            h1_terms_string,
            h2_terms_string,
            main_content_terms
        )

        ######################################################################
        # upload initial article to neuron writer API, and get initial score
        ######################################################################

        import_content_response = neuron_import_content(
            main_query_id,
            main_article_content,
            main_article_title,
            main_article_description
        )

        return_dict = {
            "main_article_title": main_article_title,
            "main_article_description": main_article_description,
            "main_article_content": main_article_content,
            "import_content_response": import_content_response,
            "h1_terms_string": h1_terms_string,
            "h2_terms_string": h2_terms_string,
            "main_search_keyword_terms": main_search_keyword_terms,
            "main_query_id": main_query_id,
            "neuron_query_response_data": neuron_query_response_data
        }

        return return_dict

    #################################################################
    #################################################################
    # content optimization process -
    # optimize h1 h2 headlines,
    # careful switching of new headlines for old ones
    # addition of grey terms (terms not used)
    # removal of red terms (terms to use less)
    #################################################################
    #################################################################

    def content_optimization_process(
            content_and_terms_dict,
            site,
    ):

        result_dict = {
            'success': False
        }

        ##########################################
        # extract content_and_terms_dict
        ##########################################

        main_article_title = content_and_terms_dict['main_article_title']
        main_article_description = content_and_terms_dict['main_article_description']

        h1_terms_string = content_and_terms_dict['h1_terms_string']
        h2_terms_string = content_and_terms_dict['h2_terms_string']

        main_article_content = content_and_terms_dict['main_article_content']
        main_search_keyword_terms = content_and_terms_dict['main_search_keyword_terms']

        import_content_response = content_and_terms_dict['import_content_response']
        main_query_id = content_and_terms_dict['main_query_id']

        neuron_query_response_data = content_and_terms_dict['neuron_query_response_data']

        main_h1_h2_terms = f'H1 TERMS:\n' \
                           f'{h1_terms_string}' \
                           f'\n\n' \
                           f'H2 TERMS:' \
                           f'{h2_terms_string}'

        ##########################################
        # optimize headings
        ##########################################

        current_score = import_content_response["content_score"]

        def optimize_headings(
                main_article_content,
                current_score
        ):
            # anchor texts
            rules_str, anchors_str = load_rules_and_anchors(
                anchors_config_path,
                site,
            )

            # optimize headings
            main_optimized_headings = gpt_optimize_headings(
                openai_model,
                main_article_content,
                main_h1_h2_terms,
                main_search_keyword_terms,
                rules_str,
                anchors_str,
                site
            )

            # switch headings
            updated_html_content_dict = switch_headings(
                main_article_content,
                main_optimized_headings,
                current_score,
                main_query_id,
                main_article_title,
                main_article_description
            )

            print(updated_html_content_dict['message'])

            updated_html_content = updated_html_content_dict['updated_html_content']

            if updated_html_content_dict['success'] is False:
                return result_dict

            # update result dict result
            result_dict['success'] = True
            result_dict['updated_html_content'] = updated_html_content

            print(f'html content with improved headings inserted:'
                  f'\n{updated_html_content}')

            # evaluate content (it's already uploaded we just need to get the score)

            new_evaluate_content_response = neuron_evaluate_content(
                main_query_id,
                updated_html_content,
                main_article_title,
                main_article_description
            )

            current_score = new_evaluate_content_response['content_score']

            return updated_html_content, current_score

        # 2 rounds of headings optimizations
        print(f'\nheadings optimization round 1:\n')
        updated_html_content, current_score = optimize_headings(
            main_article_content,
            current_score)
        '''
        print(f'\nheadings optimization round 2:\n')
        updated_html_content,current_score = optimize_headings(
            updated_html_content,
            current_score
        )
        '''

        ##########################################
        # optimize for terms not used (grey terms)
        ##########################################

        main_terms_not_used = get_terms_not_used(
            updated_html_content,
            neuron_query_response_data
        )

        if len(main_terms_not_used) > 0:

            updated_html_content = gpt_add_terms_not_used(
                openai_model,
                updated_html_content,
                main_terms_not_used
            )

            # evaluate optimized content
            new_evaluate_content_response = neuron_evaluate_content(
                main_query_id,
                updated_html_content,
                main_article_title,
                main_article_description
            )

            # compare old score to new score -
            # if the score was not downgraded, upload new version
            if current_score <= new_evaluate_content_response['content_score']:
                neuron_import_content(
                    main_query_id,
                    updated_html_content,
                    main_article_title,
                    main_article_description
                )
                # set current score to new score
                current_score = new_evaluate_content_response['content_score']
        else:
            print('\nfound 0 terms not used (grey) - skipping grey term optimization process\n')

        #############################################
        # optimize for terms to use less (red terms)
        #############################################

        print(f'\nfirst round of red-terms reduction\n')

        main_terms_to_use_less = get_terms_used_excessively(
            updated_html_content,
            neuron_query_response_data
        )

        # if no red terms found (list length is 0),
        # #then skip the red-terms optimization step
        if len(main_terms_to_use_less) > 0:
            main_terms_to_reduce_string = format_use_less_objects(
                main_terms_to_use_less
            )

            updated_html_content = gpt_reduce_terms(
                openai_model,
                updated_html_content,
                main_terms_to_reduce_string
            )

            # import optimized content (it's best to optimize the content for reduced red terms - terms to use less)
            new_evaluate_content_response = neuron_import_content(
                main_query_id,
                updated_html_content,
                main_article_title,
                main_article_description
            )
        else:
            print(f'\nfound 0 red terms - skipping red term optimization process\n')

        # **********************************************
        # second round of red-terms reduction:
        # **********************************************

        print(f'\n2nd round of red-terms reduction\n')

        main_terms_to_use_less = get_terms_used_excessively(
            updated_html_content,
            neuron_query_response_data
        )

        # if no red terms found (list length is 0),
        # #then skip the red-terms optimization step
        if len(main_terms_to_use_less) > 0:

            main_terms_to_reduce_string = format_use_less_objects(
                main_terms_to_use_less
            )

            updated_html_content = gpt_reduce_terms(
                openai_model,
                updated_html_content,
                main_terms_to_reduce_string
            )

            # import optimized content (it's best to optimize the content for reduced red terms - terms to use less)
            new_evaluate_content_response = neuron_import_content(
                main_query_id,
                updated_html_content,
                main_article_title,
                main_article_description
            )
        else:
            print(f'\nfound 0 red terms - skipping red term optimization process\n')

        return_dict = {
            'main_article_title': main_article_title,
            'main_article_description': main_article_description,
            'updated_html_content': updated_html_content,
            'content_score': int(new_evaluate_content_response['content_score']
                                 if new_evaluate_content_response
                                 else current_score)
        }

        return return_dict

    #################################################################
    #################################################################
    # run all the grouped-processes in sequence
    #################################################################
    #################################################################

    # make neuron query, and get query result
    neuron_response_dict = neuron_create_and_get_query(
        main_project_id,
        main_keyword,
        main_engine,
        main_language
    )

    # print the result
    print(f'\n{neuron_response_dict}\n')

    #################################################################
    # with GPT, create: title, meta-description, article content
    # upload all the content to neuron, to get an initial valuation
    initial_content_evaluation = neuron_create_title_desc_article(
        neuron_response_dict
    )

    # print the result
    print(f'\n{initial_content_evaluation}\n')

    #################################################################
    optimized_content_dict = content_optimization_process(
        initial_content_evaluation,
        site
    )

    response_data = {
        'success': True,
        'message': 'Article content created successfully.',
        'title': optimized_content_dict['main_article_title'],
        'meta_description': optimized_content_dict['main_article_description'],
        'article_content': optimized_content_dict['updated_html_content'],
        'content_score': optimized_content_dict['content_score']
    }

    print(f'route /create-article called:')
    print(json.dumps(response_data, indent=4))

    return response_data, 200


@create_article_bp.route('/seo/create-article', methods=['POST'])
def create_article():
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
        # 2. Read from request.form
        ###################################

        project_id = request.form.get('project_id')
        keyword = request.form.get('keyword')
        engine = request.form.get('engine')
        language = request.form.get('language')
        site = request.form.get('wordpress_site')

        ###################################
        # 3. Call your logic function
        ###################################

        response_dict, status_code = create_article_logic(
            project_id,
            keyword,
            engine,
            language,
            site
        )

        return jsonify(response_dict), status_code

    except Exception as e:
        # Prints the type of exception, the exception message, and the traceback
        print(f"Error in /create-article: {type(e).__name__}: {str(e)}")
        traceback.print_exc()

        # Return a generic error message
        return jsonify(error="An error occurred"), 500

