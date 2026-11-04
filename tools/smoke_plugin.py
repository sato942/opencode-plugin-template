"""Loads this plugin in a private, throwaway OpenCode server and checks it through the server's real API.
Usage, from the clone: python -I tools/smoke_plugin.py [--opencode PATH]

It never touches your own OpenCode: config, data, cache and state all live in .dev/ (which git ignores), the server gets a
one-time password and a free local port, and it stops when the check ends. It reads what to check from tools/smoke.json:
  commands  names the plugin must add to the command list
  rpc       methods to call, each with its input and the text its output must contain
It needs no model and no account. It shows the server part loads and runs, and that the server serves a built GUI bundle. It does
not run a model, the TUI or Desktop.
Exit codes: 0 every check passed; 1 a check failed; 2 OpenCode could not be started. The server's log is in .dev/server.log."""
import argparse
import base64
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # python -I ignores PYTHONIOENCODING

root = Path(__file__).resolve().parent.parent
dev = root / '.dev'
log_file = dev / 'server.log'
parser = argparse.ArgumentParser(description='Load this plugin in a private OpenCode server and check it.')
parser.add_argument('--opencode', default=shutil.which('opencode'), help='the OpenCode CLI to test with; default: the one on PATH')
args = parser.parse_args()
if not args.opencode:
    sys.exit('The OpenCode CLI was not found. Install it, or pass --opencode PATH.')

plan = json.loads((root / 'tools' / 'smoke.json').read_text(encoding='utf-8'))
package = json.loads((root / 'package.json').read_text(encoding='utf-8'))
shutil.rmtree(dev, ignore_errors=True)
xdg = {name: dev / name for name in ('config', 'data', 'cache', 'state')}
for folder in xdg.values():
    folder.mkdir(parents=True)
(xdg['config'] / 'opencode').mkdir()
(xdg['config'] / 'opencode' / 'opencode.json').write_text(json.dumps({'plugins': [root.as_posix()]}), encoding='utf-8', newline='\n')

with socket.socket() as s:
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
password = secrets.token_urlsafe(24)
drop = ('OPENCODE_CONFIG', 'OPENCODE_CONFIG_DIR', 'OPENCODE_CONFIG_CONTENT', 'OPENCODE_SERVER_PASSWORD')
env = {k: v for k, v in os.environ.items() if k not in drop}
env.update({f'XDG_{name.upper()}_HOME': str(folder) for name, folder in xdg.items()}, OPENCODE_PASSWORD=password)
url = f'http://127.0.0.1:{port}'
auth = 'Basic ' + base64.b64encode(f'opencode:{password}'.encode()).decode()
location = 'location[directory]=' + urllib.parse.quote(str(root))


def call(method, path, body=None, query=''):
    # OpenCode's API: GET and POST under /api, with the working directory in the query.
    request = urllib.request.Request(f'{url}{path}?{location}{query}', method=method, headers={'Authorization': auth, 'Content-Type': 'application/json'},
                                     data=None if body is None else json.dumps(body).encode())
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def stop_tree(pid):
    """Stops a process this script started, and the processes it started, children first (Windows only).
    `taskkill /T` is not used: it follows parent process ids, which Windows reuses, so a process whose parent exited long
    ago can count as a child of a new one. Here a child counts only if it started after its parent
    (plugin-dev/guide/testing.md, Desktop windows)."""
    listing = subprocess.run(['powershell', '-NoProfile', '-Command',
                              'Get-CimInstance Win32_Process | ForEach-Object { if ($_.CreationDate) { "{0} {1} {2}" -f '
                              '$_.ProcessId, $_.ParentProcessId, $_.CreationDate.ToFileTimeUtc() } }'],
                             capture_output=True, text=True).stdout
    started, children = {}, {}
    for line in listing.splitlines():
        parts = line.split()
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            child, parent, time = map(int, parts)
            started[child] = time
            children.setdefault(parent, []).append(child)
    order = []

    def walk(p, seen):
        for c in children.get(p, []):
            if c not in seen and started.get(c, 0) >= started.get(p, 0):
                seen.add(c)
                walk(c, seen)
        order.append(p)

    if pid in started:
        walk(pid, {pid})
    for p in order or [pid]:
        subprocess.run(['taskkill', '/F', '/PID', str(p)], capture_output=True)


def stop(server):
    if sys.platform == 'win32':
        stop_tree(server.pid)
    else:
        server.terminate()
    server.wait(timeout=15)


results = []


def report(name, passed, detail=''):
    results.append(passed)
    print(f'{"PASS" if passed else "FAIL"}  {name}' + (f': {detail}' if detail else ''))


with open(log_file, 'wb') as log:
    version = subprocess.run([args.opencode, '--version'], env=env, capture_output=True, text=True).stdout.strip()
    print(f'OpenCode {version}, private server on port {port}, config in .dev/')
    server = subprocess.Popen([args.opencode, 'serve', '--hostname', '127.0.0.1', '--port', str(port), '--print-logs', '--log-level', 'info'],
                              cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    try:
        for _ in range(90):
            try:
                call('GET', '/api/info')
                break
            except (urllib.error.URLError, OSError, ValueError):
                time.sleep(1)
        else:
            print('The server did not answer within 90 seconds. See .dev/server.log.')
            sys.exit(2)

        # A plugin loads after the server answers, so give it time before calling it failed or missing.
        mine = None
        for _ in range(30):
            mine = next((p for p in call('GET', '/api/plugin')['data'] if p.get('source', {}).get('path') and Path(p['source']['path']).resolve() == root), None)
            if mine:
                break
            time.sleep(1)
        report('the plugin is listed', mine is not None, mine['id'] if mine else 'not in plugin.list')
        if mine:
            state = mine['state']
            report('its state is active', state['status'] == 'active', state.get('error', ''))
            print(f'      parts found: {", ".join(sorted(mine["features"])) or "none"}')
            if mine['features'].get('gui'):
                bundle = call('GET', '/api/plugin/gui', query='&id=' + urllib.parse.quote(mine['id']))['data']
                report('the server serves its GUI bundle', bool(bundle['code']), f'{len(bundle["code"])} bytes; whether a Desktop window runs it is not checked here')
        names = {c['name'] for c in call('GET', '/api/command')['data']}
        for name in plan.get('commands', []):
            report(f'command {name} is listed', name in names)
        for item in plan.get('rpc', []):
            try:
                path = f'/api/rpc/{urllib.parse.quote(item["id"], safe="")}/{urllib.parse.quote(item["method"], safe="")}'
                output = call('POST', path, {'input': item.get('input')}).get('output')
                report(f'rpc {item["method"]}', item['expect'] in json.dumps(output), json.dumps(output))
            except urllib.error.HTTPError as e:
                report(f'rpc {item["method"]}', False, f'HTTP {e.code}: {e.read().decode(errors="replace")[:300]}')
    finally:
        stop(server)

print(f'{sum(results)} of {len(results)} checks passed. Not covered: a real model calling the tools, the TUI and Desktop.')
sys.exit(0 if results and all(results) else 1)
