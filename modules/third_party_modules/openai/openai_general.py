from openai import OpenAI
import json

from configs import *
from modules.third_party_modules.neuron_writer.neuron_general import \
    article,\
    neuron_get_query,\
    query_id, \
    article_terms_not_used_added
from modules.utils.text_and_string_functions_general import \
    get_terms_not_used,\
    get_terms_used_excessively, \
    format_use_less_objects

client = OpenAI(api_key=openai_key)


def gpt_generate_title(openai_model,title_terms,search_keyword_terms):

    prompt = prompts['title_creation_prompt'].format(
        terms=title_terms,
        search_keyword_terms=search_keyword_terms

    )
    print(f'title_creation_prompt - \n{prompt}\n')

    completion = client.chat.completions.create(
      model=openai_model,
      messages=[
        #{"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
      ]
    )

    print('\n')
    print(f'openai response: {completion}')
    print(f'message: {completion.choices[0].message.content}\n')

    return completion.choices[0].message.content


def gpt_generate_description(openai_model,terms,search_keyword_terms):

    prompt = prompts['description_creation_prompt'].format(
        terms=terms,
        search_keyword_terms=search_keyword_terms

    )
    print(f'description_creation_prompt - \n{prompt}\n')

    completion = client.chat.completions.create(
      model=openai_model,
      messages=[
        {"role": "user", "content": prompt}
      ]
    )

    print('\n')
    print(f'openai response: {completion}')
    print(f'message: {completion.choices[0].message.content}\n')

    return completion.choices[0].message.content


def gpt_generate_article(
        openai_model,
        title_terms,
        h1_terms,
        h2_terms,
        terms
):

    prompt = prompts['article_prompt'].format(
        title_terms=title_terms,
        h1_terms=h1_terms,
        h2_terms=h2_terms,
        terms=terms
    )

    print(f'article_prompt - \n{prompt}\n')

    completion = client.chat.completions.create(
      model=openai_model,
      messages=[
        {"role": "user", "content": prompt}
      ]
    )

    message = completion.choices[0].message.content
    text_without_asterisks = message.replace('*', '')

    print('\n')
    print(f'openai response: {completion}')
    print(f'raw message: {message}\n')
    print('\n')
    print(f'message (without asterisks): '
          f'{text_without_asterisks}'
          f'\n')

    return text_without_asterisks


def gpt_optimize_headings(
        openai_model,
        article,
        terms,
        search_keyword_terms,
        rules_str,
        anchors_str,
        site
):

    prompt = prompts['headings_optimization_prompt'].format(
        terms=terms,
        article=article,
        search_keyword_terms=search_keyword_terms,
        homepage=site,
        anchor_text_rules=rules_str,
        anchor_texts=anchors_str
    )

    print()
    print(f'headings_optimization_prompt - \n{prompt}')
    print()

    completion = client.chat.completions.create(
      model=openai_model,
      messages=[
        {"role": "user", "content": prompt}
      ]
    )

    message = completion.choices[0].message.content
    text_without_asterisks = message.replace('*', '')

    print('\n')
    print(f'openai response: {completion}')
    print(f'raw message: {message}\n')
    print('\n')
    print(f'message (without asterisks): '
          f'{text_without_asterisks}'
          f'\n')

    return text_without_asterisks


# gpt add terms not used
def gpt_add_terms_not_used(openai_model,article,terms_list):

    terms = ''

    for term in terms_list:
        terms += term + "\n"

    print(f'terms not used: {terms}')

    prompt = prompts['terms_not_used_prompt'].format(
        terms=terms,
        article=article
    )

    print(prompt)
    print()

    completion = client.chat.completions.create(
      model=openai_model,
      messages=[
        {"role": "user", "content": prompt}
      ]
    )

    message = completion.choices[0].message.content
    text_without_asterisks = message.replace('*', '')

    print('\n')
    print(f'openai response: {completion}')
    print(f'raw message: {message}\n')
    print('\n')
    print(f'message (without asterisks): '
          f'{text_without_asterisks}'
          f'\n')

    return text_without_asterisks


