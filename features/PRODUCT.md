# {{PROJECT}}: the product

The whole product in one place, and the order it gets built. It says what the project is; the [feature notes](README.md) hold the owner's words for each part, and the [spec files](../specs/README.md) hold the detail.

## What it is

An [OpenCode](https://github.com/anomalyco/opencode) plugin. _What it does: not set yet, the owner's description from the first session ([STATE.md](../STATE.md#in-flight))._

- **Surfaces it serves:** _not set yet._ The terminal UI, OpenCode Desktop, or both ([overview.md](../plugin-dev/guide/overview.md)).
- **OpenCode release it targets:** _not set yet._ The release, and the `@opencode/plugin` range in [package.json](../package.json) ([packaging.md](../plugin-dev/guide/packaging.md)).

## Who it is for

_Not set yet._

## What it is not

_Not set yet._ What the owner has ruled out, so no one proposes it again.

## Vocabulary

One name for each thing ([working rule 10](../AGENTS.md#working-rules)). Add a word when two names start competing for one thing, or when a word here would mislead a newcomer.

| Word | Meaning |
|---|---|
| Plugin | One package, or one local directory, that OpenCode loads. It has one or more parts |
| Part | A piece of a plugin, chosen by an `exports` key or a file name: server, TUI, GUI or RPC |
| Server part | Runs inside the OpenCode server. Adds tools, hooks, commands, agents and the like. Imports `@opencode/plugin` |
| TUI part | Runs inside the terminal UI. Imports `@opencode/plugin/tui` |
| GUI part | Runs in OpenCode Desktop, as one prebuilt bundle. Imports `@opencode/plugin/gui` |
| RPC contract | The typed methods and events a server part offers to the other parts and to clients. Imports `@opencode/plugin/rpc` |
| Surface | Where a person sees a result: the terminal UI or OpenCode Desktop. Not the same as a part |
| Host | The OpenCode process that loads a part, and provides `@opencode/plugin` and `effect` to it |
| Upstream | OpenCode's repository, [anomalyco/opencode](https://github.com/anomalyco/opencode) |
| Snapshot | The verbatim copy of upstream's plugin docs and source in [plugin-dev/upstream/](../plugin-dev/upstream/) |
| Pin | The upstream commit the snapshot is at. Also a citation in the guide, a source path with a line number |
| Drift | A place where upstream's docs and source disagree, kept in [drift.md](../plugin-dev/guide/drift.md) |
| Starter | The working example in [src/](../src/), to change into the real plugin |

## Build sequence

_Not set yet: the order the owner wants things built in, once there is more than one thing to build._
