"""Standalone golden test for client_inputs.build_inputs (stdlib only).

Run: python3 .github/scripts/test_client_inputs.py
Guards the OFIBER server/client `custom` settings blobs against accidental
change. The equivalence to rdgenerator/views.py is separately checked by
rdgenerator/tests.py (ClientInputsEquivalenceTest)."""
import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from client_inputs import build_inputs  # noqa: E402

CONFIGS = os.path.join(HERE, "..", "release-configs")

EXPECTED_SERVER = {
    "conn-type": "both",
    "app-name": "OFiber Remote Support Server",
    "override-settings": {
        "access-mode": "full", "enable-keyboard": "Y", "enable-clipboard": "Y",
        "enable-file-transfer": "Y", "enable-audio": "Y", "enable-tunnel": "Y",
        "enable-remote-restart": "Y", "enable-record-session": "Y",
        "enable-block-input": "Y", "allow-remote-config-modification": "Y",
        "direct-server": "Y", "verification-method": "use-permanent-password",
        "approve-mode": "password", "allow-hide-cm": "Y",
        "allow-remove-wallpaper": "Y", "enable-remote-printer": "Y",
        "enable-camera": "Y", "enable-terminal": "Y",
    },
    "default-settings": {},
    "password": "@Dmin12345",
    "enable-lan-discovery": "Y",
    "allow-auto-disconnect": "N",
}

EXPECTED_CLIENT = json.loads(json.dumps(EXPECTED_SERVER))
EXPECTED_CLIENT["conn-type"] = "incoming"
EXPECTED_CLIENT["app-name"] = "OFiber Remote Support Client"
EXPECTED_CLIENT["disable-settings"] = "Y"
EXPECTED_CLIENT["override-settings"].update({
    "custom-rendezvous-server": "http://speedtest-qcy.fiber.ph",
    "api-server": "http://speedtest-qcy.fiber.ph:21114",
    "privacy-mode": "Y",
    "enable-privacy-mode": "Y",
})


def _custom(name):
    cfg = json.load(open(os.path.join(CONFIGS, name, "config.json")))
    r = build_inputs(cfg, myuuid="test", has_icon=True, has_logo=True, has_privacy=True)
    return json.loads(base64.b64decode(r["inputs"]["custom"])), r["inputs"]


def main():
    failures = []
    sc, si = _custom("OFIBER")
    if sc != EXPECTED_SERVER:
        failures.append(("OFIBER custom", sc))
    if si["filename"] != "OFIBER" or si["appname"] != "OFiber Remote Support Server":
        failures.append(("OFIBER filename/appname", (si["filename"], si["appname"])))
    if si["server"] != "http://speedtest-qcy.fiber.ph" or si["serverPort"] != "21116":
        failures.append(("OFIBER server/port", (si["server"], si["serverPort"])))

    cc, ci = _custom("OFIBER_client")
    if cc != EXPECTED_CLIENT:
        failures.append(("OFIBER_client custom", cc))
    if ci["filename"] != "OFIBER_client":
        failures.append(("OFIBER_client filename", ci["filename"]))

    if failures:
        for label, got in failures:
            print(f"FAIL: {label}\n  got: {json.dumps(got)}")
        sys.exit(1)
    print("client_inputs golden test: PASS (OFIBER + OFIBER_client)")


if __name__ == "__main__":
    main()
