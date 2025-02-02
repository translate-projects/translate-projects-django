import sys
import requests
from django.conf import settings

def get_error_message(response):
    try:
        return response.json().get('message', 'Error unknown')
    except ValueError:
        return 'Error on updating translation data'

def get_translations_from_api(self,data, source_lang, target_lang, route_file):
    url_api = f'https://api.translateprojects.dev/v1/translations/?source_lang={source_lang}&target_lang={target_lang}'
    
    if route_file:
        url_api += f"&route_file={route_file}"
    
    url_api += '&type_project=django'

    token = getattr(settings, "TRANSLATE_PROJECTS_API_KEY", None)


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
    if response.status_code == 524 or response.status_code == 504:
        get_translations_from_api(self,data, source_lang, target_lang, route_file)

    if response.status_code == 400:
        error_message = get_error_message(response)
        self.stdout.write(self.style.ERROR(f"Error on updating translation data: {error_message}"))
        sys.exit(1)
        
    elif response.status_code == 403:
        error_message = get_error_message(response)
        self.stdout.write(self.style.ERROR(f"Permission error: {error_message}"))
        sys.exit(1)

    elif response.status_code != 200 and response.status_code != 524 and response.status_code != 504:
        error_message = get_error_message(response)
        self.stdout.write(self.style.ERROR(f"Error on updating translation data: {error_message}"))
        sys.exit(1)
    
    return response.json()
