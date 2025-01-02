from google.cloud import storage
from get_secret_from_google import get_secret
import json


def __fetch_file_from_bucket(bucket_name, file_name):
    try:
        # Initialize the Google Cloud Storage client
        client = storage.Client()
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(file_name)

        # Download and decode the JSON file
        data = json.loads(blob.download_as_text())
        return data
    except Exception as err:
        print("ERROR FETCHING FILE FROM BUCKETS ==> ", err)
        return {}


def get_workspaces_api_keys() -> dict:
    bucket_name = "notion-workspaces-project-bucket"
    file_name = 'workspaces_api_keys.json'

    try:
        json_data = __fetch_file_from_bucket(bucket_name, file_name)

        return json_data

    except Exception as e:
        print("ERROR GETTING WORKSPACES API KEYS ==> ",  e)
        return {}
