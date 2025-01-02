from google.cloud import secretmanager


def get_secret(secret_name, version_id='latest'):
    try:
        client = secretmanager.SecretManagerServiceClient()
        # Define the resource name of the secret

        secret_path = f"projects/837622523261/secrets/{secret_name}/versions/{version_id}"
        # Access the secret version
        response = client.access_secret_version(name=secret_path)
        # Return the decoded payload (secret value)
        return response.payload.data.decode("UTF-8")
    except Exception as err:
        print("ERROR FETCHING SECRETS: ", err)
