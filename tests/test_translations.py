import asyncio
import json
import os
import tempfile
import unittest
from unittest import mock

import django
from django.conf import settings

TMP = tempfile.mkdtemp()
settings.configure(
    INSTALLED_APPS=["translate_projects_django"],
    LANGUAGE_CODE="es",
    LANGUAGES=[("es", "Español"), ("en", "English"), ("pt-br", "Português")],
    LOCALE_PATHS=[os.path.join(TMP, "locale")],
    TRANSLATE_PROJECTS_API_KEY="test-key",
)
django.setup()

import polib  # noqa: E402
from django.utils.translation import to_language  # noqa: E402

from translate_projects_django.cases import make_translations as mt  # noqa: E402
from translate_projects_django.utils import api as api_module  # noqa: E402
from translate_projects_django.utils import channels  # noqa: E402
from translate_projects_django.utils import translations as tr  # noqa: E402
from translate_projects_django.utils.hashing import generate_short_hash  # noqa: E402

MSGIDS = ["Hola", "Hola %(name)s", "<b>Guardar</b>", ":"]
TRANSLATED = {
    "en": {"Hola": "Hello", "Hola %(name)s": "Hello %(name)s", "<b>Guardar</b>": "<b>Save</b>"},
    "pt-BR": {"Hola": "Olá", "Hola %(name)s": "Olá %(nome)s", "<b>Guardar</b>": "<b>Salvar</b>"},
}


def fake_makemessages(*args, locale, **kwargs):
    po = polib.POFile()
    po.metadata = {"Content-Type": "text/plain; charset=UTF-8"}
    for msgid in MSGIDS:
        po.append(polib.POEntry(msgid=msgid, msgstr=""))
    path = os.path.join(TMP, "locale", locale[0], "LC_MESSAGES", "django.po")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    po.save(path)


class FakeApi:
    def __init__(self, changed=None):
        self.calls = []
        self.requests_made = 0
        self.changed = changed

    def validate_changes(self, data):
        self.calls.append(("validate", data))
        return data if self.changed is None else self.changed

    def sync_sources(self, data, source_lang, route_file, cache_hash):
        self.calls.append(("sync", source_lang, sorted(data.values())))
        return {"task_id": "t-sync"}

    def make_translations(self, source_lang, target_lang, route_file):
        self.calls.append(("translate", target_lang))
        return {"task_id": f"t-{target_lang}"}

    def get_translations(self, target_lang):
        return {generate_short_hash(k): v for k, v in TRANSLATED[target_lang].items()}


def compile_noop(*args, **kwargs):
    pass


class HashTests(unittest.TestCase):
    def test_matches_backend_known_value(self):
        # Value produced by the backend's helpers/hash_utils.generate_short_hash
        self.assertEqual(generate_short_hash("Hola %(name)s"), "51br2yg5zoskw6o")


class LangTests(unittest.TestCase):
    def test_both_directions(self):
        cases = {"pt-br": "pt-BR", "zh-hans": "zh-Hans", "en": "en", "pt-pt": "pt-PT"}
        for django_code, api_code in cases.items():
            self.assertEqual(tr.to_api_lang(django_code), api_code)
            self.assertEqual(to_language(api_code), django_code)

    def test_folder_is_pt_BR(self):
        self.assertIn(os.path.join("pt_BR", "LC_MESSAGES"), tr.po_path("/x", "pt-br"))


class PlaceholderTests(unittest.TestCase):
    def test_placeholders(self):
        self.assertTrue(tr.placeholders_ok("Hola %(name)s", "Hello %(name)s"))
        self.assertFalse(tr.placeholders_ok("Hola %(name)s", "Olá %(nome)s"))
        self.assertFalse(tr.placeholders_ok("%s de %d", "%s"))
        self.assertTrue(tr.placeholders_ok("{count} items", "{count} elementos"))


