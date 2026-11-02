# How OpenCode finds, loads and reloads a plugin

Read from source at the pinned commit. Lines marked **Observed** were also seen on a real OpenCode ([testing.md](testing.md)). Pins are paths inside [upstream/](../upstream/).

## Where plugins come from

A location's list of operations is everything discovered, then everything configured, so explicit config can remove what was discovered (`packages/core/src/config/plugin/source.ts:161`).

| Source | What counts | Pin |
|---|---|---|
| `plugins` in `opencode.json(c)` | Applied from every applicable config file, lowest precedence first, not replaced | `packages/core/src/config/plugin/source.ts:125`, `services/www/src/docs/content/plugins.mdx:36` |
| `plugin/` and `plugins/` in a config directory | Direct `.ts` and `.js` files, and immediate directories. Both folder names work; symlinks are followed | `packages/core/src/plugin/source-directory.ts:7`, `packages/core/src/plugin/source-directory.ts:23` |
| A `plugins/` folder beside a project-root `opencode.json(c)` | Not discovered: it must be under `.opencode/`, or configured | `services/www/src/docs/content/plugins.mdx:64` |
| `cli.json` | TUI-only plugins: see [tui.md](tui.md) | `packages/cli/src/commands/handlers/plugin/add.ts:46` |

The config files, lowest precedence first, are in `services/www/src/docs/content/config.mdx:98`.

## Entry forms

An entry is a string, or `{ "package": "...", "options": { ... } }` (`packages/schema/src/config/plugin.ts:6`). The object form is the only way to pass options (`packages/core/src/config/plugin/source.ts:116`).

| Entry | Meaning | Pin |
|---|---|---|
| `name`, `name@1.2.0`, `@scope/name`, tag or range | npm package | `packages/util/src/npm.ts:59` |
| `github:owner/repo`, `git+ssh://...#main`, `...::path:sub/dir` | Git package | `services/www/src/docs/content/plugins.mdx:107` |
| `./x`, `../x` | Local directory, relative to the config file holding the entry. In a document with no path, relative to the location's directory | `packages/core/src/config/plugin/source.ts:143` |
| Absolute path, `file:///...` | Local directory | `packages/core/src/config/plugin/source.ts:143` |
| `-id`, `-prefix.*`, `-*` | Disable matching plugins by **id**, not by package name | `packages/core/src/plugin/supervisor.ts:35` |
| `*`, `prefix.*`, an active id | Re-enable: it selects, it does not load | `packages/core/src/plugin/supervisor.ts:43` |

**Traps the source shows:**

- A configured local path to a file is skipped, with only a warning in the log (`packages/core/src/config/plugin/source.ts:155`). Standalone files load only through discovery (`packages/core/src/plugin/module.ts:114`).
- A target starting with `opencode.`, or one that equals an active plugin's id, is treated as a selector and never installed (`packages/core/src/plugin/supervisor.ts:44`). Do not name a package `opencode.something`.
- `-` takes an id. A package's id comes from its `Plugin.define`, so `-opencode-acme-plugin` does nothing if the id is `acme`.
- A directory whose resolved entry falls outside the directory is dropped silently (`packages/core/src/config/plugin/source.ts:176`).
- Two built-ins ignore removal, so a repository cannot switch off policy: `packages/core/src/plugin/internal.ts:300`.
- Managed policy can block a plugin: `plugin.use` denied means it is skipped with no failure row (`packages/core/src/plugin/module.ts:53`, `packages/core/src/plugin/supervisor.ts:63`).

## How a directory or package resolves to parts

`Host.resolve` (`packages/plugin/src/host.ts:25`) decides each part:

| Part | Package, or directory with `name` and `exports` in package.json | Directory without them |
|---|---|---|
| Server | `./server`, else `.` (`packages/plugin/src/host.ts:57`) | `server.*`, else `index.*` |
| TUI | `./tui` | `tui.*` |
| RPC | `./rpc` | `rpc.*` |
| GUI | `./gui-experimental`, which must end in `.js` or `.cjs` (`packages/plugin/src/host.ts:61`) | `gui-experimental.cjs`, else `gui-experimental.js` |

- A missing part is normal: resolution errors such as `ERR_PACKAGE_PATH_NOT_EXPORTED` mean "no such part" (`packages/plugin/src/host.ts:39`). **Observed:** a package that exports `./gui-experimental` before the bundle is built loads with no GUI part and no error.
- A package.json that is not a JSON object counts as missing, so the directory falls back to the file names (`packages/plugin/src/host.ts:86`).
- The server entry must default-export `{ id, setup }` or `{ id, effect }`, or the load fails with a `LoadError` (`packages/core/src/plugin/module.ts:81`, `packages/core/src/plugin/module.ts:176`).
- A package with a GUI part and no server part lists under its package name, or the directory's name (`packages/core/src/plugin/module.ts:126`, `packages/plugin/src/host.ts:75`). A TUI-only package is not the server's to list (`packages/core/src/plugin/module.ts:121`).
- Options must be JSON to reach a GUI part, or the plugin fails to load (`packages/core/src/plugin/module.ts:143`).

