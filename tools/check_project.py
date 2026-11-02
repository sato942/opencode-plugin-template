"""The project check (read-only). It fails when files are stale or unmapped; AGENTS.md "Keeping the project current" says why.
It tests facts in files, never whether work is finished: it reads no code and runs no tests.
Usage, from the clone: python -I tools/check_project.py .        The pre-commit hook adds --staged.

Always: relative links and anchors resolve; spec IDs and codes are defined once; every spec ID STATE.md names exists; the map's data
block is sound (parts, references, edges, stages, loops, decisions, a reference to every feature note and spec file); every .md and
.html file is reachable from AGENTS.md through links; every top-level file or folder is mapped in Main files or the file map, by a link
or a pattern in backticks; every path pattern in those tables matches a file; AGENTS.md stays within 32 KiB; each spec file has a row in
specs/README.md and a STATE.md row whose version and counts match; each feature note is in the register and the feature matrix, and the
register names the next unused ID; each Proposed decision in the map is under "Waiting for the owner"; every open question in a spec
file is in the map's decisions; the map's ideas bank is sound (unique IDs, known values, and references, spec IDs and parts that exist);
no template placeholder is left; the hook is on.

A code folder is one the file map links with a trailing slash, as [src/](src/) does. The check does not read inside it. It reads only
files git tracks or would track, so what .gitignore names, such as node_modules, never reaches it.

With --staged, also: a changed spec file changes its version and change log, and comes with STATE.md and PROJECT_MAP.html; a changed
STATE.md or PROJECT_MAP.html changes its updated time.

While tools/start_project.py exists this is still the template: placeholders, the hook and the updated times are not checked."""
import json
import re
import subprocess
import sys
from collections import Counter
from fnmatch import fnmatch
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # python -I ignores PYTHONIOENCODING

FENCE = '`' * 3
MAP = 'PROJECT_MAP.html'
LINK = re.compile(r'\[[^\]\n]+\]\(([^)\s]+)\)')
PLACEHOLDER = re.compile(r'\{\{(?:PROJECT|OWNER|TIMEZONE|REPO|NOW)\}\}')
SPEC_ID = r'[A-Z]{3,8}-(?:\d{3}|Q\d+|V\d+)'
STATUSES = {'Specified', 'Recorded', 'Gap', 'Out of plan'}
paths = [a for a in sys.argv[1:] if not a.startswith('--')]
root = Path(paths[0] if paths else '.').resolve()
template = (root / 'tools' / 'start_project.py').exists()
errors, checked = [], 0


def git(*args):
    try:
        return subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, encoding='utf-8', errors='replace').stdout
    except OSError:
        return ''


def read(rel):
    path = root / rel
    if path.is_file():
        return path.read_text(encoding='utf-8', errors='replace')
    errors.append(f'{rel} is missing')
    return ''


def plain(text):
    # Code is not a link: fenced blocks and inline code stay out of the link checks.
    return re.sub(r'`[^`\n]*`', '', re.sub(FENCE + '.*?' + FENCE, '', text, flags=re.S))


def section(text, heading, where):
    # A section runs from its heading to the next heading of the same level.
    found = re.search(r'^' + re.escape(heading) + r'\s*$.*?(?=^## |\Z)', text, flags=re.M | re.S)
    if not found:
        errors.append(f'{where} has no "{heading}" section')
    return found.group(0) if found else ''


def anchors(text):
    # GitHub-style heading slugs.
    result, counts, in_fence = set(), {}, False
    for line in text.splitlines():
        if line.startswith(FENCE):
            in_fence = not in_fence
            continue
        if in_fence or not re.match(r'^#{1,6} ', line):
            continue
        title = re.sub(r'[\*_`]', '', line.lstrip('#').strip()).lower()
        slug = re.sub(r'[^\w\- ]', '', title).replace(' ', '-')
        n = counts.get(slug, 0)
        counts[slug] = n + 1
        result.add(slug if n == 0 else f'{slug}-{n}')
    return result


def resolves(href, where):
    target, _, anchor = href.partition('#')
    dest = root / target
    if not target or not dest.exists():
        errors.append(f'missing target {href} in {where}')
    elif anchor and dest.suffix == '.md' and anchor not in anchors(dest.read_text(encoding='utf-8', errors='replace')):
        errors.append(f'missing anchor {href} in {where}')


