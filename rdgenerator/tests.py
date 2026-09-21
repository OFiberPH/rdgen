"""Drift guard: the offline release pipeline's .github/scripts/client_inputs.py
must produce the same client `custom` blob and build inputs as
views.generate_custom_client(). If views.py changes and diverges, this fails.

Run: python manage.py test rdgenerator
"""
import base64
import json
import os
import unittest
from unittest import mock

from django.test import SimpleTestCase

import rdgenerator.views as V

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO_ROOT, ".github", "scripts")
CONFIGS = os.path.join(REPO_ROOT, ".github", "release-configs")

# Fields the release pipeline intentionally sets differently (icon delivery is
# committed-file based, not URL based; genurl/uuid are runtime values).
RELEASE_SPECIFIC = {
    "iconlink_url", "iconlink_uuid", "iconlink_file",
    "logolink_url", "logolink_uuid", "logolink_file",
    "privacylink_url", "privacylink_uuid", "privacylink_file",
    "genurl", "uuid",
}


def _load_build_inputs():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "client_inputs", os.path.join(SCRIPTS, "client_inputs.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_inputs


def _capture_views_inputs(cfg):
    """Run views.generate_custom_client with all I/O mocked, capturing the
    inputs_raw dict it would dispatch to the generator workflow."""
    captured = {}
    real_dump = V.json.dump

    def cap_dump(obj, f, *a, **k):
        if isinstance(obj, dict) and "custom" in obj and "appname" in obj:
            captured["inputs"] = json.loads(json.dumps(obj))
        return real_dump(obj, f, *a, **k)

    class _Resp:
        status_code = 204

        def json(self):
            return {"workflow_run_id": 1, "html_url": "u"}

    class _Run:
        def __init__(self, **k):
            pass

        def save(self):
            pass

    class _Zip:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def setpassword(self, *a):
            pass

        def write(self, *a, **k):
            pass

    with mock.patch.object(V.json, "dump", cap_dump), \
            mock.patch.object(V.requests, "post", lambda *a, **k: _Resp()), \
            mock.patch.object(V, "GithubRun", _Run), \
            mock.patch.object(V, "save_png", lambda file, u, d, n: (d, u, n)), \
            mock.patch.object(V.pyzipper, "AESZipFile", lambda *a, **k: _Zip()):
        V.generate_custom_client(dict(cfg), "https://svc.example")
    return captured["inputs"]


class ClientInputsEquivalenceTest(SimpleTestCase):
    def _check(self, name):
        with open(os.path.join(CONFIGS, name, "config.json")) as f:
            cfg = json.load(f)
        build_inputs = _load_build_inputs()
        views_inputs = _capture_views_inputs(cfg)
        mine = build_inputs(cfg, myuuid=views_inputs["uuid"],
                            has_icon=True, has_logo=True, has_privacy=True)["inputs"]

        views_custom = json.loads(base64.b64decode(views_inputs["custom"]))
        my_custom = json.loads(base64.b64decode(mine["custom"]))
        self.assertEqual(views_custom, my_custom, f"{name}: custom blob diverged")

        for k in set(views_inputs) | set(mine):
            if k in RELEASE_SPECIFIC:
                continue
            self.assertEqual(views_inputs.get(k), mine.get(k),
                             f"{name}: field '{k}' diverged")

    def test_server_config(self):
        self._check("OFIBER")

    def test_client_config(self):
        self._check("OFIBER_client")


if __name__ == "__main__":
    unittest.main()
