# Packaging and publishing a plugin

Read from source at the pinned commit. Lines marked **Observed** were seen on a real OpenCode ([testing.md](testing.md)). The repository's own [package.json](../../package.json) is a working example.

## The package

One package holds every part. Each part is an export ([loading.md](loading.md) says how exports resolve).

```json
{
  "name": "opencode-acme-plugin",
  "version": "1.0.0",
  "type": "module",
  "exports": {
    ".": "./src/index.ts",
    "./tui": "./src/tui.tsx",
    "./gui-experimental": "./dist/gui-experimental.cjs",
    "./rpc": "./src/rpc.ts"
  },
  "files": ["src", "dist"],
  "peerDependencies": { "@opencode/plugin": "^2.2.0" },
  "devDependencies": { "@opencode/plugin": "2.2.5" }
}
```

- **TypeScript runs as is.** The server and TUI parts can point at `.ts` and `.tsx` source: OpenCode's Bun runtime loads them. The official Figma plugin ships `index.ts` (`packages/plugins/figma/package.json`, its `exports` and `files`).
- **The GUI part cannot.** It must be one prebuilt CommonJS file ([gui.md](gui.md)), and `.ts` is rejected by the extension check (`packages/plugin/src/host.ts:61`). `dist/` is ignored by git here, so build it before publishing: `prepublishOnly` does.
- **The RPC contract** goes in its own export, so clients can import it without loading your implementation (`services/www/src/docs/content/build/plugins/index.mdx:101`).

## Depending on `@opencode/plugin`

| Package | For | npm, at the pin's date |
|---|---|---|
| `@opencode/plugin` | V2 | 2.2.5 |
| `@opencode-ai/plugin` | V1. V1 plugins do not run on V2 (`services/www/src/docs/content/build/plugins/migrate-v1.mdx:11`) | 1.19.5 |

The host provides `@opencode/plugin` and `effect` itself: imports of them, including from a plugin's own `node_modules`, resolve to the host's copies, so fibers, loggers and `Schema` share one instance (`packages/plugin/README.md`, section "Packaging And Runtime `effect`"; `packages/plugin/src/runtime.ts:1`).

- **Declare it as a peer**, with a pinned dev dependency for types. The official plugin does this (`packages/plugins/figma/package.json`). The V2 overview's example uses `"dependencies": { "@opencode/plugin": "latest" }` instead (`services/www/src/docs/content/build/plugins/index.mdx:39`); see [drift.md](drift.md).
- **Do not bundle `effect`.** Declare `"effect": "^4.0.0"` as a peer if you import it, keep it external, and use only public subpaths. A dependency built on Effect 3 is not supported, and an import of a private `internal` module fails to load.
- **Observed:** a local plugin importing `@opencode/plugin` and `@opencode/plugin/rpc` loads with no `node_modules` at all, and also with them present.
- A local plugin's other dependencies do need installing, in its own folder.

## Which version to target

Three versions can differ at once, and each has its own truth:

| What | How to read it |
|---|---|
| The snapshot here | `plugin_package_version` in [upstream/SNAPSHOT.json](../upstream/SNAPSHOT.json) |
| The CLI on PATH | `opencode --version` |
| OpenCode Desktop's own CLI copy | Settings, or the version folder under its app data. It updates with Desktop, not with the CLI |

A published plugin runs on whatever each user has. So:

1. Set the peer range to the oldest release you have tested, and test on it: `python -I tools/smoke_plugin.py --opencode <path to that CLI>`.
2. To read that release's source, snapshot its tag: `python -I tools/sync_upstream.py --sync --ref v2.2.1`.
3. Publish a compatible update when you adopt a newer API (`services/www/src/docs/content/build/plugins/index.mdx:105`).

**Observed:** the template's starter, typed against SDK 2.2.5, passes on CLI 2.2.1 and on CLI 2.2.5 ([results](../../studies/2026-11-03/results.md)).

## Publishing

```bash
npm publish
```

Check first with `npm pack --dry-run` that `dist/gui-experimental.cjs` is in the file list, if the plugin has a GUI part. A package consumer installs through `opencode plugin add`, or an entry in `plugins`; `exports` decide the rest.

Test the installed package, not only the local copy: a workspace link can hide a missing `files` entry (`services/www/src/docs/content/build/plugins/index.mdx:105`). `tools/smoke_plugin.py` loads the local directory, so it does not cover this.

Git installation also works, without a registry: `opencode plugin add github:owner/repo`, optionally with `#ref` and `::path:sub/dir` (`services/www/src/docs/content/plugins.mdx:107`). The official plugins are "currently installed from Git URLs, not npm" (`packages/plugins/README.md:3`).

## Supporting V1 and V2 from one package

A default export can carry both `server()` for V1 and `setup()` for V2; the two share no hooks. V1 object entrypoints need OpenCode 1.18.29 or newer (`services/www/src/docs/content/build/plugins/migrate-v1.mdx:335`). Prefer V2 only unless the owner needs V1 users.
