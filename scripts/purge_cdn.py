"""Refresh jsDelivr for the published rule files; fail unless every purge completed."""
import json
import os
import sys
import time
import urllib.request

FILES = ('ai', 'payment', 'accounts')
API = 'https://purge.jsdelivr.net'


def completed(result):
    """Accept the current response ({status, paths}) and the legacy one ({success})."""
    if result.get('success') is True:
        return True
    if result.get('status') != 'finished':
        return False
    paths = result.get('paths') or {}
    return bool(paths) and all(
        not item.get('throttled') and item.get('providers') and all(item['providers'].values())
        for item in paths.values()
    )


def fetch(url):
    with urllib.request.urlopen(url, timeout=45) as response:
        return json.load(response)


def purge(repository, name, tries=3):
    url = f'{API}/gh/{repository}@main/rules/{name}.yaml'
    for _ in range(tries):
        try:
            result = fetch(url)
            for _ in range(10):
                if completed(result) or result.get('status') != 'pending' or not result.get('id'):
                    break
                time.sleep(3)
                result = fetch(f'{API}/status/{result["id"]}')
            if completed(result):
                print(f'{name}: purged')
                return True
            print(f'{name}: purge not completed: {json.dumps(result)[:300]}')
        except Exception as error:  # network errors are retried, then reported
            print(f'{name}: purge request failed: {error}')
        time.sleep(5)
    return False


def main():
    repository = os.environ['RULES_REPOSITORY']
    results = [purge(repository, name) for name in FILES]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())
