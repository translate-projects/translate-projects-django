import sys
import requests
from django.conf import settings
from .style import StyledMessages

def get_error_message(response):
    """Extract error message from API response."""
    try:
        return response.json().get('message', 'Unknown error')
    except ValueError:
        return 'Error on updating translation data'


API_BASE_URL = "https://api.translateprojects.dev"

styled_messages = StyledMessages()

class Api:
    def __init__(self, base_url=API_BASE_URL, token=None):
        self.base_url = base_url.rstrip('/')
        self.token = token or getattr(settings, "TRANSLATE_PROJECTS_API_KEY", None)
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        if self.token:
            self.headers['Authorization'] = f"Token {self.token}"

    def make_request(self, method, endpoint, params=None, data=None, retries=3):
        """General method to handle API requests with retries."""
        url = f"{self.base_url}{endpoint}"
        for attempt in range(retries):
            try:
                response = requests.request(method, url, json=data, params=params, headers=self.headers)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in {524, 504}:  # Timeout errors
                    continue  # Retry if needed
                else:
                    error_message = get_error_message(response)
                    styled_messages.error(f"API Error ({response.status_code}): {error_message}")
                    sys.exit(1)
            except requests.RequestException as e:
                styled_messages.error(f"Request failed: {e}")
                sys.exit(1)
        
        styled_messages.error("Max retries reached. Request failed.")
        sys.exit(1)

    def get_translations(self, data, source_lang, target_lang, route_file=None):
        """Fetch translations from the API."""
        params = {
            'source_lang': source_lang,
            'target_lang': target_lang,
            'type_project': 'django'
        }
        if route_file:
            params['route_file'] = route_file
        
        response = self.make_request('POST', '/v1/translations/', params=params, data=data)
        return response.get('data', None)

    def fetch_translations(self, params=None):
        """Retrieve existing translations from the API."""
        params = params or {}
        response = self.make_request('GET', '/v1/translations/list', params=params)
        return response
