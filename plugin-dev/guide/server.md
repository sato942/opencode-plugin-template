# The server part

The part that runs in the OpenCode server: tools, hooks, transforms, commands, agents, storage, RPC. It works under every surface ([overview.md](overview.md)). The official docs are [server.mdx](../upstream/services/www/src/docs/content/build/plugins/server.mdx), [effect.mdx](../upstream/services/www/src/docs/content/build/plugins/effect.mdx) and [rpc.mdx](../upstream/services/www/src/docs/content/build/plugins/rpc.mdx), and [drift.md](drift.md) lists where they are wrong. Packaging is in [packaging.md](packaging.md), and loading in [loading.md](loading.md).

Read from source at the pin; not run, except where a line says **Observed**. Pins are paths inside [upstream/](../upstream/). "(inference)" marks a conclusion drawn from what was read, not a line that states it. **Observed** marks what was run: [testing.md](testing.md) says on what.

- No `node_modules` were read, so behaviour inside the `effect` library is always inference.
- Promise and Effect type files share line numbers unless a row says otherwise.

## 1. Definition shape

| Form | Import | Shape | Pin |
|---|---|---|---|
| Promise | `import { Plugin } from "@opencode/plugin"` | `{ id: string; setup(context): Promise<Cleanup \| void> \| Cleanup \| void }` | `packages/plugin/src/promise/plugin.ts:64-70`, `packages/plugin/package.json:16` |
| Effect | `import { Plugin } from "@opencode/plugin/effect"` | `{ id: string; effect(context): Effect<void, never, R = Scope.Scope> }` | `packages/plugin/src/effect/plugin.ts:62-67`, `packages/plugin/package.json:17` |
| Cleanup (Promise only) | | `() => Promise<void> \| void` | `packages/plugin/src/promise/plugin.ts:62` |

```ts
import { Plugin } from "@opencode/plugin"

export default Plugin.define({
  id: "acme",
  async setup(ctx) {
    const registration = await ctx.tool.transform((editor) => {
      editor.add({
        name: "ping",
        description: "Reply with pong",
        input: { type: "object", properties: {}, additionalProperties: false },
        options: { codemode: false },
        execute: async () => ({ content: "pong" }),
      })
    })
    return () => registration.dispose()
  },
})
```

```ts
import { Plugin } from "@opencode/plugin/effect"
import { Effect } from "effect"

export default Plugin.define({
  id: "acme",
  effect: (ctx) =>
    Effect.gen(function* () {
      yield* ctx.session.hook("context", (event) =>
        Effect.sync(() => {
          event.options.temperature = 0.2
        }),
      )
      yield* Effect.addFinalizer(() => Effect.log("unloaded"))
    }),
})
```

| Rule | Detail | Pin |
|---|---|---|
| Default export | Must have `id` plus a function `effect` or `setup`. Anything else fails with "Plugin must export a default definition with an id and an effect or setup function." | `packages/core/src/plugin/module.ts:81-94`, `packages/core/src/plugin/module.ts:176-184` |
| Both `effect` and `setup` | `effect` wins. | `packages/core/src/plugin/module.ts:185` |
| Core runs Effect only | A Promise plugin is wrapped by `fromPromise`. | `packages/core/src/plugin/module.ts:185`, `packages/core/src/plugin/promise.ts:3`, `packages/plugin/src/promise/adapter.ts:218` |
| Server entrypoint | Tries subpath `server`, then the package root. A local directory with no `package.json` `name` and `exports` uses `<dir>/server`, else `<dir>/index`. | `packages/plugin/src/host.ts:28-35`, `packages/plugin/src/host.ts:57` |
| RPC entrypoint | Subpath `rpc`. Used by clients to share a definition. | `packages/plugin/src/host.ts:59` |
| Entrypoint missing | A package with only a GUI part (and maybe a TUI part): id becomes the package name and the server part is a no-op. Otherwise "Plugin entrypoint not found". | `packages/core/src/plugin/module.ts:124`, `packages/core/src/plugin/module.ts:126-134` |
| Local discovery | Scans plugin folders for `.ts` and `.js` files, directories, and symlinks. | `packages/core/src/plugin/source-directory.ts:7-33` |
| Configured path | Must be a directory ("configured plugin path must be a directory"). Entrypoint must stay inside it. Config entries apply last. | `packages/core/src/config/plugin/source.ts:155`, `packages/core/src/config/plugin/source.ts:161-162`, `packages/core/src/config/plugin/source.ts:173-177` |
| Policy | Managed policy `plugin.use` deny blocks loading. | `packages/core/src/plugin/module.ts:53-54` |

## 2. Lifetimes

| Stage | What happens | Pin |
|---|---|---|
| Plugin list | Built-in pre plugins, SDK plugins, instance plugins, config packages, built-in post plugins. | `packages/core/src/plugin/supervisor.ts:94-98`, `packages/core/src/plugin/supervisor.ts:146` |
| First pass | Resolve without install, then with install. | `packages/core/src/plugin/supervisor.ts:150`, `packages/core/src/plugin/supervisor.ts:166` |
| Load | Fork a child scope, build the host context, call `plugin.effect(host)`. | `packages/core/src/plugin.ts:62-80` |
| Options | `operation.options` replaces the host's empty options. | `packages/core/src/plugin/host.ts:131`, `packages/core/src/plugin/module.ts:164` |
| Fiber context | Replaced with only `Scope`, loggers, and minimum log level. Host services are not reachable from plugin code. | `packages/core/src/plugin.ts:83-88` |
| Setup call | Promise: `Effect.acquireRelease(setup, cleanup)`. Cleanup runs at scope close only if setup succeeded. | `packages/plugin/src/promise/adapter.ts:666-669` |
| Setup failure | Scope closed, warning "failed to load plugin", the slot records the error. Later plugins still load. | `packages/core/src/plugin.ts:90-100`, `packages/core/src/plugin.ts:166` |
| Registration lifetime | Hooks and transforms add a scope finalizer, so unload removes them. `dispose` is idempotent. | `packages/core/src/plugin/hooks.ts:76-84` |
| Batching | A whole activation runs in `State.batch`; notifications coalesce, reads still see every registration so far. | `packages/core/src/plugin.ts:137`, `packages/core/src/state.ts:87-89`, `packages/core/src/state.ts:191-213` |
| Waiting for activation | Sessions, generate, command, and HTTP RPC wait for `awaitActivation`. | `packages/core/src/session/prompt.ts:40`, `packages/core/src/session/generate.ts:35`, `packages/core/src/session/command.ts:22`, `packages/core/src/session/runner/llm.ts:225`, `packages/server/src/handlers/rpc.ts:11` |
| Unload | Scope close runs Effect finalizers and Promise cleanup. Async iterators from `event.subscribe` and RPC subscribe close. | `packages/core/src/plugin.ts:147`, `packages/plugin/src/promise/adapter.ts:51` |

`reload()` is not a restart. It replays transforms and does not call `setup` again (`packages/core/src/state.ts:269`). A restart happens only through the triggers in section 12.

## 3. What `setup` receives: every context member

Same members in both forms (`packages/plugin/src/promise/plugin.ts:27-60`, `packages/plugin/src/effect/plugin.ts:27-60`).

| Member | Type | Status | Purpose | Pin |
|---|---|---|---|---|
| `app` | `{ name, version, channel }` | stable | Host identity. | `packages/plugin/src/promise/plugin.ts:28`, `packages/plugin/src/app.ts:1-5` |
| `location` | `Location.Info` | stable | Location this instance loaded in. | `packages/plugin/src/promise/plugin.ts:29` |
| `options` | `Readonly<Record<string, any>>` | stable | Config `options`, default `{}`. | `packages/plugin/src/promise/plugin.ts:30`, `packages/plugin/src/options.ts:1`, `packages/core/src/config/plugin/source.ts:116-123` |
| `agent` | `AgentDomain` | stable | 5.1 | `packages/plugin/src/promise/plugin.ts:31` |
| `aisdk` | `AISDKDomain` | stable | 5.2 | `packages/plugin/src/promise/plugin.ts:32` |
| `command` | `CommandDomain` | stable | 5.3 | `packages/plugin/src/promise/plugin.ts:33` |
| `credential` | `Pick<CredentialApi, "activate">` | stable | 5.4 | `packages/plugin/src/promise/plugin.ts:34` |
| `event` | `EventDomain` | stable | 5.5 | `packages/plugin/src/promise/plugin.ts:35` |
| `experimental.terminal` | `Pick<persistentPty, "read">` | experimental | 5.6 | `packages/plugin/src/promise/plugin.ts:37` |
| `experimental.generate` | `ExperimentalGenerateApi` | experimental | 5.6 | `packages/plugin/src/promise/plugin.ts:39` |
| `experimental.artifact` | `ExperimentalArtifactDomain` | experimental | 5.6 | `packages/plugin/src/promise/plugin.ts:40` |
| `integration` | `IntegrationDomain` | stable | 5.7 | `packages/plugin/src/promise/plugin.ts:42` |
| `mcp` | `MCPDomain` | stable | 5.8 | `packages/plugin/src/promise/plugin.ts:43` |
| `model` | `ModelDomain` | stable | 5.9 | `packages/plugin/src/promise/plugin.ts:44` |
| `generate` | `Pick<ExperimentalGenerateApi, "text">` | deprecated: use `experimental.generate.text` | 5.6 | `packages/plugin/src/promise/plugin.ts:45-46` |
| `permission` | `PermissionDomain` | stable | 5.10 | `packages/plugin/src/promise/plugin.ts:47` |
| `plugin` | `Pick<PluginApi, "list">` | stable | 5.11 | `packages/plugin/src/promise/plugin.ts:48` |
| `provider` | `ProviderDomain` | stable | 5.12 | `packages/plugin/src/promise/plugin.ts:49` |
| `reference` | `ReferenceDomain` | stable | 5.13 | `packages/plugin/src/promise/plugin.ts:50` |
| `rpc` | `RpcDomain` | stable | section 8 | `packages/plugin/src/promise/plugin.ts:51` |
| `session` | `SessionDomain` | stable, with experimental parts | 5.14, section 6 | `packages/plugin/src/promise/plugin.ts:52` |
| `shell` | `ShellDomain` | stable | 5.15 | `packages/plugin/src/promise/plugin.ts:53` |
| `skill` | `SkillDomain` | stable | 5.16 | `packages/plugin/src/promise/plugin.ts:54` |
| `storage` | `StorageDomain` | stable | section 9 | `packages/plugin/src/promise/plugin.ts:55` |
| `tool` | `ToolDomain` | stable | section 7 | `packages/plugin/src/promise/plugin.ts:56` |
| `vcs` | `VcsDomain` | stable | 5.17 | `packages/plugin/src/promise/plugin.ts:57` |
| `websearch` | `WebSearchDomain` | stable | 5.18 | `packages/plugin/src/promise/plugin.ts:58` |
| `worktree` | `WorktreeDomain` | stable | 5.19 | `packages/plugin/src/promise/plugin.ts:59` |

