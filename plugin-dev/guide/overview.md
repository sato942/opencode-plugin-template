# What an OpenCode plugin is

Read from source at the pin. Lines marked **Observed** ran on OpenCode CLI 2.2.1 and 2.2.5, as [testing.md](testing.md) lists. Pins are paths inside [upstream/](../upstream/).

A V2 plugin is one package, or one local directory, with one or more **parts**. Each part is an export of the package, and each runs in a different process. One config entry loads them all (`services/www/src/docs/content/build/plugins/index.mdx:84`).

## The parts

| Part | Export | Runs in | Imports | Its id | Pin |
|---|---|---|---|---|---|
| Server | `.` or `./server` | The OpenCode server process | `@opencode/plugin` | Declares it. This is the plugin's id | `packages/plugin/src/host.ts:57`, `packages/core/src/plugin/module.ts:81` |
| TUI | `./tui` | The CLI process that draws the terminal, on the client's machine | `@opencode/plugin/tui` | Declares its own, separate from the server part's | `packages/plugin/src/host.ts:58`, `packages/tui/src/plugin/context.tsx:670` |
| GUI | `./gui-experimental` | OpenCode Desktop: `setup` in every window, `main` in the Electron main process, from one prebuilt file | `@opencode/plugin/gui` | Declares none. Takes the server part's, or else the package or folder name | `packages/plugin/src/host.ts:61`, `packages/plugin/src/gui/plugin.ts:26`, `packages/plugin/src/host.ts:75` |
| RPC | `./rpc` | Nothing: a typed contract the server part implements and the others call. It needs a server part | `@opencode/plugin/rpc` | Its own, in `Rpc.define` | `packages/plugin/src/host.ts:59`, `packages/core/src/plugin/module.ts:156` |

