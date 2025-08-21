import http.client
import json
import pprint
import time
import requests
from io import BytesIO

from configs import *

'''
def midjourney_create_image(
        prompt
):

    data = {
        "prompt": prompt
    }

    headers = {
        'Authorization': f'Bearer {imagine_api_dev_key}',  # <<<< TODO: remember to change this
        'Content-Type': 'application/json'
    }

    conn = http.client.HTTPSConnection("cl.imagineapi.dev")
    conn.request("POST", "/items/images/", body=json.dumps(data), headers=headers)

    response = conn.getresponse()
    response_data = json.loads(response.read().decode('utf-8'))

    pprint.pp(response_data)

    return response_data


def midjourney_get_image(
        image_id
):

    connection = http.client.HTTPSConnection("cl.imagineapi.dev")
    headers = {
        'Authorization': f'Bearer {imagine_api_dev_key}',
        'Content-Type': 'application/json'
    }

    try:
        connection.request("GET", f"/items/images/{image_id}", headers=headers)
        response = connection.getresponse()
        data = json.loads(response.read().decode())
        pprint.pp(data, indent=4)

        return data

    except Exception as error:
        print(f"Error: {error}")
'''


##########################################
# refactored
##########################################

# send a request to imagineapi.dev (midjourney wrapper)
def send_request(method, path, prompt=None):

    body = {
        "prompt": prompt
    }

    headers = {
        'Authorization': f'Bearer {imagine_api_dev_key}',
        'Content-Type': 'application/json'
    }

    conn = http.client.HTTPSConnection("cl.imagineapi.dev")
    conn.request(method, path, body=json.dumps(body) if body else None, headers=headers)
    response = conn.getresponse()
    data = json.loads(response.read().decode())
    conn.close()
    return data


# checks if the image status is in ['completed', 'failed'], else return false
# should be used inside an iterative loop
'''
def check_image_status(prompt_response_data):

    response_data = send_request('GET', f"/items/images/{prompt_response_data['data']['id']}")

    if response_data['data']['status'] in ['completed', 'failed']:
        print('Completed image details',)
        pprint.pp(response_data['data'])
        return True
    else:
        print(f"Image is not finished generation. Status: {response_data['data']['status']}")
        return False
'''


# download the midjourney generated image
def download_image(image_url):
    # Make the GET request
    response = requests.get(image_url)

    # Check for successful (200) response
    if response.status_code == 200:
        # Store the image bytes in memory
        image_in_memory = BytesIO(response.content)

        # Now 'image_in_memory' is a file-like object that contains the PNG data.
        # You can pass it around as a variable without writing it to disk.
        return image_in_memory

    else:
        print(f"Failed to download image. Status code: {response.status_code}")
        return None


##########################################
# New wrapper function
##########################################


def generate_image_from_prompt(
    prompt,
    sleep_delay_ms=5000,   # 5 seconds
    timeout_ms=1200000     # 20 minutes
):
    """
    End-to-end function that:
    1) Sends a prompt to create a Midjourney image.
    2) Polls until the image is completed or failed, or until timeout.
    3) If completed, downloads the image and returns it as a BytesIO object.

    :param prompt: The Midjourney-style prompt string.
    :param sleep_delay_ms: Delay (in milliseconds) between status checks.
    :param timeout_ms: Maximum time (in milliseconds) to keep retrying before timing out.
    :return: BytesIO object of the image if successful, otherwise raises an Exception or TimeoutError.
    """

    start_time = time.time()
    try:
        # 1. Send creation request
        prompt_response_data = send_request('POST', '/items/images/', prompt)
        print(f'prompt_response_data -')
        pprint.pp(prompt_response_data)
        if "data" not in prompt_response_data or "id" not in prompt_response_data["data"]:
            raise ValueError("The response for image creation did not contain a valid 'data' or 'id' field.")
        image_id = prompt_response_data["data"]["id"]

        # 2. Poll for completion
        while True:
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms >= timeout_ms:
                raise TimeoutError(f"Image generation timed out after {timeout_ms} ms.")

            # Check the image status
            response_data = send_request('GET', f"/items/images/{image_id}")
            if "data" not in response_data:
                raise ValueError("No 'data' field found in image status response.")
            image_data = response_data["data"]

            status = image_data.get("status")
            if status in ["completed", "failed"]:

                print(f'response_data -')
                pprint.pp(response_data)
                if status == "failed":
                    raise Exception(f"Image generation failed for ID={image_id}.")

                # 3. If completed, attempt download
                #    Choose whether to download from image_data['url'] or the first in 'upscaled_urls'
                #    We'll pick the first upscaled URL, but you can adjust as needed.
                upscaled_urls = image_data.get("upscaled_urls", [])
                if not upscaled_urls:
                    # fallback to 'url' if upscaled_urls is empty
                    image_url = image_data.get("url")
                    if not image_url:
                        raise ValueError("No valid URLs found to download the completed image.")
                else:
                    image_url = upscaled_urls[0]  # pick first upscaled URL

                image_in_memory = download_image(image_url)
                if image_in_memory:
                    # 4. Return the BytesIO object
                    return image_in_memory
                else:
                    raise Exception("Image download failed for a completed image.")
            else:
                # Not completed yet
                print(f"Image (ID={image_id}) is not finished. Current status: {status}")
                time.sleep(sleep_delay_ms / 1000.0)

    except TimeoutError:
        # Reraise or handle the timeout
        raise

    except Exception as e:
        # Log or re-raise any other exceptions
        print(f"An error occurred while generating the image: {e}")
        raise


def tests():

    prompt = "a pretty lady at the beach --ar 9:21 --chaos 40 --stylize 1000"


    #prompt_response_data = send_request('POST', '/items/images/', prompt)
    #pprint.pp(prompt_response_data)

    '''
    while not check_image_status(prompt_response_data):
        time.sleep(5)  # wait for 5 seconds
    '''

    image_in_memory = generate_image_from_prompt(prompt)
    print(image_in_memory)


#tests()