Importable values from `@opencode/plugin`: `Plugin`, `Agent`, `Artifact`, `Command`, `Connection`, `Credential`, `Integration`, `Location`, `Mcp`, `Model`, `PersistentPty`, `Provider`, `Reference`, `Rpc`, `Skill`, `Vcs`, `WebSearch`, `Worktree` (`packages/plugin/src/promise/index.ts:3-21`). `@opencode/plugin/effect` exports the same set (`packages/plugin/src/effect/index.ts:1-20`). Neither exports `Tool`, `Session`, or `Permission`.

## 4. Mechanisms shared by all domains

### Transforms

| Fact | Pin |
|---|---|
| Type: `(callback: (editor) => void) => Promise<Registration>`. Effect version needs `Scope`. | `packages/plugin/src/promise/registration.ts:21`, `packages/plugin/src/effect/registration.ts:27` |
| The callback is synchronous. Load external data first, then call `reload()`. | `packages/plugin/src/promise/registration.ts:21`, `packages/core/src/state.ts:269` |
| Reads replay every active transform, in registration order, onto a fresh value. | `packages/core/src/state.ts:191-213` |
| Editors write drafts. A value already read is never changed by a later replay. | `packages/core/src/state.ts:168-171` |
| Disposing a registration rebuilds without it, so an earlier definition shows again (inference). | `packages/core/src/state.ts:243-268`, `packages/core/src/plugin/hooks.ts:76-82` |
| A throw inside a transform disables the whole plugin: scope closed, message "Plugin disabled after X.transform failed. Check server logs for details." | `packages/core/src/plugin.ts:65-78`, `packages/core/src/plugin.ts:194-248`, `packages/core/src/state.ts:198-203` |
| Editors that decode input throw on invalid data, so a bad value reaches the same path (inference). | `packages/core/src/plugin/host.ts:441`, `packages/core/src/plugin/host.ts:492` |

### Hooks

| Fact | Pin |
|---|---|
| Promise: `hook(name, callback)` returns `Promise<Registration>`. Effect: returns `Effect<Registration, never, Scope>`. | `packages/plugin/src/promise/registration.ts:10-13`, `packages/plugin/src/effect/registration.ts:12-17` |
| `ModelHooks` add a third `{ providerID? }` argument, only for events that have `model`. | `packages/plugin/src/promise/registration.ts:15-19` |
| Callbacks run one at a time in registration order on one shared event object. A later hook sees earlier mutations. | `packages/core/src/plugin/hooks.ts:88-95` |
| Provider filter compares with the event's model provider. | `packages/core/src/plugin/hooks.ts:90` |
| Hooks are stored per location. | `packages/core/src/plugin/hooks.ts:108` |
| Promise rejection is a defect, which fails the running operation. Only `tool` `execute.before` turns a rejection into a `Tool.Error`. | `packages/plugin/src/promise/adapter.ts:481`, `packages/plugin/src/promise/adapter.ts:625`, `packages/plugin/src/promise/adapter.ts:662`, `packages/plugin/src/promise/adapter.ts:685-691` |
| Effect hook failure channel is `never` except `execute.before`, which may fail with `Tool.Error`. | `packages/core/src/plugin/hooks.ts:24-30`, `packages/plugin/src/effect/tool.ts:48-52` |

### Method calls

| Fact | Pin |
|---|---|
| Promise methods take one argument. A second `requestOptions` argument, including `signal`, is dropped. | `packages/plugin/src/promise/adapter.ts:271` |
| Input crosses JSON and endpoint schemas before reaching the host, so non-JSON values do not survive. | `packages/plugin/src/promise/adapter.ts:273-277` |
| A single `data` success envelope is unwrapped. | `packages/plugin/src/promise/adapter.ts:191-199` |
| Most `location` inputs are ignored: command, provider, model, skill, reference, plugin, and vcs reads always answer for the plugin's own location. Only `agent.get`, `agent.list`, and `mcp.list` honour it. | `packages/core/src/plugin/host.ts:134-157`, `packages/core/src/plugin/host.ts:203`, `packages/core/src/plugin/host.ts:238`, `packages/core/src/plugin/host.ts:261`, `packages/core/src/plugin/host.ts:426-434`, `packages/core/src/plugin/host.ts:469`, `packages/core/src/plugin/host.ts:472`, `packages/core/src/plugin/host.ts:485`, `packages/core/src/plugin/host.ts:509` |

## 5. Domains

Kind is `method`, `transform`, `hook`, or `editor` (an editor member passed to a transform callback). Session hooks are in section 6, tool hooks in section 7.

### 5.1 agent

| Name | Kind | When or effect | Fields | Pin |
|---|---|---|---|---|
| `agent.list(input?)` | method | Selected default listed first. Honours `location`. | input `location?` | `packages/core/src/plugin/host.ts:153-157`, `packages/core/src/agent.ts:65-70` |
| `agent.get(input)` | method | One agent. Honours `location`. | | `packages/core/src/plugin/host.ts:134-152` |
| `agent.transform` | transform | Editor: `list`, `get`, `default`, `update`, `remove`. There is no `add`. | | `packages/plugin/src/promise/agent.ts:6-17` |
| `editor.list`, `editor.get` | editor | Read drafts in this replay. | mutable `Agent.Info` | `packages/core/src/agent.ts:75-76` |
| `editor.default(id)` | editor | Sets the default. Falls back to `defaultID`, then the first selectable, if the chosen one is a subagent or hidden. | `id \| undefined` | `packages/core/src/agent.ts:53-64`, `packages/core/src/agent.ts:77-79` |
| `editor.update(id, fn)` | editor | Creates from `Info.default(id)` if missing. `id` is reset after `fn`. This is how to add an agent. | all `Agent.Info` | `packages/core/src/agent.ts:80-85` |
| `editor.remove(id)` | editor | Deletes. | | `packages/core/src/agent.ts:86-88` |
| `agent.reload()` | method | Replays. | | `packages/plugin/src/promise/agent.ts:16` |

### 5.2 aisdk

| Name | Kind | When | Fields | Pin |
|---|---|---|---|---|
| `aisdk.hook("sdk", cb, {providerID?})` | hook | SDK cache miss, before the default SDK is built. Only for AI SDK packages. | read `model`, `package`, `options`. Set `sdk`. | `packages/plugin/src/promise/aisdk.ts:6-11`, `packages/core/src/aisdk.ts:328`, `packages/core/src/aisdk.ts:344-346`, `packages/core/src/plugin/host.ts:174` |
| `aisdk.hook("language", cb, {providerID?})` | hook | Language model cache miss. | read `model`, `sdk`, `options`. Set `language`. | `packages/plugin/src/promise/aisdk.ts:12-17`, `packages/core/src/aisdk.ts:326-327`, `packages/core/src/aisdk.ts:353`, `packages/core/src/plugin/host.ts:188` |

`model` here is `Model.Info`, which has `modelID` and `providerID` (`packages/schema/src/model.ts:114-117`). Hook rejection is a defect (`packages/plugin/src/promise/adapter.ts:305-310`).

### 5.3 command

| Name | Kind | When or effect | Fields | Pin |
|---|---|---|---|---|
| `command.list()` | method | Ignores any input. | | `packages/core/src/plugin/host.ts:261` |
| `command.transform` | transform | Editor has `add` only. | | `packages/plugin/src/promise/command.ts:19-21` |
| `editor.add(definition)` | editor | Same `name` overwrites the earlier one. | `name`, `description?`, `execute(invocation)` | `packages/plugin/src/promise/command.ts:13-17`, `packages/core/src/command.ts:66` |
| `definition.execute` | callback | Runs on `session.command`, after activation. | `sessionID`, `prompt`, `delivery` (default `"steer"`) | `packages/plugin/src/promise/command.ts:7-11`, `packages/core/src/session/command.ts:11-37`, `packages/core/src/plugin/host.ts:592` |
| execute failure | | Logged and turned into `Command.ExecutionError`. | | `packages/core/src/command.ts:84-91` |
| `command.reload()` | method | Replays. | | `packages/plugin/src/promise/command.ts:25` |

