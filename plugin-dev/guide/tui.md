# The TUI part

The part that runs in the terminal UI, on the client's machine. The official docs are [build/plugins/cli.mdx](../upstream/services/www/src/docs/content/build/plugins/cli.mdx) and [cli/plugins.mdx](../upstream/services/www/src/docs/content/cli/plugins.mdx), and [drift.md](drift.md) lists where they are wrong. The starter in [src/](../../src/) has no TUI part, and nothing on this page has been run here: `UNEXECUTED`.

Read from source at the pin. Pins are paths inside [upstream/](../upstream/). "(inference)" marks a conclusion drawn from what was read, not a line that states it. **Observed** marks what was run: [testing.md](testing.md) says on what.

- `node_modules` were not read. OpenTUI and `@solid-primitives` internals were not read either, so claims about them rest on call sites.

## 1. What a TUI part is

| Question | Answer | Pin |
|---|---|---|
| What is it? | A module whose default export is a `Plugin.Definition`. | `packages/plugin/src/tui/plugin.ts:7` |
| Where is it declared? | Package export `./tui`, or a root file named `tui` in a local directory. | `packages/plugin/src/host.ts:58` |
| Where does it run? | In the CLI process that draws the terminal, on the client machine. | `packages/tui/src/app.tsx:435` |
| Who loads it? | Only the TUI host. It calls `Host.resolve(target).tui`, then imports the file. | `packages/tui/src/plugin/context.tsx:670` |
| Does the server run it? | No. The server only sets `features.tui` for the listing. | `packages/core/src/plugin/module.ts:155` |
| Does Mini run it? | No. `PluginProvider` has one mount, in the full app; `packages/tui/src/mini` does not reference it (grep). | `packages/tui/src/app.tsx:435` |
| What does the import give? | `Plugin` (`define` and types), `PluginContextProvider`, `usePlugin`. Other types are at `@opencode/plugin/tui/context`, through the `./*` export. | `packages/plugin/src/tui/index.ts:1`, `packages/plugin/package.json:31` |

## 2. How it is found

The host folds three lists into one ordered list on every reconcile. A later entry for the same key replaces the earlier one but keeps the earlier position. The key is the local file URL, else the raw string.

| Order | Source | Entry | `install` | `optional` | Options | Pin |
|---|---|---|---|---|---|---|
| 0 | Built-ins | definition | n/a | n/a | none | `packages/tui/src/plugin/context.tsx:315` |
| 1 | Discovered directories | absolute path | true | true | none | `packages/tui/src/plugin/context.tsx:292` |
| 2 | Server listing (active, `features.tui`, source `package` or `local`) | `source.target` or `source.path` | false | true | none: the entry is a string | `packages/tui/src/plugin/context.tsx:301` |
| 3 | `cli.json` `plugins` | string or `{ package, options }` | true | false | from the object form | `packages/tui/src/plugin/context.tsx:306` |

The merge rule is in `packages/tui/src/plugin/discovery.ts:55` and tested in `packages/tui/test/plugin-discovery.test.ts:12`.

### Discovery and `cli.json`

| Fact | Pin |
|---|---|
| Discovery roots are `<global-config>` plus `.opencode` from the project root down to the cwd, each with `plugins` appended. The project root is the deepest ancestor of the cwd with `.git` or `.hg`, else the cwd. | `packages/tui/src/plugin/discovery.ts:11`, `packages/tui/src/util/config-directories.ts:15` |
| Only immediate directories and symlinks to directories count, sorted by name within each root. Direct `.ts` and `.js` files are ignored. | `packages/tui/src/plugin/discovery.ts:35`, `packages/tui/src/plugin/discovery.ts:36` |
| A discovered directory with no TUI entry is skipped silently, because discovery is `optional`. The roots use the client's cwd and global config, whatever server is connected. | `packages/tui/src/plugin/context.tsx:362`, `packages/tui/src/app.tsx:232` |
| `cli.json` is `<global-config>/cli.json`. There is one, it is global. An entry is a string, or `{ package: string, options?: Record<string, any> }`. | `packages/cli/src/config/config.ts:31`, `packages/tui/src/config/index.tsx:47` |
| `OPENCODE_CLI_CONFIG_CONTENT` merges inline JSON over the file. An array in it replaces the file's array. | `packages/cli/src/config/config.ts:32`, `packages/cli/src/config/config.ts:130` |
| Relative entries resolve against the directory of `cli.json`, not the cwd. `./`, `../`, absolute and `file://` entries are local. Anything else is a package. | `packages/tui/src/plugin/context.tsx:104`, `packages/tui/src/plugin/context.tsx:333`, `packages/plugin/src/source.ts:61` |
| The config directory is watched; a change to `plugins` triggers a reconcile. | `packages/tui/src/config/index.tsx:361`, `packages/tui/src/plugin/context.tsx:529` |

### How one entry is processed, in order

| Step | Condition on the target | Result | Pin |
|---|---|---|---|
| 1 | Starts with `-` | Disable every plugin already in the list that matches. | `packages/tui/src/plugin/context.tsx:321` |
| 2 | Matches a listed id, is `*`, ends in `.*`, or starts with `opencode.` | Enable matches. Never load anything. | `packages/tui/src/plugin/context.tsx:326` |
| 3 | Local path to a single file | Skip. | `packages/tui/src/plugin/context.tsx:334` |
| 4 | Anything else | Resolve and import. | `packages/tui/src/plugin/context.tsx:348` |

Step 2 means a package whose name starts with `opencode.` cannot load from `cli.json`. Selectors match the TUI part's own `id`, not the package name (`packages/tui/src/plugin/context.tsx:648`).

Entrypoint resolution: a package, or a local directory whose `package.json` has `name` and `exports`, resolves `<name>/tui` through `exports`. Any other local directory uses `<dir>/tui` with the extension inferred; Node tries `.ts .tsx .js .jsx .mts .mjs .cts .cjs` (`packages/plugin/src/host.ts:33`, `packages/plugin/src/host.ts:28`, `packages/plugin/src/host.ts:35`, `packages/util/src/runtime/import.node.ts:41`).

### Outcomes