@mock.patch.object(tr, "wait_task", lambda *a, **k: True)
@mock.patch.object(mt, "call_command", compile_noop)
@mock.patch.object(tr, "call_command", fake_makemessages)
class FlowTests(unittest.TestCase):
    def setUp(self):
        cache = os.path.join(TMP, "locale", tr.CACHE_FILE)
        if os.path.exists(cache):
            os.remove(cache)

    def run_command(self, fake, **kwargs):
        with mock.patch.object(mt, "Api", return_value=fake):
            mt.make_translations(None, kwargs.pop("locale", None), **kwargs)

    def test_full_run_writes_po_files(self):
        fake = FakeApi()
        self.run_command(fake)

        self.assertIn(("sync", "es", ["<b>Guardar</b>", "Hola", "Hola %(name)s"]), fake.calls)
        self.assertEqual({c[1] for c in fake.calls if c[0] == "translate"}, {"en", "pt-BR"})

        en = polib.pofile(tr.po_path(settings.LOCALE_PATHS[0], "en"))
        self.assertEqual(en.find("Hola %(name)s").msgstr, "Hello %(name)s")
        self.assertEqual(en.find("<b>Guardar</b>").msgstr, "<b>Save</b>")
        self.assertEqual(en.metadata["Language"], "en")

        pt_path = os.path.join(TMP, "locale", "pt_BR", "LC_MESSAGES", "django.po")
        pt = polib.pofile(pt_path)
        self.assertEqual(pt.find("Hola").msgstr, "Olá")
        self.assertEqual(pt.find("Hola %(name)s").msgstr, "")  # broken placeholder rejected
        self.assertEqual(pt.metadata["Language"], "pt_BR")

    def test_second_run_skips_upload_and_translation(self):
        self.run_command(FakeApi())
        fake = FakeApi(changed={})
        self.run_command(fake)
        self.assertEqual([c[0] for c in fake.calls], ["validate"])

    def test_force_translates_again(self):
        self.run_command(FakeApi())
        fake = FakeApi(changed={})
        self.run_command(fake, force=True)
        self.assertEqual(len([c for c in fake.calls if c[0] == "translate"]), 2)

    def test_invalid_locale_does_nothing(self):
        fake = FakeApi()
        self.run_command(fake, locale="ko")
        self.assertEqual(fake.calls, [])


def response(status, body):
    r = mock.Mock(status_code=status)
    r.json.return_value = body
    return r


@mock.patch.object(api_module.time, "sleep", lambda s: None)
class ApiTests(unittest.TestCase):
    def test_retries_5xx_then_succeeds(self):
        client = api_module.Api(token="k")
        with mock.patch.object(
            client.session,
            "request",
            side_effect=[response(502, {}), response(200, {"data": {"task_id": "1"}})],
        ) as request:
            self.assertEqual(client.make_translations("es", "en"), {"task_id": "1"})
        self.assertEqual(request.call_count, 2)
        self.assertEqual(request.call_args.kwargs["timeout"], api_module.TIMEOUT)

    def test_retries_connection_errors_and_gives_up(self):
        client = api_module.Api(token="k")
        error = api_module.requests.ConnectionError("down")
        with mock.patch.object(client.session, "request", side_effect=error) as request:
            self.assertIsNone(client.get_translations("en"))
        self.assertEqual(request.call_count, 3)

    def test_400_is_not_retried(self):
        client = api_module.Api(token="k")
        body = {"status": "FAILURE", "code": "INVALID_INPUT", "message": "Token no válido"}
        with mock.patch.object(
            client.session, "request", return_value=response(400, body)
        ) as request:
            self.assertIsNone(client.get_translations("en"))
        self.assertEqual(request.call_count, 1)

    def test_partial_missing_api_key_returns_data(self):
        client = api_module.Api(token="k")
        body = {"status": "PARTIAL", "error": "MISSING_API_KEY", "message": "x", "data": {"a": "b"}}
        with mock.patch.object(client.session, "request", return_value=response(200, body)):
            self.assertEqual(client.get_translations("en"), {"a": "b"})


class FakeSocket:
    def __init__(self, messages, hang=False):
        self.messages, self.hang = list(messages), hang

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def recv(self):
        if not self.messages:
            await asyncio.sleep(10)
        return self.messages.pop(0)


class WebSocketTests(unittest.TestCase):
    def test_finishes_at_100(self):
        seen = []
        msgs = [json.dumps({"progress": 40}), "not json", json.dumps({"progress": 100})]
        with mock.patch.object(channels.websockets, "connect", return_value=FakeSocket(msgs)):
            self.assertTrue(channels.wait_task("t", seen.append, idle_timeout=1))
        self.assertEqual(seen, [40.0, 100.0])

    def test_times_out_when_silent(self):
        with mock.patch.object(channels.websockets, "connect", return_value=FakeSocket([])):
            self.assertFalse(channels.wait_task("t", idle_timeout=0.05))

    def test_connection_error_does_not_raise(self):
        with mock.patch.object(channels.websockets, "connect", side_effect=OSError("refused")):
            self.assertFalse(channels.wait_task("t"))


if __name__ == "__main__":
    unittest.main()
