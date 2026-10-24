import time

import requests
from django.conf import settings
from rich.console import Console

API_BASE_URL = "https://api.translateprojects.dev"
TIMEOUT = (10, 60)  # (connect, read) seconds
RETRY_STATUS = {429, 500, 502, 503, 504, 524}

console = Console(log_time=True, log_path=False)


class Api:
    def __init__(self, base_url=API_BASE_URL, token=None):
        self.base_url = base_url.rstrip("/")
        self.token = token or getattr(settings, "TRANSLATE_PROJECTS_API_KEY", None)
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )
        if self.token:
            self.session.headers["Authorization"] = f"Token {self.token}"
        self.requests_made = 0

    def make_request(self, method, endpoint, params=None, data=None, retries=3):
        """
        Calls the API retrying timeouts, 429 and 5xx with backoff.
        Logs and returns None on failure so a command run never crashes on the API.
        """
        url = f"{self.base_url}{endpoint}"
        for attempt in range(1, retries + 1):
            if attempt > 1:
                time.sleep(2 ** (attempt - 2))
            self.requests_made += 1
            try:
                response = self.session.request(
                    method, url, json=data, params=params, timeout=TIMEOUT
                )
            except requests.RequestException as e:
                console.log(
                    f"🛑 [yellow]Warning:[/] Request failed: {e} (attempt {attempt}/{retries})"
                )
                continue
            if response.status_code == 200:
                body = response.json()
                if body.get("status") == "PARTIAL":
                    console.log(
                        f"⚠ [yellow]{body.get('error') or body.get('code')}:[/] {body.get('message')}"
                    )
                return body
            if response.status_code in RETRY_STATUS:
                console.log(
                    f"🛑 [yellow]Warning:[/] API {response.status_code} (attempt {attempt}/{retries}). Retrying..."
                )
                continue
            console.log(
                f"🛑 [red]Error:[/] API Error ({response.status_code}): {get_error_message(response)}"
            )
            return None
        console.log("🛑 [red]Error:[/] Max retries reached. Request failed.")
        return None

    def _data(self, *args, **kwargs):
        response = self.make_request(*args, **kwargs)
        return None if response is None else response.get("data")

    def make_translations(self, source_lang, target_lang, route_file=None):
        params = {"target_lang": target_lang, "source_lang": source_lang}
        if route_file:
            params["route_file"] = route_file
        return self._data("POST", "/v1/translations/", params=params)

    def get_translations(self, target_lang):
        return self._data(
            "GET",
            "/v1/translations/language-project",
            params={"target_lang": target_lang},
        )

    def validate_changes(self, file_hashes):
        """Returns the {file_hash: version_hash} entries the backend does not have yet."""
        return self._data(
            "POST", "/v1/translations/validate-changes-files", data=file_hashes
        )

    def sync_sources(self, data, source_lang, route_file=None, cache_hash=None):
        params = {
            "source_lang": source_lang,
            "route_file": route_file,
            "type_project": "django",
        }
        if cache_hash:
            params["cache_hash"] = cache_hash
        return self._data(
            "POST", "/v1/translations/load-sources", params=params, data=data
        )


def get_error_message(response):
    try:
        data = response.json()
        return f"{data.get('code', '')} {data.get('message', 'Unknown error')}".strip()
    except ValueError:
        return response.text[:200] or "Failed to decode JSON"