| State | When | User sees | Pin |
|---|---|---|---|
| `active` / `inactive` | Loaded; enabled or disabled by a directive. | Row in `/plugins`. | `packages/tui/src/plugin/context.tsx:467` |
| `unsupported` | No TUI entry. Discovered and server entries drop out. `cli.json` entries record the state. | Nothing: no toast, and `/plugins` hides it. | `packages/tui/src/plugin/context.tsx:362`, `packages/tui/src/feature-plugins/system/plugins.tsx:58` |
| `failed` | Import, shape or setup error. | Toast `Plugin failed: <target>` once, plus a `/plugins` row. A failed package resolve is remembered until the config changes, so watch events do not repeat an install. | `packages/tui/src/plugin/context.tsx:473`, `packages/tui/src/plugin/context.tsx:279` |

## 3. Remote server

The server listing carries no code and no options, only `id`, `source`, `features`, `state` (`packages/schema/src/plugin.ts:51`). The TUI part still has to exist on the client.

| Source | Same machine | Remote server | Pin |
|---|---|---|---|
| `cli.json` package | Installs and loads. | Installs and loads on the client. | `packages/tui/src/plugin/context.tsx:306` |
| `cli.json` local path | Loads. | Loads from the client's disk. | `packages/tui/src/plugin/context.tsx:343` |
| Discovered directory | Loads. | Loads from the client's disk. | `packages/tui/src/app.tsx:232` |
| Server-listed package | Loads. Server and CLI share `<cache>/npm/<key>`. | No download. Loads only if already in the client's cache. Otherwise skipped with no message. | `packages/tui/src/plugin/context.tsx:303`, `packages/cli/src/commands/handlers/default.ts:143`, `packages/util/src/npm.ts:349`, `packages/util/src/npm.ts:139` |
| Server-listed local path | Loads. | The server's path is tried on the client's disk. Skipped with no message if absent. | `packages/tui/src/plugin/context.tsx:302`, `packages/tui/src/plugin/context.tsx:343` |

