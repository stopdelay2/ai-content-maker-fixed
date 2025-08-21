import requests

from configs import *

#url = "https://midjourney-best-experience.p.rapidapi.com/mj/generate-fast"


def midjourney_generate_fast(
		prompt,
		hook_url
):

	querystring = {
		"prompt": prompt,
		"hook_url": hook_url
	}

	payload = {}
	headers = {
		"x-rapidapi-key": rapid_api_key,
		"x-rapidapi-host": "midjourney-best-experience.p.rapidapi.com",
		"Content-Type": "application/x-www-form-urlencoded"
	}

	response = requests.post(
		midjourney_generate_fast_url,
		data=payload,
		headers=headers,
		params=querystring
	)

	print(response.json())


def midjourney_get_job(
		task_id
):

	querystring = {
		"task_id": task_id
	}

	headers = {
		"x-rapidapi-key": rapid_api_key,
		"x-rapidapi-host": "midjourney-best-experience.p.rapidapi.com"
	}

	response = requests.get(
		midjourney_get_job_url,
		headers=headers,
		params=querystring)

	print(response.json())


def midjourney_action_fast(
		action,
		image_id
):


	querystring = {
		"action": action,
		"image_id": image_id,
		"hook_url": "https://www.google.com"
	}

	payload = {}
	headers = {
		"x-rapidapi-key": rapid_api_key,
		"x-rapidapi-host": "midjourney-best-experience.p.rapidapi.com",
		"Content-Type": "application/x-www-form-urlencoded"
	}

	response = requests.post(
		midjourney_action_fast_url,
		data=payload,
		headers=headers,
		params=querystring
	)

	print(response.json())


def tests():
	prompt = "a beautiful cat --ar 1920:1080"
	hook_url = "https://www.google.com/"

	task_id = 'de5a4f8b-ffa9-779b-d710-88bd9f1a1d8f'
	task_id_variation_1 = 'b6cd3e22-7af5-a64f-a081-f0b5c70fabd2'
	task_id_upsample1 = 'a9bcdc70-ec6c-dc01-cc76-c4b9835b90b7'
	task_id_upsample3 = 'a0382f48-1312-d216-6979-7884f24135b4'

	image_id = '1333958085244358656'
	action = "variation1"
	action_upsample1= 'upsample1'
	action_upsample3 = 'upsample3'

	'''
	midjourney_generate_fast(
		prompt,
		hook_url
	)	
	
	midjourney_action_fast(
		action_upsample3,
		image_id
	)
	'''

	midjourney_get_job(task_id_upsample3)


tests()