# Which files the check reads: what git tracks or would track, outside dot folders and code folders.
if git('rev-parse', '--is-inside-work-tree').strip() != 'true':
    errors.append('this is not a git repository: run git init')
agents = read('AGENTS.md')
mapped = section(agents, '## Main files', 'AGENTS.md') + section(agents, '## File map', 'AGENTS.md')
code_folders = tuple(sorted({f + '/' for f in re.findall(r'\]\(([^)\s#]+)/\)', plain(mapped))}))
own = lambda t: t and not t.startswith('.') and not t.startswith(code_folders) and (root / t).exists()
tracked = [t for t in git('ls-files', '-z', '--cached').split('\0') if own(t)]
untracked = [t for t in git('ls-files', '-z', '--others', '--exclude-standard').split('\0') if own(t)]
docs = sorted(t for t in tracked + untracked if t.endswith(('.md', '.html')))

for rel in docs:
    if not rel.endswith('.md'):
        continue
    file = root / rel
    for match in LINK.finditer(plain(file.read_text(encoding='utf-8', errors='replace'))):
        href = match.group(1).strip('<>')
        if re.match(r'^[a-z]+:', href):
            continue
        checked += 1
        target, _, anchor = href.partition('#')
        dest = (file.parent / target).resolve() if target else file
        if not dest.exists():
            errors.append(f'missing target {href} in {rel}')
        elif anchor and dest.suffix == '.md' and anchor not in anchors(dest.read_text(encoding='utf-8', errors='replace')):
            errors.append(f'missing anchor {href} in {rel}')

# Spec files: each ID is defined once, as a list item starting "- **ID**"; each code belongs to one
# spec file; and every spec ID that STATE.md names is defined.
state = read('STATE.md')
defined, prefix_owner = Counter(), {}
spec_files = sorted((root / 'specs').glob('*.spec.md'))
for spec_file in spec_files:
    ids = re.findall(r'^- \*\*(' + SPEC_ID + r')\*\*', spec_file.read_text(encoding='utf-8', errors='replace'), flags=re.M)
    defined.update(ids)
    for prefix in {i.split('-')[0] for i in ids}:
        if prefix_owner.setdefault(prefix, spec_file.name) != spec_file.name:
            errors.append(f'code {prefix} used in {prefix_owner[prefix]} and {spec_file.name}')
twice = sorted(i for i, n in defined.items() if n > 1)
if twice:
    errors.append(f'spec IDs defined more than once: {twice}')
named = set(re.findall(r'\b(' + SPEC_ID + r')\b', state))
unknown = sorted(i for i in named if i.split('-')[0] in prefix_owner and i not in defined)
if unknown:
    errors.append(f'STATE.md names spec IDs that no spec file defines: {unknown}')

# The map: PROJECT_MAP.html keeps every part in its JSON data block. Each part is defined once, under its own area, with a known
# status or "Withdrawn: ..."; a priority only on a Gap; every reference key and source code is defined; every reference path and
# anchor resolves; every overview edge names a known node; every loop and the current stage name known stages, because the page
# cannot draw otherwise; every data-path link in the page resolves; and every feature note and spec file is referenced.
page = read(MAP)
block = re.search(r'<script type="application/json" id="project-map-data">(.*?)</script>', page, flags=re.S)
data = {}
if not block:
    errors.append(f'{MAP} has no project-map-data block')
else:
    try:
        data = json.loads(block.group(1))
    except ValueError as e:
        errors.append(f'the data block in {MAP} is not valid JSON: {e}')
