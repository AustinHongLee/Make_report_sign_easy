"""Simple update checker."""
import json
from urllib.request import urlopen
from . import __version__

VERSION_URL = "https://raw.githubusercontent.com/AustinHongLee/Make_report_sign_easy/main/version.json"

def get_latest_version():
    try:
        with urlopen(VERSION_URL, timeout=3) as resp:
            data = json.load(resp)
        return data.get("version")
    except Exception as e:
        print("update check failed:", e)
        return None

def check_for_update():
    latest = get_latest_version()
    if not latest:
        return False
    try:
        from packaging import version
        if version.parse(latest) > version.parse(__version__):
            print(f"New version available: {latest} (current {__version__}).")
            print("Run `pip install -U make-report-sign-easy` to update.")
            return True
    except Exception as e:
        print("Version comparison failed:", e)
    return False
