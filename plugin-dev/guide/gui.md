# The GUI part

The part that runs in OpenCode Desktop, from one prebuilt bundle. It is marked experimental upstream: the export is `./gui-experimental`. The official doc is [build/plugins/gui/index.mdx](../upstream/services/www/src/docs/content/build/plugins/gui/index.mdx), and [drift.md](drift.md) lists where it is wrong. [src/gui.tsx](../../src/gui.tsx) is a working example of the source; the bundle has not yet been run in a real Desktop window here.

Read from source at the pin; not run, except where a line says **Observed**. Pins are paths inside [upstream/](../upstream/). "(inference)" marks a conclusion drawn from what was read, not a line that states it. **Observed** marks what was run: [testing.md](testing.md) says on what. Doc pins point at the docs only where the source has no statement of its own.

## 1. What a GUI part is and where it runs

A GUI part is one prebuilt CommonJS file that a plugin exposes as `./gui-experimental`. Its default export is a `Plugin.define` call. The same file is evaluated in the Electron main process and in every window. Each process hands it inert placeholders for the other process's modules.

| Part | What it is | When it runs | Pin |
| --- | --- | --- | --- |
| Bundle | Prebuilt CommonJS text, evaluated with `new Function("require","module","exports",code)` | Once per revision per process | `packages/plugin/src/host.ts:17-22`, `packages/plugin/src/gui/host.ts:251` |
| `setup` | Window entry. Synchronous, under a Solid owner | Once per window, per activation | `packages/plugin/src/gui/plugin.ts:26,52`, `packages/app/src/runtime/plugin/host.tsx:450-477` |
| `main` | Main-process entry. May be async | Once in the main process, per activation | `packages/plugin/src/gui/plugin.ts:44,54`, `packages/desktop/src/main/plugin/lifecycle.ts:214-250` |
| Listing | Main alone lists plugins and reads bundles, then sends windows the same set | On start, on `plugin.updated` and `server.connected` | `packages/desktop/src/main/plugin/host.ts:403-430,434-501`, `packages/app/src/runtime/plugin/plugins.tsx:24-32` |

### Where a third-party GUI loads

| Environment | Loads? | Why | Pin |
| --- | --- | --- | --- |
| Desktop, plugin listed by the app's own server | Yes | Main lists the sidecar's plugins and sends them to all windows | `packages/app/src/runtime/plugin/plugins.tsx:24-28` |
| Desktop, plugin listed only by a remote server | No | "other servers' plugins load no GUI" | `packages/app/src/runtime/plugin/plugins.tsx:27-28` |
| Desktop, a session on a remote server is open | The sidecar's GUIs keep running. `ctx.client` still targets the sidecar | One set for the whole app | `packages/plugin/src/gui/core.ts:341`, `packages/desktop/src/main/plugin/host.ts:386-399` |
| Web app | No. Only built-ins | The plugin context needs a bridge. The loader mounts only with a bridge. A config plugin "runs only in the desktop app" | `packages/app/src/runtime/plugin/root.tsx:91-103,139`, `packages/plugin/src/gui/declarations.ts:15-17`, `packages/desktop/src/renderer/platform/index.ts:57` |
| TUI | Not this API. It has its own `./tui` entry and config | Separate entrypoint | `packages/plugin/src/host.ts:15`, `packages/core/src/plugin/module.ts:121` |

The SDK still models the web: `ctx.app.platform`, `ctx.desktop === undefined`, every Ipc inactive. Those branches serve built-ins. For a third-party bundle they are unreachable (inference from the rows above).

### Which config decides

1. Main calls `client.plugin.list()` on the sidecar with no location. `packages/desktop/src/main/plugin/host.ts:440`
2. The server resolves a missing location to `process.cwd()`. `packages/server/src/location.ts:72-79`
3. Desktop starts the sidecar with `serve --service`, or adopts a running service. `packages/desktop/src/main/service/background-service.ts:60-71,82-85`. A second copy of an installed Desktop adopts the same user's running service even with a test root: [testing.md](testing.md#desktop-windows).
4. `--service` changes directory to the home directory. `packages/cli/src/server-process.ts:62-66`
5. Config discovery for that location reads the system and global config directories, then walks up from home looking for `opencode.json(c)` and `.opencode`. `packages/core/src/config/discovery.ts:71,78-82,143-151`

So the GUI set comes from the sidecar's home location only (inference: each step is read, the composition was not run).

