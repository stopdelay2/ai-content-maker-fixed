import requests

from datetime import datetime

from configs import *


class AirtableClient:
    """
    A simple Airtable Client that can:
      - Initialize with base_id, table_name, and api_key
      - Fetch all records from the specified table (handling pagination)
    """

    def __init__(self, base_id: str, table_name: str, api_key: str):
        """
        :param base_id: The ID of the Airtable base (e.g. 'appXXXXXXXXXXXXXX')
        :param table_name: Name of the table (e.g. 'keywords')
        :param api_key: Airtable API key or personal access token (e.g. 'patXXXXXXXX')
        """
        self.base_id = base_id
        self.table_name = table_name
        self.api_key = api_key
        # Construct the base endpoint URL for all requests
        # e.g., https://api.airtable.com/v0/appXXXXXXXXXXXXXX/keywords
        self.base_url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"

    def get_all_records(self) -> list:
        """
        Fetch all records from the given Airtable table.
        Automatically handles Airtable's pagination using 'offset'.

        :return: A list of record dictionaries.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        records = []
        params = {}

        while True:
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()  # Raise an error if the request failed

            data = response.json()

            # Extend our overall records list
            records.extend(data.get("records", []))

            # Check if there's more data to fetch
            offset = data.get("offset")
            if not offset:
                # No more pages
                break

            # If there's an offset, add it to params to retrieve the next batch
            params["offset"] = offset

        print(f'Fetched records from airtable\n'
              f'timestamp: {datetime.now()}\n'
              f'records: {records}\n')

        return records


# Example usage:
def tests():

    # Replace these values with your actual base ID, table name, and API key
    BASE_ID = "appAPRjscCXO29RKy"
    TABLE_NAME = "keywords"
    API_KEY = airtable_api_key

    client = AirtableClient(base_id=BASE_ID, table_name=TABLE_NAME, api_key=API_KEY)
    all_records = client.get_all_records()

    print(json.dumps(all_records, indent=2))

    '''
    # Print the total number of records and the first record for inspection
    print(f"Fetched {len(all_records)} records.")
    if all_records:
        print("First record:", all_records[0])
    '''


#tests()
