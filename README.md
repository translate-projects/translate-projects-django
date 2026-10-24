# Translate Projects Django

Translate your Django project's `.po` files with one command. `python manage.py translate` extracts the texts of your project, sends them to [Translate Projects](https://translateprojects.dev), translates them into every language in `settings.LANGUAGES`, writes the `.po` files and compiles them.

[See documentation](https://doc.translateprojects.dev/docs/python/django)

## Requirements

- Python >= 3.8
- Django >= 3.2
- GNU gettext (`xgettext`, `msgfmt`), the same tools Django's `makemessages` and `compilemessages` need:
  - Debian/Ubuntu: `sudo apt-get install gettext`
  - macOS: `brew install gettext`
  - Windows: [gettext for Windows](https://mlocati.github.io/articles/gettext-iconv-windows.html)
  - Docker: `RUN apt-get update && apt-get install -y gettext`
- A Translate Projects project with:
  - its API token;
  - its base language equal to your `LANGUAGE_CODE`;
  - an AI model and AI API key configured in the project settings (needed to translate texts that are not in the shared translation network yet).

## Installation

```bash
pip install translate-projects-django
```

## Configuration

### 1. API key

Set the project's API token as an environment variable:

```bash
export TRANSLATE_PROJECTS_API_KEY="your-project-token"
```

Never commit the token to your repository.

### 2. `settings.py`

```python
import os

INSTALLED_APPS = [
    # ...
    "translate_projects_django",
]

LANGUAGE_CODE = "es"  # language your texts are written in

LANGUAGES = [
    ("es", "Español"),
    ("en", "English"),
    ("pt-br", "Português (Brasil)"),
    ("fr", "Français"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]  # the first path is used

TRANSLATE_PROJECTS_API_KEY = os.environ.get("TRANSLATE_PROJECTS_API_KEY")

# Optional: folders makemessages must skip (glob patterns)
TRANSLATE_PROJECTS_EXCLUDE_DIRS = ["venv/*", "env/*", "node_modules/*"]
```

| Setting | Required | Description |
|---|---|---|
| `TRANSLATE_PROJECTS_API_KEY` | Yes | Project token, sent as `Authorization: Token <key>`. |
| `LANGUAGE_CODE` | Yes | Source language. Must match the project's base language. It is never translated. |
| `LANGUAGES` | Yes | Languages to translate into. Use Django codes (`pt-br`, `zh-hans`); they are mapped to the API codes (`pt-BR`, `zh-Hans`) automatically. |
| `LOCALE_PATHS` | Yes | The first path is where the `.po` and `.mo` files are written. |
| `TRANSLATE_PROJECTS_EXCLUDE_DIRS` | No | Passed to `makemessages --ignore`. |

Mark your texts as usual with `{% translate %}`, `{% blocktranslate %}`, `gettext` or `gettext_lazy`.

## Usage

Translate every language in `LANGUAGES` except `LANGUAGE_CODE`:

```bash
python manage.py translate
```

Translate one language (it must be in `LANGUAGES` and differ from `LANGUAGE_CODE`):

```bash
python manage.py translate --locale en
```

Translate again even if nothing changed (for example to download translations you edited in the dashboard):

```bash
python manage.py translate --force
python manage.py translate --locale fr --force
```

What the command does:

1. Runs `makemessages` for `LANGUAGE_CODE`.
2. Uploads the texts to the API, only if they changed since the last upload.
3. Translates up to 3 languages in parallel, showing a progress bar for each one.
4. Writes one `.po` file per language.
5. Runs `compilemessages`.

At the end it prints how long each step took and how many HTTP requests it made.

## Generated files

With `LOCALE_PATHS = [BASE_DIR / "locale"]` and the languages above:

```
locale/
├── .translate-projects.json        # cache: which languages are up to date
├── es/LC_MESSAGES/django.po        # source texts (makemessages)
├── es/LC_MESSAGES/django.mo
├── en/LC_MESSAGES/django.po        # translations
├── en/LC_MESSAGES/django.mo
├── pt_BR/LC_MESSAGES/django.po     # "pt-br" uses the pt_BR folder, as Django expects
├── pt_BR/LC_MESSAGES/django.mo
├── fr/LC_MESSAGES/django.po
└── fr/LC_MESSAGES/django.mo
```

- Each translated `.po` is rebuilt from the source `.po` every time that language is translated, so manual edits to it are overwritten. Edit translations in the Translate Projects dashboard and run with `--force` instead.
- Commit the `.po` files and `.translate-projects.json`, so other machines and CI skip languages that are already up to date. The `.mo` files can be committed or built in deploy with `compilemessages`.

## Cache

A second run with no new or changed texts:

- does not upload anything (one HTTP request checks that the API already has this version of the texts);
- does not translate any language whose `.po` is complete;
- still runs `makemessages` and `compilemessages`.

A language is marked as up to date in `locale/.translate-projects.json` only when every text came back translated. If texts are added or changed, the texts are uploaded again and every language is translated again; the API reuses translations it already has.

To skip the cache, use `--force`. With `--locale`, only that language is translated again and the cache of the other languages is kept.

## Common errors

| Message | Cause | Fix |
|---|---|---|
| `TRANSLATE_PROJECTS_API_KEY is not set in settings.py` | The setting is empty. | Export the variable and read it in `settings.py` (see Configuration). |
| `API Error (400): INVALID_INPUT Token no válido` and then `Sources upload failed.` | The token is wrong or inactive, or the project has no languages yet. | Copy the token again from the project in the dashboard and check the project has its base language. No file is changed. |
| `API Error (400): ... El idioma de origen no es el predeterminado` | `LANGUAGE_CODE` differs from the project's base language. | Use the same language in both places. |
| `<lang>: N texts without translation. Check that the project has an AI model and API key configured.` | Partial translation: the project has no AI key (`MISSING_API_KEY`), so only texts already in the shared network were translated. | Set the AI model and key in the project and run the command again. The `.po` keeps what was translated, and that language is retried on the next run because it is not marked as up to date. |
| `<lang>: placeholders changed, kept source: '...'` | The translation altered `%(name)s`, `%s`, `{name}` or `%%`, which would break `compilemessages`. | Nothing to do; that text stays in the source language. Fix it in the dashboard and run with `--force`. |
| `The language 'xx' is not valid.` | `--locale` is not in `LANGUAGES`. | Add it to `LANGUAGES`. |
| `Can't find xgettext` / `Can't find msgfmt` | GNU gettext is not installed. | Install it (see Requirements). |
| `No progress for 120s on task ..., continuing.` | The progress connection received no updates. | The command continues and downloads what is ready; anything missing is retried on the next run. |

Network errors, timeouts, `429` and `5xx` responses are retried 3 times. If a language still fails, its existing `.po` is kept and the other languages continue.

## Limitations

- Plural texts (`ngettext`, `{% blocktranslate count %}`) are not translated yet; they keep their source text.

## Development

```bash
pip install -e . pytest
python -m pytest tests
```

The tests mock the API and never call the network.

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