- The silent skip is `npm.resolve` returning a missing directory, `Host.resolve` finding no `tui`, then `optional` (inference for the resolver's error code on the missing directory; the rest is read).
- To get a combined plugin's TUI part on a remote server, list the package in `cli.json` too. That entry has `install: true` and wins the merge.
- The listing is fetched on default-location change, `plugin.updated` and `server.connected`. A fetch failure is ignored. A server part that failed hides the TUI part too, because the filter requires `state.status === "active"` (`packages/tui/src/plugin/context.tsx:539`, `packages/tui/src/plugin/context.tsx:563`, `packages/tui/src/plugin/context.tsx:569`, `packages/tui/src/plugin/context.tsx:99`).
- `context.client` and `context.data` talk to the connected server. Plugin code and its `fs` calls run on the client, while `context.location.directory` names a path on the server (inference).

## 4. Definition and lifecycle

```ts
// packages/plugin/src/tui/plugin.ts
export type Cleanup = () => Promise<void> | void
export interface Definition {
  readonly id: string
  readonly setup: (context: Context) => Promise<Cleanup | void> | Cleanup | void
}
```

There is no `reload` field. A hot reload is a deactivate followed by a fresh `setup` with a new context.

| Topic | Rule | Pin |
|---|---|---|
| `Plugin.define` and module check | `define` returns its argument and validates nothing. The loader needs a default export with a non-empty string `id` and a function `setup`. Else `Invalid V2 TUI plugin module: <spec>`. | `packages/plugin/src/tui/plugin.ts:12`, `packages/tui/src/plugin/context.tsx:694`, `packages/tui/src/plugin/context.tsx:741` |
| `id` scope | Independent of the server part's id. Used for selectors, routes and storage keys. A later plugin with the same `id` replaces the earlier and keeps its position, built-ins included. | `packages/tui/src/plugin/context.tsx:315`, `packages/tui/src/plugin/context.tsx:390` |
| `id` characters | `storage.store` throws unless `plugin.<id>.<key>` matches `^[a-zA-Z0-9][a-zA-Z0-9._-]*$`. `@scope/name` fails. | `packages/tui/src/context/storage.tsx:43` |
| Setup order | Built-ins, then entries. Each `setup` is awaited before the next. | `packages/tui/src/plugin/context.tsx:428` |
| Startup gate | The route area and `app` slot render only after the first reconcile. A slow `setup` holds `Loading plugins…`. A stall is only logged, at 5 s. A missing `cli.json` package is installed inside that reconcile, so it also holds the gate (inference). | `packages/tui/src/app.tsx:1438`, `packages/tui/src/component/startup-loading.tsx:8`, `packages/tui/src/plugin/context.tsx:119`, `packages/tui/src/plugin/context.tsx:669` |
| During `setup` | The plugin is not active yet. Slots do not render, `ui.panel.open` returns false, and an unregister is a no-op that leaves the contribution in place, because it checks `active()`. | `packages/tui/src/plugin/context.tsx:198`, `packages/tui/src/plugin/context.tsx:510`, `packages/tui/src/plugin/api.tsx:232`, `packages/tui/src/plugin/api.tsx:140` |
| Setup throws | Everything registered so far is disposed, contributions cleared, previous version restored if there was one. | `packages/tui/src/plugin/context.tsx:639`, `packages/tui/src/plugin/context.tsx:446` |
| Cleanup | Owned items run in reverse. The returned cleanup was pushed last, so it runs first. If one throws, the rest still run, with toast `<id>: cleanup failed: ...`. | `packages/tui/src/plugin/context.tsx:194`, `packages/tui/src/plugin/context.tsx:635`, `packages/tui/src/plugin/context.tsx:235` |
| Auto-removed | Slots, routes, Markdown renderers, keymap layers, this plugin's panel. | `packages/tui/src/plugin/api.tsx:99`, `packages/tui/src/plugin/api.tsx:143`, `packages/tui/src/plugin/api.tsx:147` |
| Not auto-removed | `data.on`, `data.listen`, timers, renderer listeners. `data` is passed through unwrapped. Return a cleanup. | `packages/tui/src/plugin/api.tsx:160` |
| Solid owner | `setup` is awaited inside a promise chain, so a bare `createEffect` there has no owner (inference). Built-ins render a component into the `app` slot instead. | `packages/tui/src/feature-plugins/system/plugins.tsx:331`, `packages/tui/src/feature-plugins/system/plugins.tsx:354` |
| `options` | Deep-cloned snapshot. A change restarts the plugin. | `packages/tui/src/plugin/context.tsx:737`, `packages/tui/src/plugin/context.tsx:730` |

### Reload

| Trigger | What happens | Pin |
|---|---|---|
| Save under a local plugin (root watched; every resolved local import tracked) | Debounced 100 ms. Content hash decides. Only that plugin restarts. | `packages/tui/src/plugin/context.tsx:256`, `packages/plugin/src/source.ts:13` |
| Membership or order change | Every plugin restarts, to keep slot order. | `packages/tui/src/plugin/context.tsx:404` |
| Package plugin on disk changes | No reload: "Package entrypoints never change within a session". Restart the TUI after `opencode plugin update`. | `packages/tui/src/plugin/context.tsx:663` |
| Import or setup fails | Previous version keeps running, or is reactivated. An import failure message ends `(previous version still active)`. A setup failure is remembered per version and options. | `packages/tui/src/plugin/context.tsx:367`, `packages/tui/src/plugin/context.tsx:449`, `packages/tui/src/plugin/context.tsx:378` |
| `/plugins` toggle | Activates or deactivates now. Not saved. The next reconcile restores what the config says. | `packages/tui/src/feature-plugins/system/plugins.tsx:124`, `packages/tui/src/plugin/context.tsx:419` |

## 5. Context members

Types: `packages/plugin/src/tui/context.ts:544`. Implementation: `packages/tui/src/plugin/api.tsx:152`.

| Member | What it is | When it applies | Pin |
|---|---|---|---|
| `options` | Options for this entry, or `{}`. | Filled only by the `cli.json` object form. Never from `opencode.json`. | `packages/tui/src/plugin/api.tsx:153`, `packages/tui/src/plugin/context.tsx:332` |
| `location` | Getter for the TUI's current location info. Typed `LocationRef \| undefined`. | Undefined until that location's info has synced. Real value is `Location.PublicInfo`, which omits `workspaceID`. | `packages/tui/src/plugin/api.tsx:154`, `packages/tui/src/context/location.tsx:21`, `packages/schema/src/location.ts:29` |
| `app` | `{ version, channel }`, fixed at creation. | Always. | `packages/tui/src/plugin/api.tsx:157` |
| `renderer` | OpenTUI `CliRenderer` shared with the host. | Always. | `packages/tui/src/plugin/api.tsx:158` |
| `client` | Generated client for the connected server. | Read once at activation. A managed reconnect swaps the host's client and the plugin keeps the old one (inference). | `packages/tui/src/plugin/api.tsx:159`, `packages/tui/src/context/client.tsx:36` |
| `data` | Shared reactive store. See 5.2. | Always. | `packages/tui/src/plugin/api.tsx:160` |
| `attention` | `notify()`. See 5.4. | Off unless the user enabled attention. | `packages/tui/src/plugin/api.tsx:161` |
| `theme` | Getter, current `ResolvedTheme`. | Read it inside JSX to follow theme changes. | `packages/tui/src/plugin/api.tsx:162` |
| `themeMode` | Getter, `"dark"` or `"light"`. | As above. | `packages/tui/src/plugin/api.tsx:165` |
| `markdown` | `registerCodeBlockRenderer`. See 9. | Until unregistered or deactivated. | `packages/tui/src/plugin/api.tsx:168` |
| `keymap` | Layers, dispatch, modes. See 8. | Until deactivated. | `packages/tui/src/plugin/api.tsx:179` |
| `storage` | `store`, `memory`. See 5.3. | Keys prefixed `plugin.<id>.`. | `packages/tui/src/plugin/api.tsx:200` |
| `ui` | See 5.1. | Always. | `packages/tui/src/plugin/api.tsx:204` |

`usePlugin()` returns this context inside any route, slot or dialog the plugin renders. Outside one it throws `PluginContextProvider is missing` (`packages/plugin/src/tui/solid.ts:17`, `packages/tui/src/plugin/api.tsx:104`).

### 5.1 `ui`

| Member | What it does | When it applies | Pin |
|---|---|---|---|
| `dialog.show(render, onClose?)` | Replaces whatever dialog is open. Resets size to medium and centered to false. | Previous dialog's `onClose` fires. | `packages/tui/src/plugin/api.tsx:334`, `packages/tui/src/ui/dialog.tsx:400` |
| `dialog.set({ size?, centered? })` | Sets presentation. A missing key resets it. Sizes: medium 60, large 88, xlarge 116. | Call after `show`, or from inside the dialog. | `packages/tui/src/plugin/api.tsx:337`, `packages/tui/src/ui/dialog.tsx:30`, `packages/tui/src/feature-plugins/prompt/btw.tsx:71` |
| `dialog.clear()` | Closes all, fires `onClose`, resets presentation. | Any time. | `packages/tui/src/ui/dialog.tsx:389` |
| `dialog.alert`, `confirm`, `prompt` | Promises. `alert` resolves on confirm or close. `confirm` gives `true`, `false`, or `undefined` if dismissed; takes `label.confirm`, `label.cancel`. `prompt` gives a string, or `undefined` if dismissed; takes `description`, `placeholder`, `value`. | | `packages/tui/src/plugin/api.tsx:344`, `packages/tui/src/plugin/api.tsx:350`, `packages/tui/src/plugin/api.tsx:367` |
| `dialog.select` | Value, or `undefined` if dismissed. `search` gets only enabled options and runs for every query. | Actions do not settle the promise. | `packages/tui/src/plugin/api.tsx:387` |
| select `actions` and keys | Actions fire from their binding or a footer click. Tab does not focus them: Tab then Enter selects the option. `dialog.select.prev` is `up,ctrl+p` and `next` is `down,ctrl+n`, so do not bind those. | `selection: "none"` for no selection. | `packages/plugin/src/tui/context.ts:364`, `packages/tui/test/plugin-select.test.tsx:269`, `packages/tui/src/config/keybind.ts:261` |
| `toast.show` | `title`, `message`, `variant` (default info), `duration` (default 5000 ms). With `sessionID`, if that session's family is not open, the title defaults to the session title and an `Open` action is added. | | `packages/tui/src/plugin/api.tsx:109`, `packages/tui/src/ui/toast.tsx:168`, `packages/tui/src/plugin/api.tsx:116` |
| `format.path(value)` | Abbreviates the home directory. | Client's home (inference on a remote server). | `packages/tui/src/plugin/api.tsx:208` |
| `router.*` | See 7. | | `packages/tui/src/plugin/api.tsx:210` |
| `panel.open(name, { presentation? })` | Opens `session.panel` for the current session. Replaces any open panel, from any plugin. | False if not on a session route, or during `setup`. | `packages/tui/src/plugin/api.tsx:231`, `packages/tui/src/context/panel.tsx:23` |
| `panel.close()`, `panel.current()` | `close` closes only this plugin's panel. `current` is this plugin's `{ name, sessionID }`, else undefined, and is reactive. | | `packages/tui/src/plugin/api.tsx:238`, `packages/tui/src/context/panel.tsx:34`, `packages/tui/src/plugin/api.tsx:239` |
| `tabs.enabled()`, `tabs.list()` | `enabled`: true for mode `on`, or `auto` unless `HERDR_ENV=1`. `list`: `sessionID`, `title?`, `active`, `busy`, `attention`, `unread?`, reactive. | Default mode is `auto`. | `packages/tui/src/config/index.tsx:331`, `packages/plugin/src/tui/context.ts:513`, `packages/tui/src/plugin/api.tsx:247` |
| `tabs.open`, `focus`, `move`, `close` | `open` opens without focus; `focus` opens and navigates. All return false when tabs are off; `move` and `close` also when there is no such tab. `close()` with no argument closes the active tab. | `move` maps to the root session; `close` does not. | `packages/tui/src/plugin/api.tsx:257`, `packages/tui/src/plugin/api.tsx:262`, `packages/tui/src/plugin/api.tsx:267`, `packages/tui/src/plugin/api.tsx:274` |
| `model.current()`, `model.variant.list`, `model.variant.set` | `current`: the prompt's `{ providerID, modelID, variant? }`, reactive. `set(undefined)` picks the default; false if no model or unknown variant. | | `packages/tui/src/plugin/api.tsx:283`, `packages/tui/src/plugin/api.tsx:288` |
| `slot(claim)` | See 6. | | `packages/tui/src/plugin/api.tsx:298` |

### 5.2 `data`

It is `createData` from `@opencode/client/solid`. The host object has more members than the type; only the type is API (`packages/tui/src/context/data.tsx:22`, `packages/plugin/src/tui/context.ts:63`). Reads are Solid store reads. `sync` fetches and is keyed; `invalidate` marks stale. A disconnect invalidates everything (`packages/client/src/solid/data.ts:2145`).

| Member | Behavior | Before sync | Pin |
|---|---|---|---|
| `on(type, handler)`, `listen(handler)` | `on`: one typed event. `listen`: every event, as `{ details }`. Both return unsubscribe. | n/a | `packages/client/src/solid/data.ts:1497`, `packages/client/src/solid/data.ts:1498` |
| `session.list()`, `get`, `root`, `family` | `list`: known sessions, newest update first. The rest are lookup and hierarchy. | Partial list; undefined, self, `[]` | `packages/client/src/solid/data.ts:318`, `packages/client/src/solid/data.ts:1503`, `packages/client/src/solid/data.ts:1526` |
| `session.cost(id)`, `session.status(id)` | `cost`: root is the sum of the family, child is its own, unknown is 0. `status`: `"idle"` or `"running"`. | 0, `"idle"` | `packages/client/src/solid/data.ts:1539`, `packages/client/src/solid/data.ts:1548` |
| `session.sync`, `invalidate`; `session.pending.*`, `session.message.*`, `session.permission.*` | Session record, then per-session collections: `list`, `sync`, `invalidate`, plus `message.get`. | pending `[]`, permission undefined | `packages/plugin/src/tui/context.ts:81`, `packages/plugin/src/tui/context.ts:76`, `packages/plugin/src/tui/context.ts:83`, `packages/client/src/solid/data.ts:1926` |
| `session.form.*` | `list`, `sync`, `invalidate`, `reply`, `cancel`. `location` matters only for the id `"global"`, used by MCP elicitations. | undefined | `packages/client/src/solid/data.ts:1955`, `packages/client/src/solid/data.ts:96` |
| `project.list`, `get`, `sync`, `invalidate`; `project.permission.*` | Non-archived projects, most recently active first. Saved permissions per project. | `[]`; undefined | `packages/client/src/solid/data.ts:2006`, `packages/client/src/solid/data.ts:2024` |
| `shell.list(location?)`, `shell.get(id)` | Shells at a location. `get` searches every location. | `[]`, undefined | `packages/client/src/solid/data.ts:2039`, `packages/client/src/solid/data.ts:2047` |
| `location.default()` | The server-resolved default location. | Always set | `packages/client/src/solid/data.ts:2059` |
| `location.sync(ref?)`, `location.invalidate(ref?)` | Info, vcs, all collections, shells, global forms. | n/a | `packages/client/src/solid/data.ts:2074`, `packages/tui/src/context/data.tsx:28`, `packages/client/src/solid/data.ts:2092` |
| `location.vcs.info(ref?)` | `{ provider?, branch: { current?, default? } }`. | undefined | `packages/client/src/promise/generated/types.ts:939` |
| `location.agent`, `command`, `integration`, `mcp.server`, `mcp.resource`, `model`, `provider`, `reference`, `skill` | Each has `list`, `sync`, `invalidate`. | undefined | `packages/plugin/src/tui/context.ts:55`, `packages/client/src/solid/data.ts:1463` |

### 5.3 `storage`

| Member | Behavior | Pin |
|---|---|---|
| `store(key, { initial })` | File `<state>/<channel>/tui/plugin.<id>.<key>.json`. `initial` is used only if the file is unreadable. A repeat call with the key returns the first entry and ignores the new `initial`. | `packages/tui/src/context/storage.tsx:52`, `packages/tui/src/context/storage.tsx:62`, `packages/tui/src/context/storage.tsx:59` |
| store update and sync | Update is async: it takes a file lock, re-reads the file, applies your mutation, writes atomically. Values must be JSON. Other TUI instances reload on a directory watch, 50 ms debounce. | `packages/tui/src/context/storage.tsx:72`, `packages/tui/src/context/storage.tsx:115` |
| `memory(key, { initial })` | In-process. Synchronous update. Values need not be JSON. Gone on exit. Both kinds survive a plugin reload, because entries are memoized above the plugin. | `packages/tui/src/context/storage.tsx:95`, `packages/tui/src/context/storage.tsx:59`, `packages/tui/src/context/storage.tsx:96` |

### 5.4 `attention.notify`

| Rule | Pin |
|---|---|
| `attention.notifications` and `attention.sound` default to false, so by default it returns `{ ok: false, skipped: "attention_disabled" }`. A plugin cannot override this. | `packages/tui/src/config/index.tsx:307`, `packages/tui/src/attention.ts:131` |
| Notification `when` defaults to `blurred`, sound `when` to `always`. Focus is `unknown` until the first focus event; `focused` and `blurred` then skip with `focus_unknown`. | `packages/tui/src/attention.ts:138`, `packages/tui/src/attention.ts:156`, `packages/tui/src/attention.ts:90`, `packages/tui/src/attention.ts:80` |
| `message` is required after cleanup, or `skipped: "empty_message"`. Title capped at 80, message at 240. Volume is clamped to 0..1 and defaults to config (0.4). Unknown sound names become `default`. | `packages/tui/src/attention.ts:36`, `packages/tui/src/attention.ts:135`, `packages/tui/src/attention.ts:65`, `packages/tui/src/attention.ts:157`, `packages/tui/src/config/index.tsx:309` |

## 6. Slots

Types: `packages/plugin/src/tui/context.ts:191`. Plugins cannot mount new slots (`packages/tui/src/plugin/render.tsx:107`).

| Path | Input | Mounted when | Default occupants | Pin |
|---|---|---|---|---|
| `app` | none | After the first reconcile. Below the route area. | Renderless command components | `packages/tui/src/app.tsx:1466` |
| `home.footer` | none | Home route. | `opencode.home.footer` | `packages/tui/src/routes/home.tsx:107` |
| `home.footer.status` | none | Inside that built-in's view: it must be active and not replaced, and the terminal at least 44 by 14. | none | `packages/tui/src/feature-plugins/home/footer.tsx:95`, `packages/tui/src/feature-plugins/home/footer.tsx:82` |
| `prompt.footer` | `sessionID?`, `mode`, `showDetails` | Every prompt, home and session. | `opencode.prompt.footer` | `packages/tui/src/component/prompt/index.tsx:1901`, `packages/tui/src/component/prompt/index.tsx:1611` |
| `prompt.footer.status` | same | Inside `prompt.footer`. | Host spinner or location, `opencode.btw` | `packages/tui/src/component/prompt/index.tsx:1902` |
| `prompt.footer.file` | same | Inside `prompt.footer`. | Host editor file label | `packages/tui/src/component/prompt/index.tsx:1969` |
| `session.composer.top` | `sessionID` | Session route, above the composer. | none | `packages/tui/src/routes/session/index.tsx:1597` |
| `session.panel` | `PanelInput` | Only while a panel is open for the session shown. | `opencode.diffs` | `packages/tui/src/component/panel-host.tsx:36`, `packages/tui/src/component/session-frame.tsx:88` |
| `sidebar.content` | `sessionID` | Sidebar visible: not a child session, and opened or `auto` with width over 120. | `opencode.sidebar.context`, `.limit`, `.mcp`, `.todo` | `packages/tui/src/routes/session/sidebar.tsx:70`, `packages/tui/src/component/session-frame.tsx:107` |
| `sidebar.footer` | `sessionID` | Same. | `opencode.sidebar.footer` | `packages/tui/src/routes/session/sidebar.tsx:75` |

| Placement | Effect | Pin |
|---|---|---|
| `prepend` / `append` | First or last inside the boundary, around the host's children. | `packages/tui/src/plugin/render.tsx:146` |
| `before` / `after` | Siblings outside the boundary. Not suppressed by a replace of that same target. | `packages/tui/src/plugin/render.tsx:138`, `packages/tui/src/plugin/structure.ts:120` |
| `replace` | Takes over the target. Inside claims and descendants are suppressed. | `packages/tui/src/plugin/render.tsx:141` |

| Rule | Pin |
|---|---|
| `slot()` throws unless the claim has exactly one placement key. It returns an unregister function. | `packages/tui/src/plugin/api.tsx:304` |
| Same anchor: claims coexist in enable order. Same `replace` target: last enabled wins. A replacement on an ancestor beats one on a descendant, whatever the order. | `packages/tui/src/plugin/context.tsx:505`, `packages/tui/src/plugin/structure.ts:81`, `packages/tui/src/plugin/structure.ts:91` |
| A claim on an unmounted path: additive claims of any kind append to the nearest mounted ancestor; with none they are dropped. `replace` is dropped. So a `home.footer.status` claim on a tiny terminal can render in `home.footer` (inference). | `packages/tui/src/plugin/structure.ts:77`, `packages/tui/src/plugin/structure.ts:130`, `packages/tui/src/plugin/structure.ts:139` |
| Containment is by path prefix. `app` is not an ancestor of anything else. | `packages/tui/src/plugin/structure.ts:53` |
| `suppressed` and `degraded` are computed, but only `.slotted` is read, so a suppressed claim is just absent (grep). | `packages/tui/src/plugin/render.tsx:115` |
| `render` runs once, untracked. The input stays reactive through a merged getter, so read `props.x`; destructuring freezes it (inference). | `packages/tui/src/plugin/render.tsx:128` |

### Session panels

| Rule | Pin |
|---|---|
| Only one panel exists at a time, across all plugins. The selected `name` goes to every contribution; each decides whether to render. A name with no matching contribution shows an empty pane. | `packages/tui/src/context/panel.tsx:12`, `packages/tui/src/component/panel-host.tsx:39`, `packages/tui/src/component/panel-host.tsx:36` |
| `presentation` is forced to `fullscreen` below width 108. `toggleFullscreen` does nothing there. | `packages/tui/src/context/panel.tsx:16`, `packages/tui/src/context/panel.tsx:39`, `packages/tui/src/ui/layout.ts:9` |
| Selecting a terminal closes the panel. Opening a panel deselects the terminal. `PanelInput.close` closes whichever panel is open; `ui.panel.close` closes only your own. | `packages/tui/src/component/session-frame.tsx:93`, `packages/tui/src/component/panel-host.tsx:51`, `packages/tui/src/plugin/api.tsx:238` |
| Layers created inside the panel are enabled only while it is focused. A mode pushed with no Solid owner, such as after an `await`, is not gated by that focus. | `packages/tui/src/component/panel-host.tsx:60`, `packages/tui/src/context/keymap.tsx:216`, `packages/tui/src/context/interactivity.tsx:18`, `packages/tui/src/context/keymap.tsx:197` |

## 7. Routes

| Item | Behavior | Pin |
|---|---|---|
| `Route`, `Destination`, `Page` | `Route` is `{ type: "home" }`, `{ type: "session", sessionID }`, or `{ type: "plugin", id, name, data? }`. `Destination` is a `Route`, or a plugin route without `id`. `Page` is `{ name, render({ data }) }`. | `packages/plugin/src/tui/context.ts:142`, `packages/plugin/src/tui/context.ts:152`, `packages/plugin/src/tui/context.ts:154` |
| `router.register(page)` | Throws `Route already registered: <name>` on a duplicate within the plugin. Returns unregister. | `packages/tui/src/plugin/api.tsx:212` |
| `router.navigate(dest)` | A plugin destination with no `id` uses this plugin's `id`. Passing `id` reaches another plugin's route. | `packages/tui/src/plugin/api.tsx:220` |
| `router.current()` | The live route store. It may carry host-only fields such as `prompt`. | `packages/tui/src/plugin/api.tsx:226`, `packages/tui/src/context/route.tsx:7` |
| Rendering | Keyed on route and render function, so navigation or hot reload rebuilds it and clears a crash. A missing page shows `PluginRouteMissing` with a way home. | `packages/tui/src/plugin/render.tsx:75`, `packages/tui/src/app.tsx:1458` |

## 8. Commands and keymap

Commands are registered through `context.keymap.layer(() => KeymapLayer)`. There is no other registration API.

### `KeymapLayer`

| Field | Behavior | Pin |
|---|---|---|
| `mode` | Default `base`. `"global"` opts out of modes. Host modes include `modal` while any dialog is open, plus `autocomplete`, `composer`, `menu`. A base layer is off in those. | `packages/tui/src/context/keymap.tsx:217`, `packages/tui/src/ui/dialog.tsx:322`, `packages/tui/src/component/prompt/autocomplete.tsx:116`, `packages/tui/src/routes/session/composer/index.tsx:61` |
| `enabled` | Boolean or function. ANDed with the surrounding interactivity. | `packages/tui/src/context/keymap.tsx:216` |
| `target`, `priority` | `target` limits the layer to a focused renderable. `priority` resolves conflicts with other layers. | `packages/plugin/src/tui/context.ts:441`, `packages/plugin/src/tui/context.ts:443` |
| `commands` | See below. | `packages/tui/src/context/keymap.tsx:218` |
| `bindings` | IDs whose `keybinds` config entries should be active here. | `packages/tui/src/context/keymap.tsx:258` |

Lifetime: `layer()` works from `setup` (also after `await`) or from a component. It is removed on deactivation or when the creating owner is disposed; after deactivation `layer()` is a no-op. The factory runs once untracked to validate, so shape errors throw from `layer()`. It then runs reactively, and later errors follow Solid's handling (`packages/tui/src/plugin/api.tsx:185`, `packages/tui/src/plugin/api.tsx:182`, `packages/tui/src/plugin/api.tsx:189`, `packages/tui/src/plugin/api.tsx:184`, `packages/plugin/src/tui/context.ts:465`).

### `KeymapCommand`

A command with `id` is named. Without `id` it is inline.

| Field | Named | Inline | Pin |
|---|---|---|---|
| `id` | Non-empty. Else throws. | Absent. | `packages/tui/src/context/keymap.tsx:295` |
| `title`, `description`, `group` | Shown in discovery UI. | Used as binding description. | `packages/tui/src/context/keymap.tsx:233`, `packages/tui/src/context/keymap.tsx:246` |
| `enabled` | Boolean or function. | Checked in the binding; if off, returns false. | `packages/tui/src/context/keymap.tsx:242` |
| `bind` | `false`: none. A `keybinds` entry for the id wins over the string. | Required non-empty string. | `packages/tui/src/context/keymap.tsx:252`, `packages/tui/src/context/keymap.tsx:303` |
| `palette: true`, `suggested` | Lists it in the palette. `suggested` promotes it to the suggested group. | `palette` throws `Palette commands require an ID`. | `packages/tui/src/component/command-palette.tsx:19`, `packages/tui/src/component/command-palette.tsx:29`, `packages/tui/src/context/keymap.tsx:301` |
| `slash` | `{ name, aliases?, arguments? }`. Adds `/name` to completion. With `arguments: true`, selecting inserts `/name` in the prompt; submit clears the prompt and calls `run(rawInput)`. | Throws `Slash commands require an ID`. | `packages/tui/src/component/prompt/autocomplete.tsx:493`, `packages/tui/src/component/prompt/autocomplete.tsx:498`, `packages/tui/src/component/prompt/index.tsx:1150`, `packages/tui/src/context/keymap.tsx:302` |
| `run` | `run(input, event)`. Returning `false` continues keyboard dispatch. | `run()`, no arguments: `event` is always undefined. Returning `false` continues too. | `packages/tui/src/context/keymap.tsx:232`, `packages/tui/src/context/keymap.tsx:244`, `packages/plugin/src/tui/context.ts:431` |

`keybinds` is a closed schema of built-in names, and `parse` throws on unknown names. So plugin command IDs cannot be rebound in `cli.json`, and `bindings: ["acme.x"]` finds nothing, despite the type comment "Stable command and config keybind identifier" (inference on how the decoder treats excess keys) (`packages/tui/src/config/keybind.ts:308`, `packages/tui/src/config/keybind.ts:342`, `packages/plugin/src/tui/context.ts:408`).

### Other `keymap` members

| Member | Behavior | Pin |
|---|---|---|
| `dispatch(id, input?)` | Runs a reachable command. `input` reaches `run`. No key event. | `packages/tui/src/context/keymap.tsx:69` |
| `shortcuts(id)` | Formatted shortcuts for a registered command. | `packages/tui/src/context/keymap.tsx:343` |
| `commands()` | Reachable commands, reactive. Each `run` wraps `dispatch`. | `packages/tui/src/context/keymap.tsx:359` |
| `pending()`, `active()`, `mode.current()`, `mode.push(mode)` | Pending sequence and next-key bindings, reactive. Top enabled mode. `push` returns a pop function. | `packages/tui/src/context/keymap.tsx:408`, `packages/tui/src/context/keymap.tsx:462`, `packages/tui/src/context/keymap.tsx:474` |

Built-in ids, usable in `-id` directives: `opencode.home.footer`, `opencode.prompt.footer`, `opencode.btw`, `opencode.sidebar.context`, `.limit`, `.mcp`, `.todo`, `.footer`, `opencode.notifications`, `opencode.plugins`, `opencode.stats`, `opencode.merman`, `opencode.latex`, `opencode.diffs` (`packages/tui/src/plugin/builtins.ts:17`). `opencode.storybook` exists only under `OPENCODE_STORY`.

## 9. Renderers

| Item | Behavior | Pin |
|---|---|---|
| `markdown.registerCodeBlockRenderer(language, render)` | Registers a fenced-code renderer. Returns unregister. | `packages/plugin/src/tui/context.ts:555` |
| Language and duplicates | Normalized by `infoStringToFiletype`; an empty result throws. Same plugin and language throws. Across plugins, last in enable order wins. | `packages/tui/src/plugin/api.tsx:170`, `packages/tui/src/plugin/api.tsx:172`, `packages/tui/src/plugin/markdown.ts:9` |
| Signature and cost | `MarkdownCodeBlockRenderer` from `@opentui/core`. Called as `(token, render)`, with `token.text` and `render.defaultRender()` in repo use. Changing the effective set rebuilds every Markdown block. | `packages/latex/src/markdown.ts:32`, `packages/tui/src/plugin/markdown.ts:8` |
| Built-in | `mermaid` from `opencode.merman`; `latex` and `math` from `opencode.latex`. | `packages/merman/src/plugin.ts:8`, `packages/latex/src/plugin.ts:11` |
| JSX render points | Slot `render`, `Page.render`, `dialog.show`. All wrapped for `usePlugin()`. | `packages/tui/src/plugin/api.tsx:215`, `packages/tui/src/plugin/api.tsx:309`, `packages/tui/src/plugin/api.tsx:335` |

## 10. Package, dependencies, rendering

### Minimal shapes

```jsonc
// package.json of a package with a TUI part
{
  "name": "opencode-acme-plugin",
  "type": "module",
  "exports": { "./tui": "./src/tui.tsx" },
  "dependencies": { "@opencode/plugin": "latest" },
  "peerDependencies": {
    "@opentui/core": ">=0.8.1",
    "@opentui/solid": ">=0.8.1",
    "solid-js": ">=1.9.0"
  }
}
```

```tsx
// src/tui.tsx
import { Plugin } from "@opencode/plugin/tui"

export default Plugin.define({
  id: "acme.tui",
  setup(context) {
    return context.ui.slot({ append: "home.footer.status", render: () => <text>ACME</text> })
  },
})
```

A local directory needs no `package.json`: a root `tui.tsx` is enough, as the repo's fixtures show (`packages/tui/test/fixture/plugin/native-resources/tui.tsx:6`). A package listed only in `cli.json` needs no server part; with no server or GUI part it must not go in `opencode.json`, where the server fails it with `Plugin entrypoint not found` (`packages/core/src/plugin/module.ts:124`).

### Dependencies

| Package | Why | At runtime on the Bun build | Pin |
|---|---|---|---|
| `@opencode/plugin`, `effect` | `Plugin`, `usePlugin`, types; `effect` only if used. | Host's copy, through `Bun.plugin` virtual modules. A copy loaded from the plugin's `node_modules` throws `... is not provided by OpenCode`. | `packages/plugin/src/runtime.ts:21`, `packages/plugin/src/runtime.ts:32`, `packages/plugin/src/runtime-modules.ts:7` |
| `@opentui/core`, `@opentui/solid`, `solid-js` | JSX and resources. Optional peers at `>=0.8.1` and `>=1.9.0`; the repo pins OpenTUI at 0.8.1. | Host's copy through `ensureRuntimePluginSupport` (inference: its source is not in the clone). | `packages/plugin/package.json:54`, `package.json:57`, `packages/tui/src/plugin/runtime-plugin-support.bun.ts:6` |
| `@opencode/theme` | Optional peer. Gives `ResolvedTheme` its type; `generateSyntax(theme, owner)` is a runtime import. | Not in the host's provided list, so it comes from the plugin's own install (inference). | `packages/plugin/package.json:53`, `packages/plugin/src/tui/context.ts:26`, `packages/theme/src/tui/syntax.ts:4` |

- Install uses Arborist with `ignoreScripts: true`, so a `postinstall` build does not run (`packages/util/src/npm.ts:224`).
- The repo's own TSX config is `"jsx": "preserve"`, `"jsxImportSource": "@opentui/solid"` (`packages/tui/tsconfig.json:6`).

### How it renders

| Topic | Fact | Pin |
|---|---|---|
| Stack | Solid components on OpenTUI, inside the host's single renderer. | `packages/tui/src/plugin/api.tsx:67` |
| Source form, Bun build | `.tsx` is compiled at import by OpenTUI's runtime transform (inference from the name and the comment beside it). | `packages/tui/src/plugin/runtime-plugin-support.bun.ts:6`, `packages/tui/src/plugin/runtime-plugin-support.node.ts:1` |
| Node build (`@opencode/cli-node`, command `opencode-node`) | No transform: "Node loads precompiled plugins". `ensurePluginRuntime` returns early with no `Bun`. The hook map covers `@opencode/plugin` promise and effect paths, not `@opencode/plugin/tui`. It resolves from the plugin's own install, so `usePlugin` may not see the host's provider (inference). | `packages/tui/src/plugin/runtime-plugin-support.node.ts:1`, `packages/plugin/src/runtime.ts:13`, `packages/cli/bin/opencode.cjs:36`, `packages/cli/vite.node.config.ts:171` |
| Bare text | A string or number returned from a slot or route throws `rendered bare text; wrap it in <text>`. | `packages/tui/src/plugin/render.tsx:55` |
| Crash | Contained per contribution. Toast `<id> crashed in <where>: ...`, and the contribution renders nothing. | `packages/tui/src/plugin/render.tsx:27` |
| Native resources | Pass `renderer.nativeScene` as owner, as the host and fixture do. Destroy after `renderer.idle()`. | `packages/tui/test/fixture/plugin/native-resources/tui.tsx:9`, `packages/tui/test/fixture/plugin/native-resources/tui.tsx:24` |

## 11. OpenCode Desktop

TUI parts do not run in Desktop. Nothing in the `./tui` entry has any effect there.

| Evidence | Pin |
|---|---|
| The only code that imports a `.tui` entry is the TUI host. The server reads `entrypoints.tui` only to set a feature flag, and only `server` and `gui` count as found. | `packages/tui/src/plugin/context.tsx:670`, `packages/core/src/plugin/module.ts:122`, `packages/core/src/plugin/module.ts:155` |
| Only `packages/cli` and `packages/tui` depend on `@opencode/tui`; `packages/desktop` and `packages/app` do not (grep of `package.json` files). | `packages/tui/package.json:3` |
| Desktop main keeps a set of ids with `features.tui`, only to tag a row: a badge in Settings > Extensions > Plugins. | `packages/desktop/src/main/plugin/host.ts:99`, `packages/desktop/src/main/plugin/host.ts:452`, `packages/app/src/runtime/plugin/extension-plugins.tsx:165` |
| Desktop reads only plugins that ship a GUI part; TUI-only packages never appear. Its switch does not reach a TUI part; the app's own text says to use `cli.json`. | `packages/plugin/src/gui/host.ts:383`, `packages/app/src/runtime/i18n/en.ts:826` |

| TUI feature | In Desktop | Use instead |
|---|---|---|
| Slots, routes, panels, dialogs, toasts | Not rendered. | GUI part (`./gui-experimental`). See the GUI reference. |
| `keymap` commands: bindings, palette, slash | Not registered. Desktop's composer lists server commands and GUI commands. | Server `ctx.command`, or the GUI `Command` registry (`packages/app/src/composer/model.ts:273`, `packages/plugin/src/gui/registries.ts:733`). |
| `markdown.registerCodeBlockRenderer` | No effect. | None checked here. |
| `attention.notify`, `ui.tabs`, `ui.model`, `keymap.mode` | No effect. They act on the terminal renderer or TUI state. | |
| `storage` | Files exist only for TUI hosts, under `<state>/<channel>/tui`. Desktop does not read them (inference). | |
| `cli.json` entries and options | Not read. | `opencode.json(c)`; a package that adds a GUI part must be listed there. |

If a user runs `opencode` in a terminal inside Desktop, that is an ordinary TUI process and the part loads there (inference).

## 12. Terminal-only output

A TUI command has no output channel except the terminal.

| Fact | Consequence | Pin |
|---|---|---|
| A slash command with arguments runs client-side: the prompt is cleared, and nothing goes to the server. Selecting one without arguments calls `command.run` directly. | No transcript entry. No other client sees it. | `packages/tui/src/component/prompt/index.tsx:1150`, `packages/tui/src/component/prompt/autocomplete.tsx:498` |
| `run` returns only `void`, `false` or a promise. | Show results through `ui.toast`, `ui.dialog`, a route, a slot or a panel. | `packages/plugin/src/tui/context.ts:432` |
| Server commands are listed beside TUI commands and are queueable. They go to the server as prompts. | To reach every client and the transcript, use a server command, or call `context.client`. | `packages/tui/src/component/prompt/autocomplete.tsx:503`, `packages/tui/src/component/prompt/index.tsx:1155` |
| `console.*` goes to OpenTUI's console, toggled by `app.console`, which has no default key. It does not open on error (inference on the capture itself). The renderer uses `externalOutputMode: "passthrough"`, so writing to stdout can disturb the frame (inference). | Do not rely on either for user output. | `packages/tui/src/app.tsx:259`, `packages/tui/src/app.tsx:1200`, `packages/tui/src/config/keybind.ts:51`, `packages/tui/src/app.tsx:253` |
| `opencode plugin` subcommands write plain text to stdout and stderr. | Terminal-only too. Desktop has its Extensions page instead. | `packages/cli/src/commands/handlers/plugin/add.ts:29`, `packages/cli/src/commands/handlers/plugin/list.ts:51`, `packages/cli/src/commands/handlers/plugin/check.ts:11` |

## 13. `opencode plugin` and TUI parts

| Command | TUI behavior | Pin |
|---|---|---|
| `add <pkg>` | Installs. A package with a server or GUI part goes to global `opencode.json`. A TUI-only package goes to `cli.json`. Packages only: local paths are refused. | `packages/cli/src/commands/handlers/plugin/add.ts:17`, `packages/cli/src/commands/handlers/plugin/add.ts:48` |
| `list`, `check` | `list`: server rows plus TUI rows from `cli.json` and discovery; a TUI-only row shows id `-`. `check`: `Server` and `TUI` groups; TUI rows come from installable `cli.json` targets only. | `packages/cli/src/commands/handlers/plugin/list.ts:29`, `packages/cli/src/commands/handlers/plugin/list.ts:87`, `packages/cli/src/commands/handlers/plugin/inventory.ts:47`, `packages/cli/src/commands/handlers/plugin/inventory.ts:87` |
| `update [target]`, `remove <pkg>` | `update`: TUI targets via `npm.update` on the client; a running TUI needs a restart. `remove`: removes the exact entry from both `opencode.json` and `cli.json`. | `packages/cli/src/commands/handlers/plugin/update.ts:29`, `packages/tui/src/plugin/context.tsx:663`, `packages/cli/src/commands/handlers/plugin/remove.ts:16`, `packages/cli/src/commands/handlers/plugin/remove.ts:19` |
| `/plugins` in the TUI | Lists TUI and server parts. Toggles TUI parts for this session. Updates server packages. | `packages/tui/src/feature-plugins/system/plugins.tsx:336`, `packages/tui/src/feature-plugins/system/plugins.tsx:143` |
