import requests

def upload_file(server_url, file_path):
    with open(file_path, "rb") as f:
        response = requests.post(server_url, data=f.read())
    return response.status_code
