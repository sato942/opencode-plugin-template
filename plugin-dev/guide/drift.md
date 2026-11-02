# Where OpenCode's docs and source disagree

[The source wins](../README.md#what-wins-when-sources-disagree). This page lists what was found by reading the docs against the source, so nobody has to find it twice, and every entry names what to do instead.

**Last reviewed at commit `1bf08ae46a`, on 3 November 2026.** The pin can move on: `tools/sync_upstream.py --check` lists any entry here whose file has changed. When you re-read one, keep it, correct it or remove it, and update this line. Add a row when you find a new one.

**Evidence.** Most entries were read from both sides, and not run. **Observed** means a real run on OpenCode CLI 2.2.1 and 2.2.5, in an isolated instance ([testing.md](testing.md)). "(inference)" marks a conclusion no single line states.

## These break a plugin

| The doc | What it says | What really happens | Do this instead | Evidence |
|---|---|---|---|---|
| `services/www/src/docs/content/build/plugins/rpc.mdx:71-73`, `services/www/src/docs/content/build/plugins/effect/rpc.mdx:48-49` | Leave out `input` or `output` if a method has no such value | Both are required (`packages/schema/src/rpc.ts:13-17`). Each call fails with HTTP 500 `rpc.internal` (`packages/core/src/rpc.ts:117`, `packages/core/src/rpc.ts:139`). With only `output` missing, **the handler runs first**, so its effects happen and the caller still gets an error | Always give both. OpenCode's own tests use `input: Schema.Undefined` (`packages/core/test/rpc-handler-errors.test.ts:18`) | **Observed.** All three cases failed, and the handler ran in the `output` case |
| `services/www/src/docs/content/build/plugins/rpc.mdx:113` | Presents `events` as something to add when a contract has events | `Rpc.define` adds no default (`packages/schema/src/rpc.ts:54-60`), and `Object.entries(definition.events)` throws while registering (`packages/core/src/rpc.ts:60`, `packages/core/src/rpc.ts:87`). With `await ctx.rpc.register`, the plugin shows `state: failed`, with `TypeError: Object.entries requires that input parameter not be null or undefined`. Without `await`, the plugin reads `active` and its methods work, and the server only logs an unhandled rejection | Always write `events: {}`, and always `await` the registration. `npm run typecheck` catches the missing key | **Observed**, both ways |
| `services/www/src/docs/content/build/plugins/gui/index.mdx:225`, and the comment at `packages/core/src/plugin.ts:44` | A rebuild reloads the GUI. "The server entry does not restart" | The bundle's modified time goes into the plugin's revision (`packages/core/src/config/plugin/source.ts:178-191`, `packages/core/src/plugin/module.ts:135`), so that plugin's `setup` runs again, and so does every plugin's after it (`packages/core/src/plugin.ts:122-126`). The test that says otherwise passes no modified time (`packages/core/test/plugin.test.ts:140`) | Keep server state restart-safe, and expect other plugins to restart while you run `vite build --watch` | **Observed.** Changing only the bundle took `setup` from 1 to 2 runs in the plugin and in the one after it |
| `services/www/src/docs/content/build/plugins/effect.mdx:1476`, `services/www/src/docs/content/build/plugins/effect.mdx:1484` | `Effect.fail(new Tool.Error(...))`, with no import shown | `@opencode/plugin/effect` exports no `Tool` (`packages/plugin/src/effect/index.ts:1`), and `@opencode/schema/tool` is not a package the host shares (`packages/plugin/src/runtime-modules.ts:7`). The example cannot be written as shown | Read `packages/plugin/src/effect/tool.ts` for what the Effect API accepts. Not settled here | Read |
| `services/www/src/docs/content/build/plugins/gui/index.mdx:199-201`, `services/www/src/docs/content/plugins.mdx:135-136` | "Configure the plugin in the global `opencode.json(c)` to make its GUI available in every window." This reads as if a project's config gives some windows the GUI | There is no per-window set. Desktop lists plugins with no location (`packages/desktop/src/main/plugin/host.ts:440`), the server falls back to its working directory (`packages/server/src/location.ts:72-79`), and the background service runs from the home directory (`packages/cli/src/server-process.ts:62-66`). A plugin configured in a project elsewhere gets no GUI in any window, with no message (inference for the composition; each step is read) | For a GUI, use the global config. Say so in the plugin's install notes | Read, `UNEXECUTED` |
| `services/www/src/docs/content/cli/plugins.mdx:15-16` | Lists `"opencode.example"` and `"opencode.example@1.0.0"` as `cli.json` entries | A target starting `opencode.` is a selector. Nothing loads, and no error appears (`packages/tui/src/plugin/context.tsx:327`, `packages/core/src/plugin/supervisor.ts:48`) | Never name a package `opencode.something` | Read |
| `services/www/src/docs/content/cli/plugins.mdx:7`, `services/www/src/docs/content/build/plugins/cli.mdx:656` | A plugin in `opencode.json` needs no `cli.json` entry, "so this also works when the server is remote" | Server entries are not installed on the client. If the package is not already in the client's cache, it is skipped with no message (`packages/tui/src/plugin/context.tsx:301-305`, `packages/util/src/npm.ts:349-356`, `packages/tui/src/plugin/context.tsx:362-363`). A same-machine server shares the cache, which hides this (inference for the resolver's error) | For a remote server, list the package in `cli.json` too | Read |
| `services/www/src/docs/content/cli/plugins.mdx:6`, `services/www/src/docs/content/build/plugins/cli.mdx:31` | "You do not need to add the same package to `cli.json`", with `context.options` used in the same page | The plugin list carries no options (`packages/schema/src/plugin.ts:51-56`), so options in `opencode.json` never reach a TUI part (`packages/tui/src/plugin/context.tsx:332`), though they do reach a GUI part | A TUI part that reads options must be in `cli.json`, in object form | Read |
| `services/www/src/docs/content/build/plugins/cli.mdx:323,328` | An inline command with `run: (_input, event) => (event ? false : undefined)`, to continue keyboard dispatch | An inline command's `run` gets no arguments (`packages/tui/src/context/keymap.tsx:244`), so `event` is always undefined, and the key is consumed | Give the command an `id`, which gets the event (`packages/tui/src/context/keymap.tsx:232`), or return `false` unconditionally | Read |