## Activation order

Built-ins, then SDK and instance plugins, then packages and local plugins, then the late built-ins (`packages/core/src/plugin/supervisor.ts:94`, `packages/core/src/plugin/supervisor.ts:146`). Hooks and transforms run in that registration order, so a later plugin sees earlier changes.

- A duplicate id keeps the first in boot order; later ones are reported as failed with `Duplicate plugin ID` (`packages/core/src/plugin/supervisor.ts:99`).
- Packages already installed activate at once; missing ones install in the background and then activate (`packages/core/src/plugin/supervisor.ts:149`).

## Reload

| Trigger | What happens | Pin |
|---|---|---|
| A file in a `plugin/` or `plugins/` config directory, or a config update | Plugins re-activate, debounced by 100 ms | `packages/core/src/plugin/supervisor.ts:205`, `packages/core/src/plugin/supervisor.ts:221` |
| A configured local plugin outside the config roots | Its target is watched directly | `packages/core/src/config/plugin/source.ts:46` |
| A file in a local plugin's import graph | Fingerprinted and watched; an unchanged graph is not re-evaluated | `packages/plugin/src/source.ts:6` |
| A local `./gui-experimental` bundle | Watched and hashed, and the GUI revision changes. **Observed:** it also restarts the plugin's server part, and every plugin after it, though the docs and a source comment say it does not ([drift.md](drift.md)) | `packages/core/src/plugin/module.ts:136`, `packages/core/src/config/plugin/source.ts:178` |
| Every 24 hours | Re-activates, and checks packages for updates | `packages/core/src/plugin/supervisor.ts:207`, `packages/core/src/plugin/update.ts:9` |

**What a reload does to running plugins.** Registrations are ordered by setup, so only the unchanged prefix of the list stays alive: changing plugin N tears down everything after N in reverse order and sets those up again (`packages/core/src/plugin.ts:122`, `packages/core/src/plugin.ts:139`). So `setup` can run again for a plugin you did not change. Make it safe to repeat, and return a cleanup.

## Failure

| What fails | Result | Pin |
|---|---|---|
| Module load, or the export has the wrong shape | A failed row in `plugin.list`. If an earlier revision of that target is running, it stays in place | `packages/core/src/plugin/supervisor.ts:74` |
| `setup` throws | Failed row with the error. If an older revision was active, it is restored and keeps running, with the error shown | `packages/core/src/plugin.ts:95`, `packages/core/src/plugin.ts:168` |
| A transform throws when a domain's state is computed | The plugin is disabled: "Plugin disabled after `<state>`.transform failed", with a ref to find in the server log | `packages/core/src/plugin.ts:65` |
| The same failed revision again | Not retried until it changes | `packages/core/src/plugin.ts:153` |

Other plugins keep running. **Observed:** a load-time `TypeError` in `setup` showed as `state: failed` with the stack in `error`, and its command and RPC were absent ([drift.md](drift.md)).

## The CLI

`opencode plugin` is defined at `packages/cli/src/commands/commands.ts:282`. Everything it writes goes to the **global** config.

| Command | What it does | Pin |
|---|---|---|
| `plugin add <spec>` | Installs, then adds to the global `opencode.json(c)`; a TUI-only package goes to `cli.json`. npm and Git specs only: no local paths, tarballs or aliases | `packages/cli/src/commands/handlers/plugin/add.ts:17`, `packages/cli/src/commands/handlers/plugin/add.ts:48` |
| `plugin list [--builtin]` | Lists server plugins and TUI-only plugins | `packages/cli/src/commands/handlers/plugin/list.ts:1` |
| `plugin check [target]` | Reports outdated packages; a failed check exits 1 | `packages/cli/src/commands/handlers/plugin/check.ts:12` |
| `plugin update [target]` | Updates outdated packages. Local plugins and exact revisions are skipped | `packages/cli/src/commands/handlers/plugin/update.ts:9`, `packages/cli/src/commands/handlers/plugin/inventory.ts:31`, `packages/util/src/npm.ts:365` |
| `plugin remove <spec>` | Removes an entry whose string or `package` equals the spec **exactly**, from both configs. `name` does not match `name@1.2.0` | `packages/cli/src/commands/handlers/plugin/remove.ts:71` |

Packages install under `<cache>/npm/<key>` (`packages/util/src/npm.ts:139`), not the `~/.cache/opencode/node_modules/` that the V1 docs name.

## Global paths

XDG variables set the config, data, cache and state roots, each under an `opencode` folder, with `~/.config`, `~/.local/share`, `~/.cache` and `~/.local/state` as defaults on every system, Windows included (`packages/util/src/global-roots.ts:5`). That is what makes [an isolated test instance](testing.md) possible.