refs = data.get('refs', {})
part_ids, decision_ids, ideas = [], [], []
try:
    for area in data.get('areas', []):
        for part in area['parts']:
            part_ids.append(part['id'])
            if not part['id'].startswith(area['id'] + '.'):
                errors.append(f'map part {part["id"]} sits in area {area["id"]}')
            if part['status'] not in STATUSES and not part['status'].startswith('Withdrawn: '):
                errors.append(f'map part {part["id"]} has unknown status {part["status"]!r}')
            if part.get('priority') and part['status'] != 'Gap':
                errors.append(f'map part {part["id"]} has a priority but is not a Gap')
            errors.extend(f'map part {part["id"]} names unknown reference {r!r}' for r in part.get('refs', []) if r not in refs)
            errors.extend(f'map part {part["id"]} names unknown source {c!r}' for c in part.get('seen', []) if c not in data['sources'])
    twice = sorted(i for i, n in Counter(part_ids).items() if n > 1)
    if twice:
        errors.append(f'map parts defined more than once: {twice}')

    for key, ref in refs.items():
        checked += 1
        resolves(ref['href'], f'{MAP} reference {key!r}')
    for href in re.findall(r'data-path="([^"]+)"', page):
        checked += 1
        resolves(href, MAP)
    stage_ids = {s['id'] for s in data.get('stages', [])}
    for f in [f for s in data.get('stages', []) for f in s['files']] + data.get('stage_rails', []) + [data.get('notice') or {}, data.get('origin') or {}]:
        if f.get('path'):
            checked += 1
            resolves(f['path'], MAP)
    errors.extend(f'map loop {x["id"]} names an unknown stage' for x in data.get('loops', []) if x['from'] not in stage_ids or x['to'] not in stage_ids)
    errors.extend(f'map stage_now names unknown stage {s!r}' for s in (data['stage_now']['stages'] + data['stage_now']['not_started'] if data else []) if s not in stage_ids)
    nodes = {a['id'] for a in data.get('areas', [])} | {'user', 'outside'}
    errors.extend(f'map edge {e} names an unknown node' for e in data.get('edges', []) if e[0] not in nodes or e[1] not in nodes)
    referenced = {ref['href'].partition('#')[0] for ref in refs.values()}
    feature_notes = sorted((root / 'features').glob('F[0-9][0-9][0-9]-*.md'))
    for note in feature_notes + spec_files:
        if note.relative_to(root).as_posix() not in referenced:
            errors.append(f'{MAP} does not reference {note.relative_to(root).as_posix()}')

    # Decisions in the map: each is defined once, Decided, Proposed or Open; each spec key is a reference to a spec file,
    # and each requirement ID or § section it names exists in that file; each part exists; study and record are references.
    spec_parts = {}
    for spec_file in spec_files:
        text = spec_file.read_text(encoding='utf-8', errors='replace')
        spec_parts[spec_file.relative_to(root).as_posix()] = (
            set(re.findall(r'^- \*\*(' + SPEC_ID + r')\*\*', text, flags=re.M)),
            {'§' + n for n in re.findall(r'^#{2,3} (\d+(?:\.\d+)?)\.? ', text, flags=re.M)})
    decision_ids = [x['id'] for x in data.get('decisions', [])]
    twice = sorted(i for i, n in Counter(decision_ids).items() if n > 1)
    if twice:
        errors.append(f'map decisions defined more than once: {twice}')
    known_parts = set(part_ids)
    for x in data.get('decisions', []):
        if x.get('status') not in ('Decided', 'Proposed', 'Open'):
            errors.append(f'map decision {x["id"]} has unknown status {x.get("status")!r}')
        if x.get('status') == 'Proposed' and not x.get('recommended'):
            errors.append(f'map decision {x["id"]} is Proposed but names no recommended option')
        for key, ids in x.get('specs', {}).items():
            href = refs.get(key, {}).get('href', '')
            if href not in spec_parts:
                errors.append(f'map decision {x["id"]} names {key!r}, which is not a spec file reference')
                continue
            reqs, sections = spec_parts[href]
            errors.extend(f'map decision {x["id"]} names {i}, which {href} does not define' for i in ids if i not in reqs and i not in sections)
        errors.extend(f'map decision {x["id"]} names unknown part {i}' for i in x.get('parts', []) if i not in known_parts)
        errors.extend(f'map decision {x["id"]} names unknown reference {r!r}' for r in (x.get('study'), x.get('record')) if r and r not in refs)
    # Every open question in a spec file is in the map's decisions, as a decision's ID or among its requirement IDs.
    in_map = set(decision_ids) | {i for x in data.get('decisions', []) for ids in x.get('specs', {}).values() for i in ids}
    unlisted = sorted(i for i in defined if re.search(r'-Q\d+$', i) and i not in in_map)
    if unlisted:
        errors.append(f"spec questions missing from the map's decisions: {unlisted}")

    # The ideas bank: a study of an outside source adds its good ideas here.
    ideas = data.get('ideas', [])
    twice = sorted(str(i) for i, n in Counter(x.get('id') for x in ideas).items() if n > 1)
    if twice:
        errors.append(f'ideas defined more than once: {twice}')
    feature_codes = {n.name[:4] for n in feature_notes}
    for x in ideas:
        name = x.get('id')
        if not re.fullmatch(r'IDEA-\d{3}', str(name)):
            errors.append(f'idea {name!r} is not named IDEA-NNN')
        errors.extend(f'idea {name} has no {key}' for key in ('name', 'what', 'sources', 'seen', 'evidence', 'gives', 'next', 'settle') if not x.get(key))
        if x.get('evidence') not in ('Measured', 'Vendor’s test', 'Claim', 'Design only'):
            errors.append(f'idea {name} has unknown evidence {x.get("evidence")!r}')
        if x.get('next') not in ('Owner', 'Measure', 'Study', 'Carry', 'Spec', 'Carried', 'Not for us'):
            errors.append(f'idea {name} has unknown next {x.get("next")!r}')
        errors.extend(f'idea {name} gives unknown {g!r}' for g in x.get('gives', []) if g not in ('Success', 'Speed', 'Latency', 'Cost', 'Safety', 'Use'))
        if (x.get('seen') or [''])[0] not in refs:
            errors.append(f'idea {name} names unknown study {(x.get("seen") or [""])[0]!r}')
        errors.extend(f'idea {name} names unknown source {s}' for s in x.get('sources', []) if re.fullmatch(r'S\d+', s) and s not in data['sources'])
        errors.extend(f'idea {name} names unknown part {i}' for i in x.get('parts', []) if i not in known_parts)
        errors.extend(f'idea {name} names {i}, which no spec file defines' for i in x.get('specs', []) if i not in defined and i not in prefix_owner and i not in feature_codes)
