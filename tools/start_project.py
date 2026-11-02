"""Turns a fresh copy of this template into a plugin project, once, and then deletes itself.
Usage, from the new clone: python tools/start_project.py [--project NAME] [--owner NAME] [--timezone ZONE] [--repo OWNER/NAME] [--plugin NAME]

Each option has a default: the folder's name, the GitHub owner and repository from the origin remote, this machine's time zone, and a
plugin name made from the project's name.
It fills in the placeholders in every .md and .html file, names the starter plugin, replaces README.md with the project's own, turns on
the pre-commit hook, deletes this script and runs the project check. It commits nothing, and it leaves plugin-dev/upstream/ alone,
because that is a verbatim copy. What only the owner can say, such as what the plugin does and what decisions are judged on, waits for
the first session: STATE.md, "In flight"."""
import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TEMPLATE_NAME = 'opencode-plugin-template'
STARTER_NAME = 'opencode-plugin-starter'
STARTER_FILES = ('package.json', 'package-lock.json', 'tools/smoke.json', 'src/index.ts', 'src/rpc.ts', 'src/gui.tsx')
README = """# {{PROJECT}}

An [OpenCode](https://github.com/anomalyco/opencode) plugin.

- **What it is:** [features/PRODUCT.md](features/PRODUCT.md)
- **Where it stands:** [STATE.md](STATE.md)
- **How to work on it:** [AGENTS.md](AGENTS.md), for people and coding agents alike
- **How OpenCode plugins work:** [plugin-dev/README.md](plugin-dev/README.md)
- **Everything about it on one page:** open [PROJECT_MAP.html](PROJECT_MAP.html) in a browser, from a local clone

After a new clone, turn on the check that runs before each commit:

```bash
git config core.hooksPath tools/hooks
```

To build the plugin and load it in a private OpenCode, which never touches your own:

```bash
npm install
```

```bash
npm run build:gui
```

```bash
python -I tools/smoke_plugin.py
```
"""
root = Path(__file__).resolve().parent.parent


def git(*args):
    try:
        done = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, encoding='utf-8', errors='replace')
    except OSError:
        sys.exit('git was not found. Install git, then run this again.')
    return done.stdout.strip() if done.returncode == 0 else ''


origin = re.search(r'github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$', git('remote', 'get-url', 'origin'))
if origin and origin.group(2) == TEMPLATE_NAME:
    sys.exit(f'The origin remote is the template itself, so nothing was changed. Create the project with:\n'
             f'  gh repo create my-plugin --template {origin.group(1)}/{TEMPLATE_NAME} --private --clone\n'
             f'or, in a plain copy you mean to keep apart, run: git remote remove origin')

parser = argparse.ArgumentParser(description='Turn a fresh copy of this template into a plugin project.')
parser.add_argument('--project', default=root.name, help="the project's name; default: this folder's name")
parser.add_argument('--owner', default=origin.group(1) if origin else git('config', 'user.name') or 'the owner', help='who decides; default: the GitHub owner')
parser.add_argument('--timezone', default=datetime.now().astimezone().tzname(), help="for all dates and times, such as Europe/Paris; default: this machine's")
parser.add_argument('--repo', default=f'{origin.group(1)}/{origin.group(2)}' if origin else 'not on GitHub yet', help='OWNER/NAME; default: from the origin remote')
parser.add_argument('--plugin', help="the plugin's npm name and id, such as opencode-acme-plugin; default: made from the project's name")
args = parser.parse_args()
args.plugin = args.plugin or re.sub(r'[^a-z0-9]+', '-', args.project.lower()).strip('-')
for name, value in vars(args).items():
    if not value or re.search(r'["\\<>&{}\r\n]', value):
        sys.exit(f'--{name} cannot be {value!r}: it goes into JSON and HTML, so it cannot be empty or hold " \\ < > & {{ }}. Nothing was changed.')
if not re.fullmatch(r'(@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*', args.plugin):
    sys.exit(f'--plugin cannot be {args.plugin!r}: an npm name is lowercase letters, digits, dots, hyphens and underscores, with an optional @scope/. Nothing was changed.')
if args.plugin.startswith('opencode.'):
    sys.exit(f'--plugin cannot be {args.plugin!r}: OpenCode reads a config entry starting with "opencode." as a selector and never installs it (plugin-dev/guide/loading.md). Nothing was changed.')

values = {'{{PROJECT}}': args.project, '{{OWNER}}': args.owner, '{{TIMEZONE}}': args.timezone, '{{REPO}}': args.repo,
          '{{NOW}}': f'{datetime.now().strftime("%d %b %Y, %H:%M")} {args.timezone}'}

with open(root / 'README.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(README)


def is_copy(path):
    return path.relative_to(root).as_posix().startswith('plugin-dev/upstream/')


for path in sorted(p for p in root.rglob('*') if p.suffix in ('.md', '.html') and p.is_file() and not {'.git', '.upstream', 'node_modules'} & set(p.relative_to(root).parts) and not is_copy(p)):
    with open(path, encoding='utf-8', newline='') as f:
        old = f.read()
    new = old
    for placeholder, value in values.items():
        new = new.replace(placeholder, value)
    if new != old:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(new)

for rel in STARTER_FILES:
    path = root / rel
    if path.is_file():
        with open(path, encoding='utf-8', newline='') as f:
            old = f.read()
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(old.replace(STARTER_NAME, args.plugin))

if not (root / '.git').exists():
    git('init', '-b', 'main')
git('config', 'core.hooksPath', 'tools/hooks')
Path(__file__).unlink()

print(f'Project:    {args.project}\nOwner:      {args.owner}\nTime zone:  {args.timezone}\nRepository: {args.repo}\nPlugin:     {args.plugin}')
print('The pre-commit hook is on and this script is gone. Nothing is committed. If a value above is wrong, change it where it appears.\n', flush=True)
check = subprocess.run([sys.executable, '-I', str(root / 'tools' / 'check_project.py'), str(root)])
print('\nNext: open this folder with your coding agent. It asks what the plugin should do, on which surfaces and for which OpenCode release, then checks its knowledge against upstream and extends the map for that goal.')
sys.exit(check.returncode)
