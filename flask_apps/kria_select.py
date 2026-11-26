"""The hexacontroller (Kria) that task4 and task5 drive, chosen in the GUI.

The pick reaches the bench as MMTS_KRIA_IP on the make command line, and
on_client.sh turns it into KRIA_IP on the client host, overriding the one in
the client's ~/.bashrc. Empty = use the client's own KRIA_IP.
"""
import re
import shlex

import yaml

import flask_apps.shared_state as shared_state

MMTS_CONF = 'data/mmts_configurations.yaml'

### a hostname or an IPv4 address; it ends up in a shell command
_HOST = re.compile(r'^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$')


def _load():
    try:
        with open(MMTS_CONF, 'r') as fIN:
            bench = (yaml.safe_load(fIN) or {}).get('MMTS_bench', {}) or {}
    except FileNotFoundError:
        bench = {}
    ### an entry is a host, or {host:, name:} (the pedestal page shows the name)
    hosts = [k.get('host', '') if isinstance(k, dict) else k for k in (bench.get('krias') or [])]
    return [str(h).strip() for h in hosts if str(h).strip()]


KRIAS = _load()
if not shared_state.kria_ip and KRIAS:
    shared_state.kria_ip = KRIAS[0]


def valid(host: str) -> bool:
    return host == '' or bool(_HOST.match(host))


def select(host) -> str:
    """Store the pick. Raises ValueError on something that is not a host."""
    host = (host or '').strip()
    if not valid(host):
        raise ValueError(f'"{host}" is not a hostname or an IP address')
    shared_state.kria_ip = host
    return host


def env_prefix() -> str:
    """'MMTS_KRIA_IP=... ' for the make command line, or '' for the client default."""
    if not shared_state.kria_ip:
        return ''
    return f'MMTS_KRIA_IP={shlex.quote(shared_state.kria_ip)} '