except (KeyError, TypeError, AttributeError) as e:
    errors.append(f'the data block in {MAP} has the wrong shape near {e!r}: "Keeping it current" on the page lists each field')


# Upkeep: every document is mapped, and the facts kept in two places agree.
def links_from(rel):
    path = root / rel
    if path.suffix == '.md':
        found = [(path.parent, m.group(1).strip('<>')) for m in LINK.finditer(plain(path.read_text(encoding='utf-8', errors='replace')))]
    elif rel == MAP:
        found = [(root, ref.get('href', '')) for ref in refs.values()] + [(root, h) for h in re.findall(r'data-path="([^"]+)"', page)]
    else:
        return
    for base, href in found:
        if href.startswith('#') or re.match(r'^[a-z]+:', href):
            continue
        dest = (base / href.partition('#')[0]).resolve()
        dest = dest / 'README.md' if dest.is_dir() else dest
        if dest.is_relative_to(root):
            yield dest.relative_to(root).as_posix()


reached, todo = set(), ['AGENTS.md']
while todo:
    rel = todo.pop()
    if rel not in reached and (root / rel).is_file() and not rel.startswith(code_folders):
        reached.add(rel)
        todo.extend(links_from(rel))
errors.extend(f'{t} is not reachable from AGENTS.md: link it from its folder index' for t in tracked if t.endswith(('.md', '.html')) and t not in reached)
unmapped = [t for t in untracked if t.endswith(('.md', '.html')) and t not in reached]

named_in_map = re.findall(r'`([^`\s<>]+)`', mapped)
for top in sorted({t.split('/')[0] for t in tracked}):
    if not re.search(r'\]\(' + re.escape(top) + r'[/)#]', mapped) and not any(fnmatch(top, p) for p in named_in_map):
        errors.append(f'{top} is not mapped in Main files or the file map in AGENTS.md')
for pattern in re.findall(r'`([^`\s<>]*[/*][^`\s<>]*)`', mapped):
    if not list(root.glob(pattern)):
        errors.append(f'the file map in AGENTS.md names {pattern}, which matches no file')
size = len(agents.encode('utf-8'))
if size > 32768:
    errors.append(f'AGENTS.md is {size} bytes, over the 32 KiB where Codex stops reading: move detail to the file it belongs to')