### 5.4 credential

| Name | Kind | Effect | Pin |
|---|---|---|---|
| `credential.activate(input)` | method | Activates a stored credential. | `packages/plugin/src/promise/plugin.ts:34`, `packages/core/src/plugin/host.ts:265-267` |

### 5.5 event

| Name | Kind | Behaviour | Pin |
|---|---|---|---|
| `event.subscribe(options?)` Promise | method | `AsyncIterable`. Closes on plugin unload or `signal` abort. | `packages/plugin/src/promise/event.ts:6-10`, `packages/plugin/src/promise/adapter.ts:51`, `packages/plugin/src/promise/adapter.ts:65-66` |
| `event.subscribe({ types? })` Effect | method | `Stream`. | `packages/plugin/src/effect/event.ts:4-10` |
| No `types` | | All public events. | `packages/core/src/plugin/host.ts:271` |
| Unknown type | | Warning. If every type is unknown, the stream never emits. | `packages/core/src/plugin/host.ts:279-283` |
| Location | | Sees all locations: the bus filters only when a `Location` service is present, and plugin fibers do not have one (inference). | `packages/core/src/bus.ts:708-728`, `packages/core/src/plugin/host.ts:271`, `packages/core/src/plugin.ts:83-88` |

### 5.6 experimental and generate

| Name | Kind | Effect | Pin |
|---|---|---|---|
| `experimental.terminal.read(input)` | method, experimental | Reads a persistent terminal: `sessionID`, `lines`. | `packages/core/src/plugin/host.ts:288` |
| `experimental.generate.text`, `.image`, `.decisions` | method, experimental | Stateless generation: no session, history, or tools. | `packages/plugin/src/promise/plugin.ts:38-39`, `packages/core/src/plugin/host.ts:290-294` |
| `generate.text` | method, deprecated | Same as `experimental.generate.text`. | `packages/plugin/src/promise/plugin.ts:45-46`, `packages/core/src/plugin/host.ts:321-323` |
| `experimental.artifact.transform` | transform, experimental | Editor: `add`, `remove`, `default.get`, `default.set`. | `packages/plugin/src/promise/artifact.ts:45-57` |
| `editor.add(definition)` | editor | `id`, `name`, `capabilities`, `prompt`, `create`, `read`, `update`, `delete`. Same id overwrites. | `packages/plugin/src/promise/artifact.ts:24-43`, `packages/core/src/artifact.ts:248-250` |
| `editor.remove(id)` | editor | Local provider cannot be removed. Clears selection if it pointed there. | `packages/core/src/artifact.ts:251-255` |
| `editor.default.set(id \| undefined)` | editor | Missing selection falls back to the local provider. | `packages/core/src/artifact.ts:256-261`, `packages/core/src/artifact.ts:274-277` |
| Gate | | Artifact operations need config `experimental.artifacts === true`. | `packages/core/src/artifact.ts:266-272` |
| `experimental.artifact.reload()` | method | Replays. | `packages/plugin/src/promise/artifact.ts:56` |

### 5.7 integration

| Name | Kind | Effect | Pin |
|---|---|---|---|
| `integration.list`, `get` | method | Client API, minus `wellknown`. | `packages/plugin/src/promise/integration.ts:94`, `packages/client/src/effect/api/api.ts:1692-1716` |
| `integration.connect.key`, `.external` | method | Connect with a key or external form. | `packages/core/src/plugin/host.ts:331-346`, `packages/client/src/effect/api/api.ts:1695-1698` |
| `integration.oauth.connect`, `.status`, `.complete`, `.cancel` | method | OAuth flow. | `packages/core/src/plugin/host.ts:347-375` |
| `integration.command.connect`, `.status`, `.cancel` | method | Command flow. | `packages/core/src/plugin/host.ts:376-397` |
| `integration.connection.active(id)` | method | Active connection or `undefined`. | `packages/plugin/src/promise/integration.ts:98`, `packages/core/src/plugin/host.ts:399-408` |
| `integration.connection.resolve(connection)` | method | Credential value or `undefined`. | `packages/plugin/src/promise/integration.ts:99` |
| `integration.connection.status(input)` | method | Report a problem on a connection. `status: undefined` clears it. | `packages/plugin/src/promise/integration.ts:100-105` |
| `integration.transform` | transform | Editor below. | `packages/plugin/src/promise/integration.ts:82-92`, `packages/core/src/plugin/host.ts:409-423` |
| `editor.list`, `get` | editor | `{ id, name }` refs. | `packages/core/src/integration.ts:326-327` |
| `editor.update(id, fn)` | editor | Creates if missing. `id` reset after `fn`. | `packages/core/src/integration.ts:316-332` |
| `editor.remove(id)` | editor | Deletes. | `packages/core/src/integration.ts:333` |
| `editor.method.list(id)` | editor | Methods of one integration. | `packages/core/src/integration.ts:335` |
| `editor.method.update(input)` | editor | Replaces the same method or appends. Creates the integration if missing. Registers `authorize` when present. | `packages/plugin/src/promise/integration.ts:64-80`, `packages/core/src/integration.ts:336-344` |
| `editor.method.remove(id, method)` | editor | Removes, and drops the OAuth implementation. | `packages/core/src/integration.ts:345-351` |
| `integration.reload()` | method | Replays. | `packages/plugin/src/promise/integration.ts:96` |

Method types: `oauth`, `command`, `key`, `external`, `env` (`packages/plugin/src/promise/integration.ts:10-47`). OAuth `authorize(answer)` returns `{ url, instructions, expiresAt?, mode, callback }`, where `mode: "auto"` has a Promise callback and `mode: "code"` has a function callback (`packages/plugin/src/promise/integration.ts:49-62`). In Effect, `authorize` requires `Scope` (`packages/plugin/src/effect/integration.ts:67`).

### 5.8 mcp

| Name | Kind | Effect | Pin |
|---|---|---|---|
| `mcp.list(input?)` | method | Honours `location`. | `packages/core/src/plugin/host.ts:426-434` |
| `mcp.transform` | transform | Editor: `list`, `get`, `set`, `update`, `remove`. | `packages/plugin/src/promise/mcp.ts:6-12` |
| `editor.set(name, config)` | editor | Decodes `ServerConfig`, which throws on bad input. No-op if config set the server to `false`. | `packages/core/src/plugin/host.ts:441`, `packages/core/src/mcp/index.ts:655`, `packages/core/src/mcp/index.ts:660-664` |
| `editor.update(name, fn)` | editor | No-op if missing. | `packages/core/src/mcp/index.ts:665-669` |
| `editor.remove(name)` | editor | Deletes. | `packages/core/src/mcp/index.ts:670` |
| `mcp.reload()` | method | Replays, then reconciles connections. | `packages/core/src/mcp/index.ts:672`, `packages/core/src/plugin/host.ts:435` |

### 5.9 model

| Name | Kind | Effect | Pin |
|---|---|---|---|
| `model.list(input?)` | method | `models.available(types)`. Ignores `location`. | `packages/core/src/plugin/host.ts:238` |
| `model.default()` | method | Default model. | `packages/client/src/effect/api/api.ts:1478-1481` |
| `model.transform` | transform | Runs on materialized models of available providers. | `packages/plugin/src/promise/model.ts:7-23` |
| `editor.list(providerID?)`, `get` | editor | Drafts, including models disabled by earlier transforms. | `packages/plugin/src/promise/model.ts:8-10`, `packages/core/src/model.ts:131-137` |
| `editor.update(providerID, modelID, fn)` | editor | No-op if the provider is unavailable. Creates from `Info.default` if the model is missing. `id` and `providerID` reset after `fn`. | `packages/core/src/model.ts:138-155` |
| `editor.remove(providerID, modelID)` | editor | Deletes. | `packages/core/src/model.ts:156-158` |
| `editor.default.get`, `.set` | editor | Default model. | `packages/core/src/model.ts:159-164` |
| `editor.provider.list`, `.get` | editor | Immutable provider records, including inactive ones. | `packages/plugin/src/promise/model.ts:18-22`, `packages/core/src/model.ts:165-168` |
| `model.reload()` | method | Replays. | `packages/plugin/src/promise/model.ts:27` |

### 5.10 permission

| Name | Kind | When or effect | Fields | Pin |
|---|---|---|---|---|
| `permission.list`, `get`, `reply` | method | Client API. `reply` decision is `once`, `always`, or `reject`. | | `packages/plugin/src/promise/permission.ts:23`, `packages/schema/src/permission.ts:42` |
| `permission.assert(input)` | method | See rules below. | required `sessionID`, `action`, `resources`. Optional `agent`, `save`, `metadata`, `source`. | `packages/plugin/src/permission.ts:5-13`, `packages/schema/src/permission.ts:26-33`, `packages/core/src/permission.ts:256-288` |
| `permission.hook("evaluate", cb)` | hook | During evaluation, unless a configured rule already denies. | read `sessionID`, `agent?`, `action`, `resources`, `metadata?`, `source?`. Mutate `effect`, `message`. | `packages/plugin/src/promise/permission.ts:8-17`, `packages/core/src/permission.ts:184-198` |

