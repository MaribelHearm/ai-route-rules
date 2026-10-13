#!/usr/bin/env python3
"""Convert the public global sing-box list without broadening domain matches."""
import argparse
import ipaddress
import json
import re
import subprocess
from pathlib import Path
from urllib.request import urlopen

import yaml

SOURCE = 'https://raw.githubusercontent.com/VPSDance/ai-proxy-rules/main/rules/sing-box/global.json'
ROOT = Path(__file__).resolve().parents[1]


def domain(value):
    if not isinstance(value, str) or len(value) > 253 or not re.fullmatch(
            r'[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+', value):
        raise ValueError('invalid domain')
    return value


def convert(data):
    if not isinstance(data, dict) or set(data) != {'version', 'rules'} or data['version'] not in (1, 2, 3):
        raise ValueError('unsupported source schema')
    if not isinstance(data['rules'], list) or not data['rules']:
        raise ValueError('missing rules')
    payload = set()
    for rule in data['rules']:
        if not isinstance(rule, dict) or not rule or set(rule) - {
                'domain', 'domain_suffix', 'domain_keyword', 'domain_regex', 'process_name', 'ip_cidr'}:
            raise ValueError('unsupported match type')
        for kind, values in rule.items():
            if not isinstance(values, list):
                raise ValueError('match values must be lists')
            for value in values:
                if not isinstance(value, str) or not value or any(ch in value for ch in '\n\r,'):
                    raise ValueError('invalid match value')
                if kind == 'process_name':
                    # This repository publishes destination lists, not process policy.
                    continue
                if kind == 'ip_cidr':
                    net = ipaddress.ip_network(value, strict=True)
                    payload.add(f"{'IP-CIDR' if net.version == 4 else 'IP-CIDR6'},{net},no-resolve")
                elif kind == 'domain':
                    payload.add('DOMAIN,' + domain(value))
                elif kind == 'domain_keyword':
                    payload.add('DOMAIN-KEYWORD,' + value)
                elif kind == 'domain_regex':
                    payload.add('DOMAIN-REGEX,' + value)
                else:
                    # sing-box .example.com means subdomains only. Do not silently
                    # turn that into a suffix rule which also includes the apex.
                    payload.add('DOMAIN-SUFFIX,' + domain(value))
    expressions = [entry.split(',', 1)[1] for entry in payload if entry.startswith('DOMAIN-REGEX,')]
    # Validate before any write. Use the same regexp implementation as consumers.
    if expressions:
        result = subprocess.run(['go', 'run', str(ROOT / 'scripts/validate_regex.go')],
                                input=json.dumps(expressions), text=True, capture_output=True, timeout=60)
        if result.returncode:
            raise ValueError('invalid Go domain expression')
    return sorted(payload)


def validate(payload, previous=None):
    if not isinstance(payload, list) or len(set(payload)) != len(payload):
        raise ValueError('invalid or duplicate payload')
    if len(payload) < 200:
        raise ValueError('fewer than 200 entries')
    if previous and len(payload) * 5 < len(previous) * 4:
        raise ValueError('more than 20 percent removed')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-file', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'rules/ai.yaml')
    args = parser.parse_args()
    if args.source_file:
        data = json.loads(args.source_file.read_text())
    else:
        with urlopen(SOURCE, timeout=45) as response:
            body = response.read(2 * 1024 * 1024 + 1)
        if len(body) > 2 * 1024 * 1024:
            raise ValueError('source too large')
        data = json.loads(body)
    payload = convert(data)
    previous = yaml.safe_load(args.output.read_text())['payload'] if args.output.exists() else None
    validate(payload, previous)
    content = '# Generated from the public global list; see README.md.\n' + yaml.safe_dump(
        {'payload': payload}, allow_unicode=True, sort_keys=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not args.output.exists() or args.output.read_text() != content:
        args.output.write_text(content)
    print(f'Validated {len(payload)} entries')


if __name__ == '__main__':
    main()