index = read('specs/README.md')
for spec_file in spec_files:
    name, text = spec_file.name, spec_file.read_text(encoding='utf-8', errors='replace')
    if f']({name})' not in index:
        errors.append(f'specs/README.md has no row for {name}')
    row = next((line for line in state.splitlines() if line.startswith(f'| [{name}]')), None)
    if not row:
        errors.append(f'STATE.md has no progress row for {name}')
        continue
    cells = row.split(' | ')
    if len(cells) < 6:
        errors.append(f'the STATE.md row for {name} has too few cells')
        continue
    count = lambda kind: str(len(re.findall(r'^- \*\*[A-Z]{3,8}-' + kind + r'\*\*', text, flags=re.M)))
    version = re.search(r'\*\*Version\*\* \| (\d+\.\d+)', text)
    wanted = {'version': (cells[1].split(',')[0], version.group(1) if version else '?'),
              'requirements': (re.match(r'\d*', cells[2]).group(0), count(r'\d{3}')),
              'open questions': (re.match(r'\d*', cells[3]).group(0), count(r'Q\d+')),
              'validations': ((re.search(r' of (\d+)', cells[4]) or [0, ''])[1], count(r'V\d+')),
              'implemented out of': ((re.search(r' of (\d+)', cells[5]) or [0, ''])[1], count(r'\d{3}'))}
    errors.extend(f'STATE.md says {name} has {what} {said}; the file has {real}' for what, (said, real) in wanted.items() if said != real)

register = read('features/README.md')
matrix = read('FEATURE_MATRIX.md')
feature_notes = sorted((root / 'features').glob('F[0-9][0-9][0-9]-*.md'))
for note in feature_notes:
    if note.name not in register:
        errors.append(f'features/README.md does not list {note.name}')
    if f'| [{note.name[:4]}](' not in matrix:
        errors.append(f'FEATURE_MATRIX.md has no {note.name[:4]}')
next_id = f'F{max((int(n.name[1:4]) for n in feature_notes), default=0) + 1:03d}'
if f'**{next_id}**' not in register:
    errors.append(f'features/README.md does not name {next_id} as the next unused ID')

waiting = section(state, '## Waiting for the owner', 'STATE.md')
errors.extend(f'map decision {x["id"]} is Proposed but is not under "Waiting for the owner" in STATE.md'
              for x in data.get('decisions', []) if x.get('status') == 'Proposed' and x['id'] not in waiting)
if not template:
    if git('config', '--get', 'core.hooksPath').strip() != 'tools/hooks':
        errors.append('the pre-commit hook is off: run git config core.hooksPath tools/hooks')
    errors.extend(f'{t} still has a template placeholder: {PLACEHOLDER.search(read(t)).group(0)}' for t in docs if PLACEHOLDER.search(read(t)))

if '--staged' in sys.argv:
    staged = [t for t in git('diff', '--cached', '--name-only', '-z').split('\0') if t]
    first = lambda pattern, s: (re.search(pattern, s) or [None])[0]
    for rel in staged:
        if not fnmatch(rel, 'specs/*.spec.md') or not (root / rel).exists():
            continue
        errors.extend(f'{rel} changed, so {p} must change in the same commit (AGENTS.md, Coupled files)' for p in ('STATE.md', MAP) if p not in staged)
        old, new = git('show', f'HEAD:{rel}'), read(rel)
        if old and first(r'\*\*Version\*\* \| \d+\.\d+', old) == first(r'\*\*Version\*\* \| \d+\.\d+', new):
            errors.append(f'{rel} changed but its version did not')
        if old and old.rstrip().rsplit('\n', 1)[-1] == new.rstrip().rsplit('\n', 1)[-1]:
            errors.append(f'{rel} changed but its change log has no new line')
    for rel, pattern in (('STATE.md', r'last updated [^*]*'), (MAP, r'"updated": "[^"]*"')):
        if not template and rel in staged and first(pattern, git('show', f'HEAD:{rel}')) == first(pattern, read(rel)):
            errors.append(f'{rel} changed but its updated time did not')

print(f'checked {checked} relative links in {len(docs)} files and the map; {len(defined)} spec IDs in {len(spec_files)} spec files; '
      f'{len(part_ids)} map parts; {len(decision_ids)} map decisions; {len(ideas)} banked ideas')
if unmapped:
    print('note, untracked and not mapped: ' + ', '.join(unmapped))
print('\n'.join(errors) if errors else 'OK: nothing broken, unmapped or stale that the check can see')
sys.exit(1 if errors else 0)
