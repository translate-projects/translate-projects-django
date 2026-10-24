# Translate Projects Django

Automate the translation of your Django project's `.po` files with [Translate Projects](https://translateprojects.dev). One management command extracts your strings, syncs them with the Translate Projects API, translates them into every language in `settings.LANGUAGES`, writes the `.po` files and compiles them.

[See documentation](https://doc.translateprojects.dev/docs/python/django)

## How it works

`python manage.py translate`:

1. Runs `makemessages` for your default language (`LANGUAGE_CODE`) and reads the resulting `django.po`.
2. Asks the API whether it already has this exact set of texts; if not, uploads every `msgid` (keyed by a short SHA-256/Base36 hash) as the project's source strings.
3. Translates up to 3 languages in parallel: requests the translation, shows live progress (WebSocket, with a timeout) and downloads the results.
4. Writes `locale/<locale>/LC_MESSAGES/django.po` (`pt-br` → `pt_BR`). Translations that change a placeholder (`%(name)s`, `%s`, `{name}`) are dropped so `compilemessages` never breaks.
5. Runs `compilemessages`.

A second run with no new texts makes one HTTP request and skips every language that is already complete (tracked in `locale/.translate-projects.json`). Use `--force` to download again, e.g. after editing translations in the dashboard.

## Requirements

- Python >= 3.8
- Django >= 3.2
- A Translate Projects API key

## Installation

```bash
pip install translate-projects-django
```

## Configuration

In `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    "translate_projects_django",
]

LANGUAGE_CODE = "es"  # source language of your strings

LANGUAGES = [
    ("es", "Español"),
    ("en", "English"),
    ("fr", "Français"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]  # the first entry is used

TRANSLATE_PROJECTS_API_KEY = "your-api-key"

# Optional: glob patterns ignored by makemessages
TRANSLATE_PROJECTS_EXCLUDE_DIRS = ["venv/*", "node_modules/*"]
```

| Setting | Required | Description |
|---|---|---|
| `TRANSLATE_PROJECTS_API_KEY` | Yes | API token sent as `Authorization: Token <key>`. |
| `LANGUAGE_CODE` | Yes | Source language. Never translated. |
| `LANGUAGES` | Yes | Target languages. |
| `LOCALE_PATHS` | Yes | Where `.po` files are written (first path). |
| `TRANSLATE_PROJECTS_EXCLUDE_DIRS` | No | Passed to `makemessages --ignore`. |

## Usage

Translate into every language in `LANGUAGES` (except `LANGUAGE_CODE`):

```bash
python manage.py translate
```

Translate a single language:

```bash
python manage.py translate --locale en
```

The language must exist in `LANGUAGES` and differ from `LANGUAGE_CODE`.

Download every language again, even if it is up to date:

```bash
python manage.py translate --force
```

Requires GNU gettext (`xgettext`, `msgfmt`), like any Django translation workflow.

## Project structure

```
translate_projects_django/
├── management/commands/translate.py   # `translate` management command
├── cases/make_translations.py         # orchestrates the whole flow
└── utils/
    ├── api.py            # HTTP client for api.translateprojects.dev (timeouts, retries)
    ├── channels.py       # WebSocket progress with idle timeout
    ├── hashing.py        # short SHA-256 → Base36 hashes used as string keys
    └── translations.py   # makemessages, upload, translate and write .po per language
```

## Support

If you have any questions, need help, or want to contribute, feel free to reach out:

- **Website**: [neiderruiz.com](https://neiderruiz.com)
- **GitHub**: [@neiderruiz](https://github.com/neiderruiz)
- **Twitter**: [@neiderruiz](https://x.com/neiderruiz_)
- **YouTube**: [Neider Ruiz](https://youtube.com/@neiderruiz)

## Support the Project

If you find this project useful, consider buying me a coffee to help me keep improving it. Your support means a lot! ☕

[![Buy me a coffee](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&emoji=☕&slug=neiderruiz&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff)](https://www.buymeacoffee.com/neiderruiz)

## License

MIT