| Question | Answer | Pin |
| --- | --- | --- |
| Global `opencode.json(c)` in the global config directory | Yes, GUI loads | `packages/core/src/config/discovery.ts:68,141` |
| Plugin directory under the global `plugins/` or `plugin/` folder | Yes, if it is a directory with a GUI entry | `packages/core/src/plugin/source-directory.ts:7`, `packages/core/src/config/plugin/source.ts:130-136` |
| `~/opencode.json(c)`, `~/.opencode/`, or the same in an ancestor of home | Yes (inference: home is the walk's start) | `packages/core/src/config/discovery.ts:78-82` |
| Project `opencode.json(c)` or `.opencode/plugins/<dir>` in a repo elsewhere | No GUI. No row in Settings (inference). Its server part can still load for sessions at that location (inference) | Steps 1-5 |
| `cli.json` | No. The server reads `plugins` from `opencode.json(c)` documents | `packages/core/src/config/plugin/source.ts:137-140`, `packages/core/src/config/discovery.ts:12` |
| A remote server's config | No GUI. Settings shows name-only rows while that server is selected | `packages/app/src/runtime/plugin/extension-plugins.tsx:19-41` |
| Standalone `.ts`/`.js` file in `plugins/` | No GUI. A file gets only a server entry | `packages/core/src/plugin/module.ts:116-119` |
| Configured path to a single file | Skipped with a warning | `packages/core/src/config/plugin/source.ts:154-157` |
| Entry that resolves outside the plugin directory | Dropped | `packages/core/src/config/plugin/source.ts:173-177` |
| Managed policy `plugin.use` denies it | Blocked, no row | `packages/core/src/plugin/module.ts:53-54`, `packages/core/src/plugin/supervisor.ts:63-69` |
| `"-<id>"` in `plugins` | Whole plugin off, GUI included | `packages/core/src/plugin/supervisor.ts:34-40` |
| Package with only a GUI part | Allowed. Lists with a no-op server effect | `packages/core/src/plugin/module.ts:122,131-134` |
| Server part failed to load | No GUI on a first load. See section 11 for later revisions | `packages/plugin/src/gui/host.ts:383-388` |
| `options` are not JSON | Load fails: "Plugin options must be JSON to reach its ./gui-experimental" | `packages/core/src/plugin/module.ts:143-150` |

Server routes: `GET /api/plugin` lists, `GET /api/plugin/gui?id=` returns `{ code, revision, options }`. `packages/protocol/src/groups/plugin.ts:9-40`, `packages/server/src/handlers/plugin.ts:11-27`, `packages/schema/src/plugin.ts:35-43`. The server reads the bundle file at request time. `packages/core/src/plugin.ts:53-60`

`ctx.options` crosses to windows, so never put a secret there that a window should not hold (inference). `packages/plugin/src/gui/host.ts:398-399`, `packages/core/src/plugin/module.ts:143-150`

## 2. The bundle

### Entry resolution

| Case | How `./gui-experimental` is found | Pin |
| --- | --- | --- |
| Installed package | Package `exports` subpath `./gui-experimental` | `packages/plugin/src/host.ts:33-35,61` |
| Local directory whose `package.json` has `name` and `exports` | Through those, like a published package | `packages/plugin/src/host.ts:26-30` |
| Local directory without them | `gui-experimental.cjs`, then `gui-experimental.js`, at its root | `packages/plugin/src/host.ts:61` |
| Resolved file does not end in `.js` or `.cjs` | Ignored, no GUI | `packages/plugin/src/host.ts:60-63` |

The preset writes `dist/gui-experimental.cjs` by default. A directory without `name` and `exports` will not find that file unless you set `outFile: "gui-experimental.cjs"` (inference). `packages/plugin/src/gui/vite.ts:34`, `packages/plugin/src/host.ts:61`

### Build with the preset

```ts
// vite.config.ts
import { defineConfig } from "vite"
import { gui } from "@opencode/plugin/gui/vite"

export default defineConfig({ plugins: [gui()] })
```

```json
{
  "name": "acme",
  "exports": { "./gui-experimental": "./dist/gui-experimental.cjs" }
}
```

| Preset behaviour | Detail | Pin |
| --- | --- | --- |
| Options | `entry` default `src/gui.tsx`. `outFile` default `dist/gui-experimental.cjs` | `packages/plugin/src/gui/vite.ts:8-13,34,46` |
| Solid | Adds `vite-plugin-solid` | `packages/plugin/src/gui/vite.ts:37` |
| Format | `lib.formats: ["cjs"]`, `exports: "named"` | `packages/plugin/src/gui/vite.ts:47,50` |
| Chunks | `inlineDynamicImports: true`, so one file. `lazy()` defers evaluation, not download (inference) | `packages/plugin/src/gui/vite.ts:50` |
| Output folder | `emptyOutDir: false` | `packages/plugin/src/gui/vite.ts:44` |
| External | Provided modules, `electron`, Node built-ins | `packages/plugin/src/gui/vite.ts:16,54` |
| Build error | Any other `effect/*`, `solid-js/*`, `@opencode/*` value import | `packages/plugin/src/gui/vite.ts:56-57` |
| Everything else | Bundled | `packages/plugin/src/gui/vite.ts:53-58` (no branch returns it as external) |
| Peer deps (optional) | `solid-js >=1.9.0`, `vite >=6`, `vite-plugin-solid >=2.11`, `electron *` | `packages/plugin/package.json:52-60` |

### Modules a bundle may require

| Module | Window | Main | Pin |
| --- | --- | --- | --- |
| `effect` | Provided | Provided | `packages/plugin/src/gui/modules.ts:11` |
| `@opencode/plugin/gui` | Window SDK | Main SDK | `packages/plugin/src/gui/modules.ts:12`, `packages/app/src/runtime/plugin/module.ts:13`, `packages/desktop/src/main/plugin/module.ts:16` |
| `@opencode/plugin/gui/main` | Window SDK | Main SDK | `packages/plugin/src/gui/modules.ts:13`, `packages/app/src/runtime/plugin/module.ts:14` |
| `@opencode/plugin/rpc`, `@opencode/schema/rpc` | Provided | Provided | `packages/plugin/src/gui/modules.ts:14-15` |
| `@opencode/client`, `@opencode/client/effect` | Provided | Provided | `packages/plugin/src/gui/modules.ts:16-17` |
| `solid-js`, `solid-js/web`, `solid-js/store` | Provided | Inert | `packages/plugin/src/gui/modules.ts:25-27` |
| `@opencode/plugin/gui/file`, `/review`, `/browser` | Provided | Inert | `packages/plugin/src/gui/modules.ts:28-30` |
| `@opencode/client/solid` | Provided | Inert | `packages/plugin/src/gui/modules.ts:31` |
| `electron`, `node:*` | Inert | Real | `packages/plugin/src/gui/host.ts:106-172`, `packages/desktop/src/main/plugin/module.ts:38-48` |
| Anything else | Must be bundled | Must be bundled | `packages/app/src/runtime/plugin/module.ts:50`, `packages/desktop/src/main/plugin/module.ts:47` |

An inert module is a Proxy. Reading or calling it does nothing, and it is not thenable. `packages/plugin/src/gui/host.ts:185-209`. So code at module scope must not depend on the other process's APIs.

`@opencode/plugin/gui` means different modules per process. `Command`, `Panel` and the other window registries are not exported by the main SDK, and `MenubarItem` is not in the window SDK. Touch each one only inside the setup that runs in its process (inference). `packages/plugin/src/gui/main.ts:15,17`, `packages/plugin/src/gui/index.ts`

Not published, never importable: `gui/host`, `gui/builtin`, `gui/updater`. `packages/plugin/script/pack.ts:7`

Also unavailable at runtime: `@opencode/ui/*`, `@opencode/util/*`, bare `@opencode/plugin`. Use `ctx.ui` for app components. `packages/plugin/src/gui/modules.ts:10-32`, `packages/gui-plugins/README.md:239`. Type-only imports erase and are fine (inference).

### What fails if you get it wrong

| Mistake | Result | Pin |
| --- | --- | --- |
| Value import of a non-provided `effect/*`, `solid-js/*`, `@opencode/*` with the preset | Build error `... is not a module the OpenCode app provides to plugin GUIs: ...` | `packages/plugin/src/gui/vite.ts:56-57` |
| Same, without the preset | Load fails: `Plugin GUI bundle requires a module the app does not share: <name>` | `packages/app/src/runtime/plugin/module.ts:50`, `packages/desktop/src/main/plugin/module.ts:47` |
| Bundling your own `solid-js` | Not caught by the host. It would not share the app's Solid instance (doc claim, inference for failure mode) | `services/www/src/docs/content/build/plugins/gui/index.mdx:134-135` |
| ES module text or TS entry | `.ts` is ignored at resolution. An ESM `.js` throws at `new Function` (inference) | `packages/plugin/src/host.ts:60-63`, `packages/plugin/src/gui/host.ts:251` |
| Default export is not a `Plugin.define` shape | `A plugin's ./gui-experimental bundle must default-export a ...` with the field named | `packages/plugin/src/gui/host.ts:257-263` |
| Neither `setup` nor `main` | `A plugin's GUI must have a window setup, a main setup, or both` | `packages/plugin/src/gui/host.ts:265-266` |
| Lazy locale (function in `i18n`) or unknown `os` | Shape check fails | `packages/plugin/src/gui/host.ts:289-304` |

The default export is `module.exports.default`, else `module.exports`. `packages/plugin/src/gui/host.ts:253`

## 3. The definition

```ts
Plugin.define({ os?, stores?, i18n?, setup?, main? })
```

`define` with no setup returns only declarations, so setups in other files can be typed with `Plugin.Setup<typeof definition>`. A bundle's default export needs a setup. `packages/plugin/src/gui/plugin.ts:77-98`

| Field | Type | Applies | Pin |
| --- | --- | --- | --- |
| `os` | `readonly OS[]`, where `OS` is `"macos" \| "windows" \| "linux"` | Excluded system: never runs, Settings row says "Not available on this system." | `packages/plugin/src/gui/declarations.ts:15-18`, `packages/plugin/src/gui/core.ts:18`, `packages/plugin/src/gui/host.ts:68-70`, `packages/desktop/src/main/plugin/host.ts:497-500` |
| `stores` | Record of `Store.global` / `Store.session` | Windows. `ctx.stores.<name>` | `packages/plugin/src/gui/declarations.ts:25`, `packages/plugin/src/gui/core.ts:495-527` |
| `i18n` | `Catalog`: `en` plus other locales, all inline strings | `ctx.t`, `ctx.plural` in both processes | `packages/plugin/src/gui/declarations.ts:20`, `packages/plugin/src/gui/core.ts:34-39` |
| `setup` | `(ctx) => Cleanup \| void` | Each window | `packages/plugin/src/gui/plugin.ts:26` |
| `main` | `(ctx) => Cleanup \| void \| Promise<Cleanup \| void>` | Main process | `packages/plugin/src/gui/plugin.ts:44` |

`en` is required by the type. At runtime a missing `en` becomes `{}`. `packages/plugin/src/gui/core.ts:34-39`, `packages/plugin/src/gui/host.ts:273`

### Id

A definition declares no id. The host assigns it. `packages/plugin/src/gui/plugin.ts:59`, `packages/plugin/src/gui/declarations.ts:9-10`. The TSDoc on `ctx.id` says otherwise and is wrong. `packages/plugin/src/gui/core.ts:352`

| Case | Id | Pin |
| --- | --- | --- |
| Has a server part | The server plugin's `id` | `packages/core/src/plugin/module.ts:131`, `packages/plugin/src/gui/host.ts:383-388` |
| GUI-only package | Package name | `packages/plugin/src/host.ts:76` |
| GUI-only local directory | `package.json` `name`, else folder name | `packages/plugin/src/host.ts:77-78` |
| Reserved | Equal to a built-in id, nested in one, has one nested under it, or `opencode` namespace. No GUI, row says "Not loaded. A built-in plugin already uses this ID." | `packages/plugin/src/gui/host.ts:317-321`, `packages/desktop/src/main/plugin/host.ts:448`, `packages/app/src/runtime/i18n/en.ts:814-826` |
| Duplicate id | Later one gets a failed row `Duplicate plugin ID: <id>` | `packages/core/src/plugin/supervisor.ts:101-113` |

| The id prefixes | Form | Pin |
| --- | --- | --- |
| Published commands | `${plugin}.${id}` | `packages/app/src/runtime/plugin/commands.tsx:20` |
| Panel tab keys | `${plugin}:${tab id}` | `packages/app/src/runtime/plugin/host-apis.tsx:691` |
| Window stores | `plugin.<id>.<name>` | `packages/app/src/runtime/plugin/stores.ts:25-27` |
| Main storage namespace | `plugin.<id>` | `packages/desktop/src/main/plugin/storage.ts:31` |
| Menubar items | `${plugin}.${id}` | `packages/desktop/src/main/plugin/host.ts:248` |
| Contributed servers | `${plugin}:${entry.id}` | `packages/app/src/runtime/plugin/servers.tsx:96` |
| Contract and Ipc ids | Must be `<id>` or `<id>.<name>`, or `provide` throws | `packages/plugin/src/gui/core.ts:108,127`, `packages/app/src/runtime/plugin/host.tsx:723-725`, `packages/desktop/src/main/plugin/host.ts:631-646` |
| Settings page id | Not prefixed. It is the raw `/settings?tab=<id>` value, so pick one that will not collide (inference) | `packages/plugin/src/gui/registries.ts:380-381`, `packages/app/src/runtime/plugin/settings-pages.ts:11` |

### i18n behaviour

| Call | Lookup | Pin |
| --- | --- | --- |
| Window `ctx.t(key, params)` | Plugin catalog in current locale, then `en`, then the app's shared keys. Reactive | `packages/plugin/src/gui/core.ts:417-428`, `packages/app/src/runtime/plugin/host.tsx:748-755` |
| Main `ctx.t(key, params)` | Plugin catalog, then the desktop's native messages, then the key | `packages/desktop/src/main/plugin/host.ts:764-765` |
| `ctx.plural(key, count, params?)` | `<key>.<category>`, then `<key>.other`. `{{count}}` is set | `packages/plugin/src/gui/core.ts:430-442`, `packages/app/src/runtime/plugin/host.tsx:756-764`, `packages/desktop/src/main/plugin/host.ts:766-777` |

Labels follow the language only if the host reads them again. Use the function form of `ctx.add`, or getters on objects the host keeps stable. `packages/plugin/src/gui/core.ts:373-388`, `packages/gui-plugins/README.md:77-79`

## 4. Context members

Host APIs are lazy getters, built on first read. `packages/plugin/src/gui/core.ts:326-327`, `packages/app/src/runtime/plugin/host.tsx:770-785`. Before the app interface mounts, reads return defaults and writes wait, then apply in call order. `packages/app/src/runtime/plugin/host-apis.tsx:102-105,124-143`

### Shared (window and main)

| Member | What it is | When | Pin |
| --- | --- | --- | --- |
| `options` | The `options` from the config entry | JSON only | `packages/plugin/src/gui/core.ts:339` |
| `client` | `OpenCodeClient` of the sidecar. New after that server restarts, so read it where you call it. Rejects while unreachable | Both | `packages/plugin/src/gui/core.ts:340-350`, `packages/app/src/runtime/plugin/host.tsx:695-697,1001-1008`, `packages/desktop/src/main/plugin/host.ts:377-399` |
| `id` | The assigned id | Both | `packages/plugin/src/gui/core.ts:359` |
| `signal` | Aborts on disable, reload, window close or quit | Check after every `await` | `packages/plugin/src/gui/core.ts:361-371` |
| `add(registry, item)` | Contribute a fixed item, or a function that returns one or undefined. Returns a withdraw function. Withdrawn with the current owner, else the plugin | Window reruns the function reactively. Main reads it on each list | `packages/plugin/src/gui/core.ts:388,403`, `packages/app/src/runtime/plugin/host.tsx:699-720`, `packages/desktop/src/main/plugin/host.ts:604-615` |
| `list(registry)` | All plugins' items in contribution order | Reactive in the window | `packages/plugin/src/gui/core.ts:415`, `packages/desktop/src/main/plugin/host.ts:617-626` |
| `t`, `plural` | See section 3 | Both | `packages/plugin/src/gui/core.ts:428,442` |

Runtime only, not public: every main context has a `lifecycle` getter. `packages/desktop/src/main/plugin/host.ts:705,720-724`. Do not rely on it. It is typed only through `builtinMainContext`. `packages/gui-plugins/README.md:322`

### Window (`Plugin.Setup`)

| Member | Type | What it does | Pin |
| --- | --- | --- | --- |
| `provide(token, impl)` | `Cleanup` | Provide a `Contract` under your id | `packages/plugin/src/gui/context.ts:63` |
| `use(token)` | `Accessor<Live<...>>` | Follow a `Contract` or an `Ipc` | `packages/plugin/src/gui/context.ts:77` |
| `main(ipc)` | `IpcClient` | Your own main entry. Calls wait for it | `packages/plugin/src/gui/context.ts:79-93` |
| `stores` | Per declaration | Global: `Persisted`. Session: `(session) => Persisted` | `packages/plugin/src/gui/context.ts:292-311` |
| `layout` | `Layout` | Side panel tabs, scroll, settings, open project, draft | `packages/plugin/src/gui/context.ts:102` |
| `sessions` | `Sessions` | Open-tab sessions, mounted session | `packages/plugin/src/gui/context.ts:111` |
| `screen` | `Screen` | Files, comments, composer of the routed session | `packages/plugin/src/gui/context.ts:122` |
| `storage` | `Storage` | Runtime-key stores, window memory | `packages/plugin/src/gui/context.ts:131` |
| `system` | `System` | Clipboard, save, open external | `packages/plugin/src/gui/context.ts:140` |
| `desktop` | `Desktop \| undefined` | OS actions. Undefined on the web | `packages/plugin/src/gui/context.ts:150`, `packages/app/src/runtime/plugin/host-apis.tsx:275-305` |
| `dialogs` | `Dialogs` | App dialogs. Close with owner | `packages/plugin/src/gui/context.ts:159` |
| `toast` | `Toasts` | Toasts that close with the plugin | `packages/plugin/src/gui/context.ts:170` |
| `tabs` | `Tabs` | Shell tab strip | `packages/plugin/src/gui/context.ts:179` |
| `attention` | `Attention` | Notifications and sounds, per user settings | `packages/plugin/src/gui/context.ts:188` |
| `commands` | `Commands` | Run a published or app command | `packages/plugin/src/gui/context.ts:197` |
| `links` | `Links` | Open or check a local link | `packages/plugin/src/gui/context.ts:206` |
| `embeds` | `Embeds` | Show a web page main created | `packages/plugin/src/gui/context.ts:215` |
| `ui` | `Ui` | App components | `packages/plugin/src/gui/context.ts:225` |
| `app` | `App` | name, version, channel, platform, packaged | `packages/plugin/src/gui/context.ts:234`, `packages/plugin/src/gui/core.ts:48-72` |
| `locale` | `Locale` | Locale, direction | `packages/plugin/src/gui/context.ts:243` |
| `appearance` | `Appearance` | Mono font, light or dark | `packages/plugin/src/gui/context.ts:252` |
| `router` | `Router` | Route path, routing flag | `packages/plugin/src/gui/context.ts:261` |
| `keybinds` | `Keybinds` | Effective keybinds of published commands | `packages/plugin/src/gui/context.ts:270` |
| `servers` | `Servers` | Listed servers, live `ServerRef` | `packages/plugin/src/gui/context.ts:280` |
| `workspaces` | `Workspaces` | `on("remove", ...)` | `packages/plugin/src/gui/context.ts:289` |

Components read the same object with `usePlugin<typeof definition>()`. `packages/plugin/src/gui/solid.ts:19-26`

### Main (`Plugin.MainSetup`)

| Member | Type | What it does | Pin |
| --- | --- | --- | --- |
| `onCleanup(fn)` | `void` | Runs when the instance goes away | `packages/plugin/src/gui/main.ts:188` |
| `storage` | `Storage` | Synchronous stores | `packages/plugin/src/gui/main.ts:197` |
| `log` | `Log` | `write(level, message, data?)` to the desktop log file, included in exported debug logs | `packages/plugin/src/gui/main.ts:152-170,206` |
| `app` | `App` | `platform` is always `desktop` | `packages/plugin/src/gui/main.ts:215` |
| `serverEndpoints` | `ServerEndpoints` | `get(id)`: `{ id, url, headers, sameMachine, password? }`. Sidecar known first-hand. Others come from windows | `packages/plugin/src/gui/main.ts:112-149,224`, `packages/desktop/src/main/plugin/host.ts:289-323`, `packages/app/src/runtime/plugin/server-shell.tsx:87-113` |
| `windows` | `Windows` | `get(id)`, `list()`, `focused()`, `on("open"\|"close", fn)` | `packages/plugin/src/gui/main.ts:20-39,233` |
| `embeds` | `Embeds` | `create(view, window)` returns `Embed` | `packages/plugin/src/gui/main.ts:42-75,242` |
| `cli` | `Cli` | `version`, `command`, `binary?`, `development` | `packages/plugin/src/gui/main.ts:129-138,251` |
| `provide(ipc, impl)` | `IpcProvider` | Provide an Ipc under your id | `packages/plugin/src/gui/main.ts:266` |

### Solid helpers

| Helper | Use | Pin |
| --- | --- | --- |
| `usePlugin()` | The context in a component | `packages/plugin/src/gui/solid.ts:19-26` |
| `bindPlugin(component)` | Bind a contract component to the provider's context. Annotate its props | `packages/plugin/src/gui/solid.ts:41-51`, `packages/gui-plugins/README.md:71` |
| `usePanel()` | `PanelFrame` of the current panel: `visible`, `present`, placement, sidebar | `packages/plugin/src/gui/solid.ts:54-108` |
| `useDrawer()` | Narrow-screen drawer context | `packages/plugin/src/gui/solid.ts:122-124`, `packages/plugin/src/gui/internal.ts:25-37` |

## 5. Registries

| Token | Id | Process | An item is | Pin |
| --- | --- | --- | --- | --- |
| `Command` | `command` | Window | Palette command, keybind, slash | `packages/plugin/src/gui/registries.ts:747` |
| `MenuItem` | `menu-item` | Window | Item in a host menu | `packages/plugin/src/gui/registries.ts:757` |
| `Panel` | `panel` | Window | Tabs in the side region | `packages/plugin/src/gui/registries.ts:772` |
| `SettingsPage` | `settings-page` | Window | Page, section, or rows | `packages/plugin/src/gui/registries.ts:782` |
| `Server` | `server` | Window | A source of servers | `packages/plugin/src/gui/registries.ts:792` |
| `LinkHandler` | `link-handler` | Window | Opens local links | `packages/plugin/src/gui/registries.ts:802` |
| `TitlebarItem` | `titlebar-item` | Window | Titlebar pill | `packages/plugin/src/gui/registries.ts:812` |
| `ComposerPill` | `composer-pill` | Window | Pill above the composer | `packages/plugin/src/gui/registries.ts:828` |
| `Slot` | `slot` | Window | Content at a named place | `packages/plugin/src/gui/registries.ts:838` |
| `Style` | `style` | Window | CSS string, added while contributed. Import with `?inline` | `packages/plugin/src/gui/registries.ts:840-849`, `packages/app/src/runtime/plugin/render.tsx:66-74` |
| `MenubarItem` | `menubar-item` | Main | App menu item | `packages/plugin/src/gui/main.ts:270-309` |
| Your own | `Registry.define<T>(id)` | Either | Start the id with your plugin id. Read with `ctx.list` | `packages/plugin/src/gui/core.ts:585-592` |

### `Command`

| Field | Meaning | Pin |
| --- | --- | --- |
| `id` | Published as `${plugin}.${id}` | `packages/plugin/src/gui/registries.ts:15`, `packages/app/src/runtime/plugin/commands.tsx:20` |
| `title`, `description`, `keywords`, `group` | Palette text. `group` is the category | `packages/plugin/src/gui/registries.ts:17-23`, `packages/app/src/runtime/plugin/commands.tsx:22-25` |
| `section` | `general`, `session`, `navigation`, `model`, `terminal`, `prompt` | `packages/plugin/src/gui/registries.ts:33` |
| `bind` | Default keybind | `packages/plugin/src/gui/registries.ts:35` |
| `slash` | `{ name, arguments?: true, after? }`. With `arguments`, text after the name goes to `run` | `packages/plugin/src/gui/registries.ts:37-44` |
| `hidden`, `suggested`, `featured`, `editable` | Listing flags | `packages/plugin/src/gui/registries.ts:46-50,59` |
| `enabled` | `false` lists it disabled. `ctx.commands.run` will not run it | `packages/plugin/src/gui/registries.ts:52`, `packages/app/src/runtime/plugin/host-apis.tsx:1006-1014` |
| `scope` | CSS selector. Runs only while the key event target is inside it | `packages/plugin/src/gui/registries.ts:54`, `packages/app/src/runtime/plugin/commands.tsx:54-55` |
| `run(input?)` | Returns `void`, `false`, or a promise | `packages/plugin/src/gui/registries.ts:73` |

A literal-typed field in the function form needs a return annotation: `(): Command => ({ ... })`. `packages/gui-plugins/README.md:78`

### `MenuItem`

| `menu` | Fields | Pin |
| --- | --- | --- |
| Base | `id`, `title`, `order?` | `packages/plugin/src/gui/registries.ts:77-84` |
| `session.panel` | `icon?`, `keybind?`, `description?`, `opened?`, `primary?: true`, `run()` | `packages/plugin/src/gui/registries.ts:87-109` |
| `server.add` | `run()` | `packages/plugin/src/gui/registries.ts:112-117` |
| `server.row` | `when?(server)`, `enabled?(server)`, `run(server)` | `packages/plugin/src/gui/registries.ts:120-141` |

### `Panel`

| Field | Meaning | Pin |
| --- | --- | --- |
| `id`, `region: "side"`, `wide?`, `transient?` | Identity, region and defaults | `packages/plugin/src/gui/registries.ts:261-270` |
| `normalize?` | Rewrites a stored tab id | `packages/plugin/src/gui/registries.ts:277` |
| `mobile?` | `MobileView`: `title`, `order`, `kind` (`tab`, `menu`, `drawer`), `icon?`, `cached?` | `packages/plugin/src/gui/registries.ts:211-230,289` |
| `list({ session, screen, open })` | Returns `PanelTab[]`. Return stable objects | `packages/plugin/src/gui/registries.ts:299`, `packages/gui-plugins/README.md:461` |
| `render(props)` | `PanelProps`: `tab`, `session`, `screen`, all live getters. Runs once | `packages/plugin/src/gui/registries.ts:237-244,313`, `packages/gui-plugins/README.md:136,139` |
| `close?`, `closed?`, `restore?` | Close, reopen list entry (`ClosedPanelTab`), and reopen | `packages/plugin/src/gui/registries.ts:247-256,319-334` |
| `focus?`, `enter?` | Selection and enter events | `packages/plugin/src/gui/registries.ts:350,363` |

`PanelTab` fields: `id`, `title`, `label?`, `pinned?`, `draggable?`, `closable?`, `transient?`, `fallback?`, `group?`, `missing?`, `hidden?`, `file?`, `tabbable?`. `packages/plugin/src/gui/registries.ts:157-208`

Open a tab with its key: `ctx.layout.open(`${ctx.id}:${tab.id}`, session)`. `packages/app/src/runtime/plugin/host-apis.tsx:691-696,770-808`

### `SettingsPage`

| Field | Meaning | Pin |
| --- | --- | --- |
| `id` | `/settings?tab=<id>`, and the `ctx.layout.settings` argument | `packages/plugin/src/gui/registries.ts:380-381` |
| `page?` | `general` or `servers`: a section on that host page. Omit for a new page | `packages/plugin/src/gui/registries.ts:387` |
| `section?` | `general` with `page: "general"`: rows placed in the host section | `packages/plugin/src/gui/registries.ts:393` |
| `group?` | `about`: list below About | `packages/plugin/src/gui/registries.ts:398` |
| `title`, `icon?` | Nav label and icon | `packages/plugin/src/gui/registries.ts:400-402` |
| `entries?` | `SettingEntry[]`: search data, indexed without mounting | `packages/plugin/src/gui/registries.ts:367-376,404` |
| `render({ target? })` | `target` is the entry search is revealing | `packages/plugin/src/gui/registries.ts:410` |

### `Server`

`{ ready, order?, entries }`. Startup waits once until every source is ready or its plugin's main failed. A not-ready, reloading, or failed source keeps its last inventory as stopped entries. `packages/plugin/src/gui/registries.ts:514-524`, `packages/app/src/runtime/plugin/servers.tsx:60-62,128-133`

So a `Server` item that never becomes `ready` holds up the app's start unless main failed (inference). `packages/app/src/runtime/plugin/servers.tsx:129-133`

`ServerEntry`: `id`, `name`, `label?`, `state`, `listed?`, `http?`, `reconnect?(signal)`, `connect?()`, `remove?()`, `row?(row)`, `cover?(input)`. `packages/plugin/src/gui/registries.ts:461-511`. `ServerState`: `stopped`, `starting`, `auth`, `ready`, `failed`, `incompatible`. `packages/plugin/src/gui/registries.ts:425`. `cover` hides the routed session or draft while the server is not ready. `packages/app/src/runtime/plugin/server-shell.tsx:14-84`

### Other registries

| Registry | Fields | Pin |
| --- | --- | --- |
| `LinkHandler` | `priority?`, `match(link)`, `open(link)`, `exists?(link)` | `packages/plugin/src/gui/registries.ts:546-570` |
| `Link` | `href`, `origin?`, `exact?`, `background?`, `base?`, `session?` | `packages/plugin/src/gui/registries.ts:527-543` |
| `TitlebarItem` | `id`, `label`, `title?`, `icon?`, `busy?`, `pressed?`, `run?()` | `packages/plugin/src/gui/registries.ts:573-588` |
| `ComposerPill` | `id`, `order?`, `show(input)` returns `ComposerPillView` or undefined, `menu?(input)` | `packages/plugin/src/gui/registries.ts:652-674` |
| `ComposerPillView` | `label`, `icon?`, `tone?`, `title?`, `rows?`, `run?()`. `rows` are unused when the pill has `menu` | `packages/plugin/src/gui/registries.ts:629-645` |
| `ComposerPillRow` | `id`, `label`, `icon?`, `tone?`, `detail?`, `run?()` | `packages/plugin/src/gui/registries.ts:607-620` |
| `Slot` | `{ at, order?, render(input) }` | `packages/plugin/src/gui/registries.ts:714-730` |
| `MenubarItem` | `menu` (`app`, `file`, `edit`, `view`, `go`, `window`, `help`), `id`, `label`, `after?`, `enabled?()`, `run(window)` | `packages/plugin/src/gui/main.ts:270-291` |

| `Slot.at` | Input | Pin |
| --- | --- | --- |
| `window.bottom` | `{}` | `packages/plugin/src/gui/registries.ts:679` |
| `session.header` | `screen`, `session`, `active`, `compact` | `packages/plugin/src/gui/registries.ts:681-694` |
| `session.location.menu` | `screen`, `session`, `shown`. Subscribe only while `shown` | `packages/plugin/src/gui/registries.ts:696-703` |
| `session.panel.end` | `screen`, `session` | `packages/plugin/src/gui/registries.ts:705-710` |

Menu placement: the native menu is built only on macOS. Windows and Linux render plugin items in the in-app menu. `packages/desktop/src/main/native/menu.ts:55`, `packages/app/src/shell/titlebar/titlebar.tsx:657-658`, `packages/app/src/shell/titlebar/windows-menu.tsx:40-49`. `after` names a sibling's local id, or a built-in's command, action, or role. No match puts it last. `packages/desktop/src/main/plugin/host.ts:253-258`, `packages/app/src/shell/commands/desktop-menu.ts:298-322`

## 6. Window host APIs

### Sessions and servers

| Member | What it is | Pin |
| --- | --- | --- |
| `ServerRef` | `id`, `name`, `url`, `password?`, `client`, `data`, `local`, `builtin`, `compatible`, `connected`. Id: `"sidecar"`, an http URL, or `${plugin}:${id}` | `packages/plugin/src/gui/host-apis.ts:13-34`, `packages/app/src/runtime/server/registry.tsx:192-193,202` |
| `SessionRef` | `key`, `id`, `tab`, `server`, `pending`, `location` | `packages/plugin/src/gui/host-apis.ts:37-53` |
| `MountedSession` | `SessionRef` plus `visit`, `project`, `listedProject`, `directory`, `local`, `background` | `packages/plugin/src/gui/host-apis.ts:714-742` |
| `sessions.list()`, `sessions.current()` | Open-tab sessions. The routed, mounted session | `packages/plugin/src/gui/host-apis.ts:773,780` |
| `screen.current()` | `SessionScreen`: `file`, `comment`, `composer`. Undefined on Home, a draft, before mount, during first render | `packages/plugin/src/gui/host-apis.ts:750-768`, `packages/gui-plugins/README.md:138` |
| `servers.list()`, `servers.get(id)` | Listed server ids. Live ref. A ref starts its controller on first use | `packages/plugin/src/gui/host-apis.ts:1211,1225`, `packages/app/src/runtime/plugin/host-apis.tsx:503-516` |
| `workspaces.on("remove", fn)` | Fires on workspace removal | `packages/plugin/src/gui/host-apis.ts:1237` |

Read `props.session` or `input.session` where you use it. Do not copy it. Key per-session state by `session.key`, per-screen state by the screen. `packages/gui-plugins/README.md:134-139`

### `Layout`

| Member | What it does | Pin |
| --- | --- | --- |
| `narrow()` | Viewport under 768px | `packages/plugin/src/gui/host-apis.ts:819`, `packages/app/src/runtime/plugin/host-apis.tsx:111-112` |
| `ready()` | Layout storage loaded | `packages/plugin/src/gui/host-apis.ts:821` |
| `open(key, session, options?)` | `options.tab`: `open`, `preview`, `append`, `select`. `options.background` | `packages/plugin/src/gui/host-apis.ts:793-809,832` |
| `close`, `toggle`, `hide` | `(key, session)` | `packages/plugin/src/gui/host-apis.ts:839,846,855` |
| `state(key, session)` | `closed`, `open`, `active`, `visible` | `packages/plugin/src/gui/host-apis.ts:790,863` |
| `stored(session)` | This plugin's stored tab ids | `packages/plugin/src/gui/host-apis.ts:870`, `packages/app/src/runtime/plugin/host-apis.tsx:1086-1095` |
| `side.opened`, `side.toggle`, `side.menu` | Side region state, toggle, `session.panel` items | `packages/plugin/src/gui/host-apis.ts:878,884,894` |
| `sidebar.opened()` | Inner sidebar preference | `packages/plugin/src/gui/host-apis.ts:902` |
| `scroll.get(session, key)`, `scroll.set(session, key, value)` | Stored scroll offset | `packages/plugin/src/gui/host-apis.ts:912,930` |
| `settings(page?)` | Open settings | `packages/plugin/src/gui/host-apis.ts:946` |
| `project(server, title)` | Open-project picker. Waits until the server is listed | `packages/plugin/src/gui/host-apis.ts:953`, `packages/app/src/runtime/plugin/host-apis.tsx:875-905` |
| `draft({ server, directory, prompt })` | New draft | `packages/plugin/src/gui/host-apis.ts:966-972` |

`layout.command` exists only on `BuiltinLayout`. `packages/plugin/src/gui/builtin.ts:272-278`

### `Files` (`screen.file`)

| Member | Pin |
| --- | --- |
| `root`, `ready()`, `resolve(path)`, `absolute(path)` | `packages/plugin/src/gui/host-apis.ts:168-182` |
| `get(path)` returns `FileState`. `missing(path)` | `packages/plugin/src/gui/host-apis.ts:130-145,188,194` |
| `sync(...)`, `unwatch(path)`, `exists(path)`, `search(...)` | `packages/plugin/src/gui/host-apis.ts:201,215,222,230` |
| `selection.get(path)`, `selection.set(path, range)` | `packages/plugin/src/gui/host-apis.ts:252,259` |
| `scroll.get(path)`, `scroll.set(...)` | `packages/plugin/src/gui/host-apis.ts:268,280` |
| `tree.list(path)`, `tree.state(path)`, `tree.sync(...)`, `tree.expand(...)`, `tree.collapse(path)` | `packages/plugin/src/gui/host-apis.ts:297,303,321,334,346` |

### `Comments` (`screen.comment`)

| Member | Pin |
| --- | --- |
| `list(file?)`, `add(input)`, `update(id, comment)`, `remove(id)` | `packages/plugin/src/gui/host-apis.ts:371,378,385,391` |
| `focus.current()`, `focus.set(...)` | `packages/plugin/src/gui/host-apis.ts:395,406` |
| `active.current()`, `active.set(...)` | `packages/plugin/src/gui/host-apis.ts:418,429` |

### `Composer` (`screen.composer`)

| Member | What it does | Pin |
| --- | --- | --- |
| `text()`, `insert(text)`, `setText(text)` | Draft text | `packages/plugin/src/gui/host-apis.ts:589,602,610` |
| `model()`, `setModel(model)`, `setVariant(variant)` | Model. Setters return boolean | `packages/plugin/src/gui/host-apis.ts:616,625,632` |
| `attach(part)` | `ComposerFile`, `ComposerNote`, `ComposerQuote` | `packages/plugin/src/gui/host-apis.ts:441-532,639` |
| `quotable()` | Whether quoting works now | `packages/plugin/src/gui/host-apis.ts:647` |
| `focus(commentID?, options?)` | `options.anchor` is a `ComposerQuoteAnchor` | `packages/plugin/src/gui/host-apis.ts:544-562,656` |
| `update(id, patch)`, `detach(id)`, `focused()` | Part edits, focus check | `packages/plugin/src/gui/host-apis.ts:664,678,685` |

`ComposerNote` has optional `title` and `subtitle` display fields. `comment: ""` attaches only the subject. `packages/plugin/src/gui/host-apis.ts:476-507`, `packages/gui-plugins/README.md:164-172`

### Dialogs, toasts, notifications

| Member | What it does | Pin |
| --- | --- | --- |
| `dialogs.open(...)` | Custom dialog. Returns `DialogHandle.close()` | `packages/plugin/src/gui/host-apis.ts:1268-1275,1297` |
| `dialogs.active()` | A dialog is open | `packages/plugin/src/gui/host-apis.ts:1305` |
| `dialogs.confirm`, `alert`, `prompt`, `select` | Promise-based app dialogs | `packages/plugin/src/gui/host-apis.ts:1320,1332,1345,1358` |
| `toast.show(options)` | `title`, `description?`, `variant?`, `icon?`, `duration?`, `persistent?`, `actions?`. Returns `{ dismiss() }` | `packages/plugin/src/gui/host-apis.ts:1440-1467,1483` |
| `attention.notify(options)` | `title`, `message?`, `variant?`, `session?`, `sound?`, `id?`. Follows user settings. A keyed notification shows once across windows, only while none has focus. Returns `{ notification, sound }` | `packages/plugin/src/gui/host-apis.ts:1487-1526,1538`, `packages/app/src/runtime/plugin/host-apis.tsx:1016-1051` |

### Others

| Member | What it does | Pin |
| --- | --- | --- |
| `tabs.list()`, `open(session, options?)`, `focus(key)`, `move(key, index)`, `close(key)` | Shell tab strip. `ShellTab`: `key`, `session`, `active` | `packages/plugin/src/gui/host-apis.ts:1556-1563,1571,1585,1605,1612,1618` |
| `commands.run(id)` | Runs by published id, or an app command id. False if missing or disabled | `packages/plugin/src/gui/host-apis.ts:1552`, `packages/app/src/runtime/plugin/host-apis.tsx:1006-1014` |
| `links.open(link)`, `links.exists(link)` | Uses the best handler | `packages/plugin/src/gui/host-apis.ts:1256,1264`, `packages/app/src/runtime/plugin/host.tsx:271-291` |
| `system.copy`, `save({ name, content })`, `openExternal(url)` | `save` returns false on cancel | `packages/plugin/src/gui/host-apis.ts:1067,1074,1086` |
| `desktop.os`, `zoom()`, `launch(path, app?)`, `reveal(path)`, `installed(app)`, `pick(options?)` | `pick` returns paths. `directory` uses the folder picker | `packages/plugin/src/gui/host-apis.ts:1092-1128`, `packages/app/src/runtime/plugin/host-apis.tsx:275-305` |
| `locale.locale()`, `direction()` | `setDirection` is built-in only | `packages/plugin/src/gui/host-apis.ts:1146,1152`, `packages/gui-plugins/README.md:321` |
| `appearance.font("mono")`, `mode()` | | `packages/plugin/src/gui/host-apis.ts:1162,1174` |
| `router.routing()`, `path()` | | `packages/plugin/src/gui/host-apis.ts:1180,1182` |
| `keybinds.keybind(command)`, `keys(bind)`, `matches(command, event)` | Published ids | `packages/plugin/src/gui/host-apis.ts:1192,1198,1205` |
| `embeds.View(props)`, `capture(id)` | `EmbedProps`: `id`, `visible`, `frozen?`, `page?`, `radius?`, `background?`, `class?`, `children?` | `packages/plugin/src/gui/host-apis.ts:1622-1660` |
| `ui.Icon`, `Button`, `IconButton`, `Tooltip`, `Menu`, `Loader`, `Dialog`, `Switch`, `TextInput`, `Keybind`, `Markdown`, `Code` | App components. Props at `Ui*Props` | `packages/plugin/src/gui/host-apis.ts:1663-1936,1943-2086` |

### Contracts the app provides

Follow with `ctx.use(token)`. Handle every `Live` status.

| Token | Id | Import | Members | Pin |
| --- | --- | --- | --- | --- |
| `FileTree` | `file.tree` | `@opencode/plugin/gui/file` | `Tree(props)`, `List(props)` | `packages/plugin/src/gui/file.ts:52-70` |
| `OpenInApp` | `file.openInApp` | `@opencode/plugin/gui/file` | `Button(props)` | `packages/plugin/src/gui/file.ts:81-92` |
| `FileViewer` | `file.viewer` (registry) | `@opencode/plugin/gui/file` | `kinds`, `problem?(bytes)`, `View` | `packages/plugin/src/gui/file.ts:116-132` |
| `Changes` | `review.changes` | `@opencode/plugin/gui/review` | `diffs`, `ready`, `kinds`, `active`, `details`, `focus`, `open`, `watch` | `packages/plugin/src/gui/review.ts:14-76` |
| `Browser` | `browser` | `@opencode/plugin/gui/browser` | `attached`, `canOpen`, `open`, `openFile` | `packages/plugin/src/gui/browser.ts:5-38` |

## 7. Tokens, Ipc and Live

| Token | Defined with | Provided by | Read with | Crosses IPC | Pin |
| --- | --- | --- | --- | --- | --- |
| `Registry<T>` | `Registry.define<T>(id)` | Anyone, `ctx.add` | `ctx.list` | No | `packages/plugin/src/gui/core.ts:86-93,585-592` |
| `Contract<T, Id>` | `Contract.define<T, Id>(id)` | Window `ctx.provide` | `ctx.use` | No | `packages/plugin/src/gui/core.ts:105-112,602-609` |
| `Ipc<S>` | `Ipc.define(spec)` | Main `ctx.provide` | `ctx.main`, `ctx.use` | Yes, Effect Schema encoded | `packages/plugin/src/gui/core.ts:125-159,619-626` |

### Ipc

| Part | Shape | Pin |
| --- | --- | --- |
| `spec.id` | Plugin id or `<id>.<name>`. Main starts the plugin on demand when a window subscribes | `packages/plugin/src/gui/core.ts:127-130`, `packages/desktop/src/main/plugin/host.ts:886-894`, `packages/desktop/src/main/plugin/index.ts:109-121` |
| `spec.state?` | Per-window state schema | `packages/plugin/src/gui/core.ts:132` |
| `spec.methods` | `{ input?, output? }` per method | `packages/plugin/src/gui/core.ts:117-122,134` |
| `spec.events?` | Event schemas | `packages/plugin/src/gui/core.ts:136` |
| `IpcImpl` | `method(input, caller)`, plus `state(window)` if the spec has state | `packages/plugin/src/gui/core.ts:274-288` |
| `Caller` | `window`, `signal` | `packages/plugin/src/gui/core.ts:262-267` |
| `IpcProvider` | `changed(window?)`, `emit(name, data, window?)`, `dispose()` | `packages/plugin/src/gui/core.ts:299-323` |
| `IpcClient` | One async function per method. No-input methods take only `options?`. `state()`, `on(name, listener)` | `packages/plugin/src/gui/core.ts:180-210` |
| `IpcCallOptions` | `signal?` | `packages/plugin/src/gui/core.ts:213-216` |

`ctx.main(ipc)` versus `ctx.use(ipc)`:

| Situation | `ctx.main(ipc)` call | `ctx.use(ipc)()` | Pin |
| --- | --- | --- | --- |
| Main starting | Waits | `pending` | `packages/app/src/runtime/plugin/host.tsx:199-212,597-640` |
| Main provides it | Runs | `active` with `generation` | `packages/app/src/runtime/plugin/host.tsx:544-566` |
| Plugin disabled | Rejects | `inactive`, `disabled` | `packages/app/src/runtime/plugin/host.tsx:204` |
| Main failed | Rejects | `inactive`, `failed` | `packages/app/src/runtime/plugin/host.tsx:206` |
| Bundle has no `main` entry | Waits forever | `pending` forever | `packages/plugin/src/gui/context.ts:79-82`, `packages/app/src/runtime/plugin/host.tsx:199-212` |
| Main runs but never provides this token | Waits forever (inference) | `pending` forever. Line 209 skips the "not coming" branch for main | `packages/app/src/runtime/plugin/host.tsx:208-211` |
| Web | Rejects | `inactive`, `disabled` | `packages/app/src/runtime/plugin/ipc.ts:152-168`, `packages/app/src/runtime/plugin/root.tsx:109` |
| Method throws or schema fails | Rejects. `PluginError` codes: `unavailable`, `method`, `input`, `output` | Unchanged | `packages/desktop/src/main/plugin/host.ts:910-938`, `packages/desktop/src/main/plugin/error.ts:4-19` |

A per-call `signal` does not seem to apply while the call waits for main to become ready (inference). `packages/app/src/runtime/plugin/host.tsx:642-654`

### `Live<T>`

| Status | Fields | Meaning | Pin |
| --- | --- | --- | --- |
| `pending` | | Not started yet, or restarting | `packages/plugin/src/gui/core.ts:238-241` |
| `active` | `value`, `generation` | Running. `generation` counts activations from 1 | `packages/plugin/src/gui/core.ts:242-249` |
| `inactive` | `reason`: `disabled` or `failed` | Gone | `packages/plugin/src/gui/core.ts:250-259` |

A window provider that is active but never provides the token reads `inactive`, `disabled`. `packages/app/src/runtime/plugin/host.tsx:208-209`

`provide` errors: token not under your id, or wrong kind for the process. Providing after the plugin ended is a no-op. `packages/app/src/runtime/plugin/host.tsx:722-744`, `packages/desktop/src/main/plugin/host.ts:628-700`

## 8. Stored state

| Kind | Where | Value | Loads | Pin |
| --- | --- | --- | --- | --- |
| `Store.global(schema, initial, from?)` | Window, declared | Never undefined | Before setup. A failed load fails setup | `packages/plugin/src/gui/core.ts:496-513`, `packages/app/src/runtime/plugin/host.tsx:480-485` |
| `Store.session(schema, initial, from?)` | Window, declared | `ctx.stores.x(session).value`, undefined until loaded and while location is unknown | When the session mounts | `packages/plugin/src/gui/core.ts:514-526`, `packages/app/src/runtime/plugin/stores.ts:199-274` |
| `ctx.storage.store(key, options)` | Window, runtime | Undefined until loaded | When opened | `packages/plugin/src/gui/host-apis.ts:998-1010,1025`, `packages/app/src/runtime/plugin/host-apis.tsx:194-222` |
| `ctx.storage.memory(key, { initial })` | Window, not persisted | Solid store plus setter | Now | `packages/plugin/src/gui/host-apis.ts:1034-1040`, `packages/app/src/runtime/plugin/host-apis.tsx:223-238` |
| Main `ctx.storage.store(key, options)` | Main | Always defined | Synchronous | `packages/plugin/src/gui/main.ts:78-109`, `packages/desktop/src/main/plugin/storage.ts:63-135` |

| Rule | Detail | Pin |
| --- | --- | --- |
| Window schema | Object schema only: `Schema.ConstraintCodec<object, unknown>` | `packages/plugin/src/gui/core.ts:458`, `packages/plugin/src/gui/host-apis.ts:998,1025` |
| Main schema | Any codec, primitives included | `packages/plugin/src/gui/main.ts:94` |
| Runtime scope | `global`, `{ server, directory? }`, or `{ session }` | `packages/plugin/src/gui/host-apis.ts:984-995` |
| Decode failure | Struct field missing or bad takes `initial`. A whole-value failure reads as `initial` | `packages/plugin/src/gui/core.ts:472-473`, `packages/desktop/src/main/plugin/storage.ts:98-99` |
| `Persisted` | `value`, `ready()`, `update(mutate)`, `set(next)` | `packages/plugin/src/gui/core.ts:540-565` |
| `update` | Draft is `Mutable<T>`. Returning a value throws at runtime in both processes | `packages/plugin/src/gui/core.ts:552-557`, `packages/app/src/runtime/plugin/stores.ts:130`, `packages/desktop/src/main/plugin/storage.ts:128-129` |
| Write order | Window waits for load, keeps call order. Main writes at once | `packages/plugin/src/gui/core.ts:547-548,559-560`, `packages/app/src/runtime/plugin/stores.ts:90-143` |
| `from` | Older key of the same storage, imported once. List is newest first | `packages/plugin/src/gui/core.ts:446-456` |
| `remove` | Window: `remove(key, options?)`, reads as `initial`, never imports `from` again. Main: `remove(key)` | `packages/plugin/src/gui/host-apis.ts:1049-1057`, `packages/plugin/src/gui/main.ts:108`, `packages/gui-plugins/README.md:449` |
| Session store without location | `ctx.storage.store` defers it until the location is known | `packages/app/src/runtime/plugin/host-apis.tsx:210-220` |
| Memory lifetime | Map lives in the window host, not the plugin instance, so it survives a plugin reload in that window (inference) | `packages/app/src/runtime/plugin/host-apis.tsx:116,223-238` |

## 9. Reactive helpers

| Helper | Signature | Use | Pin |
| --- | --- | --- | --- |
| `createKeyed` | `(source, fn, { otherwise?, equals? }?)` | One run per key: per `Live` generation, or per truthy value. What `fn` registers ends with the run. `equals` is ignored for `Live` | `packages/plugin/src/gui/reactive.ts:62-132` |
| `createLatest` | `(source, fetch(value, signal))` returns `{ latest, loading, error }` | Async data. Never suspends. Drops stale replies | `packages/plugin/src/gui/reactive.ts:149-189` |
| `createVisitState` | `(initial)` returns `[value, set]` | State reset each time the user routes back. Needs plugin context | `packages/plugin/src/gui/reactive.ts:204-222` |

An object-building source is a new key on each read. Pass `equals`. `packages/gui-plugins/README.md:458`

## 10. Lifetimes

| Thing | Window | Main | Pin |
| --- | --- | --- | --- |
| Setup form | Synchronous. A thenable return fails with "Window setup must be synchronous. Start async work with createKeyed or createLatest." | May be async | `packages/app/src/runtime/plugin/host.tsx:467-469`, `packages/plugin/src/gui/plugin.ts:44` |
| Cleanup | Returned function, `onCleanup` | Returned function, `ctx.onCleanup` | `packages/app/src/runtime/plugin/host.tsx:459`, `packages/plugin/src/gui/main.ts:188`, `packages/plugin/src/gui/scope.ts:16-39` |
| Registration ends with | Current Solid owner, else the plugin | The plugin instance | `packages/plugin/src/gui/core.ts:373-376`, `packages/app/src/runtime/plugin/host.tsx:505-539` |
| After `await` | No owner. Check `ctx.signal`. A late registration is withdrawn at once | Check `ctx.signal` | `packages/plugin/src/gui/core.ts:361-371`, `packages/app/src/runtime/plugin/host.tsx:523` |
| Cleanup deadline | | 3s, then logs and continues | `packages/desktop/src/main/plugin/lifecycle.ts:5,149-167` |
| Stall log | | After 10s of setup | `packages/desktop/src/main/plugin/lifecycle.ts:8,134` |
| Reload failure | No last-good fallback. New setup failing leaves it failed | Keeps last good bundle, runs it again | `packages/app/src/runtime/plugin/host.tsx:912-952`, `packages/desktop/src/main/plugin/lifecycle.ts:290-332` |
| Module state | Bundle evaluated once per revision, so it survives Reload and disable within a revision (inference) | Same (inference) | `packages/app/src/runtime/plugin/plugins.tsx:88-103`, `packages/desktop/src/main/plugin/host.ts:486-492` |

Window state machine: `loading`, then `active`, `failed`, or `disabled`. `packages/app/src/runtime/plugin/host.tsx:395-488,851-873`. Main uses `activate`, `deactivate`, `reload`. `packages/desktop/src/main/plugin/lifecycle.ts:252-332`. `did-start-navigation` resets a window's embeds and subscriptions. `packages/desktop/src/main/plugin/host.ts:830-848`

Embeds: `Embed.dispose` is yours to call. `release` does not close the `webContents`. `packages/plugin/src/gui/main.ts:62`, `packages/desktop/src/main/plugin/embeds.ts:105-116`

## 11. Failure behaviour

| Failure | Effect | User sees | Pin |
| --- | --- | --- | --- |
| Server part fails on first load | No GUI | Bare name row. `plugin.state` is never rendered (inference for "bare") | `packages/core/src/plugin/supervisor.ts:74-79`, `packages/plugin/src/gui/host.ts:383-388`, `packages/app/src/runtime/plugin/extension-plugins.tsx:70-84,141-206` |
| Server import fails on a later revision | Running generation keeps its place and stays listed active, beside a failed row | GUI stays (inference) | `packages/core/src/plugin/supervisor.ts:80-85`, `packages/core/test/plugin/supervisor-reload.test.ts:275-284` |
| Server setup throws on a later revision | Old activation restored, but the slot reports `failed`, so no GUI | Bare row (inference) | `packages/core/src/plugin.ts:166-176,298-303`, `packages/plugin/src/gui/host.ts:387` |
| Main cannot list | Logged as `plugin listing failed` | Nothing specific | `packages/desktop/src/main/plugin/host.ts:440-443` |
| Main cannot read a bundle | `unreadable`, never reaches windows | Row with error | `packages/desktop/src/main/plugin/host.ts:475-480`, `packages/app/src/runtime/plugin/extension-plugins.tsx:79,181-183` |
| Bundle fails to evaluate in main | Entry throws the cause on activation | Row with error, "Failed" | `packages/desktop/src/main/plugin/host.ts:346-370`, `packages/desktop/src/main/plugin/module.ts:31-56` |
| Bundle fails to evaluate in a window | `windowEntry` rejects | Row with error | `packages/app/src/runtime/plugin/module.ts:58` |
| Window setup throws | `fail` logs `[plugin] <id>`, status `failed`, error with stack. Waits for Reload or a new revision. Other plugins continue | Row "Failed", first line, "Show details" | `packages/app/src/runtime/plugin/host.tsx:438-445,453-472,862-873,943-946`, `packages/app/src/runtime/plugin/extension-plugins.tsx:223-249` |
| Contribution render throws | ErrorBoundary. Renders nothing. Error recorded with phase `render` | Row error | `packages/app/src/runtime/plugin/render.tsx:17-36`, `packages/app/src/runtime/plugin/host.tsx:862-873` |
| Main setup throws or rejects | `fail` keeps the message only, no stack. Window setup keeps running. Ipc reads `inactive`, `failed` | Row "Failed" even though window status is active | `packages/desktop/src/main/plugin/lifecycle.ts:80-84`, `packages/app/src/runtime/plugin/root.tsx:87`, `packages/app/src/runtime/plugin/extension-plugins.tsx:114` |
| `main` hangs | Log at 10s. Ipc stays `pending` (inference) | Nothing specific | `packages/desktop/src/main/plugin/lifecycle.ts:8,134` |
| Main reload fails | Last good revision runs again | Error row | `packages/desktop/src/main/plugin/lifecycle.ts:316,330` |
| Scope cleanup throws | Logged | | `packages/plugin/src/gui/scope.ts:85,106` |
| Sidecar unreachable | `ctx.client` calls reject: "The server that runs this plugin is unavailable" | Whatever you show | `packages/app/src/runtime/plugin/host.tsx:1001-1008`, `packages/desktop/src/main/plugin/host.ts:377-384` |
| `Persisted.update` callback returns a value | Throws | | `packages/app/src/runtime/plugin/stores.ts:130`, `packages/desktop/src/main/plugin/storage.ts:128-129` |
| Toast action or queued write throws | Logged as `[plugin]`, isolated | | `packages/app/src/runtime/plugin/host-apis.tsx:131-143,370-371` |

## 12. Develop and reload a local plugin in Desktop

1. Make a directory with `package.json`, `vite.config.ts`, and `src/gui.tsx`. See sections 2 and 16.
2. Add it to the global config, not a project one (section 1): `{ "plugins": ["/abs/path/to/acme"] }`. Relative paths resolve from the config file's directory. `file://` also works. `packages/core/src/config/plugin/source.ts:142-147`
3. Run `vite build --watch`.

### What triggers what

| Trigger | Chain | Result | Pin |
| --- | --- | --- | --- |
| Bundle rewrite | Watcher on bundle and on the target, 100ms debounce, rescan, `plugin.updated`, main relists, new revision, `evaluateMain`, `lifecycle.reload`, `PluginGuisChanged`, windows `forget` then `activate` | GUI reloads in main and all windows | `packages/core/src/plugin/module.ts:140-142`, `packages/core/src/config/plugin/source.ts:51-73`, `packages/core/src/plugin/supervisor.ts:221`, `packages/core/src/plugin.ts:44-49`, `packages/desktop/src/main/plugin/host.ts:468-501,505-545`, `packages/app/src/runtime/plugin/host.tsx:901-952` |
| Same rewrite, server side | The scan's `mtime` takes the max over all entries, GUI included, and goes into `revision`. A changed revision restarts that plugin and every plugin after it. **Observed** on CLI 2.2.1 and 2.2.5: changing only the bundle ran `setup` again in that plugin and in the one after it. The test that says otherwise passes no `mtime`, and the docs are wrong here ([drift.md](drift.md)) | Server part restarts too | `packages/core/src/config/plugin/source.ts:178-191`, `packages/core/src/plugin/module.ts:135`, `packages/core/src/plugin.ts:122-126`, `packages/core/test/plugin.test.ts:140` |
| Server entry edit | New `revision`, and the GUI revision hashes it | Both reload | `packages/core/src/plugin/module.ts:135,160` |
| `options` change | `operation` is part of `revision` | Both reload | `packages/core/src/plugin/module.ts:135` |
| Package update | `installed.revision` changes. A package's GUI changes only with its version | Both reload | `packages/core/src/plugin/module.ts:135-139` |
| Settings Reload | `host.reload(id)` plus `bridge.manager.reload(id)`. Reruns the bundle main last read. Does not fetch a new one | Re-activate same revision | `packages/app/src/runtime/plugin/extension-plugins.tsx:136-139`, `packages/desktop/src/main/plugin/host.ts:968-976`, `packages/app/src/runtime/plugin/host.tsx:974-986` |
| Settings switch off | `manager.disable`. Saved in the desktop's `plugin` table. No row means enabled. Server and TUI parts keep running | GUI off | `packages/desktop/src/main/plugin/host.ts:950-967`, `packages/desktop/src/main/plugin/manager.ts:11-18`, `packages/plugin/src/gui/host.ts:89-101`, `packages/app/src/runtime/i18n/en.ts:814-826` |
| Dev HMR | Built-ins only, DEV only | Not for you | `packages/app/src/runtime/plugin/hmr.tsx:6`, `packages/app/src/runtime/plugin/root.tsx:26` |

Since a build restarts the server part and every plugin after it, keep state in that server part restart-safe while developing.

### How to see failures

| Process | Where | Detail | Pin |
| --- | --- | --- | --- |
| Window | Window console: `console.error("[plugin] <id>")`. Settings row | Message and stack | `packages/app/src/runtime/plugin/host.tsx:863,870` |
| Main | Settings row, desktop log file. Your `ctx.log.write` goes there | Message only in the row | `packages/desktop/src/main/plugin/lifecycle.ts:80-84`, `packages/desktop/src/main/plugin/index.ts:82-83`, `packages/plugin/src/gui/main.ts:152-170` |
| Main listing | Desktop log | | `packages/desktop/src/main/plugin/host.ts:442,478` |
| Server | Server log: `failed to load plugin` | Row shows no reason. `GET /api/plugin` has `state.error` and `ref` | `packages/core/src/plugin/supervisor.ts:58,75-79`, `packages/schema/src/plugin.ts:45-48` |

A bare row with no switch and no Server badge usually means the server part failed or the id never reached the window (inference). `packages/app/src/runtime/plugin/extension-plugins.tsx:70-84,144,155,189`

## 13. What users see in Settings > Extensions > Plugins

The tab lists `api.plugin.list()` for the selected server. `own` is true only for the desktop's built-in server. `packages/app/src/settings/providers/extensions.tsx:67-78,206`

| Situation | Row | Pin |
| --- | --- | --- |
| Other server, or web | Icon and name only | `packages/app/src/runtime/plugin/extension-plugins.tsx:19-41` |
| Loaded, enabled | Name, Reload, switch | `packages/app/src/runtime/plugin/extension-plugins.tsx:189-203` |
| Loading | "Loading" label | `packages/app/src/runtime/plugin/extension-plugins.tsx:111-120` |
| Failed, or active with a main error | "Failed" label and error, with Show/Hide details when multi-line | `packages/app/src/runtime/plugin/extension-plugins.tsx:114,175-177,223-249` |
| Other parts | Server and TUI badges | `packages/app/src/runtime/plugin/extension-plugins.tsx:161-167` |
| `os` excludes this system | "Not available on this system." No switch | `packages/app/src/runtime/plugin/extension-plugins.tsx:76,144,178-180` |
| Bundle unreadable | Error, no switch | `packages/app/src/runtime/plugin/extension-plugins.tsx:79,181-183` |
| Reserved id | "Not loaded. A built-in plugin already uses this ID." | `packages/app/src/runtime/plugin/extension-plugins.tsx:73,184-186`, `packages/app/src/runtime/i18n/en.ts:814-826` |
| Plugin with no GUI | Name only | `packages/app/src/runtime/plugin/extension-plugins.tsx:69,81-83` |
| Main knows it, server list does not | Row by id | `packages/app/src/runtime/plugin/extension-plugins.tsx:86-97,212` |
| Built-ins | Hidden unless failed, then Reload without a switch | `packages/app/src/runtime/plugin/extension-plugins.tsx:102-108,196,213` |
| Footer note | How to turn off server and TUI parts: `"-<id>"` in `opencode.json`, `-` plus TUI id in `cli.json`. Shown when any non-built-in exists | `packages/app/src/runtime/plugin/extension-plugins.tsx:215-217`, `packages/app/src/runtime/i18n/en.ts:814-826` |

Reload is shown on every live row, not only after a failure. `packages/app/src/runtime/plugin/extension-plugins.tsx:189-194`

## 14. How the GUI talks to the server part

| Mechanism | Detail | Pin |
| --- | --- | --- |
| `ctx.client` | Sidecar's `OpenCodeClient`. Window: built from the app's server provider. Main: `OpenCode.make({ baseUrl, headers })`, no directory | `packages/app/src/runtime/plugin/plugins.tsx:40-44,77`, `packages/desktop/src/main/plugin/host.ts:386-399` |
| `ctx.client.rpc(Def)` | `RpcClient`: one function per method, plus `events` | `packages/client/src/promise/client.ts:15`, `packages/client/src/promise/rpc.ts:18-34,49-51` |
| Call | `method(input, options?)`. `options`: `location?`, `signal?`, `headers?`. `POST /api/rpc/:rpcID/:method` | `packages/client/src/promise/rpc.ts:8-10,100-112`, `packages/protocol/src/groups/rpc.ts:14` |
| Server handling | Awaits activation, then `rpc.call`. Unknown id: `rpc.unavailable`. Unknown method: `rpc.method_not_found` | `packages/server/src/handlers/rpc.ts:10-14`, `packages/core/src/rpc.ts:110-114` |
| Definition | `Rpc.define({ id, methods, events })` from `@opencode/plugin/rpc` or `@opencode/schema/rpc`, both provided in both processes | `packages/plugin/src/rpc.ts:1`, `packages/schema/src/rpc.ts:43-60`, `packages/plugin/src/gui/modules.ts:14-15` |
| Events | `rpc(Def).events.on(name, handler, { signal? })`, returns a stop function. `events.subscribe(name, options?)` is an async iterable | `packages/client/src/promise/rpc.ts:23-33,124-139` |
| Errors | Rejects with `{ type, message, data? }` | `packages/client/src/promise/rpc.ts:114-119` |
| Server part requirement | `features.rpc` needs both a server entry and `./rpc`. A GUI-only package has no RPC | `packages/core/src/plugin/module.ts:156`, `packages/plugin/src/host.ts:59` |

Location: with no `location`, the request falls back to the sidecar's cwd, which is home. Your server part answers from its home-location instance, not the session's directory. To reach a session's location, pass it (inference from `packages/server/src/location.ts:72-79`, `packages/protocol/src/groups/rpc.ts:16,26`):

```ts
const session = ctx.sessions.current()
const directory = session?.location?.directory
await ctx.client.rpc(Acme).search({ query: "todo" }, { location: { directory } })
```

The input and `location` types come from `packages/client/src/promise/rpc.ts:8-20` and `packages/client/src/promise/generated/types.ts:3223,4276-4281`.

A plugin configured only at project level has no GUI, so this path assumes a global plugin (section 1). A session on a remote server has its own `session.server.client`, but your server part may not exist there. `packages/plugin/src/gui/host-apis.ts:23,45`

Main can also read `ctx.serverEndpoints.get("sidecar")` for `url` and `headers`. `packages/plugin/src/gui/main.ts:112-149`. Prefer `ctx.client` unless you need a raw request (inference).

Follow server events from a window with `ServerRef.data.on(type, handler)`. `packages/plugin/src/gui/host-apis.ts:25`, `services/www/src/docs/content/build/plugins/gui/index.mdx:1760-1765`

## 15. What the built-ins guide means for third-party bundles

`packages/gui-plugins/README.md` and `AGENTS.md` are written for built-ins in the workspace.

| Item | Third-party? | Note | Pin |
| --- | --- | --- | --- |
| `@opencode/plugin/gui`, `/gui/main` | Yes | | `packages/gui-plugins/README.md:5-6` |
| `gui/host`: `compose`, bridge | No | Never published | `packages/gui-plugins/README.md:7`, `packages/plugin/script/pack.ts:7` |
| `gui/builtin`: `onIdle`, `Builtin*`, `builtinContext`, `builtinMainContext`, `builtinCatalog` | No | Never published | `packages/gui-plugins/README.md:8,313-325` |
| `gui/updater` | No | Workspace-only | `packages/plugin/script/pack.ts:7` |
| Host lists in `src/renderer.ts`, `src/main.ts` | No | Your plugin comes from config | `packages/gui-plugins/README.md:48,686-734` |
| `src/<id>/renderer.tsx`, `main.ts` split | Optional | One entry file is fine. All chunks inline into one bundle | `packages/plugin/src/gui/vite.ts:46,50` |
| Lazy locales | No | Rejected at load | `packages/gui-plugins/README.md:325`, `packages/plugin/src/gui/host.ts:289-304` |
| `lazy()` for heavy UI | Partly | Defers evaluation, not download (inference) | `packages/plugin/src/gui/vite.ts:50` |
| `ctx.layout.command`, `ctx.desktop.forceFocus`, `ctx.locale.setDirection`, `lifecycle.restart` | No | Typed only through built-in helpers. Host builds them on every context, but they are not public | `packages/gui-plugins/README.md:321-325`, `packages/plugin/src/gui/builtin.ts:272-278` |
| Rename migrations: keybind map, `BuiltinPanel.legacy` | No | `from` works for stores. Commands and panel keys have no third-party migration | `packages/gui-plugins/README.md:450` |
| Rules: derive don't sync, effects only for external sync, key objects, Suspense on first load, stable objects, no timeline work, no module state | Yes, as guidance | Lint enforces them only in `packages/gui-plugins/src` | `packages/gui-plugins/README.md:456-463` |
| Lifetimes, routed session, Live handling, stored state | Yes | | `packages/gui-plugins/README.md:89-142,356-371,399-449` |
| Test gates, lint, keeper suites, graph matrix, `sdk-docs` | No | Workspace tooling | `packages/gui-plugins/README.md:467-477,744-746` |
| `os` "omit it to run everywhere, the web included" | No | A config plugin runs only on desktop | `packages/gui-plugins/README.md:42`, `packages/plugin/src/gui/declarations.ts:15-17` |
| "A bundle [gets] the server plugin's id" | Mostly | A GUI-only plugin gets its package or folder name | `packages/gui-plugins/README.md:38`, `packages/plugin/src/host.ts:75-79` |
| `src/pairing` example | Shape only | Its `main.ts` uses `builtinMainContext` and `renderer.tsx` uses `onIdle`. Replace with `ctx.storage.store` and no idle preload. Its `if (!ctx.desktop) return` is not needed for you (inference) | `packages/gui-plugins/README.md:534-546,620-631`, `packages/gui-plugins/src/pairing/contract.ts:9-26` |

## 16. Minimal example

Both processes, one file. This plugin's id must be `acme` (a server part with `id: "acme"`, or a GUI-only `package.json` name of `acme`) or the Ipc `provide` throws. `packages/desktop/src/main/plugin/host.ts:628-646`

```tsx
import { Schema } from "effect"
import { Command, Ipc, Plugin, Store } from "@opencode/plugin/gui"

const Ping = Ipc.define({ id: "acme.ping", methods: { ping: { output: Schema.String } } })

export default Plugin.define({
  i18n: { en: { open: "Ping Acme" } },
  stores: { prefs: Store.global(Schema.Struct({ shown: Schema.Boolean }), { shown: true }) },
  setup(ctx) {
    ctx.add(Command, () => ({ id: "open", title: ctx.t("open"), run: () => void ctx.main(Ping).ping() }))
  },
  main(ctx) {
    ctx.provide(Ping, { ping: () => "pong" })
  },
})
```

Published command id: `acme.open`. `packages/app/src/runtime/plugin/commands.tsx:20`. `Ipc`, `Plugin` and `Store` are in both SDKs. `Command` is window-only and is read only inside `setup`. `packages/plugin/src/gui/main.ts:15,17`, `packages/plugin/src/gui/index.ts`