| Assert case | Result | Pin |
|---|---|---|
| Configured rule denies | Hook skipped. `Tool.Error` from `BlockedError`. | `packages/core/src/permission.ts:186`, `packages/core/src/permission.ts:262-268`, `packages/core/src/plugin/host.ts:458-466` |
| Hook or rules allow | Resolves. | `packages/core/src/permission.ts:270` |
| Effect is `ask` | Prompt published with `message`, waits for reply. | `packages/core/src/permission.ts:212-227`, `packages/core/src/permission.ts:271-272` |
| Effect is `ask`, unattended session, rules do not settle it | Denied: "needs approval, and nobody is present to give it". | `packages/core/src/permission.ts:199-209` |
| Rejected with feedback | `Tool.Error` carrying the reason. | `packages/core/src/plugin/host.ts:458-466` |
| Plain rejection | Defect that ends the step. Rethrow it. | `packages/core/src/permission.ts:273-278`, `packages/plugin/src/promise/permission.ts:25-30`, `packages/core/src/plugin/host.ts:457` |
| Promise input | Decoded through `AssertInput`. | `packages/plugin/src/promise/adapter.ts:486` |

### 5.11 plugin

| Name | Kind | Effect | Pin |
|---|---|---|---|
| `plugin.list()` | method | Inventory of slots with status `active` or `failed`, not only active ones. Updated after an activation finishes, so during `setup` it shows the previous inventory. Ignores input. | `packages/core/src/plugin.ts:50-52`, `packages/core/src/plugin.ts:184`, `packages/core/src/plugin.ts:298-307`, `packages/core/src/plugin/host.ts:469` |

### 5.12 provider

| Name | Kind | Effect | Pin |
|---|---|---|---|
| `provider.list()` | method | `providers.available()`. Ignores input. | `packages/core/src/plugin/host.ts:203` |
| `provider.get(input)` | method | Fails with "Provider not found". | `packages/core/src/plugin/host.ts:204-213` |
| `provider.transform` | transform | Editor below. | `packages/plugin/src/promise/provider.ts:15-28` |
| `editor.list`, `get` | editor | Records: `provider`, `models`, `sourceConnection?`. | `packages/plugin/src/promise/provider.ts:9-13`, `packages/core/src/provider.ts:418-419` |
| `editor.add({info, models, sourceConnection?})` | editor | Replaces any record with that id. | `packages/core/src/provider.ts:420-426` |
| `editor.update(id, fn)` | editor | Creates `Info.empty(id)` if missing. `id` reset after `fn`. | `packages/core/src/provider.ts:401-408`, `packages/core/src/provider.ts:427-436` |
| `editor.remove(id)` | editor | Deletes. | `packages/core/src/provider.ts:437-439` |
| `editor.models.set(id, models)` | editor | Replaces the provider's models. Creates the provider if missing. | `packages/core/src/provider.ts:441-443` |
| `editor.models.update(id, modelID, fn)` | editor | Owned copy of a definition. Creates provider and model if missing. | `packages/core/src/provider.ts:444-467` |
| `editor.models.remove(id, modelID)` | editor | No-op if the provider is missing. | `packages/core/src/provider.ts:468-471` |
| `provider.reload()` | method | Replays. | `packages/core/src/plugin/host.ts:214` |

Helpers: `Model.Info.default(providerID, id)` and `Provider.Info.empty(id)` (`packages/schema/src/model.ts:142-155`, `packages/schema/src/provider.ts:125`). `Provider.Info.activation` is `auto`, `enabled`, or `disabled` (`packages/schema/src/provider.ts:35`).

### 5.13 reference

| Name | Kind | Effect | Pin |
|---|---|---|---|
| `reference.list()` | method | Ignores input. | `packages/core/src/plugin/host.ts:472` |
| `reference.transform` | transform | Editor: `add`, `remove`, `list`, `get`. | `packages/plugin/src/promise/reference.ts:5-10` |
| `editor.add(name, source)` | editor | Local or Git source, decoded. Same name overwrites. | `packages/core/src/plugin/host.ts:477`, `packages/core/src/reference.ts:99` |
| change | | Triggers a background refresh. Also checks hourly. | `packages/core/src/reference.ts:104-109`, `packages/core/src/reference.ts:113` |
| `reference.reload()` | method | Replays. | `packages/plugin/src/promise/reference.ts:14` |

### 5.14 session methods

Hooks are in section 6.

| Name | Kind | Effect | Pin |
|---|---|---|---|
| `session.list`, `create`, `get`, `remove` | method | Client API. | `packages/plugin/src/promise/session.ts:201-206`, `packages/protocol/src/groups/session.ts:126`, `packages/protocol/src/groups/session.ts:165`, `packages/protocol/src/groups/session.ts:232`, `packages/protocol/src/groups/session.ts:245` |
| `session.switchAgent`, `switchModel` | method | Change agent or model. | `packages/protocol/src/groups/session.ts:273`, `packages/protocol/src/groups/session.ts:287` |
| `session.update`, `move` | method | Update (including permission rules) or move a session. | `packages/core/src/plugin/host.ts:594-601`, `packages/protocol/src/groups/session.ts:323` |
| `session.prompt` | method | Admits user input and wakes the session unless `resume` is `false`. | `packages/core/src/session/session.ts:155-191` |
| `session.generate` | method | Transient text from the current context. Does not change the session. | `packages/core/src/session/generate.ts:25-68` |
| `session.command` | method | Host maps `{...input, command: input.name}`. | `packages/core/src/plugin/host.ts:592` |
| `session.compact`, `synthetic`, `interrupt`, `context` | method | Client API. | `packages/protocol/src/groups/session.ts:439`, `packages/protocol/src/groups/session.ts:398`, `packages/protocol/src/groups/session.ts:672`, `packages/protocol/src/groups/session.ts:502` |
| `session.wait` | method, experimental | Typed from `ExperimentalSessionApi`. Endpoint under `/api/experimental/`. | `packages/plugin/src/promise/session.ts:219`, `packages/protocol/src/groups/session.ts:457` |
| `session.instructions.entry.list`, `.put`, `.remove` | method, experimental | Key validated by `InstructionEntry.Key`. | `packages/plugin/src/promise/session.ts:219`, `packages/core/src/plugin/host.ts:610-627` |

Not on the plugin context, though on the client: `active`, `fork`, `shell`, `revert`, `diff`, `inbox`, `background`, `message`, `form`, `environment`, `view` (`packages/client/src/effect/api/api.ts:402-443` versus `packages/plugin/src/promise/session.ts:201-221`).

### 5.15 shell

| Name | Kind | When | Fields | Pin |
|---|---|---|---|---|
| `shell.hook("create.before", cb)` | hook | Before a shell is created. Workspace locations do not inherit `process.env` in the base env. | mutate `command`, `cwd`, `timeout`, `shell`, `env` | `packages/plugin/src/promise/shell.ts:3-13`, `packages/core/src/shell.ts:269-272`, `packages/core/src/shell.ts:284` |

### 5.16 skill

| Name | Kind | Effect | Pin |
|---|---|---|---|
| `skill.list()` | method | Ignores input. | `packages/core/src/plugin/host.ts:485` |
| `skill.transform` | transform | Editor: `list`, `get`, `add`, `update`, `remove`. | `packages/plugin/src/promise/skill.ts:6-12` |
| `editor.add(skill)` | editor | Decodes `Skill.Info`, which throws on bad input. Same id overwrites. The core `files` argument is not reachable from a plugin. | `packages/core/src/plugin/host.ts:492`, `packages/core/src/skill.ts:128-140` |
| `editor.update(id, fn)` | editor | No-op if missing. `id` reset after `fn`. | `packages/core/src/skill.ts:141-147` |
| `editor.remove(id)` | editor | Deletes. | `packages/core/src/skill.ts:148-152` |
| `skill.reload()` | method | Replays. | `packages/core/src/plugin/host.ts:486` |

### 5.17 vcs

| Name | Kind | Effect | Pin |
|---|---|---|---|
| `vcs.get`, `status`, `branch.list` | method | Ignore `location`. | `packages/core/src/plugin/host.ts:509-514` |
| `vcs.base()` | method | Review base `{ name, ref, source }` or `null`. | `packages/core/src/plugin/host.ts:510`, `packages/core/src/vcs.ts:199-203`, `packages/schema/src/vcs.ts:21-25` |
| `vcs.diff(input)` | method | Forwards only `mode`, `context`, `base`. A client `untracked` input is dropped. | `packages/core/src/plugin/host.ts:515` |
| `vcs.transform` | transform | Editor: `add`, `default.get`, `default.set`. | `packages/plugin/src/promise/vcs.ts:41-47` |
| `editor.add(definition)` | editor | Required `id`, `name`, `info`, `branches`, `status`, `diff`. Optional `init`, `base`. Same id overwrites. | `packages/plugin/src/promise/vcs.ts:25-34`, `packages/core/src/vcs.ts:85` |
| `editor.default.set(id)` | editor | Provider used is `selection ?? detected type`. | `packages/core/src/vcs.ts:86-89`, `packages/core/src/vcs.ts:93-97` |
| callback failures | | `branches` and `status` failures return `[]`. `base` and `diff` go through a separate error path. | `packages/core/src/vcs.ts:204-228`, `packages/core/src/vcs.ts:199-203`, `packages/core/src/vcs.ts:229-245` |
| `vcs.reload()` | method | Replays and refreshes. | `packages/core/src/vcs.ts:91`, `packages/core/src/plugin/host.ts:517` |

