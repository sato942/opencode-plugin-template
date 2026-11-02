"""Keeps plugin-dev/upstream/ a verbatim, pinned copy of OpenCode's plugin docs and source. plugin-dev/README.md says why.
Usage, from the clone:

  python -I tools/sync_upstream.py --check            Has upstream moved since the pin? Lists changed files and the guide pins they touch.
  python -I tools/sync_upstream.py --sync             Copy upstream's newest commit on the tracked branch and move the pin.
  python -I tools/sync_upstream.py --sync --ref v2.2.5   Copy a release instead, for a plugin that targets it.
  python -I tools/sync_upstream.py --verify           Offline: the copy matches its hashes, and every guide pin names a real file and line.

Exit codes: 0 current or sound; 1 behind upstream, or a verify failure; 2 upstream could not be reached.
It keeps a sparse clone in .upstream/, which git ignores, and runs nothing from it. It commits nothing."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # python -I ignores PYTHONIOENCODING

root = Path(__file__).resolve().parent.parent
dev = root / 'plugin-dev'
copy = dev / 'upstream'
snapshot_file = copy / 'SNAPSHOT.json'
clone = root / '.upstream' / 'opencode'
manifest = json.loads((dev / 'MANIFEST.json').read_text(encoding='utf-8'))
PIN = re.compile(r'`((?:packages|services|specs)/[^`\s:]+):(\d+)(?:-\d+)?(?:,\d+(?:-\d+)?)*`')


def git(*args, check=True, stdin=None):
    done = subprocess.run(['git', '-C', str(clone), *args], input=stdin, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if check and done.returncode != 0:
        raise RuntimeError(f'git {" ".join(args)} failed: {done.stderr.strip()}')
    return done.stdout.strip()


def group_of(path):
    if any(fnmatch(path, p) for p in manifest['exclude']):
        return None
    for group, entries in manifest['groups'].items():
        for entry in entries:
            if path == entry or (entry.endswith('/') and path.startswith(entry)) or ('*' in entry and fnmatch(path, entry) and '/' not in path[len(entry.split('*')[0]):]):
                return group
    return None


def fetch(ref):
    """Brings the sparse clone to ref and returns its commit. Raises OSError or RuntimeError if upstream cannot be reached."""
    if not (clone / '.git').exists():
        clone.parent.mkdir(parents=True, exist_ok=True)
        done = subprocess.run(['git', '-c', 'core.longpaths=true', 'clone', '--quiet', '--filter=blob:none', '--no-checkout', '--no-tags',
                               '--single-branch', '--branch', manifest['branch'], manifest['repo'], str(clone)], capture_output=True, text=True)
        if done.returncode != 0:
            raise RuntimeError(done.stderr.strip())
        git('config', 'core.longpaths', 'true')
        git('config', 'core.autocrlf', 'false')  # hashes and line pins must see upstream's exact bytes
    git('fetch', '--quiet', '--no-tags', 'origin', ref)
    return git('rev-parse', 'FETCH_HEAD^{commit}')


def snapshot():
    return json.loads(snapshot_file.read_text(encoding='utf-8')) if snapshot_file.exists() else None


def pins():
    """Yields (guide file, pinned path, line) for each pin in the guide."""
    for page in sorted((dev / 'guide').glob('*.md')):
        for path, line in PIN.findall(page.read_text(encoding='utf-8', errors='replace')):
            yield page.name, path, int(line)


def report_pins(changed):
    touched = sorted({(page, path) for page, path, _ in pins() if path in changed})
    if not touched:
        print('No guide pin points at a changed file.')
        return
    print(f'{len(touched)} guide pins point at changed files. Re-read each one, and correct the guide if the source moved:')
    for page, path in touched:
        print(f'  plugin-dev/guide/{page}: {path}')


def check():
    old = snapshot()
    if not old:
        print('No snapshot yet: run --sync.')
        return 1
    try:
        head = fetch(manifest['branch'])
    except (OSError, RuntimeError) as e:
        print(f'Upstream could not be reached, so the pin at {old["commit"][:10]} is unchecked: {e}')
        return 2
    if head == old['commit']:
        print(f'Current: {manifest["branch"]} is still at the pin, {head[:10]}.')
        return 0
    git('fetch', '--quiet', '--no-tags', 'origin', old['commit'], check=False)
    names = git('diff', '--name-only', old['commit'], head).splitlines()
    changed = {n for n in names if group_of(n)}
    print(f'Pin: {old["ref"]} at {old["commit"][:10]} ({old["committed_at"]}). Upstream {manifest["branch"]}: {head[:10]}, {len(names)} files changed.')
    if not changed:
        print('None of them are in the snapshot, so the plugin docs and source it holds are still current.')
        return 0
    for group in manifest['groups']:
        files = sorted(n for n in changed if group_of(n) == group)
        if files:
            print(f'{group} ({len(files)}):')
            print('\n'.join(f'  {f}' for f in files[:40]) + (f'\n  ... and {len(files) - 40} more' if len(files) > 40 else ''))
    report_pins(changed)
    print('Run --sync to move the pin, or read the changed files in .upstream/ before relying on them.')
    return 1


def sync(ref):
    old = snapshot() or {'files': {}}
    try:
        commit = fetch(ref)
    except (OSError, RuntimeError) as e:
        print(f'Upstream could not be reached, so nothing changed: {e}')
        return 2
    wanted = [p for p in git('ls-tree', '-r', '--name-only', commit).splitlines() if group_of(p)]
    # A sparse checkout fetches the wanted blobs in one batch; asking for them one at a time would take minutes.
    git('sparse-checkout', 'set', '--no-cone', '--stdin', stdin=''.join(f'/{p}\n' for p in wanted))
    git('checkout', '--quiet', '--detach', commit)
    if copy.exists():
        shutil.rmtree(copy)
    files = {}
    for rel in wanted:
        data = (clone / rel).read_bytes()
        dest = copy / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        files[rel] = hashlib.sha256(data).hexdigest()
    version = json.loads((clone / 'packages/plugin/package.json').read_text(encoding='utf-8'))['version']
    snapshot_file.write_text(json.dumps({
        'repo': manifest['repo'], 'ref': ref, 'commit': commit,
        'committed_at': git('log', '-1', '--format=%cI', commit), 'plugin_package_version': version,
        'synced_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'license': 'MIT, see LICENSE in this folder',
        'files': files}, indent=1) + '\n', encoding='utf-8', newline='\n')
    changed = {p for p in set(files) | set(old['files']) if files.get(p) != old['files'].get(p)}
    print(f'Copied {len(files)} files from {ref} at {commit[:10]}, @opencode/plugin {version}. {len(changed)} differ from the last pin.')
    report_pins(changed)
    print('Nothing is committed. Re-read the pins above and re-check plugin-dev/guide/drift.md (AGENTS.md, Coupled files).')
    return 0


def verify():
    old = snapshot()
    if not old:
        print('No snapshot yet: run --sync.')
        return 1
    errors = []
    on_disk = {p.relative_to(copy).as_posix() for p in copy.rglob('*') if p.is_file()} - {'SNAPSHOT.json'}
    errors.extend(f'{p} is in the copy but not in SNAPSHOT.json' for p in sorted(on_disk - set(old['files'])))
    for rel, digest in old['files'].items():
        path = copy / rel
        if not path.is_file():
            errors.append(f'{rel} is missing from the copy')
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append(f'{rel} differs from upstream: the copy is never edited by hand')
    count = 0
    for page, rel, line in pins():
        count += 1
        path = copy / rel
        if rel not in old['files']:
            errors.append(f'guide/{page} pins {rel}, which is not in the snapshot: add it to MANIFEST.json')
        elif line > len(path.read_bytes().split(b'\n')):
            errors.append(f'guide/{page} pins {rel}:{line}, past the end of the file')
    print(f'checked {len(old["files"])} copied files at {old["commit"][:10]} and {count} guide pins')
    print('\n'.join(errors) if errors else 'OK: the copy matches upstream and every pin resolves')
    return 1 if errors else 0


parser = argparse.ArgumentParser(description='Keep plugin-dev/upstream/ a pinned copy of OpenCode plugin docs and source.')
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument('--check', action='store_true', help='has upstream moved since the pin?')
mode.add_argument('--sync', action='store_true', help='copy upstream and move the pin')
mode.add_argument('--verify', action='store_true', help='offline: the copy and the guide pins are sound')
parser.add_argument('--ref', default=manifest['branch'], help='with --sync: the branch or tag to copy')
args = parser.parse_args()
sys.exit(check() if args.check else sync(args.ref) if args.sync else verify())