## These mislead

Read from both sides, not run.

| The doc | What it says | What the source does | Source |
|---|---|---|---|
| `services/www/src/docs/content/build/plugins/server.mdx:1439` | "`options` starts empty for each model call; it does not contain resolved model settings." | Primary and compaction start with `{ maxTokens: outputLimit(...) }`. Only title and generate start `{}`. The comment says hooks "see the default output limit and may change or remove it". | `packages/core/src/session/model-request.ts:261-275` |
| `services/www/src/docs/content/build/plugins/server.mdx:39-40`, `services/www/src/docs/content/build/plugins/server.mdx:223-224`, and every `requestOptions?: RequestOptions` signature, such as `services/www/src/docs/content/build/plugins/server.mdx:650`, `services/www/src/docs/content/build/plugins/server.mdx:842-866`, `services/www/src/docs/content/build/plugins/server.mdx:1117-1122`, `services/www/src/docs/content/build/plugins/server.mdx:1301-1302` | "Its read and action methods use the same inputs and responses as the client." `list(input?: AgentListInput, requestOptions?: RequestOptions)` | The Promise adapter's method wrapper is `((input?: unknown) => ...)`. A second argument is ignored, so `signal` and `headers` have no effect. `RequestOptions` has `signal`, `headers`, `onActivity`. | `packages/plugin/src/promise/adapter.ts:271`, `packages/client/src/promise/generated/client.ts:330-335` |
| `services/www/src/docs/content/build/plugins/server.mdx:389`; signatures `services/www/src/docs/content/build/plugins/server.mdx:650`, `services/www/src/docs/content/build/plugins/server.mdx:1117`, `services/www/src/docs/content/build/plugins/server.mdx:1119`, `services/www/src/docs/content/build/plugins/server.mdx:1121` | "Read the commands available at a location." Inputs are the client types, which include `location`. | Host ignores input for command, provider, model, plugin, reference, skill, and vcs reads. Only `agent.get`, `agent.list`, and `mcp.list` honour `location`. | `packages/core/src/plugin/host.ts:261`, `packages/core/src/plugin/host.ts:203`, `packages/core/src/plugin/host.ts:238`, `packages/core/src/plugin/host.ts:469`, `packages/core/src/plugin/host.ts:472`, `packages/core/src/plugin/host.ts:485`, `packages/core/src/plugin/host.ts:509-514`, `packages/core/src/plugin/host.ts:134-157`, `packages/core/src/plugin/host.ts:426-434`, `packages/client/src/promise/generated/types.ts:4268` |
| `services/www/src/docs/content/build/plugins/effect.mdx:113`, `services/www/src/docs/content/build/plugins/effect.mdx:116-146` | "The plugin definition and complete context are declared as follows." The block has no `credential` or `experimental.artifact`, and has `readonly generate: GenerateApi<unknown>`. | Source has `credential`, `experimental.artifact`, and `experimental.generate: ExperimentalGenerateApi`. | `packages/plugin/src/effect/plugin.ts:34`, `packages/plugin/src/effect/plugin.ts:39-40` |
| `services/www/src/docs/content/build/plugins/server.mdx:1588-1601` | `interface SessionHooks` ends at `retry: SessionRetryHook`. | Source also has `"experimental.idle"`, and it does fire. | `packages/plugin/src/promise/session.ts:198`, `packages/core/src/session/runner/llm.ts:179-183` |
| `services/www/src/docs/content/build/plugins/effect.mdx:1406-1418` | `interface SessionHooks` starts at `context` and ends at `retry`. | Source also has `prompt` and `"experimental.idle"`. | `packages/plugin/src/effect/session.ts:185-199` |
| `services/www/src/docs/content/build/plugins/effect.mdx:14`, `services/www/src/docs/content/build/plugins/effect.mdx:1541-1542`, `services/www/src/docs/content/build/plugins/effect.mdx:1556`, `services/www/src/docs/content/build/plugins/effect.mdx:1559` | `bun add --peer @opencode/plugin effect@4.0.1`; "pin the version `@opencode/plugin` uses"; `"effect": "4.0.1"` | Workspace catalog is `"effect": "4.1.0"`. | `package.json:83`, `packages/plugin/package.json:43-51` |
| `services/www/src/docs/content/build/plugins/server.mdx:638` | "List the plugins currently active for a location." | Inventory slots include status `failed`. `services/www/src/docs/content/build/plugins/effect.mdx:708` was checked and is accurate. | `packages/core/src/plugin.ts:43`, `packages/core/src/plugin.ts:298-307` |
| `services/www/src/docs/content/build/plugins/migrate-v1.mdx:228` | "Tool schemas use JSON Schema" | `ValueSchema` also takes Effect `Schema.Codec` and Standard Schema. | `packages/schema/src/tool.ts:44` |
| `services/www/src/docs/content/build/plugins/gui/index.mdx:212` | "A plugin whose server part fails to load has no GUI." | True on first load, and when setup throws. When a later revision fails to import, the running generation keeps its place and stays listed `active`, so its GUI stays (inference for the GUI step) | `packages/core/src/plugin/supervisor.ts:80-85`, `packages/core/test/plugin/supervisor-reload.test.ts:275-284`, `packages/plugin/src/gui/host.ts:383-388` |
| `services/www/src/docs/content/build/plugins/gui/index.mdx:3051-3052`, `services/www/src/docs/content/build/plugins/gui/index.mdx:3245-3246` | "A call waits while `main` starts. It rejects when `main` cannot answer: on the web, while the plugin's `main` is off or failed, or when the method throws." | With no `main` entry the call "waits indefinitely". `absent(id, true)` skips the "not coming" branch, so main that runs but never provides the token also stays `pending` (inference for the second case) | `packages/plugin/src/gui/context.ts:79-82`, `packages/app/src/runtime/plugin/host.tsx:199-212` |
| `services/www/src/docs/content/build/plugins/gui/index.mdx:413-414,2333,2342,2662,3051,3093,3178,3243` | Web branches, such as "`ctx.desktop` ... is `undefined` on the web" and "`Browser` is `inactive` on the web", with no statement that third-party GUIs do not run on the web | A config plugin "runs only in the desktop app". The web has no bridge, so no loader. The doc page never says this | `packages/plugin/src/gui/declarations.ts:15-17`, `packages/app/src/runtime/plugin/root.tsx:91-103,139`, `packages/app/src/runtime/plugin/extension-plugins.tsx:19-22` |
| `services/www/src/docs/content/plugins.mdx:145` | "**Reload** loads it again after a failure." | Reload is on every live row. It reruns the bundle main last read and does not fetch a new one | `packages/app/src/runtime/plugin/extension-plugins.tsx:136-139,189-194`, `packages/desktop/src/main/plugin/host.ts:968-976` |
| `services/www/src/docs/content/build/plugins/gui/index.mdx:2468-2469` | `global(schema: Schema, initial: T, from?: string \| string[])`, and `session` likewise | Window stores take only an object schema: `StoreSchema = Schema.ConstraintCodec<object, unknown>`. Primitives work only in main | `packages/plugin/src/gui/core.ts:458,504-508,522-526`, `packages/plugin/src/gui/main.ts:94` |
| `services/www/src/docs/content/build/plugins/gui/index.mdx:1160-1162`, `services/www/src/docs/content/build/plugins/gui/index.mdx:1170-1174` | "`rows` make the pill open a menu" and "Without `rows`, the pill runs `run` on click". Reference: `interface ComposerPill { id; order?; show(...) }` | `ComposerPill` also has `menu?(input: ComposerPillMenuProps)`. With `menu`, `rows` are unused | `packages/plugin/src/gui/registries.ts:623-626,641,665-673` |
| `services/www/src/docs/content/build/plugins/cli.mdx:432-433` | `context.ui.dialog.set({ size: "large", centered: true })`, then `context.ui.dialog.show(`. | `show` calls `dialog.replace`, which runs `setStore("size", options?.size ?? "medium")` and `setStore("centered", false)`. A `set` before `show` is discarded. The repo calls `show` first. `set` also resets a missing key: `options.size ?? "medium"`, `options.centered ?? false`. | `packages/tui/src/plugin/api.tsx:334-336`, `packages/tui/src/ui/dialog.tsx:409-410`, `packages/tui/src/feature-plugins/prompt/btw.tsx:71`, `packages/tui/src/plugin/api.tsx:338-339` |
| `services/www/src/docs/content/build/plugins/cli.mdx:411` | "or Tab focus followed by Enter." | The test is named "actions deliver the selected value %p from keyboard and footer click, not tab". After `pressTab()` then Enter, the option value resolves and the action is not triggered. `dialog-select.tsx` has no Tab handling (grep). Test read, not run. | `packages/tui/test/plugin-select.test.tsx:269`, `packages/tui/test/plugin-select.test.tsx:298` |
| `services/www/src/docs/content/build/plugins/cli.mdx:649-650` | `"@opentui/core": ">=0.6.6"`, `"@opentui/solid": ">=0.6.6"`. | `@opencode/plugin` peers are `">=0.8.1"`. The repo catalog is `0.8.1`. | `packages/plugin/package.json:54-55`, `package.json:57` |
| `services/www/src/docs/content/build/plugins/cli.mdx:497-498,506` | "replace the built-in variant cycle", with `bind: "tab"`. | The built-in is `"variant.cycle": keybind("ctrl+t", ...)` and stays registered. `tab` is `prompt.autocomplete.complete`. `agent.cycle` is `shift+tab`. The example adds a binding on another key and replaces nothing. | `packages/tui/src/config/keybind.ts:178`, `packages/tui/src/app.tsx:986`, `packages/tui/src/config/keybind.ts:280`, `packages/tui/src/config/keybind.ts:176` |
| `services/www/src/docs/content/build/plugins/cli.mdx:21`, `services/www/src/docs/content/cli/plugins.mdx:60` | "OpenCode resolves this import at runtime" | True on the Bun build. On the Node build: "Node loads precompiled plugins without it", `if (typeof Bun === "undefined") return {}`, and the module map has no `@opencode/plugin/tui`. Scope is narrow: only `@opencode/cli-node`, command `opencode-node`. | `packages/tui/src/plugin/runtime-plugin-support.bun.ts:5`, `packages/tui/src/plugin/runtime-plugin-support.node.ts:1`, `packages/plugin/src/runtime.ts:13`, `packages/cli/vite.node.config.ts:171`, `packages/cli/bin/opencode.cjs:36` |

