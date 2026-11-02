# The guide

Pages written for this project about how OpenCode plugins work, each claim cited to the source. It is a summary: [the source wins](../README.md#what-wins-when-sources-disagree). The commit it was read at is in [SNAPSHOT.json](../upstream/SNAPSHOT.json).

| Page | What it covers | Read when |
|---|---|---|
| [overview.md](overview.md) | The parts, the surfaces, what runs where, V1 and V2 | Any plugin design or code |
| [loading.md](loading.md) | Where plugins come from, how they resolve, activation order, reload, failure, the CLI | Configuring or installing a plugin, or reading a failure |
| [server.md](server.md) | The server part: tools, hooks, transforms, commands, agents, storage, RPC, Effect | Anything that runs in the OpenCode server |
| [tui.md](tui.md) | The TUI part: commands, routes, slots, renderers, themes | Anything that shows in the terminal UI |
| [gui.md](gui.md) | The GUI part: windows and main process, what it can add, the bundle | Anything that shows in OpenCode Desktop |
| [packaging.md](packaging.md) | package.json, dependencies, target versions, publishing | Changing dependencies or exports; before a release |
| [testing.md](testing.md) | Demonstrating a plugin without touching your own OpenCode | Showing that anything works |
| [drift.md](drift.md) | Where the docs and the source disagree, and which wins | A doc seems wrong; re-checking after a sync |
| [source-index.md](source-index.md) | Which upstream file holds which concept, and the real plugins to read | Looking for the code behind a concept |

## How to read and write a citation

A citation such as `packages/plugin/src/host.ts:57` is a path inside [upstream/](../upstream/) with a line number. It can name a range or several places, as in `:44-52` or `:135,160`. `tools/sync_upstream.py --verify` checks its first line.

- **Every claim about OpenCode gets one,** unless it is marked as our own reasoning.
- **The citation goes to what settles the claim:** code that runs, before a type, a comment or a doc.
- **Cite only what was read.** A new file goes in [MANIFEST.json](../MANIFEST.json) first, then a sync at the same commit, or `--verify` fails.

## Kinds of evidence

Each page says what it rests on. Keep the kinds apart, as [AGENTS.md](../../AGENTS.md#working-rules) working rule 4 says.

- **Read from source at the pin** is the default. It says what the code does, and nothing about whether it was run.
- **Observed** marks what was seen on a real OpenCode, with the version. [testing.md](testing.md) lists what has run.
- `UNEXECUTED` marks what has never been run here.
