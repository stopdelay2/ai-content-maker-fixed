from configs import *
import json
import requests

headers = {
    "X-API-KEY": neuron_api_key,
    "Accept": "application/json",
    "Content-Type": "application/json",
}

def list_neuron_projects():

    #print(neuron_api_endpoint)

    response = requests.request(
        "POST",
        neuron_api_endpoint + "/list-projects",
        headers=headers,
        #data=payload
    )

    print(response.text)


def main():
    list_neuron_projects()


#main()
