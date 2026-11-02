"""Does a changed GUI bundle restart a plugin's server part? The docs say no. Loads two throwaway plugins in a private OpenCode.
Usage, from the clone: python -I studies/2026-11-03/probes/rebuild_probe.py OPENCODE

It never touches your own OpenCode: everything lives in .dev/probe-rebuild/. Results of the runs of 3 November 2026 are in ../results.md."""
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

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
opencode = sys.argv[1]
base = Path(__file__).resolve().parents[3] / '.dev' / 'probe-rebuild'
shutil.rmtree(base, ignore_errors=True)
plugin = base / 'plugin'
(plugin / 'dist').mkdir(parents=True)
later = base / 'later'
later.mkdir()
log = base / 'setups.log'
(plugin / 'package.json').write_text(json.dumps({'name': 'rebuild-probe', 'version': '1.0.0', 'type': 'module',
                                                 'exports': {'.': './index.ts', './gui-experimental': './dist/gui-experimental.cjs'}}), encoding='utf-8', newline='\n')
server_source = f'''import {{ Plugin }} from "@opencode/plugin"
import {{ appendFileSync }} from "node:fs"
export default Plugin.define({{ id: "rebuild-probe", async setup() {{ appendFileSync("{log.as_posix()}", "A\\n") }} }})
'''
(plugin / 'index.ts').write_text(server_source, encoding='utf-8', newline='\n')
bundle = plugin / 'dist' / 'gui-experimental.cjs'
bundle.write_text('module.exports = { default: { setup() {} } } // one\n', encoding='utf-8', newline='\n')
# A second plugin, ordered after the first, to see whether it restarts too.
(later / 'index.ts').write_text(f'''import {{ Plugin }} from "@opencode/plugin"
import {{ appendFileSync }} from "node:fs"
export default Plugin.define({{ id: "rebuild-later", async setup() {{ appendFileSync("{log.as_posix()}", "B\\n") }} }})
''', encoding='utf-8', newline='\n')

xdg = {n: base / n for n in ('config', 'data', 'cache', 'state')}
for folder in xdg.values():
    folder.mkdir()
(xdg['config'] / 'opencode').mkdir()
(xdg['config'] / 'opencode' / 'opencode.json').write_text(json.dumps({'plugins': [plugin.as_posix(), later.as_posix()]}), encoding='utf-8', newline='\n')
with socket.socket() as s:
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
password = secrets.token_urlsafe(24)
env = {k: v for k, v in os.environ.items() if k not in ('OPENCODE_CONFIG', 'OPENCODE_CONFIG_DIR', 'OPENCODE_CONFIG_CONTENT', 'OPENCODE_SERVER_PASSWORD')}
env.update({f'XDG_{n.upper()}_HOME': str(f) for n, f in xdg.items()}, OPENCODE_PASSWORD=password)
auth = 'Basic ' + base64.b64encode(f'opencode:{password}'.encode()).decode()
url = f'http://127.0.0.1:{port}'
location = 'location[directory]=' + urllib.parse.quote(str(base))


def call(path, query=''):
    request = urllib.request.Request(f'{url}{path}?{location}{query}', headers={'Authorization': auth})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def counts():
    text = log.read_text(encoding='utf-8') if log.exists() else ''
    return f'setup runs: plugin {text.count("A")}, later plugin {text.count("B")}'


def stop(server):
    if sys.platform == 'win32':
        subprocess.run(['taskkill', '/F', '/T', '/PID', str(server.pid)], capture_output=True)
    else:
        server.terminate()
    server.wait(timeout=15)


with open(base / 'server.log', 'wb') as out:
    print('OpenCode', subprocess.run([opencode, '--version'], env=env, capture_output=True, text=True).stdout.strip())
    server = subprocess.Popen([opencode, 'serve', '--hostname', '127.0.0.1', '--port', str(port), '--print-logs', '--log-level', 'info'], cwd=base, env=env, stdout=out, stderr=subprocess.STDOUT)
    try:
        for _ in range(90):
            try:
                call('/api/info')
                break
            except (urllib.error.URLError, OSError, ValueError):
                time.sleep(1)
        for _ in range(30):
            ids = {p.get('id') for p in call('/api/plugin')['data']}
            if {'rebuild-probe', 'rebuild-later'} <= ids and log.exists():
                break
            time.sleep(1)
        time.sleep(3)
        print('after start:                ', counts())
        before = call('/api/plugin/gui', '&id=rebuild-probe')['data']
        bundle.write_text('module.exports = { default: { setup() {} } } // two, a rebuild\n', encoding='utf-8', newline='\n')
        time.sleep(8)
        after = call('/api/plugin/gui', '&id=rebuild-probe')['data']
        print('after only the bundle changed:', counts(), '| GUI revision changed:', before.get('revision') != after.get('revision'))
        (plugin / 'index.ts').write_text(server_source + '// changed\n', encoding='utf-8', newline='\n')
        time.sleep(8)
        print('after the server file changed (control):', counts())
    finally:
        stop(server)