`.` runs on the Promise API. `@opencode/plugin/effect` is the same API for Effect code ([server.md](server.md#11-promise-and-effect-differences)).

## Surfaces: where a person sees a result

A **part** is where code runs. A **surface** is where a person sees it. They are not the same, and mixing them up is the most expensive mistake here: a feature can load, run and report success, and still show nothing to the person using it.

| What the plugin adds | Part | Terminal UI | OpenCode Desktop | Pin |
|---|---|---|---|---|
| A tool the model calls | Server | Yes | Yes | `packages/core/src/plugin/host.ts:592` |
| A hook or transform on sessions, models, tools | Server | Yes | Yes | |
| A slash command from the server | Server | Listed | Listed | `packages/tui/src/component/prompt/autocomplete.tsx:503`, `packages/app/src/composer/model.ts:273` |
| A command, keybinding, route, slot, panel, dialog or toast from the TUI | TUI | Yes | **No** | `packages/tui/src/plugin/context.tsx:670`, `packages/core/src/plugin/module.ts:122` |
| A command, panel, settings page, menu item or toast from the GUI | GUI | **No** | Yes | `packages/plugin/src/gui/registries.ts:733` |
| A remote server's plugin UI | | Its TUI part, if already on the client | **No**: "other servers' plugins load no GUI" | `packages/app/src/runtime/plugin/plugins.tsx:27`, [tui.md](tui.md#3-remote-server) |
| A GUI on the web app | GUI | | **No**: a config plugin runs only in the desktop app | `packages/plugin/src/gui/declarations.ts:15` |

**A server command shows nothing by itself.** Its `execute` returns `Promise<void>` (`packages/plugin/src/promise/command.ts:16`), so it has no output channel of its own. A person sees a result only if it puts one in the session: `ctx.session.prompt`, which starts the model, or `ctx.session.synthetic` (`services/www/src/docs/content/build/plugins/server.mdx:802`). A command that only logs, or that only writes to a TUI toast, looks broken on the other surface.

**A TUI command has no output except the terminal.** It runs client-side, and nothing goes to the server or the transcript (`packages/tui/src/component/prompt/index.tsx:1150`).

### So, where does a feature go?

1. **Put the logic in the server part.** It runs under every surface.
2. **If the result belongs in the conversation,** send it into the session from the server part. Every surface then shows it.
3. **If it needs its own UI,** add a thin TUI part, a thin GUI part, or both. Each calls the server part through [RPC](server.md#8-rpc). A feature that serves both surfaces needs both, so a Desktop user never sees a TUI panel.
4. **Say which surfaces each feature serves,** in [FEATURE_MATRIX.md](../../FEATURE_MATRIX.md).

## Where each part is loaded from

| | Server | TUI | GUI |
|---|---|---|---|
| Config | `plugins` in `opencode.json(c)`, from every applicable location | The server's list of active plugins, plus `cli.json` | **Only** what Desktop's own background server lists at its home location, which in practice is the global `opencode.json(c)` |
| Discovery | `plugin/` and `plugins/` in a config directory: files and directories | The same folders: directories only | Global `plugins/` directories |
| A project's own config | Yes, for sessions at that location | Yes, through the server's list | **No GUI, and no message saying so** ([drift.md](drift.md)) |
| Pin | `packages/core/src/config/plugin/source.ts:125` | `packages/tui/src/plugin/context.tsx:301` | `packages/desktop/src/main/plugin/host.ts:440` |

[loading.md](loading.md) has the full rules, [tui.md](tui.md#2-how-it-is-found) and [gui.md](gui.md#1-what-a-gui-part-is-and-where-it-runs) the rest.

## The smallest plugin

The server part, from the docs (`services/www/src/docs/content/build/plugins/index.mdx:9`), which loads from `.opencode/plugins/example/index.ts` with no config and no install:

```ts
import { Plugin } from "@opencode/plugin"

export default Plugin.define({
  id: "example",
  async setup(ctx) {
    await ctx.storage.set("loaded", true)
  },
})
```

[src/](../../src/) has a server part, a GUI part and an RPC contract that run. **Observed:** it loads, its GUI bundle is served, its command is listed, and its RPC method returns.

## Rules that hold in every part

- **`setup` runs more than once.** A reload re-runs it, even for a plugin that did not change, if an earlier one did ([loading.md](loading.md#reload)). Make it safe to repeat, and return a cleanup.
- **Never let a transform throw.** One throw disables the whole plugin (`packages/core/src/plugin.ts:65`).
- **Use source to check names.** A wrong key can fail with no type error if you cast, and the failure shows only as `state: failed` in the plugin list.
- **A plugin runs with OpenCode's rights.** Server and TUI parts are imported into OpenCode's own process (`packages/core/src/plugin/module.ts:174`, `packages/tui/src/plugin/context.tsx:670`), nothing read in the loader isolates them (inference), and a GUI `main` has "full access to Node.js built-ins" (`services/www/src/docs/content/build/plugins/gui/index.mdx:2811`). So treat a plugin you install, and the data your plugin handles, accordingly.

## V1 and V2

They are different APIs, in different packages, with different docs. A V1 plugin does not run on V2 (`services/www/src/docs/content/build/plugins/migrate-v1.mdx:11`).

| | V1 | V2 |
|---|---|---|
| Package | `@opencode-ai/plugin` | `@opencode/plugin` |
| Entry | A function returning a hooks object | `Plugin.define({ id, setup })` |
| Config key | `plugin` | `plugins` (`services/www/src/docs/content/build/plugins/migrate-v1.mdx:14`) |
| Parts | Server, and a separate TUI | Server, TUI, GUI and RPC, in one package |
| Docs | `packages/web/src/content/docs/plugins.mdx` | `services/www/src/docs/content/build/plugins/` |

**To port one,** follow [migrate-v1.mdx](../upstream/services/www/src/docs/content/build/plugins/migrate-v1.mdx), section by section: config, entrypoint, context, hooks, request hooks, tools, events and cleanup, options and state. One default export can carry both APIs (`services/www/src/docs/content/build/plugins/migrate-v1.mdx:333`). Its verify list is in [testing.md](testing.md#verifying-a-port-from-v1).

**To spot V1 in what you read,** look for `@opencode-ai/plugin`, `tool.execute.before`, `experimental.*` keys on a returned object, `$` from the plugin input, or a `plugin` config key. Most web articles and examples are V1.