`vcs.init` is omitted from the context (`packages/plugin/src/promise/vcs.ts:36`). Scope fields: `directory`, `worktree`, `canonical`, `store?` (`packages/plugin/src/promise/vcs.ts:6-11`). Effect `VcsDiffInput` has `untracked?`; Promise does not (`packages/plugin/src/effect/vcs.ts:19-25`, `packages/plugin/src/promise/vcs.ts:18-23`). Core does send it to providers when set (`packages/core/src/vcs.ts:240`).

### 5.18 websearch

| Name | Kind | Effect | Pin |
|---|---|---|---|
| `websearch.providers()`, `query({query, providerID?})` | method | Client API. | `packages/core/src/plugin/host.ts:520-527`, `packages/schema/src/websearch.ts:17-20` |
| `websearch.transform` | transform | Editor: `add`, `default.get`, `default.set`. Core's `list` and `remove` are not exposed. | `packages/plugin/src/promise/websearch.ts:19-25`, `packages/core/src/plugin/host.ts:532-544` |
| `editor.add(definition)` | editor | `id`, `name`, `execute({query}, {signal})`. Returns `WebSearch.Result[]`: `url`, `title?`, `content?`, `time: { published? }`. | `packages/plugin/src/promise/websearch.ts:5-12`, `packages/schema/src/websearch.ts:24-33` |
| `editor.default.set(value)` | editor | Provider id, `false` to disable, or `"random"`. The Promise type reads `string \| false`, so `"random"` fits it. | `packages/core/src/plugin/host.ts:540-543`, `packages/core/src/websearch.ts:32` |
| `"random"` | | Picks an available provider, and retries another on HTTP 429. | `packages/core/src/websearch.ts:143-153`, `packages/core/src/websearch.ts:192-214` |
| `websearch.reload()` | method | Replays. | `packages/core/src/plugin/host.ts:528` |

### 5.19 worktree

| Name | Kind | Effect | Pin |
|---|---|---|---|
| `worktree.list`, `create`, `remove`, `refresh` | method | Project based: `projectID` is required. Strategies come from this location unless it is a workspace location. | `packages/core/src/plugin/host.ts:82`, `packages/core/src/plugin/host.ts:549-552`, `packages/schema/src/worktree.ts:11-28` |
| `worktree.transform` | transform | Editor has `add` only. The latest `add` becomes selected. | `packages/plugin/src/promise/worktree.ts:15-18`, `packages/core/src/worktree/strategies.ts:59-63` |
| `editor.add(definition)` | editor | `id`, `create`, `remove`, `list`. `create` returns `{ directory }`. `list` returns `{ directory, type }[]`. Results decoded. | `packages/plugin/src/promise/worktree.ts:5-13`, `packages/plugin/src/worktree.ts:1-21`, `packages/core/src/plugin/host.ts:557-563` |
| Force required | | Strategies may fail with `Worktree.OperationError` with `forceRequired`. | `packages/schema/src/worktree.ts:47-50` |
| `worktree.reload()` | method | Replays. | `packages/core/src/plugin/host.ts:553` |

## 6. Session hooks

`session.hook(name, callback, options?)` (`packages/plugin/src/promise/session.ts:185-199`, `packages/plugin/src/promise/session.ts:220`). All hooks except `prompt` and `experimental.idle` have `model`, so they accept `{ providerID }` (`packages/plugin/src/promise/registration.ts:18`).

| Hook | Kind | Fires | Read | Mutate | Pin |
|---|---|---|---|---|---|
| `prompt` | hook | During `session.prompt`, before admission, after activation. Skipped when the message id was already admitted. | `sessionID`, `messageID` | `prompt`, `metadata`, `delivery` (default `steer`) | `packages/plugin/src/promise/session.ts:14-20`, `packages/core/src/session/prompt.ts:40-53`, `packages/core/src/session/session.ts:161-171` |
| `context` | hook | Each primary model call, in the agent loop. | `sessionID`, `model`, `agent` | `system`, `messages`, `options`, `tools` | `packages/plugin/src/promise/session.ts:25-40`, `packages/core/src/session/model-request.ts:428`, `packages/core/src/session/runner/llm.ts:260-274` |
| `compaction` | hook | Compaction request. Setting `result` skips the model call. | as `context` | as `context`, plus `result` | `packages/plugin/src/promise/session.ts:42-53`, `packages/core/src/session/model-request.ts:429`, `packages/core/src/session/compaction.ts:842`, `packages/core/src/session/compaction.ts:617` |
| `generate` | hook | `session.generate`. | as `context` | as `context` | `packages/plugin/src/promise/session.ts:55`, `packages/core/src/session/model-request.ts:430`, `packages/core/src/session/generate.ts:47` |
| `title` | hook | Title generation. No `agent` or `tools` on the event. Setting `result` skips the model call. | `sessionID`, `model` | `system`, `messages`, `options`, `result` | `packages/plugin/src/promise/session.ts:57-60`, `packages/core/src/session/title.ts:71-78`, `packages/core/src/session/model-request.ts:431` |
| `model.request` | hook | Every kind, after the request is shaped. | `sessionID`, `agent`, `model`, `kind` | `baseURL`, `headers` | `packages/plugin/src/promise/session.ts:68-75`, `packages/core/src/session/model-request.ts:318-333` |
| `http.request` | hook | Each HTTP request when a hook exists. Same object keeps the original body. A replacement has its body read. | `sessionID`, `agent`, `model`, `kind` | `request` | `packages/plugin/src/promise/session.ts:77-83`, `packages/core/src/session/model-request.ts:335-353` |
| `http.response` | hook | Each HTTP response. | as above, plus `request` | `response` | `packages/plugin/src/promise/session.ts:85-92`, `packages/core/src/session/model-request.ts:356-363` |
| `experimental.ws.handshake` | hook, experimental | WebSocket transport only, once per call before socket selection. Changing `url` or `headers` selects a different socket. | `sessionID`, `agent`, `model`, `kind` | `url`, `headers` | `packages/plugin/src/promise/session.ts:94-105`, `packages/core/src/session/model-request.ts:369-376`, `packages/core/src/session/model-transport.ts:309-314` |
| `experimental.ws.send` | hook, experimental | Each outbound frame. | as above | `frame` | `packages/plugin/src/promise/session.ts:112-118`, `packages/core/src/session/model-request.ts:384` |
| `experimental.ws.receive` | hook, experimental | Each inbound frame, before the driver. | as above | `frame` | `packages/plugin/src/promise/session.ts:124-130`, `packages/core/src/session/model-request.ts:388` |
| `retry` | hook | After a retryable failure, when the policy still allows a decision. | `sessionID`, `agent`, `model`, `error`, `attempt` | `decision` | `packages/plugin/src/promise/session.ts:134-141`, `packages/core/src/session/runner/retry.ts:32-55` |
| `experimental.idle` | hook, experimental | Session is about to go idle after model work with no pending input. Not after control-only work. Input the hook admits continues the same execution. | `sessionID`, `background` (kinds `shell`, `subagent`, `image`) | none | `packages/plugin/src/promise/session.ts:147-183`, `packages/core/src/session/runner/llm.ts:175-185` |

| Detail | Pin |
|---|---|
| `kind` values: `primary`, `compaction`, `title`, `generate`. | `packages/plugin/src/promise/session.ts:66` |
| `model` on session events is `Model.Ref`, not the `Model.Info` of `aisdk` hooks. | `packages/plugin/src/promise/session.ts:27`, `packages/plugin/src/promise/aisdk.ts:7` |
| The instructions system part lists sources in `metadata.experimental.instructions` as `{ key, text }`. Editing `text` does not update it. Experimental. | `packages/plugin/src/promise/session.ts:28-31` |
| Only two callers ask for WebSocket: the primary loop and one compaction path. Title and generate never do. | `packages/core/src/session/runner/llm.ts:272`, `packages/core/src/session/compaction.ts:556`, `packages/core/src/session/title.ts:71-77`, `packages/core/src/session/generate.ts:47-58` |
| `options` starts with `{ maxTokens }` for primary and compaction, `{}` for title and generate. | `packages/core/src/session/model-request.ts:261-275` |
| Option keys in `GENERATION_KEYS` are generation settings. Others are provider options. | `packages/core/src/session/model-request.ts:48`, `packages/core/src/session/model-request.ts:287-289` |
| `tools` holds deep copies. Entries match by identity, then name. Invented entries are dropped. A rename maps back to the real tool. | `packages/core/src/session/model-request.ts:252-260`, `packages/core/src/session/model-request.ts:278-286` |
| A tool deleted from `tools` fails if the model calls it: "Tool is not available for this request". | `packages/core/src/tool.ts:308-311` |
| `tools` shows direct tools and `execute`. Code Mode tools are not listed individually (inference). | `packages/core/src/tool.ts:293-298` |
| The built-ins `read` and `write` are direct tools. | `packages/core/src/tool/plugin/read.ts:47`, `packages/core/src/tool/plugin/write.ts:49` |
| Retry: when the limit is reached, no decision is offered and the hook does not fire. | `packages/core/src/session/runner/retry.ts:37-38`, `packages/core/src/model-retry.ts:25-36` |
| Retry: the starting `decision` can already be `{ retry: false }`. A hook may change it either way. | `packages/core/src/session/runner/retry.ts:45`, `packages/core/src/session/runner/retry.ts:47-53` |
| Retry: an invalid delay (`NaN`, infinite, negative) falls back to the computed delay. | `packages/core/src/session/runner/retry.ts:49-52` |
| Retry: `error` is `SessionError.Error`: `type`, `message`, `status`, `response`, `retryAfterMs`. | `packages/schema/src/session-error.ts:7-14` |
| `session.generate` uses `ModelRetry.retry`, so `retry` does not fire there. Title uses no retry policy. | `packages/core/src/session/generate.ts:64`, `packages/core/src/session/title.ts:79` |
| Compaction `result`: `summary`, `native?`, `metadata?`, `tokens?`. Tokens are billed with the model's cost. | `packages/plugin/src/promise/session.ts:42-48`, `packages/core/src/session/compaction.ts:855-866` |
| A `prompt` draft is a `structuredClone`. | `packages/core/src/session/prompt.ts:45-51` |
| Prompt input with `id` retried while admitted returns the original result, hooks not rerun. | `packages/core/src/session/session.ts:161-167` |
| Child sessions copy the parent's permission rules (read at one line only). | `packages/core/src/session/projector.ts:168` |

