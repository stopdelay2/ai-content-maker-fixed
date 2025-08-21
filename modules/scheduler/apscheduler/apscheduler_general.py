import requests
from datetime import datetime

from flask import Flask

import atexit

from modules.third_party_modules.airtable.airtable_general import AirtableClient
from routes.publish_to_stopdelay_blog import create_article_and_publish_internal

from configs import *
from configs import airtable_api_key


def keyword_scheduled_job():
    """
    This function runs every 24 hours. It:
      1. Queries Airtable for records.
      2. Filters records that do NOT have article_was_created = True.
      3. Takes up to MAX_KEYWORDS_PER_DAY of them and calls create_article_and_publish_internal() for each.
      4. After successful publish, updates that record's 'article_was_created' field in Airtable.
    """
    print(f"\nRunning scheduled job for airtable keywords, datetime: {datetime.now() }\n")

    client = AirtableClient(stopdelay_airtable_base,
                            stopdelay_airtable_table_name,
                            airtable_api_key
                            )
    all_records = client.get_all_records()

    # Filter records to those that do NOT have article_was_created = True
    # For example, some might not have 'article_was_created' at all, or might be False

    unprocessed_records = []
    for record in all_records:
        fields = record.get('fields', {})
        if not fields.get('article_was_created', False):
            unprocessed_records.append(record)

    # sort records by dateCreated, ascending
    # Sort the unprocessed_records list in-place by createdTime ascending
    unprocessed_records.sort(key=lambda keyword_record: keyword_record["createdTime"])

    # Limit to the first N = MAX_KEYWORDS_PER_DAY
    to_process = unprocessed_records[:max_keywords_per_day]

    for record in to_process:
        fields = record['fields']
        record_id = record['id']

        keyword = fields.get('keyword')
        category_id = fields.get('category_id')
        tags_list = fields.get('tags_list', [])
        project_id = fields.get('project_Id')  # from your example JSON
        engine = fields.get('engine')
        language = fields.get('language')

        print(f"\nrunning scheduled job for keyword {keyword}\n")

        # 1) Call your internal function to create & publish the article
        result = create_article_and_publish_internal(
            keyword, category_id, tags_list, project_id, engine, language
        )
        print(f"Result for keyword {keyword}: {result}")

        # 2) If success, update Airtable to set article_was_created = True
        if result['success']:
            try:
                # Patch the record in Airtable
                update_url = f"https://api.airtable.com/v0/{stopdelay_airtable_base}/{stopdelay_airtable_table_name}/{record_id}"
                headers = {
                    "Authorization": f"Bearer {airtable_api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "fields": {
                        "article_was_created": True
                    }
                }
                resp = requests.patch(update_url, headers=headers, json=data)
                resp.raise_for_status()
                print(f"Successfully updated record {record_id} in Airtable.")
            except Exception as e:
                print(f"Error updating record {record_id} in Airtable: {e}")





