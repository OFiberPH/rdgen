"""
Pure, Django-free reproduction of the RustDesk client build-input logic in
rdgenerator/views.py:generate_custom_client().

This is the single source of truth for the offline **release** pipeline
(.github/workflows/release-ofiber.yml). It builds the exact same `custom`
settings blob and workflow inputs that the live RDGen web service would send
to the generator-* workflows, so release binaries are identical to
service-generated ones.

If views.py changes, tests/test_client_inputs.py fails, flagging the drift.
Only standard library is used so it can run on a bare CI runner.
"""
import base64
import json
import re
import uuid as _uuid


def _truthy(v):
    """Match views.py checkbox semantics: web-form 'on' / JSON true are truthy,
    False / '' / absent are falsy (views.py uses plain Python truthiness)."""
    return bool(v)


def build_inputs(params, *, myuuid=None, genurl="", has_icon=False,
                 has_logo=False, has_privacy=False):
    """Reproduce views.generate_custom_client up to `inputs_raw`.

    params: dict of raw config fields (same keys as GenerateForm / saved config).
    Returns dict: {"inputs": <inputs_raw>, "custom_decoded": <dict>, "uuid": ...}.
    """
    platform = params.get('platform', 'windows')
    version = params.get('version', '1.4.9')
    delayFix = params.get('delayFix', True)
    xOffline = params.get('xOffline', False)
    hidecm = params.get('hidecm', False)
    removeNewVersionNotif = params.get('removeNewVersionNotif', False)
    server = params.get('serverIP', '')
    serverPort = params.get('serverPort', '')
    key = params.get('key', '')
    apiServer = params.get('apiServer', '')
    urlLink = params.get('urlLink', '')
    downloadLink = params.get('downloadLink', '')
    if not server:
        server = 'rs-ny.rustdesk.com'
    if not serverPort:
        serverPort = '21116'
    if not key:
        key = 'OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw='
    if not apiServer:
        apiServer = server + ":21114"
    if not urlLink:
        urlLink = "https://rustdesk.com"
    if not downloadLink:
        downloadLink = "https://rustdesk.com/download"
    direction = params.get('direction', 'both')
    installation = params.get('installation', 'installationY')
    settings = params.get('settings', 'settingsY')
    appname = params.get('appname', '')
    if not appname:
        appname = "rustdesk"
    filename = params.get('exename', 'rustdesk')
    compname = params.get('compname', '')
    if not compname:
        compname = "Purslane Ltd"
    androidappid = params.get('androidappid', '')
    if not androidappid:
        androidappid = "com.carriez.flutter_hbb"
    compname = compname.replace("&", "\\&")
    permPass = params.get('permanentPassword', '')
    theme = params.get('theme', 'system')
    themeDorO = params.get('themeDorO', 'default')
    passApproveMode = params.get('passApproveMode', 'password-click')
    denyLan = params.get('denyLan', False)
    enableDirectIP = params.get('enableDirectIP', False)
    autoClose = params.get('autoClose', False)
    permissionsDorO = params.get('permissionsDorO', 'default')
    permissionsType = params.get('permissionsType', 'custom')
    enableKeyboard = params.get('enableKeyboard', True)
    enableClipboard = params.get('enableClipboard', True)
    enableFileTransfer = params.get('enableFileTransfer', True)
    enableAudio = params.get('enableAudio', True)
    enableTCP = params.get('enableTCP', True)
    enableRemoteRestart = params.get('enableRemoteRestart', True)
    enableRecording = params.get('enableRecording', True)
    enableBlockingInput = params.get('enableBlockingInput', True)
    enableRemoteModi = params.get('enableRemoteModi', False)
    removeWallpaper = params.get('removeWallpaper', True)
    defaultManual = params.get('defaultManual', '')
    overrideManual = params.get('overrideManual', '')
    enablePrinter = params.get('enablePrinter', True)
    enableCamera = params.get('enableCamera', True)
    enableTerminal = params.get('enableTerminal', True)

    if all(char.isascii() for char in filename):
        filename = re.sub(r'[^\w\s-]', '_', filename).strip()
        filename = filename.replace(" ", "_")
    else:
        filename = "rustdesk"
    if not all(char.isascii() for char in appname):
        appname = "rustdesk"

    if myuuid is None:
        myuuid = str(_uuid.uuid4())

    decodedCustom = {}
    if direction != "Both":
        decodedCustom['conn-type'] = direction
    if installation == "installationN":
        decodedCustom['disable-installation'] = 'Y'
    if settings == "settingsN":
        decodedCustom['disable-settings'] = 'Y'
    if appname.upper != "rustdesk".upper and appname != "":
        decodedCustom['app-name'] = appname
    decodedCustom['override-settings'] = {}
    decodedCustom['default-settings'] = {}
    if permPass != "":
        decodedCustom['password'] = permPass
    if theme != "system":
        if themeDorO == "default":
            if platform == "windows-x86":
                decodedCustom['default-settings']['allow-darktheme'] = 'Y' if theme == "dark" else 'N'
            else:
                decodedCustom['default-settings']['theme'] = theme
        elif themeDorO == "override":
            if platform == "windows-x86":
                decodedCustom['override-settings']['allow-darktheme'] = 'Y' if theme == "dark" else 'N'
            else:
                decodedCustom['override-settings']['theme'] = theme
    decodedCustom['enable-lan-discovery'] = 'N' if denyLan else 'Y'
    decodedCustom['allow-auto-disconnect'] = 'Y' if autoClose else 'N'

    target = 'default-settings' if permissionsDorO == "default" else 'override-settings'
    decodedCustom[target]['access-mode'] = permissionsType
    decodedCustom[target]['enable-keyboard'] = 'Y' if enableKeyboard else 'N'
    decodedCustom[target]['enable-clipboard'] = 'Y' if enableClipboard else 'N'
    decodedCustom[target]['enable-file-transfer'] = 'Y' if enableFileTransfer else 'N'
    decodedCustom[target]['enable-audio'] = 'Y' if enableAudio else 'N'
    decodedCustom[target]['enable-tunnel'] = 'Y' if enableTCP else 'N'
    decodedCustom[target]['enable-remote-restart'] = 'Y' if enableRemoteRestart else 'N'
    decodedCustom[target]['enable-record-session'] = 'Y' if enableRecording else 'N'
    decodedCustom[target]['enable-block-input'] = 'Y' if enableBlockingInput else 'N'
    decodedCustom[target]['allow-remote-config-modification'] = 'Y' if enableRemoteModi else 'N'
    decodedCustom[target]['direct-server'] = 'Y' if enableDirectIP else 'N'
    decodedCustom[target]['verification-method'] = 'use-permanent-password' if hidecm else 'use-both-passwords'
    decodedCustom[target]['approve-mode'] = passApproveMode
    decodedCustom[target]['allow-hide-cm'] = 'Y' if hidecm else 'N'
    decodedCustom[target]['allow-remove-wallpaper'] = 'Y' if removeWallpaper else 'N'
    decodedCustom[target]['enable-remote-printer'] = 'Y' if enablePrinter else 'N'
    decodedCustom[target]['enable-camera'] = 'Y' if enableCamera else 'N'
    decodedCustom[target]['enable-terminal'] = 'Y' if enableTerminal else 'N'
    if permissionsDorO != "default" and direction == 'incoming':
        decodedCustom['override-settings']['custom-rendezvous-server'] = server
        decodedCustom['override-settings']['api-server'] = apiServer

    if defaultManual:
        for line in defaultManual.splitlines():
            if '=' in line:
                k, value = line.split('=', 1)
                decodedCustom['default-settings'][k.strip()] = value.strip()
    if overrideManual:
        for line in overrideManual.splitlines():
            if '=' in line:
                k, value = line.split('=', 1)
                decodedCustom['override-settings'][k.strip()] = value.strip()

    decodedCustomJson = json.dumps(decodedCustom)
    encodedCustom = base64.b64encode(decodedCustomJson.encode("ascii")).decode("ascii")

    # In release mode the generators read committed PNGs (see release-ofiber.yml)
    # rather than downloading; 'local' means "provided", 'false' means "absent".
    iconlink = ("local", myuuid, "icon.png") if has_icon else ("false", "false", "false")
    logolink = ("local", myuuid, "logo.png") if has_logo else ("false", "false", "false")
    privacylink = ("local", myuuid, "privacy.png") if has_privacy else ("false", "false", "false")

    inputs_raw = {
        "server": server,
        "serverPort": serverPort,
        "key": key,
        "apiServer": apiServer,
        "custom": encodedCustom,
        "uuid": myuuid,
        "iconlink_url": iconlink[0], "iconlink_uuid": iconlink[1], "iconlink_file": iconlink[2],
        "logolink_url": logolink[0], "logolink_uuid": logolink[1], "logolink_file": logolink[2],
        "privacylink_url": privacylink[0], "privacylink_uuid": privacylink[1], "privacylink_file": privacylink[2],
        "appname": appname,
        "genurl": genurl,
        "urlLink": urlLink,
        "downloadLink": downloadLink,
        "delayFix": 'true' if _truthy(delayFix) else 'false',
        "rdgen": 'true',
        "xOffline": 'true' if _truthy(xOffline) else 'false',
        "removeNewVersionNotif": 'true' if _truthy(removeNewVersionNotif) else 'false',
        "compname": compname,
        "androidappid": androidappid,
        "filename": filename,
    }
    return {"inputs": inputs_raw, "custom_decoded": decodedCustom, "uuid": myuuid,
            "version": version, "platform": platform}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True, help="path to write secrets.json")
    ap.add_argument("--uuid", default=None)
    ap.add_argument("--has-icon", action="store_true")
    ap.add_argument("--has-logo", action="store_true")
    ap.add_argument("--has-privacy", action="store_true")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    res = build_inputs(cfg, myuuid=a.uuid, has_icon=a.has_icon,
                       has_logo=a.has_logo, has_privacy=a.has_privacy)
    with open(a.out, "w") as f:
        json.dump(res["inputs"], f)
    print(json.dumps(res["inputs"], indent=2))