## 7. Tools

### Definition

Fields: `name`, `description`, `input`, `execute`, `output?`, `options?` (`packages/schema/src/tool.ts:92-102`, Promise form `packages/plugin/src/promise/tool.ts:16-24`).

```ts
await ctx.tool.transform((editor) => {
  editor.add({
    name: "greet",
    description: "Greet by name",
    input: {
      type: "object",
      properties: { name: { type: "string" } },
      required: ["name"],
      additionalProperties: false,
    },
    options: { codemode: false },
    execute: async (input, context) => {
      await context.progress({ status: "greeting" })
      return { content: `Hello ${(input as { name: string }).name}` }
    },
  })
})
```

### Schema forms

`ValueSchema` is an Effect `Schema.Codec`, a Standard Schema, or a JSON Schema object (`packages/schema/src/tool.ts:44`).

| Form | As `input` | As `output` | Pin |
|---|---|---|---|
| Effect Schema | Decoded, all errors. JSON Schema generated with `onExcessProperty: "error"`. | Encoded. Failure gives `Tool.Error`. | `packages/core/src/tool/runtime.ts:78-85`, `packages/core/src/tool/runtime.ts:112-118`, `packages/core/src/tool/runtime.ts:175-176` |
| Standard Schema | Validated. Needs `~standard.jsonSchema`, or be a Zod type. Otherwise conversion throws and registration is skipped with a log. | Validated. Same conversion rule. | `packages/core/src/tool/runtime.ts:76`, `packages/core/src/tool/runtime.ts:119-128`, `packages/core/src/tool/runtime.ts:169-173`, `packages/core/src/tool.ts:403-407` |
| JSON Schema | Converted to a codec. Draft 07 or 2020-12. If conversion fails, input is not validated. | Only checked as valid JSON, not against the schema. | `packages/core/src/tool/runtime.ts:15-20`, `packages/core/src/tool/runtime.ts:79`, `packages/core/src/tool/runtime.ts:103-109`, `packages/core/src/tool/runtime.ts:129-133` |

Invalid input gives a `Tool.Error` with a message that asks the model to fix its arguments (`packages/core/src/tool/runtime.ts:64-70`, `packages/core/src/tool/runtime.ts:100`).

### What `execute` receives and returns

| Item | Detail | Pin |
|---|---|---|
| Context | `sessionID`, `agent`, `messageID`, `id`, `progress(update)`. | `packages/schema/src/tool.ts:14-20` |
| Promise extras | `signal`, and `progress` returns a Promise. | `packages/plugin/src/promise/tool.ts:11-14`, `packages/plugin/src/promise/adapter.ts:693-702` |
| Effect form | Returns `Effect<Result, Tool.Error>`. | `packages/schema/src/tool.ts:99` |
| Return | `{ output?, content?, metadata? }`. `content` is a string or an array of text and file parts. | `packages/schema/src/tool.ts:68-90` |
| No `output` schema | Must not return an `output` key, even `undefined`. `"output" in result` is a defect: "Tool result declared output without an output schema". | `packages/core/src/tool/runtime.ts:47-48` |
| Has `output` schema | Must return `output`, or `Tool.Error` "Tool did not return its declared output". | `packages/core/src/tool/runtime.ts:55` |
| No `content` | Text falls back to stringified `output`. | `packages/core/src/tool/runtime.ts:273-277`, `packages/core/src/tool/runtime.ts:279-286` |
| Throw or typed failure | Any failure becomes `Tool.Error` with the message. Original metadata only survives on a real `Tool.Error`. | `packages/core/src/tool/runtime.ts:38-46`, `packages/plugin/src/promise/adapter.ts:680-683` |
| Decline tunnel | A permission decline passes as a defect, not as tool output. | `packages/core/src/tool/runtime.ts:33-37`, `packages/core/src/permission.ts:273-278` |

`Tool.Error` fields: `message`, `error?`, `metadata?` (`packages/schema/src/tool.ts:61-65`). Getting the class: `@opencode/plugin/promise/tool` exports it as `Error` (`packages/plugin/src/promise/tool.ts:1`, `packages/plugin/package.json:31`). `@opencode/plugin/effect` and `effect/tool` do not export it (`packages/plugin/src/effect/index.ts:1-20`, `packages/plugin/src/effect/tool.ts:1-6`). An Effect plugin can import that same path (inference: same underlying class). `@opencode/schema` is not a host-shared package, so a private copy would fail `instanceof Tool.Error` and lose metadata (inference from `packages/plugin/src/runtime-modules.ts:7`, `packages/core/src/tool/runtime.ts:40`).

### Options and Code Mode

| Option | Effect | Pin |
|---|---|---|
| `namespace` | Prefixes the effective name. Dots become `_`. Each dot-separated segment must match `[A-Za-z0-9_-]+`. | `packages/core/src/tool/runtime.ts:290-293`, `packages/core/src/tool.ts:410-413` |
| `codemode` omitted or `true` | When Code Mode is on, the tool is reachable only through `execute`, not as a direct model tool. | `packages/core/src/tool.ts:262-265`, `packages/schema/src/tool.ts:32-42` |
| `codemode: false` | Direct model tool. Cannot be named `execute`. | `packages/core/src/tool.ts:262-264`, `packages/core/src/tool.ts:401-402` |
| Code Mode denied | When rules wholly deny `execute`, all tools become direct. | `packages/core/src/tool.ts:260-264` |
| `pinned` | Only with Code Mode. Marks a tool as pinned in the Code Mode catalog. | `packages/schema/src/tool.ts:34-41`, `packages/core/src/codemode/tool.ts:221-225` |
| `permission` | Action name used to hide the tool. Default is the tool's effective name. | `packages/core/src/tool.ts:257`, `packages/schema/src/tool.ts:29` |

### Permissions

| Fact | Pin |
|---|---|
| A tool is removed from a request's snapshot when the last matching rule is a `*` deny on its action. | `packages/core/src/tool.ts:257`, `packages/core/src/tool.ts:379-382` |
| The execution path shown does not prompt on its own. Call `ctx.permission.assert` inside `execute` (inference). | `packages/core/src/tool.ts:299-320`, `packages/core/src/tool.ts:131-179`, `packages/plugin/src/promise/permission.ts:25-31` |

### Editor and collisions

| Name | Kind | Effect | Pin |
|---|---|---|---|
| `tool.transform` | transform | Editor below. | `packages/plugin/src/promise/tool.ts:26-36` |
| `editor.namespace({name, description})` | editor | Invalid name is logged and skipped. | `packages/core/src/tool.ts:204-211`, `packages/core/src/tool.ts:232-244` |
| `editor.add(tool)` | editor | Stored under the effective name. A later valid add overwrites the same name. An invalid add is logged and leaves the previous one. | `packages/core/src/tool.ts:212-215`, `packages/core/src/tool.ts:364-377` |
| `editor.update(id, fn)` | editor | Missing id ignored. `name`, `id`, and namespace are restored after `fn`. Invalid result is logged and leaves the previous one. | `packages/core/src/tool.ts:216-226` |
| `editor.remove(id)` | editor | Deletes. | `packages/core/src/tool.ts:227-230` |
| `editor.list`, `get` | editor | Current tools with `id`. | `packages/core/src/tool.ts:202-203` |
| `tool.list()` | method | After every transform. | `packages/plugin/src/promise/tool.ts:69-70`, `packages/core/src/tool.ts:250` |
| `tool.reload()` | method | Replays. | `packages/plugin/src/promise/tool.ts:68` |

Name rules: unsupported name characters become `_` (`packages/core/src/tool/runtime.ts:288`), then the name is checked against `^[A-Za-z0-9_-]+$` (`packages/core/src/tool.ts:397-399`). Because order is plugin order, a later plugin overrides an earlier one, and built-in post plugins run after external plugins (`packages/core/src/plugin/supervisor.ts:94-98`, `packages/core/src/plugin/internal.ts:276-296`).

### Tool hooks