## Small differences

| The doc | What it says | What the source does | Source |
|---|---|---|---|
| `services/www/src/docs/content/build/plugins/server.mdx:1607`, `services/www/src/docs/content/build/plugins/server.mdx:1616`, `services/www/src/docs/content/build/plugins/server.mdx:1624` | WebSocket hook `kind: "primary" \| "compaction" \| "title" \| "generate"` | The type agrees, but title and generate never pass `webSocket: "session"`, so these hooks see `primary` or `compaction` only. | `packages/core/src/session/model-request.ts:369-370`, `packages/core/src/session/runner/llm.ts:272`, `packages/core/src/session/compaction.ts:556`, `packages/core/src/session/title.ts:71-77`, `packages/core/src/session/generate.ts:47-58` |
| `services/www/src/docs/content/build/plugins/server.mdx:1687` | Example calls `ctx.generate.text`, while `services/www/src/docs/content/build/plugins/server.mdx:704` calls it deprecated. | `generate` is `@deprecated`. | `packages/plugin/src/promise/plugin.ts:45-46` |
| `services/www/src/docs/content/build/plugins/migrate-v1.mdx:221` | "Use `model.request` for model request headers and raw request settings," | The event's mutable fields are only `baseURL` and `headers`. | `packages/plugin/src/promise/session.ts:68-75` |
| `packages/plugin/src/README.md:67-79`, `packages/plugin/src/README.md:187-199` | "Available transform hooks" and "Available reload operations" lists | Omit `ctx.worktree` and `ctx.experimental.artifact`, which have both. | `packages/plugin/src/promise/adapter.ts:601-621`, `packages/plugin/src/promise/adapter.ts:352-374` |
| `packages/plugin/src/effect/README.md:52-64`, `packages/plugin/src/effect/README.md:178-190` | Same two lists. | Same omission. | `packages/plugin/src/effect/worktree.ts:19-20`, `packages/plugin/src/effect/plugin.ts:40`, `packages/plugin/src/effect/plugin.ts:59` |
| `services/www/src/docs/content/build/plugins/server.mdx:1634`, `services/www/src/docs/content/build/plugins/effect.mdx:1426` | `readonly error: { type: string; message: string; status?: number }` | `SessionError.Error` also has `response` and `retryAfterMs`. | `packages/schema/src/session-error.ts:7-14` |
| `services/www/src/docs/content/build/plugins/effect.mdx:884-904` | `SessionDomain = Pick<SessionApi<unknown>, ... "wait" ... "instructions">`, with no `hook`. | `wait` and `instructions` come from `ExperimentalSessionApi`, and the type adds `hook`. `SessionApi.wait` is deprecated. | `packages/plugin/src/effect/session.ts:201-221`, `packages/client/src/effect/api/api.ts:456-472` |
| `services/www/src/docs/content/build/plugins/server.mdx:841-867` | Reference `interface SessionContext` starts at `create`. | `list` is also on the domain. Usage appears at `services/www/src/docs/content/build/plugins/server.mdx:785`, but the reference omits it. | `packages/plugin/src/promise/session.ts:203` |
| `services/www/src/docs/content/plugins.mdx:144` | "lists them when the app's own server is selected" | Other servers and the web also list them, by name only | `packages/app/src/runtime/plugin/extension-plugins.tsx:19-41` |
| `services/www/src/docs/content/build/plugins/gui/index.mdx:266` | "In `main`, a missing key returns the key." | Main tries `nativeMessage(key)` first | `packages/desktop/src/main/plugin/host.ts:764-765` |
| `services/www/src/docs/content/build/plugins/gui/index.mdx:2475` | `update(mutate: (draft: T) => undefined): void` | Draft type is `Mutable<T>`, which removes readonly | `packages/plugin/src/gui/core.ts:552-557,568` |
| `services/www/src/docs/content/build/plugins/gui/index.mdx:991` | `"session.header": { screen; session; active }` | Also `compact: boolean` | `packages/plugin/src/gui/registries.ts:681-694` |
| `services/www/src/docs/content/build/plugins/gui/index.mdx:1648-1658` | `ComposerNote` with no `title` or `subtitle` | Both exist as optional display fields | `packages/plugin/src/gui/host-apis.ts:486,488` |
| `services/www/src/docs/content/build/plugins/gui/index.mdx:1739` | `focus(commentID?: string): void` | `focus(commentID?: string, options?: ComposerFocusOptions): void`, plus `ComposerQuoteAnchor` | `packages/plugin/src/gui/host-apis.ts:544-562,656` |
| `services/www/src/docs/content/build/plugins/gui/index.mdx:933-941` | `SettingsPage` with no `group` | `group?: "about"` | `packages/plugin/src/gui/registries.ts:398` |
| `services/www/src/docs/content/build/plugins/cli.mdx:520-521` | Slot list of nine names ends with `sidebar.content`, or `sidebar.footer`, without `session.panel`. | `readonly "session.panel": PanelInput` is a tenth slot. The doc covers it later, at `services/www/src/docs/content/build/plugins/cli.mdx:547`. | `packages/plugin/src/tui/context.ts:199` |

