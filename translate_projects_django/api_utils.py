import requests
from django.conf import settings

def get_translations_from_api(data, source_lang, target_lang, route_file):
    url_api = f'https://translateprojects.neiderruiz.com/api/general_translations/?source_lang={source_lang}&target_lang={target_lang}'
    
    if route_file:
        url_api += f"&route_file={route_file}"
    
    url_api += '&type_project=django'

    token = settings.TRANSLATEFILES_API_TOKEN

    if token:
        token = f"Token {token}"

    response = requests.post(
        url_api,
        json=data,
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token,
        }
    )
    if response.status_code == 524:
        get_translations_from_api(data, source_lang, target_lang, route_file)

    if response.status_code != 200 and response.status_code != 524:
        raise Exception(f"Error on updating translation data: {response.status_code}")
    
    return response.json()