| Hook | Kind | Fires | Read | Mutate | Pin |
|---|---|---|---|---|---|
| `tool.hook("execute.before", cb)` | hook | Before each call. With Code Mode it fires for the `execute` wrapper and again for each inner call. | `sessionID`, `agent`, `messageID`, `id` | `tool` (redirects the call), `input` | `packages/plugin/src/promise/tool.ts:39-46`, `packages/core/src/tool.ts:121-129`, `packages/core/src/tool.ts:181-182`, `packages/core/src/tool.ts:275`, `packages/core/src/tool.ts:307-316` |
| `tool.hook("execute.after", cb)` | hook | After `execute` finishes or fails. Not fired when `execute.before` failed or no tool was found (inference). | `tool`, `sessionID`, `agent`, `messageID`, `id`, `input`, `status` | `result` when `completed`, `error` when `error` | `packages/plugin/src/promise/tool.ts:47-63`, `packages/core/src/tool.ts:154-178`, `packages/core/src/tool.ts:307-319` |

`execute.before` rejecting fails that call with `Tool.Error` (`packages/plugin/src/promise/adapter.ts:685-689`). `execute.after` rejecting is a defect (`packages/plugin/src/promise/adapter.ts:690`). The mutated `error` or `result` is what the caller gets (`packages/core/src/tool.ts:160-161`, `packages/core/src/tool.ts:172-177`).

## 8. RPC

### Define

`Rpc.define` from `@opencode/plugin/rpc` or the main entry (`packages/plugin/src/rpc.ts:1`, `packages/plugin/src/promise/index.ts:17`, `packages/schema/src/rpc.ts:54-60`).

```ts
import { Rpc } from "@opencode/plugin/rpc"

export const Acme = Rpc.define({
  id: "acme",
  methods: {
    search: {
      input: {
        type: "object",
        properties: { query: { type: "string" } },
        required: ["query"],
        additionalProperties: false,
      },
      output: {
        type: "object",
        properties: { text: { type: "string" } },
        required: ["text"],
        additionalProperties: false,
      },
      errors: {
        not_found: {
          type: "object",
          properties: { query: { type: "string" } },
          required: ["query"],
          additionalProperties: false,
        },
      },
    },
  },
  events: { updated: { schema: { type: "object", additionalProperties: false } } },
})
```

| Rule | Detail | Pin |
|---|---|---|
| `input`, `output` | Both required. For "no value", declare a schema that accepts it, as the tests do with `Schema.Undefined`. | `packages/schema/src/rpc.ts:13-17`, `packages/core/test/rpc-handler-errors.test.ts:18` |
| Missing `input` or `output` at runtime | `parse`/`encode` read `"~standard" in undefined`, a `TypeError`, so a defect. Over HTTP it becomes `rpc.internal`. **Observed:** HTTP 500 for each of the three cases, and with only `output` missing the handler still ran first. The docs say otherwise ([drift.md](drift.md)). | `packages/core/src/rpc.ts:117`, `packages/core/src/rpc.ts:139`, `packages/core/src/rpc.ts:202-229`, `packages/core/src/rpc.ts:260-262`, `packages/server/src/handlers/rpc.ts:26-30` |
| `errors` | Optional map of name to schema. Names starting `rpc.` throw in `define`. | `packages/schema/src/rpc.ts:9-11`, `packages/schema/src/rpc.ts:54-58` |
| Method name | `events` is forbidden. | `packages/schema/src/rpc.ts:45` |
| `events` map | Required, may be empty. **Observed:** leaving it out makes `await ctx.rpc.register` throw a `TypeError`, which fails the plugin ([drift.md](drift.md)). Event data must be an object. | `packages/schema/src/rpc.ts:29-36`, `packages/schema/src/rpc.ts:43-47` |
| Promise register | Needs `PortableDefinition`: Standard Schema or JSON Schema. | `packages/schema/src/rpc.ts:19-27`, `packages/schema/src/rpc.ts:49-52`, `packages/plugin/src/promise/rpc.ts:27` |
| Effect register | Takes `Definition`, which also allows Effect codecs. | `packages/plugin/src/effect/rpc.ts:25` |

### Register

```ts
const registration = await ctx.rpc.register(Acme, {
  search: async (input, context) => {
    const { query } = input as { query: string }
    const text = await find(query, context.signal)
    if (!text) return context.error("not_found", "Result not found", { query })
    return { text }
  },
})
await registration.events.emit("updated", {})
```

`input` is `unknown` under JSON Schema, hence the cast (`packages/schema/src/rpc.ts:68-72`).

| Fact | Pin |
|---|---|
| Handler context. Promise: `{ signal, error }`. Effect: `{ error }`. | `packages/plugin/src/promise/rpc.ts:7-10`, `packages/plugin/src/effect/rpc.ts:7-9` |
| `context.error(name, message, data)` may be returned or thrown. | `packages/plugin/src/promise/adapter.ts:136-152` |
| Registration: `dispose` plus `events.emit(name, data)`. | `packages/plugin/src/promise/rpc.ts:19-23` |
| Unloading closes it through the scope. | `packages/core/src/rpc.ts:82-85` |
| Several registrations of one id: the last one answers. | `packages/core/src/rpc.ts:111` |
| Registry is per location. | `packages/core/src/rpc.ts:177` |

### Call

| Route | Shape | Pin |
|---|---|---|
| Same plugin or another, in process | `ctx.rpc(Acme).search(input, { signal? })`. `location` and `headers` are typed `never`. | `packages/plugin/src/promise/rpc.ts:25-26` |
| Effect, in process | `ctx.rpc(Acme).search(input)` returns an Effect. | `packages/plugin/src/effect/rpc.ts:24`, `packages/client/src/effect/rpc.ts:14-25` |
| HTTP client | `client.rpc(Acme).search(input, { location?, signal?, headers? })`. | `packages/client/src/promise/rpc.ts:8-10`, `packages/client/src/promise/rpc.ts:18-21` |
| Wire | `POST /api/rpc/:rpcID/:method`. Waits for activation. Empty output is `{}`. | `packages/protocol/src/groups/rpc.ts:14`, `packages/server/src/handlers/rpc.ts:11-14` |
| In-process during setup | Does not wait for activation, so an RPC from a later plugin gives `rpc.unavailable` (inference). | `packages/core/src/rpc.ts:111-112` |

| Failure | Result | Pin |
|---|---|---|
| Closed location or no registration | `rpc.unavailable` | `packages/core/src/rpc.ts:109-112` |
| Method missing | `rpc.method_not_found` | `packages/core/src/rpc.ts:113-114` |
| Bad input | `rpc.invalid_input` | `packages/core/src/rpc.ts:117-119` |
| Bad output | `rpc.invalid_output`; HTTP 500. | `packages/core/src/rpc.ts:139-141`, `packages/server/src/handlers/rpc.ts:17-18`, `packages/protocol/src/errors.ts:31-39` |
| Undeclared error, or any other throw | Logged, `rpc.internal`. | `packages/core/src/rpc.ts:127-131`, `packages/core/src/rpc.ts:231-235` |
| Declared error | `{ type, message, data? }`; HTTP 400. | `packages/core/src/rpc.ts:236-239`, `packages/protocol/src/errors.ts:21-29` |
| Client rejection value | A plain object, not an `Error`. | `packages/client/src/promise/rpc.ts:114-119` |

### Events

| Fact | Pin |
|---|---|
| Published ephemeral with type `rpc.<id>.<name>`, tagged with the plugin's location. | `packages/core/src/rpc.ts:91-103`, `packages/core/src/rpc.ts:195-200` |
| Unknown event name fails `emit`. Data is encoded first. | `packages/core/src/rpc.ts:93`, `packages/core/src/rpc.ts:97` |
| In-plugin subscribe is filtered to the plugin's location. | `packages/core/src/rpc.ts:164-167` |
| HTTP clients are not location filtered. | `packages/client/src/promise/rpc.ts:70-72` |
| Promise: `events.subscribe(name, {signal?})` and `events.on(name, handler, {signal?})`. | `packages/client/src/promise/rpc.ts:23-33`, `packages/plugin/src/promise/adapter.ts:104-115` |
| Effect: `events.subscribe(name)` only. | `packages/client/src/effect/rpc.ts:26-32` |
| `events.on` logs handler errors rather than stopping. | `packages/plugin/src/promise/adapter.ts:113` |

## 9. Storage

| Name | Kind | Effect | Pin |
|---|---|---|---|
| `storage.get(key)` | method | `Json \| undefined`. | `packages/plugin/src/promise/storage.ts:5` |
| `storage.set(key, value)` | method | `value` must be `Schema.Json`. | `packages/plugin/src/promise/storage.ts:6` |
| `storage.remove(key)` | method | | `packages/plugin/src/promise/storage.ts:7` |
| `storage.scan({prefix, after?, limit?})` | method | `{ entries, next? }`. `prefix` is required. | `packages/plugin/src/storage.ts:8-17` |

| Fact | Pin |
|---|---|
| Namespaced by plugin id: `plugin:<hex of id>:`. Renaming the id loses access (inference). | `packages/core/src/plugin/host.ts:664-667` |
| Backing KV is a global node, so all locations share the same values for one plugin id. | `packages/core/src/kv.ts:92` |
| Durable, in a database table. | `packages/core/src/kv.ts:58`, `packages/core/src/kv.ts:63-65` |
| Limit default 100, clamped to 1..1000. Ascending key order. | `packages/core/src/kv.ts:61`, `packages/core/src/kv.ts:73` |
| `next` is the last returned key. Pass it as `after`. | `packages/core/src/kv.ts:77-79`, `packages/core/src/plugin/host.ts:676` |
| Returned keys have the namespace stripped. | `packages/core/src/plugin/host.ts:680-686` |

## 10. Options