The SDK's own comments can be wrong too, and editor hovers show them:

| Source location | What it says | What the source does | Pin |
| --- | --- | --- | --- |
| `packages/plugin/src/gui/core.ts:352` | `ctx.id`: "as its `Plugin.define` declares it" | "It declares no id". The host assigns it | `packages/plugin/src/gui/plugin.ts:59`, `packages/plugin/src/gui/declarations.ts:9-10` |
| `packages/core/src/plugin.ts:44` | "A changed `./gui-experimental` bundle alone restarts nothing" | **Observed** false: see the first table | `packages/core/src/config/plugin/source.ts:178-191` |

## Also misleading, though not wrong

| Where | What to know | Pin |
|---|---|---|
| A search for the OpenCode plugin docs | `opencode.ai/docs/plugins` is the V1 page, live and with no note of V2. Its package and API do not work on V2 | `packages/web/src/content/docs/plugins.mdx:131` |
| GitHub's "latest release" | On 3 November 2026 the API's latest release was a V1 tag, v1.19.5, though v2.2.5 existed. Read npm's `@opencode/cli` for the V2 version | |
| The V2 overview's `package.json` | Uses `"dependencies": { "@opencode/plugin": "latest" }`. The official Figma plugin uses a peer range, which suits a published package better ([packaging.md](packaging.md)) | `services/www/src/docs/content/build/plugins/index.mdx:39`, `packages/plugins/figma/package.json:1` |
| Where packages install | The V1 docs name `~/.cache/opencode/node_modules/`. V2 uses `<cache>/npm/<key>` | `packages/util/src/npm.ts:139` |

## What the docs do not say

Source behaviour that a plugin author will meet, and the docs leave out.

### Server