def gpt_reduce_terms(openai_model,article,terms):

    print(f'terms not used: {terms}')

    prompt = prompts['terms_to_use_less_prompt'].format(
        terms=terms,
        article=article
    )

    print(prompt)
    print()

    completion = client.chat.completions.create(
      model=openai_model,
      messages=[
        {"role": "user", "content": prompt}
      ]
    )

    message = completion.choices[0].message.content
    text_without_asterisks = message.replace('*', '')

    print('\n')
    print(f'openai response: {completion}')
    print(f'raw message: {message}\n')
    print('\n')
    print(f'message (without asterisks): '
          f'{text_without_asterisks}'
          f'\n')

    return text_without_asterisks

def tests():

    search_keyword_terms = """
    "w6"
    "1030"
    "flight"
    "delayed"
    "or"
    "cancelled"
    """

    title_terms = """
    - "flight" (60%)
    - "w61030" (40%)
    - "wizz air flight" (30%)
    - "delay" (20%)
    - "cancel" (20%)
    - "1030" (20%)
    - "w6 1030 flight" (20%)
    - "wzz1030" (20%)
    - "moment" (20%)
    """

    description_terms = """
    - "flight" (70%)
    - "delay" (50%)
    - "flight status" (50%)
    - "status" (50%)
    - "track" (50%)
    - "1030" (30%)
    - "compensation" (30%)
    - "w61030" (30%)
    - "departure" (30%)
    - "schedule" (30%)
    - "real-time" (30%)
    - "delayed or cancelled" (20%)
    - "cancel" (20%)
    - "wizz air flight" (20%)
    - "airport" (20%)
    - "arrival" (20%)
    - "cancellation" (20%)
    """

    h1_h2_terms = '''
    H1 TERMS:
    flight
    delay
    delayed or cancelled
    cancel
    wizz air flight
    1030
    w61030
    arrival
    en.flightera.net
    flight status
    compensation
    status
    claim
    departure
    wizz air flight w61030
    information
    w61030 flight
    wzz1030
    refund
    claim compensation
    plan
    
    H2 TERMS:
    flight
    flight status
    status
    route
    delay
    cancel
    wizz air flight
    1030
    w6 1030 flight
    information
    wizz air w6 1030 funchal
    w6 1030 funchal to katowice
    1030 funchal to katowice flight
    disruption
    map
    flight delay
    compensation
    w61030
    claim
    track
    passenger
    cancellation
    schedule
    refund
    travel
    passenger rights
    cause
    available
    avoid
    '''

    title = 'Wizz Air Flight W6 1030 Delayed or Cancelled? Updates on W61030'
    description = 'Track the real-time flight status of W6 1030. Check if your flight is delayed or cancelled. Stay updated on schedule changes and potential compensation.'

    score = 84

    '''
    gpt_generate_title(
        openai_model,
        title_terms,
        search_keyword_terms
    )
    

    gpt_generate_description(
        openai_model,
        description_terms,
        search_keyword_terms
    )
    

    gpt_generate_article(
        openai_model,
        prompts['article_test_prompt']
    )
    

    gpt_optimize_headings(
        openai_model,
        article,
        h1_h2_terms,
        search_keyword_terms
    )
    '''

    query_result = neuron_get_query(query_id)

    #terms_not_used = get_terms_not_used(article, query_result)
    #gpt_add_terms_not_used(openai_model, article, terms_not_used)

    terms_to_use_less = get_terms_used_excessively(
        article_terms_not_used_added,
        query_result
    )

    terms_to_reduce_string = format_use_less_objects(terms_to_use_less)

    gpt_reduce_terms(
        openai_model,
        article_terms_not_used_added,
        terms_to_reduce_string
    )


#tests()
