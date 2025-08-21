import requests

from configs import *


#API_KEY = article_maker_main_api_key
API_KEY = wordpress_article_maker_api_key
#API_KEY = '123'

URL = f'http://localhost:{app_port}/seo/create-article'
#URL = f'https://microservice.stopdelay.com/seo/create-article'

HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': f'Bearer {API_KEY}'
}

project_id = '6ed49b94d882d5bf'
#keyword = 'авиакомпания отменила рейс что делать'
#engine = 'google.com'
#language = 'English'

test_data = {
    #'project_id': project_id,
    #'keyword': keyword,
    #'engine': engine,
    #'language': language
}


# Function to perform the POST request
def send_request(data):
    response = requests.post(URL, data=data, headers=HEADERS)
    print("Status Code:", response.status_code)
    print("Response Body:", response.text)


def make_article(
    func_project_id,
    func_keyword,
    func_engine,
    func_language
):

    data = {
        'project_id': func_project_id,
        'keyword': func_keyword,
        'engine': func_engine,
        'language': func_language
    }

    response = requests.post(URL, data=data, headers=HEADERS)
    print("Status Code:", response.status_code)
    print("Response Body:", response.text)


def make_article_upload_stopdelay(
    func_project_id,
    func_keyword,
    func_engine,
    func_language,
    category_id,
    tags_list,
    url
):

    data = {
        'project_id': func_project_id,
        'keyword': func_keyword,
        'engine': func_engine,
        'language': func_language,
        'category_id': category_id,
        'tags_list': tags_list
    }

    response = requests.post(url, data=data, headers=HEADERS)
    print("Status Code:", response.status_code)
    print("Response Body:", response.text)




def stopdelay_tests():

    keywords_list = [
        'emirates flight tracker',
        'etihad airways flights status',
        'airport arrivals leeds bradford',
        'airport luton london arrivals',
        'az211',
        'ryanair overbooking',
        'British airways overbooking',
        'Lot overbooking',
        'az247 Flight Delayed or Cancelled'
    ]



    #publish_stopdelay_url = f'http://localhost:{app_port}/seo/create-article/publish-to-stopdelay-blog'
    publish_stopdelay_url = 'https://microservice.stopdelay.com/seo/create-article/publish-to-stopdelay-blog'

    test_keyword = 'az247 Flight Delayed or Cancelled'
    category_id = 1
    tags = [1, 2, 3]

    '''
    for search_keyword in keywords_list:
        make_article(
            project_id,
            search_keyword,
            engine,
            language
        )
    '''

    make_article_upload_stopdelay(
        project_id,
        test_keyword,
        engine,
        language,
        category_id,
        tags,
        publish_stopdelay_url
    )


#stopdelay_tests()


def botly_articles():

    botly_keywords = [
        #'chatbot ai',
        'ai customer service chatbot',
    ]

    bolty_project_id = '58ef7f3a5bc9af7f'
    bolty_engine = 'google.com'
    bolty_language = 'English'

    # the target keyword
    botly_keyword = 'chatbot ai'

    make_article(
        bolty_project_id,
        botly_keyword,
        bolty_engine,
        bolty_language
    )


#botly_articles()


def make_article_upload_wordpress(
    func_project_id,
    func_keyword,
    func_engine,
    func_language,
    url,
    site
):

    data = {
        'project_id': func_project_id,
        'keyword': func_keyword,
        'engine': func_engine,
        'language': func_language,
        'site': site
    }

    response = requests.post(url, data=data, headers=HEADERS)
    print("Status Code:", response.status_code)
    print("Response Body:", response.text)



def wordpress_tests():

    url = f'http://localhost:{app_port}/seo/create-article/publish-to-wordpress-blog'

    keyword = '알리익스프레스 PC 버전' #wizz air overbooking_2'
    engine = 'google.co.kr' #google.co.uk'
    language = 'Korean'
    site = 'https://aliexprass.co.il/'

    make_article_upload_wordpress(
        project_id,
        keyword,
        engine,
        language,
        url,
        site
    )


wordpress_tests()