| Behaviour | Source | Note |
|---|---|---|
| Plugin tools default to Code Mode only: without `codemode: false` the tool is not a direct model tool while Code Mode is on. | `packages/core/src/tool.ts:262-265` | Docs show `codemode: true` and `codemode: false` in examples only (`services/www/src/docs/content/build/plugins/server.mdx:994`, `services/www/src/docs/content/build/plugins/effect.mdx:1022`, `packages/plugin/src/README.md:157`). Likely time sink for authors. |
| `options.pinned` | `packages/schema/src/tool.ts:36`, `packages/core/src/codemode/tool.ts:221-225` | No doc hit. |
| `options.permission` | `packages/schema/src/tool.ts:29`, `packages/core/src/tool.ts:257` | No doc hit. |
| A transform throw disables the whole plugin. | `packages/core/src/plugin.ts:65-78`, `packages/core/src/state.ts:198-203` | No doc hit. |
| A restart re-runs every plugin after the changed one. | `packages/core/src/plugin.ts:122-151` | No doc hit. |
| A failed reload loads the previous definition again and keeps the error on the slot. | `packages/core/src/plugin.ts:168-181` | No doc hit. |
| `execute` must not return an `output` key without an `output` schema: defect. | `packages/core/src/tool/runtime.ts:47-48` | No doc hit in the tool sections read. |
| JSON Schema `output` is checked only as JSON, not against the schema. | `packages/core/src/tool/runtime.ts:129-133` | |
| Standard Schema tools need JSON Schema conversion (`~standard.jsonSchema` or Zod), else registration is skipped. | `packages/core/src/tool/runtime.ts:169-173`, `packages/core/src/tool.ts:403-407` | `services/www/src/docs/content/build/plugins/rpc.mdx:64-67` lists Valibot and ArkType for RPC, not for tools. |
| `execute.before` fires for the `execute` wrapper and again for each inner Code Mode call. | `packages/core/src/tool.ts:181-182`, `packages/core/src/tool.ts:275`, `packages/core/src/tool.ts:307` | |
| Setting `event.tool` redirects the call. | `packages/core/src/tool.ts:307-316` | Docs mention replacing input only (`services/www/src/docs/content/build/plugins/server.mdx:1749`). |
| `context` hook drops invented tool entries. | `packages/core/src/session/model-request.ts:278-286` | |
| `retry` hook does not fire for `session.generate`. | `packages/core/src/session/generate.ts:64` | |
| `ctx.aisdk.hook` | `packages/plugin/src/promise/aisdk.ts:5-22`, `packages/core/src/aisdk.ts:344-353` | READMEs only (`packages/plugin/src/README.md:101-110`, `packages/plugin/src/effect/README.md:89-104`), plus a type line at `services/www/src/docs/content/build/plugins/effect.mdx:121`. |
| `session.hook("experimental.idle")` | `packages/plugin/src/promise/session.ts:147-183` | READMEs only (`packages/plugin/src/README.md:126-146`). |
| Session and shell hook rejection is a defect. | `packages/plugin/src/promise/adapter.ts:625`, `packages/plugin/src/promise/adapter.ts:662` | README only (`packages/plugin/src/README.md:145-146`, partial). |
| `ctx.experimental.artifact` | `packages/plugin/src/promise/artifact.ts:45-57`, `packages/core/src/plugin/host.ts:295-319` | No doc hit. |
| `ctx.experimental.terminal.read` | `packages/core/src/plugin/host.ts:288` | Type line at `services/www/src/docs/content/build/plugins/effect.mdx:125` only. |
| `integration.connect.external` | `packages/client/src/effect/api/api.ts:1697`, `packages/core/src/plugin/host.ts:331-346` | Reference block `services/www/src/docs/content/build/plugins/server.mdx:523-525` shows `key` only. |
| `integration.connection.status` | `packages/plugin/src/promise/integration.ts:100-105` | Reference blocks `services/www/src/docs/content/build/plugins/server.mdx:548-551`, `services/www/src/docs/content/build/plugins/effect.mdx:638-641` stop at `resolve`. |
| `vcs.base()` and `VcsDefinition.base` | `packages/plugin/src/promise/vcs.ts:30`, `packages/core/src/plugin/host.ts:510`, `packages/core/src/vcs.ts:199-203` | Reference blocks `services/www/src/docs/content/build/plugins/server.mdx:1116-1125`, `services/www/src/docs/content/build/plugins/server.mdx:1135-1138` omit them. |
| Effect `VcsDiffInput.untracked`, absent in the Promise type. `ctx.vcs.diff` drops the client input. | `packages/plugin/src/effect/vcs.ts:24`, `packages/plugin/src/promise/vcs.ts:18-23`, `packages/core/src/plugin/host.ts:515` | No doc hit. |
| `websearch` default `"random"` | `packages/core/src/plugin/host.ts:540-543`, `packages/core/src/websearch.ts:32` | No doc hit. |
| RPC: last registration of an id wins. | `packages/core/src/rpc.ts:111` | No doc hit. |
| RPC: system error names, and that an undeclared throw becomes `rpc.internal`. | `packages/schema/src/rpc.ts:102-109`, `packages/core/src/rpc.ts:127-131`, `packages/core/src/rpc.ts:231-235` | No doc hit for `rpc.internal` or `rpc.unavailable`. |
| RPC: client rejection value is a plain object. | `packages/client/src/promise/rpc.ts:114-119` | |
| Storage is global across locations for a plugin id, and scan limit clamps to 1..1000. | `packages/core/src/kv.ts:61`, `packages/core/src/kv.ts:92`, `packages/core/src/plugin/host.ts:664-667` | Docs say only "scoped to the plugin" (`services/www/src/docs/content/build/plugins/server.mdx:929`, `services/www/src/docs/content/build/plugins/migrate-v1.mdx:324-325`). |
| `ctx.plugin.list` during `setup` returns the inventory from before this activation. | `packages/core/src/plugin.ts:50-52`, `packages/core/src/plugin.ts:184` | |
| Post built-ins run after external plugins, so their transforms replay last. | `packages/core/src/plugin/supervisor.ts:94-98`, `packages/core/src/plugin/internal.ts:276-296` | |

### TUI

