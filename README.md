# OpenCode plugin template

A starting point for building an [OpenCode](https://github.com/anomalyco/opencode) plugin with coding agents. It is [project-template](https://github.com/sato942/project-template), specialized in three ways:

- **It knows how OpenCode plugins really work.** [plugin-dev/](plugin-dev/README.md) holds a verbatim copy of OpenCode's plugin docs and source at a pinned commit, and a guide whose every claim cites a source line. A tool says when upstream moves.
- **Source outranks docs.** OpenCode changes constantly and its docs can fall behind, so `AGENTS.md` tells agents to confirm every fact in the source. Where docs and source disagree, it is written down in [drift.md](plugin-dev/guide/drift.md).
- **A working starter plugin, and a way to show it works.** [src/](src/) has a server part, a GUI part and an RPC contract. [tools/smoke_plugin.py](tools/smoke_plugin.py) loads it in a private OpenCode and checks it through the real API, without touching your own setup.

It targets OpenCode V2 and `@opencode/plugin`. V1 plugins do not run on V2.

This is an independent project, not made by or affiliated with the OpenCode team.

## Start a plugin

You need git and Python 3.9 or newer. To run the plugin you also need [OpenCode](https://opencode.ai) and Node.js. With the [GitHub CLI](https://cli.github.com/):

```bash
gh repo create my-plugin --template sato942/opencode-plugin-template --private --clone
```

```bash
cd my-plugin
```

```bash
python tools/start_project.py
```

Or choose **Use this template** on GitHub and clone the result. Then see the starter run:

```bash
npm install
```

```bash
npm run build:gui
```

```bash
python -I tools/smoke_plugin.py
```

Then open the folder with your coding agent. `AGENTS.md` and `STATE.md` tell it what to do first: ask what the plugin should do, on which surfaces and on which OpenCode release, check the knowledge against upstream, and extend the map for your plugin's goal.

**What the script does, once:** it fills in the project's name, owner, time zone and repository everywhere, names the plugin after the folder, replaces this README with the project's own, turns on the check that runs before each commit, deletes itself and runs that check. It commits nothing. Run `python tools/start_project.py --help` to set the values yourself. It refuses to run while `origin` still points at this template.

## What the knowledge covers

| | Where | What it holds |
|---|---|---|
| The way in | [plugin-dev/README.md](plugin-dev/README.md) | What wins when sources disagree, and a table from task to page to source |
| The guide | [plugin-dev/guide/](plugin-dev/guide/README.md) | Parts and surfaces, loading, server, TUI, GUI, packaging, testing, drift, each cited line by line |
| The copy | [plugin-dev/upstream/](plugin-dev/upstream/) | OpenCode's V2 and V1 plugin docs, the SDK, the code that hosts plugins on the server, TUI and Desktop, and examples, unchanged and with upstream's paths |
| What gets copied | [plugin-dev/MANIFEST.json](plugin-dev/MANIFEST.json) | The list, with the commit and each file's hash in [SNAPSHOT.json](plugin-dev/upstream/SNAPSHOT.json) |

```bash
python -I tools/sync_upstream.py --check
```

That says whether upstream has moved since the pin, which plugin files changed, and which guide citations they touch. `--sync` moves the pin, or copies a release with `--sync --ref v2.2.5`. `--verify` checks the copy and the citations offline.

## What has been demonstrated, and what has not

[results.md](studies/2026-11-03/results.md) has the output and how to repeat it. In short, on OpenCode CLI 2.2.1 and 2.2.5: the starter loads in an isolated server, its parts are found, the server serves its GUI bundle, its command is listed and its RPC method runs. Runs also confirmed that some of the official docs' advice fails when followed: see [drift.md](plugin-dev/guide/drift.md). **Not yet run:** the bundle inside a real Desktop window, a real model calling its tool, a terminal UI session, and an installed package.

## What else is inside

| File | What it is |
|---|---|
| [AGENTS.md](AGENTS.md) | How agents work here, always in context: the rules, the plugin knowledge and a map of every other file |
| [STATE.md](STATE.md) | Where the project stands now, what is in flight and what waits for the owner |
| [PROJECT_MAP.html](PROJECT_MAP.html) | The interface to all of it: every part the project needs and how far each is covered, every decision, the stages of work and an ideas bank. Open it in a browser from a local clone. It works offline and decides nothing |
| [features/](features/README.md) | The owner's intent, in their own words, one note per feature, with [PRODUCT.md](features/PRODUCT.md) for the whole product |
| [studies/](studies/README.md) | Dated research: the [anatomy study](studies/ANATOMY.md) that sets the map, then the options compared before each decision, with every query and URL in a research log |
| [specs/](specs/README.md) | The specification, one file per feature, with requirement IDs and `UNEXECUTED` validations |
| [FEATURE_MATRIX.md](FEATURE_MATRIX.md) | Every feature's status on every surface |
| [LEGAL_FLAGS.md](LEGAL_FLAGS.md) | License and terms flags, for a legal review before release |
| [tools/check_project.py](tools/check_project.py) | One command that finds stale or unmapped files. The [pre-commit hook](tools/hooks/pre-commit) runs it |

## How work moves

Each feature moves through Idea → Research → Spec → Decide → Build → Demonstrate → Measure → Deliver. Any stage can send work back to an earlier one, for a reason: the stages are an order, not gates. Decisions go to the owner only after research, as a multiple choice question with exactly one recommended option. Building needs the owner's instruction.

Building itself follows **build → demonstrate → deliver**:

- **Build** the requested behavior first, in small changes that are easy to undo.
- **Demonstrate** it through its real entry point, and report honestly what happened.
- **Deliver** it, with a short report of what changed, what was not done and any known problems.

## What it leaves out on purpose

- **No test-driven development.** Automated tests are added only where they give clear value, with no test count or coverage target.
- **No gate systems, readiness scores or expanding checklists.** Completed work stays completed unless new evidence contradicts it.
- **No endless repair loops.** After two failed attempts at the same problem, an agent stops, explains the blocker and looks for a simpler path.
- **No CI.** The project check tests facts in files and never whether work is finished, and it reads no code. Add CI when a project needs it.

## Changing the template

This folder is itself a template: while `tools/start_project.py` exists, the check allows the placeholders. Run `python -I tools/check_project.py .` after a change. New projects copy the template as it is then, and existing projects do not change.

## License

OpenCode's files in [plugin-dev/upstream/](plugin-dev/upstream/) stay under [their MIT license](plugin-dev/upstream/LICENSE). [LEGAL_FLAGS.md](LEGAL_FLAGS.md) lists what has not been reviewed.
