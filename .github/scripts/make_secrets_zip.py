"""Build the encrypted secrets.zip + release PNG set for an offline release
build, mirroring rdgenerator/views.generate_custom_client's packaging.

Usage:
  python .github/scripts/make_secrets_zip.py \
      --config-name OFIBER --version 1.4.9 \
      --zip-password "$ZIP_PASSWORD" \
      --out-zip secrets.zip --png-dir release-pngs --github-output "$GITHUB_OUTPUT"
"""
import argparse
import json
import os
import shutil
import sys
import uuid as _uuid

import pyzipper

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from client_inputs import build_inputs  # noqa: E402

CONFIGS = os.path.join(HERE, "..", "release-configs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config-name", required=True)
    ap.add_argument("--version", default=None)
    ap.add_argument("--zip-password", required=True)
    ap.add_argument("--out-zip", default="secrets.zip")
    ap.add_argument("--png-dir", default="release-pngs")
    ap.add_argument("--github-output", default=None)
    a = ap.parse_args()

    if not a.zip_password:
        sys.exit("ERROR: empty zip password. Set the repo secret ZIP_PASSWORD "
                 "(the same one your live RDGen service uses).")

    cfg_dir = os.path.join(CONFIGS, a.config_name)
    with open(os.path.join(cfg_dir, "config.json")) as f:
        cfg = json.load(f)
    if a.version:
        cfg["version"] = a.version

    has_icon = os.path.exists(os.path.join(cfg_dir, "icon.png"))
    has_logo = os.path.exists(os.path.join(cfg_dir, "logo.png"))
    # privacy image customization is applied only by the windows top-most-window
    # helper; skipped here (privacylink=false) so no live host fetch is needed.
    res = build_inputs(cfg, myuuid=str(_uuid.uuid4()), has_icon=has_icon,
                       has_logo=has_logo, has_privacy=False)
    inputs_raw = res["inputs"]

    # Package exactly like views.py: AES-encrypted LZMA zip holding secrets.json
    with open("secrets.json", "w") as f:
        json.dump(inputs_raw, f)
    with pyzipper.AESZipFile(a.out_zip, "w", compression=pyzipper.ZIP_LZMA,
                             encryption=pyzipper.WZ_AES) as zf:
        zf.setpassword(a.zip_password.encode())
        zf.write("secrets.json", arcname="secrets.json")
    os.remove("secrets.json")

    # Stage PNGs the generators pick up in release_mode
    os.makedirs(a.png_dir, exist_ok=True)
    for png in ("icon.png", "logo.png"):
        src = os.path.join(cfg_dir, png)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(a.png_dir, png))

    print(f"config={a.config_name} filename={inputs_raw['filename']} "
          f"appname={inputs_raw['appname']} uuid={res['uuid']} "
          f"version={res['version']} icon={has_icon} logo={has_logo}")

    if a.github_output:
        with open(a.github_output, "a") as f:
            f.write(f"filename={inputs_raw['filename']}\n")
            f.write(f"appname={inputs_raw['appname']}\n")
            f.write(f"uuid={res['uuid']}\n")
            f.write(f"version={res['version']}\n")


if __name__ == "__main__":
    main()