| Behaviour | Source |
|---|---|
| Attention is off by default: `attention.notifications ?? false`, `attention.sound ?? false`, then `skipped("attention_disabled")`. A plugin's `notify` does nothing until the user enables it. | `packages/tui/src/config/index.tsx:307-308`, `packages/tui/src/attention.ts:131` |
| A slow or hung async `setup` holds startup. `<Show when={plugins.ready()}>` waits, the screen shows `Loading plugins…`, plugins are awaited in sequence, and a stall is only logged. | `packages/tui/src/app.tsx:1438`, `packages/tui/src/component/startup-loading.tsx:8`, `packages/tui/src/plugin/context.tsx:428`, `packages/tui/src/plugin/context.tsx:119` |
| Package plugins do not hot reload: "Package entrypoints never change within a session". | `packages/tui/src/plugin/context.tsx:663` |
| The `/plugins` toggle is not saved: "config wins over manual dialog toggles on every reconcile". | `packages/tui/src/plugin/context.tsx:419-422` |
| During `setup`, slots do not render, `ui.panel.open` returns false, and an unregister is a no-op that leaves the contribution in place. | `packages/tui/src/plugin/context.tsx:510`, `packages/tui/src/plugin/api.tsx:232`, `packages/tui/src/plugin/api.tsx:140` |
| `toast.sessionID` and the default duration of 5000 ms. | `packages/plugin/src/tui/context.ts:276-277`, `packages/tui/src/plugin/api.tsx:116`, `packages/tui/src/ui/toast.tsx:168` |
| `router.navigate({ type: "plugin", id, name })` reaches another plugin's route. A duplicate name throws `Route already registered`. | `packages/tui/src/plugin/api.tsx:221`, `packages/tui/src/plugin/api.tsx:212` |
| Slot resolution rules: last enabled wins, an ancestor replacement beats a descendant, an unmounted path degrades or is dropped. `services/www/src/docs/content/build/plugins/cli.mdx:587` says only "existing replacement ordering rules". The rules are stated only in SDK comments. | `packages/plugin/src/tui/context.ts:205-223`, `packages/tui/src/plugin/structure.ts:77-141` |
| Bare text is rejected with `rendered bare text; wrap it in <text>`. A crash is contained per contribution, with a toast. `render` runs once, untracked. | `packages/tui/src/plugin/render.tsx:55-56`, `packages/tui/src/plugin/render.tsx:27-47`, `packages/tui/src/plugin/render.tsx:128` |
| Storage key rule `^[a-zA-Z0-9][a-zA-Z0-9._-]*$` applies to `plugin.<id>.<key>`, so an id like `@scope/name` throws. Files live under `<state>/<channel>/tui`. A repeat `store` returns the first entry, and the new `initial` is ignored. | `packages/tui/src/context/storage.tsx:43`, `packages/tui/src/plugin/api.tsx:201`, `packages/tui/src/context/storage.tsx:52`, `packages/tui/src/context/storage.tsx:59` |
| A layer's default mode is `base`, so it is inactive while a dialog pushes `modal`. Also undocumented: layer `enabled`, command `bind: false`, command `description`. | `packages/tui/src/context/keymap.tsx:217`, `packages/tui/src/ui/dialog.tsx:322`, `packages/tui/src/context/keymap.tsx:216`, `packages/tui/src/context/keymap.tsx:252`, `packages/plugin/src/tui/context.ts:413` |
| Plugin command IDs cannot be rebound in `keybinds`: the schema is closed and `parse` throws `Unrecognized keybind`. The `bindings: ["acme.status"]` example at `services/www/src/docs/content/build/plugins/cli.mdx:302` therefore finds nothing, despite the type comment "Stable command and config keybind identifier" (inference on how the decoder treats excess keys and on the lookup's miss). | `packages/tui/src/config/keybind.ts:308-315`, `packages/tui/src/config/keybind.ts:342-343`, `packages/tui/src/context/keymap.tsx:258`, `packages/plugin/src/tui/context.ts:408` |
| A later plugin with the same `id` overrides an earlier one, built-ins included. Selectors match the TUI part's `id`, not the package name. | `packages/tui/src/plugin/context.tsx:315`, `packages/tui/src/plugin/context.tsx:390`, `packages/tui/src/plugin/context.tsx:648` |
| Relative `cli.json` entries resolve against the directory of `cli.json`, not the cwd. | `packages/tui/src/plugin/context.tsx:104`, `packages/tui/src/plugin/context.tsx:333` |
| A server part that failed or is inactive hides the TUI part: `plugin.state.status === "active"`. | `packages/tui/src/plugin/context.tsx:99` |
| A `cli.json` entry with no `./tui` becomes `unsupported`: no toast, and `/plugins` hides it. | `packages/tui/src/plugin/context.tsx:362-365`, `packages/tui/src/feature-plugins/system/plugins.tsx:58` |
| A TUI-only package listed in `opencode.json` fails on the server with `Plugin entrypoint not found`. | `packages/core/src/plugin/module.ts:122-124` |
| `context.client` is read once at activation, while a managed reconnect swaps the host's client (inference that the plugin keeps the old one). | `packages/tui/src/plugin/api.tsx:159`, `packages/tui/src/context/client.tsx:36` |
| Smaller API items: `themeMode`, select `placeholder`, option `footer`, `prompt.description` and `value`, the `"global"` id for `session.form`, `dialog.set` size `xlarge`. | `packages/tui/src/plugin/api.tsx:165`, `packages/plugin/src/tui/context.ts:382`, `packages/plugin/src/tui/context.ts:359`, `packages/plugin/src/tui/context.ts:350`, `packages/plugin/src/tui/context.ts:352`, `packages/client/src/solid/data.ts:96`, `packages/tui/src/ui/dialog.tsx:30` |
| Build facts: repo TSX config (`"jsx": "preserve"`, `"jsxImportSource": "@opentui/solid"`), `ignoreScripts: true` on install, `@opencode/theme` as a peer. | `packages/tui/tsconfig.json:6-7`, `packages/util/src/npm.ts:224`, `packages/plugin/package.json:53` |
| TUI parts do not run in OpenCode Desktop or in Mini. No doc says so. | `packages/tui/src/plugin/context.tsx:670`, `packages/tui/src/app.tsx:435` |

### GUI

- A standalone `.ts`/`.js` plugin file has no GUI. `packages/core/src/plugin/module.ts:116-119`
- Non-JSON `options` fail the plugin's load when it has a GUI. `packages/core/src/plugin/module.ts:143-150`
- Managed policy `plugin.use` deny blocks the plugin with no row. `packages/core/src/plugin/module.ts:53-54`, `packages/core/src/plugin/supervisor.ts:63-69`
- A GUI entry that resolves outside the plugin directory is dropped. `packages/core/src/config/plugin/source.ts:173-177`
- `ctx.options` reach every window. `packages/plugin/src/gui/host.ts:398-399`
- The preset's default `dist/gui-experimental.cjs` is not found by a local directory without `name` and `exports` (inference). `packages/plugin/src/gui/vite.ts:34`, `packages/plugin/src/host.ts:61`
- A rebuild also restarts every plugin ordered after the changed one (inference). `packages/core/src/plugin.ts:126,139-140`
- Main keeps a last-good revision on a failed reload. Windows do not. `packages/desktop/src/main/plugin/lifecycle.ts:290-332`, `packages/app/src/runtime/plugin/host.tsx:912-952`
- A main failure leaves window setup running. The row still says "Failed". `packages/app/src/runtime/plugin/root.tsx:87`, `packages/app/src/runtime/plugin/extension-plugins.tsx:114`
- Main errors reach Settings as message only. Window errors include the stack. `packages/desktop/src/main/plugin/lifecycle.ts:80-84`, `packages/app/src/runtime/plugin/host.tsx:870`
- A server-failed plugin shows a bare row. `plugin.state` is never rendered (inference from no use of it in the file). `packages/app/src/runtime/plugin/extension-plugins.tsx:54-220`
- Server and TUI badges, and "Show details" on errors. `packages/app/src/runtime/plugin/extension-plugins.tsx:161-167,223-249`
- Module state survives Reload and disable within a revision (inference). `packages/app/src/runtime/plugin/plugins.tsx:88-103`
- `ctx.storage.memory` values survive a plugin reload in that window (inference). `packages/app/src/runtime/plugin/host-apis.tsx:116,223-238`
- A per-call Ipc `signal` is not applied while the call waits for main (inference). `packages/app/src/runtime/plugin/host.tsx:642-654`
- A `Server` item that never becomes `ready` holds startup unless main failed (inference). `packages/app/src/runtime/plugin/servers.tsx:128-133`
- With no `location`, `ctx.client.rpc` reaches the home-location instance, not the session's directory (inference). `packages/server/src/location.ts:72-79`, `packages/client/src/promise/rpc.ts:8-10`
- `ctx.lifecycle` exists at runtime on every main context, but is not public. `packages/desktop/src/main/plugin/host.ts:705,720-724`
- `i18n.en` is optional at runtime, though the type requires it. `packages/plugin/src/gui/host.ts:273`

## What was checked and agrees

These were read on both sides, with no disagreement, so they need no second look unless the source changes.

### Server

- Definition shape, cleanup return, and V1+V2 default export: `packages/core/src/plugin/module.ts:81-94`, `packages/plugin/src/promise/plugin.ts:62-70`.
- `ctx.location` and options: `services/www/src/docs/content/build/plugins/server.mdx:50-54`, `services/www/src/docs/content/build/plugins/server.mdx:63-91`.
- Transform replay, batching, and read isolation: `services/www/src/docs/content/build/plugins/server.mdx:93-99`, `services/www/src/docs/content/build/plugins/server.mdx:129-131`, `packages/core/src/state.ts:168-213`.
- Example helpers `Model.Info.default`, `Provider.Info.empty`, `activation: "enabled"`: `services/www/src/docs/content/build/plugins/server.mdx:110-118`, `packages/schema/src/model.ts:142-155`, `packages/schema/src/provider.ts:35`, `packages/schema/src/provider.ts:125`.
- Prompt hook rules, including retried IDs not rerunning hooks: `services/www/src/docs/content/build/plugins/server.mdx:1387-1400`, `packages/core/src/session/prompt.ts:40-53`, `packages/core/src/session/session.ts:161-171`.
- Compaction and title `result`: `services/www/src/docs/content/build/plugins/server.mdx:1411-1415`, `packages/core/src/session/compaction.ts:617`, `packages/core/src/session/title.ts:78`.
- `delete event.tools.write` and `event.tools.read.description` are valid because `write` and `read` are direct tools: `services/www/src/docs/content/build/plugins/server.mdx:1420`, `packages/core/src/tool/plugin/write.ts:49`, `packages/core/src/tool/plugin/read.ts:47`.
- `event.model.modelID` in the AI SDK examples: `packages/plugin/src/README.md:109`, `packages/schema/src/model.ts:116`.
- Handshake timing: `services/www/src/docs/content/build/plugins/server.mdx:1508-1511`, `packages/core/src/session/model-transport.ts:309-314`.
- Retry numbering, limit, invalid delay: `services/www/src/docs/content/build/plugins/effect.mdx:1400`, `packages/core/src/session/runner/retry.ts:37-52`.
- Permission hook rules and assert outcomes: `services/www/src/docs/content/build/plugins/server.mdx:744-751`, `services/www/src/docs/content/build/plugins/server.mdx:1700-1703`, `packages/core/src/permission.ts:184-209`, `packages/core/src/permission.ts:256-288`.
- Child session inherits rules: `services/www/src/docs/content/build/plugins/server.mdx:762`, `packages/core/src/session/projector.ts:168` (one line read).
- Tool update rules, name normalization, overwrite, invalid updates: `services/www/src/docs/content/build/plugins/server.mdx:976-977`, `services/www/src/docs/content/build/plugins/server.mdx:1020-1025`, `packages/core/src/tool.ts:212-226`, `packages/core/src/tool.ts:364-377`, `packages/core/src/tool/runtime.ts:288-293`.
- Vcs custom provider example: `services/www/src/docs/content/build/plugins/server.mdx:1092`, `services/www/src/docs/content/build/plugins/server.mdx:1101-1103`, `packages/schema/src/vcs.ts:6-16`, `packages/core/src/vcs.ts:236-243`.
- Websearch result shape: `services/www/src/docs/content/build/plugins/server.mdx:1281`, `packages/schema/src/websearch.ts:24-33`.
- Worktree inputs and `OperationError`: `services/www/src/docs/content/build/plugins/server.mdx:1184-1191`, `services/www/src/docs/content/build/plugins/server.mdx:1212-1214`, `packages/schema/src/worktree.ts:11-28`, `packages/schema/src/worktree.ts:47-50`, `packages/plugin/src/promise/index.ts:21`.
- Hook ordering: `packages/core/src/plugin/hooks.ts:88-95`.
- Unknown event type warning: `packages/core/src/plugin/host.ts:281-283`.
- RPC define, reserved `rpc.` names, event objects, register and handler context, return or throw, external clients unfiltered: `services/www/src/docs/content/build/plugins/rpc.mdx:60-126`, `services/www/src/docs/content/build/plugins/rpc.mdx:139-161`, `services/www/src/docs/content/build/plugins/rpc.mdx:254`, `packages/schema/src/rpc.ts:29-60`, `packages/plugin/src/promise/adapter.ts:136-152`, `packages/client/src/promise/rpc.ts:70-72`.
- `PluginApi` block `services/www/src/docs/content/build/plugins/effect.mdx:736-743` shows only `list`, matching the `Pick` in effect/plugin.ts. `WebsearchApi<unknown>` at `services/www/src/docs/content/build/plugins/effect.mdx:1205` is the same type as `WebSearchApi`: `packages/client/src/effect/api.ts:8`, `packages/plugin/src/effect/websearch.ts:12`.

### GUI

- Context member list, window and main.
- `Layout`, `Files`, `Comments`, `Dialogs`, `Toasts`, `Attention`, `Tabs`, `Keybinds`, `Commands`, `System`, `Desktop`, `Locale`, `Appearance`, `Router`, `Workspaces`, `Ui` props.
- `Panel`, `PanelTab`, `MobileView`, `Command`, `MenuItem`, `TitlebarItem`, `Link`, `LinkHandler`, `Server*`.
- `Live`, `IpcClient`, `IpcProvider`, `Caller`, `App`, `PanelFrame`.
- `FileTree`, `FileViewer`, `Changes`, `Browser`.
- `Windows`, `ServerEndpoint`, `Cli`, `Log`, `MenubarItem` shape.
- Preset behaviour (`services/www/src/docs/content/build/plugins/gui/index.mdx:128-141`, `packages/plugin/src/gui/vite.ts:33-61`).
- Shared modules list (`services/www/src/docs/content/build/plugins/gui/index.mdx:191-195`, `packages/plugin/src/gui/modules.ts:10-32`).
- Id derivation, reserved ids (`services/www/src/docs/content/build/plugins/gui/index.mdx:232-236`), `os` row text.
- Entry resolution (`services/www/src/docs/content/build/plugins/gui/index.mdx:222-224`, `packages/plugin/src/host.ts:25-65`).
- Options reload (`services/www/src/docs/content/build/plugins/gui/index.mdx:227,380`), package GUI versioning (`services/www/src/docs/content/build/plugins/gui/index.mdx:226,228`).
- 3s quit deadline, main storage flush.
- Pill order (`services/www/src/docs/content/build/plugins/gui/index.mdx:1164`): the source comment agrees, though the lane can place plugin pills visually first when aligned to the end (`packages/app/src/session/composer/plugin-pills.tsx:29-30,57`).

### TUI

`build/plugins/cli.mdx`:

- Context intro; client (`client.plugin.list`, `.data`); events (`session.execution.succeeded`, `permission.asked`, `event.data.id`).
- Sessions, pending, messages, permissions, forms, projects, shells, location data, vcs (`vcs?.branch.current`).
- Attention option shape; `usePlugin`; Markdown registration shape.
- Layer lifetime text (`:306-311`); keymap dispatch and modes; storage shape.
- Dialogs `alert`, `confirm`, `prompt`, `select`; select search and inline categories; select settle rules (`:424-427`); `ctrl+n` and `ctrl+p`.
- Basic toasts; routes; tabs; model API; slot placements; `home.footer.status` position; session panels (`:586-595`).
- The `@opencode/plugin/tui/context` import; formatting.

`cli/plugins.mdx`:

- Path forms; order and `-` directives (`opencode.notifications` exists); object form; discovery paths.

`plugins.mdx`:

- Terminal section (`:148-156`): accurate as written. `cli.json` entries install on the client and stay active on a remote server.

## What was not checked

Server:

- `services/www/src/docs/content/build/plugins/server.mdx:1401` concurrent admission.
- `services/www/src/docs/content/build/plugins/server.mdx:1442-1445` option precedence and body overlays, which live in `packages/ai`.
- `services/www/src/docs/content/build/plugins/index.mdx:88` extension list: `packages/util/src/runtime-import.ts:1` only re-exports `resolveModule`.
- `services/www/src/docs/content/build/plugins/server.mdx:1197-1198`, `services/www/src/docs/content/build/plugins/server.mdx:1216-1219` worktree create, refresh, and prune details in `packages/core/src/worktree.ts`.
- `services/www/src/docs/content/build/plugins/server.mdx:1390` command-to-prompt path, beyond the fact that a command's `execute` is plugin code.

TUI: Not checkable from this clone, because `node_modules` is absent and OpenTUI's source was not available: the OpenTUI-specific claims at `services/www/src/docs/content/build/plugins/cli.mdx:224-257`. Only call sites were seen:

- `renderer.nativeScene`: `packages/tui/src/context/theme.tsx:319`
- `.idle()`: `packages/tui/src/context/theme.tsx:410`
- `getPadding`: `packages/tui/test/fixture/plugin/native-resources/tui.tsx:15`
- `invalidateIntrinsicSize`: `packages/tui/src/component/prompt/index.tsx:348`
- `generateSyntax(theme, owner)`: `packages/theme/src/tui/syntax.ts:4`

These are neither confirmed nor reported as drift.
