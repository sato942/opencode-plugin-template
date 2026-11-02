# Where each concept lives in upstream

A map of [upstream/](../upstream/), for finding the code behind a concept. Paths are as upstream has them. [MANIFEST.json](../MANIFEST.json) lists what is copied, and [the full repository](https://github.com/anomalyco/opencode) has the rest. To copy another file, add it to the manifest and sync.

## What a plugin author imports

| Concept | Where |
|---|---|
| Server API, Promise | `packages/plugin/src/promise/`: `plugin.ts` is the context; one file per domain, such as `tool.ts`, `command.ts`, `session.ts` |
| Server API, Effect | `packages/plugin/src/effect/`, the same files |
| How they connect to the host | `packages/plugin/src/promise/adapter.ts` |
| TUI API | `packages/plugin/src/tui/`: `context.ts` has every member |
| GUI API | `packages/plugin/src/gui/`: `context.ts`, `registries.ts`, `host-apis.ts` for windows, `main.ts` for the main process |
| Modules Desktop provides to a bundle | `packages/plugin/src/gui/modules.ts` |
| Vite preset for the bundle | `packages/plugin/src/gui/vite.ts` |
| RPC contract | `packages/plugin/src/rpc.ts`, which re-exports `packages/schema/src/rpc.ts` |
| Tool shapes and schemas | `packages/schema/src/tool.ts` |
| Config entry shape | `packages/schema/src/config/plugin.ts` |
| What the package publishes | `packages/plugin/package.json`, `packages/plugin/script/pack.ts` |
| The authors' own notes | `packages/plugin/README.md`, `packages/plugin/src/README.md`, `packages/plugin/src/effect/README.md`, `packages/gui-plugins/README.md` |

## How the host runs a plugin

| Concept | Where |
|---|---|
| Which files are the parts | `packages/plugin/src/host.ts` |
| Finding config entries and directories | `packages/core/src/config/plugin/source.ts`, `packages/core/src/plugin/source-directory.ts` |
| Loading one plugin | `packages/core/src/plugin/module.ts` |
| Order, selectors, reload triggers, failed reloads | `packages/core/src/plugin/supervisor.ts` |
| Activation, teardown, the plugin list | `packages/core/src/plugin.ts` |
| Building the `ctx` a plugin receives | `packages/core/src/plugin/host.ts` |
| Hook ordering | `packages/core/src/plugin/hooks.ts` |
| Transform replay | `packages/core/src/state.ts` |
| Tools at runtime, schemas, Code Mode | `packages/core/src/tool.ts`, `packages/core/src/tool/runtime.ts` |
| Commands | `packages/core/src/command.ts`, `packages/core/src/session/command.ts` |
| RPC dispatch | `packages/core/src/rpc.ts`, `packages/server/src/handlers/rpc.ts` |
| Plugin storage | `packages/core/src/kv.ts` |
| Importing with the host's `effect` | `packages/plugin/src/runtime.ts`, `packages/plugin/src/runtime-modules.ts`, `packages/cli/src/node/plugin-runtime.promise.ts` |
| Installing packages | `packages/util/src/npm.ts`, `packages/core/src/plugin/update.ts` |
| Global paths | `packages/util/src/global-roots.ts` |
| HTTP API for plugins | `packages/protocol/src/groups/plugin.ts`, `packages/protocol/src/groups/rpc.ts`, `packages/server/src/handlers/plugin.ts` |
| `opencode plugin` commands | `packages/cli/src/commands/commands.ts`, `packages/cli/src/commands/handlers/plugin/` |
| Terminal UI host | `packages/tui/src/plugin/`: `context.tsx` loads, `api.tsx` builds the context, `discovery.ts` finds directories |
| Desktop's main process host | `packages/desktop/src/main/plugin/`: `host.ts` lists and evaluates, `lifecycle.ts` runs |
| Desktop's window host | `packages/app/src/runtime/plugin/`: `plugins.tsx` chooses which plugins, `host.tsx` runs them, `extension-plugins.tsx` is the Settings page |

## Real plugins to read

| Plugin | Shows | Where |
|---|---|---|
| Figma | The smallest published plugin: a package, an MCP server and skills | `packages/plugins/figma/` |
| Browser | A larger server plugin with RPC, tools, a skill and tests | `packages/plugin-browser/` |
| Pairing | A GUI plugin with a window part and a main part. It uses built-in helpers a third-party bundle cannot ([gui.md](gui.md#15-what-the-built-ins-guide-means-for-third-party-bundles)) | `packages/gui-plugins/src/pairing/` |
| Built-in server plugins | Every server feature in use | `packages/core/src/plugin/`: `command.ts`, `skill.ts`, `plan.ts`, `goal/` and the rest |
| Built-in TUI plugin | A real TUI part | `packages/tui/src/feature-plugins/system/plugins.tsx` |

## Tests, as a record of intended behaviour

| What | Where |
|---|---|
| Loading, reload and failure | `packages/core/test/plugin.test.ts`, `packages/core/test/plugin-failure.test.ts`, `packages/core/test/plugin/` |
| Resolving parts | `packages/plugin/test/host.test.ts` |
| The GUI build | `packages/plugin/test/gui-vite.test.ts` |
| `plugin add` | `packages/cli/test/plugin-add.test.ts` |
| A TUI part | `packages/tui/test/plugin-discovery.test.ts`, `packages/tui/test/plugin-select.test.tsx` |

## The official docs

| Topic | Where |
|---|---|
| Overview, server, RPC, TUI, GUI, Effect, migration | `services/www/src/docs/content/build/plugins/` |
| Configuring and installing | `services/www/src/docs/content/plugins.mdx`, `services/www/src/docs/content/cli/plugins.mdx` |
| The whole docs' order | `services/www/src/docs/lib/navigation.ts` |
| What plugins hook into | `services/www/src/docs/content/`: `tools.mdx`, `agents.mdx`, `commands.mdx`, `skills.mdx`, `permissions.mdx`, `policies.mdx`, `providers.mdx`, `models.mdx`, `mcp-servers.mdx`, `compaction.mdx` and others |
| V1 | `packages/web/src/content/docs/plugins.mdx`, `custom-tools.mdx`, `ecosystem.mdx`, `sdk.mdx`, `server.mdx` |
| Design notes | `specs/v2/catalog-config-plugin-lifecycle.md`, `specs/v2/tools.md`, `specs/v2/session.md` |