| Fact | Pin |
|---|---|
| `ctx.options` is `Readonly<Record<string, any>>`. | `packages/plugin/src/options.ts:1` |
| Config object form supplies it. Default `{}`. | `packages/core/src/config/plugin/source.ts:116-123` |
| A `-target` config entry removes a plugin. | `packages/core/src/config/plugin/source.ts:116-123`, `packages/core/src/plugin/supervisor.ts:35-41` |
| `options` is part of the plugin revision, so changing it restarts that plugin and later ones (inference). | `packages/core/src/plugin/module.ts:135`, `packages/core/src/plugin.ts:122-126` |

## 11. Promise and Effect differences

| Topic | Promise | Effect | Pin |
|---|---|---|---|
| Entry | `setup` | `effect` | `packages/plugin/src/promise/plugin.ts:64-67`, `packages/plugin/src/effect/plugin.ts:62-65` |
| Cleanup | Return a function | Scope finalizers | `packages/plugin/src/promise/plugin.ts:62`, `packages/plugin/src/effect/plugin.ts:62-65` |
| `dispose` | `() => Promise<void>` | `Effect<void>` | `packages/plugin/src/promise/registration.ts:2`, `packages/plugin/src/effect/registration.ts:4` |
| Hook registration | `Promise<Registration>` | Needs `Scope` | `packages/plugin/src/promise/registration.ts:10-13`, `packages/plugin/src/effect/registration.ts:12-17` |
| Hook failure | Rejection is a defect, `execute.before` excepted | Typed `never`, `execute.before` may fail with `Tool.Error` | `packages/plugin/src/promise/adapter.ts:625`, `packages/plugin/src/effect/tool.ts:48-52` |
| Method calls | JSON round trip through endpoint schemas | Direct host call (inference) | `packages/plugin/src/promise/adapter.ts:266-281`, `packages/core/src/plugin/module.ts:164` |
| Domain error type | Rejection | `unknown` error channel, for example `PermissionApi<unknown>` | `packages/plugin/src/effect/permission.ts:25` |
| `permission.assert` | Rejects | `Effect<void, Tool.Error>` | `packages/plugin/src/promise/permission.ts:31`, `packages/plugin/src/effect/permission.ts:32` |
| `event.subscribe` | `AsyncIterable` with `signal` | `Stream` with `types` | `packages/plugin/src/promise/event.ts:6-10`, `packages/plugin/src/effect/event.ts:4-10` |
| Tool `execute` | `(input, ToolContext) => Promise<Result>` with `signal` | `(input, Tool.Context) => Effect<Result, Tool.Error>` | `packages/plugin/src/promise/tool.ts:11-24`, `packages/schema/src/tool.ts:99` |
| RPC handler context | `{ signal, error }` | `{ error }` | `packages/plugin/src/promise/rpc.ts:7-10`, `packages/plugin/src/effect/rpc.ts:7-9` |
| RPC definition | `PortableDefinition` | `Definition` | `packages/plugin/src/promise/rpc.ts:27`, `packages/plugin/src/effect/rpc.ts:25` |
| Provider callbacks, for example vcs | Return a Promise | Return an Effect | `packages/plugin/src/promise/vcs.ts:25-34`, `packages/plugin/src/effect/vcs.ts:27-36` |
| Cancellation in callbacks | `{ signal }` argument | Interruption | `packages/plugin/src/promise/websearch.ts:8-11`, `packages/plugin/src/promise/adapter.ts:674-676` |
| `Tool.Error` export | `@opencode/plugin/promise/tool` | none | `packages/plugin/src/promise/tool.ts:1`, `packages/plugin/src/effect/tool.ts:1-6` |
| `VcsDiffInput.untracked` | absent | present | `packages/plugin/src/promise/vcs.ts:18-23`, `packages/plugin/src/effect/vcs.ts:24` |
| `PluginOptions` type export | yes | no | `packages/plugin/src/promise/index.ts:1`, `packages/plugin/src/effect/index.ts:1-4` |

## 12. Runtime module sharing

| Fact | Pin |
|---|---|
| Host-provided packages: `effect` and `@opencode/plugin`. | `packages/plugin/src/runtime-modules.ts:7` |
| Each is registered with `Bun.plugin` `build.module`, one per specifier. | `packages/plugin/src/runtime.ts:17-27` |
| A copy of either under plugin `node_modules` throws on load: `plugins must use the host's "effect" and "@opencode/plugin" modules`. | `packages/plugin/src/runtime.ts:28-34`, `packages/plugin/src/runtime.ts:3-4` |
| Subpaths skipped from the shared list: `internal/`, `/internal/`, `source.*`, `runtime*`, `gui/`. | `packages/plugin/src/runtime-modules.ts:44-52` |
| Outside Bun, setup is a no-op. | `packages/plugin/src/runtime.ts:13` |
| Current `effect` version is the workspace catalog `4.1.0`. | `package.json:83`, `packages/plugin/package.json:43-51` |
| Package exports map `./gui/*` to `null` and every other subpath `./*` to `./src/*.ts`. | `packages/plugin/package.json:30-31` |

So: do not bundle `effect` or `@opencode/plugin`. Keep them external and declare them as peers (inference from the throw above; `packages/plugin/README.md:14` says the same for `effect`). Other dependencies, including `@opencode/schema`, are not shared by this mechanism (`packages/plugin/src/runtime-modules.ts:7`).

## 13. Ordering, failure, restart

### Ordering

| Fact | Pin |
|---|---|
| Boot order: internal pre, SDK, instance, config packages, internal post. | `packages/core/src/plugin/supervisor.ts:94-98`, `packages/core/src/plugin/supervisor.ts:146` |
| Post built-ins include the dynamic provider loader, which must see `sdk` hooks from external plugins. | `packages/core/src/plugin/internal.ts:276-296` |
| Transforms and hooks follow setup order, so a later plugin wins on overwrite and sees earlier mutations. | `packages/core/src/state.ts:191-213`, `packages/core/src/plugin/hooks.ts:75`, `packages/core/src/plugin/hooks.ts:89` |
| Guarded built-ins cannot be removed by config. | `packages/core/src/plugin/internal.ts:300` |

### Failure

| Failure | Behaviour | Pin |
|---|---|---|
| `setup` rejects or Effect dies | Scope closed, warning logged, slot `failed`. No cleanup call. | `packages/core/src/plugin.ts:90-100`, `packages/plugin/src/promise/adapter.ts:666-669` |
| Reload fails on setup | Previous definition is loaded again, and the error stays on the slot. If that fails too, "failed to restore plugin; deactivating". | `packages/core/src/plugin.ts:168-181` |
| Same failed revision | Not retried on reorder. | `packages/core/src/plugin.ts:153-157` |
| Unchanged failing module | Not re-evaluated, from the digest cache. | `packages/plugin/src/source.ts:35-38` |
| Transform throws | Whole plugin disabled, scope closed. | `packages/core/src/plugin.ts:65-78`, `packages/core/src/plugin.ts:194-248` |
| Hook rejects | Defect fails the running operation. | `packages/plugin/src/promise/adapter.ts:625` |
| Tool invalid at registration | Logged "Skipping invalid tool registration". Previous definition stays. | `packages/core/src/tool.ts:232-244`, `packages/core/src/tool.ts:364-377` |
| Duplicate plugin id | First kept. Later reported failed: "Duplicate plugin ID". | `packages/core/src/plugin/supervisor.ts:99-113`, `packages/core/src/plugin.ts:110` |
| Module fails to install or load | Running generation kept when an error occurs on update. | `packages/core/src/plugin/supervisor.ts:74-85` |
| Pending package install | Not listed as failure; the install pass follows. | `packages/core/src/plugin/supervisor.ts:70-73`, `packages/core/src/plugin/supervisor.ts:166` |
| Blocked by policy | Not loaded. | `packages/core/src/plugin/supervisor.ts:63-69`, `packages/core/src/plugin/module.ts:53-54` |

### Restart

| Fact | Pin |
|---|---|
| Triggers: `sources.changes()`, `modules.changes()`, a 24 hour timer, bus events `Event.Updated` and `SdkPlugins.Updated`, package update state. Initial activation runs at once; later requests debounce 100 ms. | `packages/core/src/plugin/supervisor.ts:205-221` |
| Diff compares id and revision position by position. | `packages/core/src/plugin.ts:122-126` |
| Only the unchanged prefix stays alive. Everything after the first change is closed in reverse order and started again. | `packages/core/src/plugin.ts:139-151` |
| So a change to one plugin re-runs `setup` for every plugin after it (inference, restating the comment at the pin). | `packages/core/src/plugin.ts:139` |
| All of it runs in one `State.batch`. | `packages/core/src/plugin.ts:137` |
| Nothing changed: inventory refreshed, no restart. | `packages/core/src/plugin.ts:131-135` |
| Local sources are watched. | `packages/core/src/plugin/module.ts:27-39` |

## 14. Not checked

- Option precedence and body overlay rules claimed at `services/www/src/docs/content/build/plugins/server.mdx:1442-1445`: these live in `packages/ai`, which was not read.
- Concurrent prompt admission behaviour, `services/www/src/docs/content/build/plugins/server.mdx:1401`.
- `resolveModule` extension handling (`packages/util/src/runtime-import.ts:1` only re-exports it), so the file extension list at `services/www/src/docs/content/build/plugins/index.mdx:88` is unverified.
- Exact input and output types of generated client operations are not repeated here; see `packages/client/src/promise/generated/types.ts`.
- Code Mode runner internals under `packages/core/src/codemode/`, beyond the `pinned` filter.
