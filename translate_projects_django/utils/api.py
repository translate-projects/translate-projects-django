import requests
from django.conf import settings
from rich.console import Console

API_BASE_URL = "https://api.translateprojects.dev"

console = Console(log_time=True, log_path=False)


class Api:
    def __init__(self, base_url=API_BASE_URL, token=None):
        self.base_url = base_url.rstrip("/")
        self.token = token or getattr(settings, "TRANSLATE_PROJECTS_API_KEY", None)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.token:
            self.headers["Authorization"] = f"Token {self.token}"

    def make_request(self, method, endpoint, params=None, data=None, retries=3):
        """
        Makes requests to the API with retries.
        In case of an error, it logs the issue and returns None to prevent execution from being interrupted.
        """
        url = f"{self.base_url}{endpoint}"
        for attempt in range(1, retries + 1):
            try:
                response = requests.request(
                    method, url, json=data, params=params, headers=self.headers
                )
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in {524, 504}:  # Timeout errors
                    console.log(
                        f"🛑 [yellow]Warning:[/] Timeout detected (attempt {attempt}/{retries}). Retrying..."
                    )
                    continue
                else:
                    error_message = get_error_message(response)
                    console.log(
                        f"🛑 [red]Error:[/] API Error ({response.status_code}): {error_message}"
                    )
                    # Instead of raising an exception, return None to avoid breaking the application flow.
                    return None
            except requests.RequestException as e:
                console.log(
                    f"🛑 [red]Error:[/] Request failed: {e} (attempt {attempt}/{retries})"
                )
        console.log("🛑 [red]Error:[/] Max retries reached. Request failed.")
        return None

    def make_translations(self, source_lang, target_lang, route_file=None):
        """
        Retrieves translations from the API.
        If an error occurs, returns None.
        """
        params = {"target_lang": target_lang, "source_lang": source_lang}
        if route_file:
            params["route_file"] = route_file
        response = self.make_request("POST", "/v1/translations/", params=params)
        if response is None:
            return None
        return response.get("data", None)

    def get_translations(self, target_lang):
        """
        Retrieves translations from the API for a language project.
        """
        params = {"target_lang": target_lang}
        response = self.make_request(
            "GET", "/v1/translations/language-project", params=params
        )
        if response is None:
            return None
        return response.get("data", None)

    def fetch_translations(self, params=None):
        """
        Fetches existing translations from the API.
        """
        params = params or {}
        response = self.make_request("GET", "/v1/translations/list", params=params)
        if response is None:
            return None
        return response.get("data", None)

    def sync_sources(self, data, source_lang, route_file=None):
        """
        Synchronizes translation sources with the API.
        """
        params = {
            "source_lang": source_lang,
            "route_file": route_file,
            "type_project": "django",
        }
        response = self.make_request(
            "POST", "/v1/translations/load-sources", params=params, data=data
        )
        if response is None:
            return None
        return response.get("data", None)


def get_error_message(response):
    try:
        data = response.json()
        return data.get("message", "Unknown error")
    except Exception:
        console.log("🛑 [red]Error:[/] Failed to decode JSON", response)
        return "Failed to decode JSON"
