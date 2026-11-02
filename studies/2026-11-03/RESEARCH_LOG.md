# Research log, 3 November 2026

Times are not recorded per call: the work ran as one session. Everything read was treated as data, and nothing from upstream was run except the published OpenCode CLI and the `@opencode/plugin` package, in private instances. Source text is under the MIT license ([LEGAL_FLAGS.md](../../LEGAL_FLAGS.md)).

**Source commit:** `1bf08ae46a91f7793c756e4ee521e37b6b554064`, on branch `dev` of [anomalyco/opencode](https://github.com/anomalyco/opencode), committed 2 November 2026, with packages at version 2.2.5. It is 123 commits ahead of tag `v2.2.5`.

1. git. `https://github.com/anomalyco/opencode`, a full clone at the commit above, for reading. On Windows, `core.longpaths=true` was needed for a full checkout.
2. git. The two doc sets, located: `services/www/src/docs/content/` (V2) and `packages/web/src/content/docs/` (V1). Commit `db52b1821`, "docs: remove V2 details from V1 docs", separates them.
3. Web fetch. `https://opencode.ai/llms.txt`, which leads to `https://opencode.ai/v2/llms.txt`, listing the V2 pages. It confirmed the V2 docs' base path.
4. Web fetch. `https://opencode.ai/v2/docs/` overview, server, TUI, GUI, RPC, Effect and migration pages. Each returned HTTP 200, and held text found in the repository's copy.
5. Web fetch. `https://opencode.ai/docs/plugins/`. It returned the V1 page, naming `@opencode-ai/plugin` and not `@opencode/plugin` or `Plugin.define`.
6. npm. `@opencode/plugin`, latest 2.2.5. `@opencode-ai/plugin`, 1.19.5. `@opencode/cli`, latest 2.2.5.
7. GitHub API. The "latest release" was `v1.19.5`, though `v2.2.5` existed.
8. Read in full: `packages/plugin/README.md`, `packages/plugin/AGENTS.md`, `packages/plugin/src/README.md`, `packages/plugin/src/host.ts`, `packages/plugin/src/promise/plugin.ts`, `packages/plugin/src/gui/vite.ts`, `packages/plugin/src/gui/plugin.ts`, `packages/plugin/src/gui/modules.ts`, `packages/core/src/plugin.ts`, `packages/core/src/plugin/module.ts`, `packages/core/src/plugin/supervisor.ts`, `packages/core/src/plugin/update.ts`, `packages/core/src/plugin/source-directory.ts`, `packages/core/src/config/plugin/source.ts`, the handlers in `packages/cli/src/commands/handlers/plugin/`, `packages/gui-plugins/README.md`, `packages/gui-plugins/AGENTS.md`, and the docs in `services/www/src/docs/content/build/plugins/`, `plugins.mdx`, `cli/plugins.mdx` and `lib/navigation.ts`.
9. Three independent read-throughs of the commit, one per part, each writing `path:line` citations and comparing the docs against the source. They became [server.md](../../plugin-dev/guide/server.md), [tui.md](../../plugin-dev/guide/tui.md), [gui.md](../../plugin-dev/guide/gui.md) and [drift.md](../../plugin-dev/guide/drift.md). Their citations were checked mechanically, and random samples of them, with every high-severity drift entry, were read against the cited lines.
10. Runs on the real CLI: [results.md](results.md).

**How deep this went.** The hosts and the SDK types were read in full, or cited line by line. **Not reached:** `packages/ai`, for option precedence; OpenTUI's source, because `node_modules` were not read; Code Mode's runner; a real Desktop window, a real model and a real TUI session.
