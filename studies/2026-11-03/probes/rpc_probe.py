"""Does an RPC contract work without input, output or events, as the docs suggest? Loads a throwaway plugin in a private OpenCode.
Usage, from the clone: python -I studies/2026-11-03/probes/rpc_probe.py OPENCODE [--no-events] [--no-await]

It never touches your own OpenCode: everything lives in .dev/probe-rpc/. Results of the runs of 3 November 2026 are in ../results.md."""
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

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
parser = argparse.ArgumentParser()
parser.add_argument('opencode')
parser.add_argument('--no-events', action='store_true', help='leave events out of the contract')
parser.add_argument('--no-await', action='store_true', help='call ctx.rpc.register without await')
args = parser.parse_args()
base = Path(__file__).resolve().parents[3] / '.dev' / 'probe-rpc'
shutil.rmtree(base, ignore_errors=True)
plugin = base / 'plugin'
plugin.mkdir(parents=True)
marks = base / 'handler-ran.log'
(plugin / 'package.json').write_text(json.dumps({'name': 'rpc-probe', 'version': '1.0.0', 'type': 'module', 'exports': {'.': './index.ts', './rpc': './rpc.ts'}}), encoding='utf-8', newline='\n')
events = '' if args.no_events else '  events: {},\n'
(plugin / 'rpc.ts').write_text(f'''import {{ Rpc }} from "@opencode/plugin/rpc"
const text = {{ type: "object", properties: {{ text: {{ type: "string" }} }}, required: ["text"] }} as const
export const Probe = Rpc.define({{
  id: "rpc-probe",
  methods: {{
    full: {{ input: text, output: text }},
    noInput: {{ output: text }},
    noOutput: {{ input: text }},
    neither: {{}},
  }} as any,
{events}}} as any)
''', encoding='utf-8', newline='\n')
(plugin / 'index.ts').write_text(f'''import {{ Plugin }} from "@opencode/plugin"
import {{ appendFileSync }} from "node:fs"
import {{ Probe }} from "./rpc.ts"
const ran = (name: string) => appendFileSync("{marks.as_posix()}", name + "\\n")
export default Plugin.define({{
  id: "rpc-probe",
  async setup(ctx) {{
    {"" if args.no_await else "await "}ctx.rpc.register(Probe, {{
      full: async () => {{ ran("full"); return {{ text: "ok" }} }},
      noInput: async () => {{ ran("noInput"); return {{ text: "ok" }} }},
      noOutput: async () => {{ ran("noOutput") }},
      neither: async () => {{ ran("neither") }},
    }} as any)
  }},
}})
''', encoding='utf-8', newline='\n')

xdg = {n: base / n for n in ('config', 'data', 'cache', 'state')}
for folder in xdg.values():
    folder.mkdir()
(xdg['config'] / 'opencode').mkdir()
(xdg['config'] / 'opencode' / 'opencode.json').write_text(json.dumps({'plugins': [plugin.as_posix()]}), encoding='utf-8', newline='\n')
with socket.socket() as s:
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
password = secrets.token_urlsafe(24)
env = {k: v for k, v in os.environ.items() if k not in ('OPENCODE_CONFIG', 'OPENCODE_CONFIG_DIR', 'OPENCODE_CONFIG_CONTENT', 'OPENCODE_SERVER_PASSWORD')}
env.update({f'XDG_{n.upper()}_HOME': str(f) for n, f in xdg.items()}, OPENCODE_PASSWORD=password)
auth = 'Basic ' + base64.b64encode(f'opencode:{password}'.encode()).decode()
url = f'http://127.0.0.1:{port}'
location = 'location[directory]=' + urllib.parse.quote(str(base))


def call(method, path, body=None):
    request = urllib.request.Request(f'{url}{path}?{location}', method=method, headers={'Authorization': auth, 'Content-Type': 'application/json'},
                                     data=None if body is None else json.dumps(body).encode())
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def stop(server):
    if sys.platform == 'win32':
        subprocess.run(['taskkill', '/F', '/T', '/PID', str(server.pid)], capture_output=True)
    else:
        server.terminate()
    server.wait(timeout=15)


log_path = base / 'server.log'
with open(log_path, 'wb') as out:
    print('OpenCode', subprocess.run([args.opencode, '--version'], env=env, capture_output=True, text=True).stdout.strip(), '| events' + (' left out' if args.no_events else ' present'), '| register' + (' not awaited' if args.no_await else ' awaited'))
    server = subprocess.Popen([args.opencode, 'serve', '--hostname', '127.0.0.1', '--port', str(port), '--print-logs', '--log-level', 'info'], cwd=base, env=env, stdout=out, stderr=subprocess.STDOUT)
    try:
        for _ in range(90):
            try:
                call('GET', '/api/info')
                break
            except (urllib.error.URLError, OSError, ValueError):
                time.sleep(1)
        mine = None
        for _ in range(30):
            mine = next((p for p in call('GET', '/api/plugin')['data'] if p.get('id') == 'rpc-probe'), None) or next((p for p in call('GET', '/api/plugin')['data'] if p.get('state', {}).get('status') == 'failed'), None)
            if mine:
                break
            time.sleep(1)
        print('plugin state:', mine and mine['state']['status'], ((mine or {}).get('state', {}).get('error') or '').split('\n')[0][:160])
        if mine and mine['state']['status'] == 'active':
            for name, body in (('full', {'input': {'text': 'x'}}), ('noInput', {}), ('noOutput', {'input': {'text': 'x'}}), ('neither', {})):
                before = marks.read_text(encoding='utf-8').count(name) if marks.exists() else 0
                try:
                    result = 'HTTP 200 ' + json.dumps(call('POST', f'/api/rpc/rpc-probe/{name}', body))[:120]
                except urllib.error.HTTPError as e:
                    result = f'HTTP {e.code} ' + e.read().decode(errors='replace')[:120]
                after = marks.read_text(encoding='utf-8').count(name) if marks.exists() else 0
                print(f'{name:9} handler ran={after > before}  {result}')
    finally:
        stop(server)
for line in log_path.read_text(encoding='utf-8', errors='replace').splitlines():
    if 'unhandled rejection' in line:
        print('server log: unhandled rejection:', line.split('cause=')[-1][:110])
