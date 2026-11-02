# The anatomy of an OpenCode plugin

**Date:** 3 November 2026. **Goal, in the request's words:** "make it specialized for opencode plugins". **Method:** reading OpenCode's official docs and its source at the pin, and running a real OpenCode where a doc looked wrong. **Status:** research only, an inventory and not a decision. It says what any OpenCode plugin has to think about. What one plugin's goal needs is added in its first session ([ANATOMY.md](../ANATOMY.md)).

## The answer in brief

81 parts in 16 areas. The core is the **plugin's shape**: one package whose parts run in different processes, so every feature has to say which part it lives in and which surface shows its result. Most of the rest follows from what each part can reach. Of the 81 parts, 11 are Recorded by a rule here and 70 are Gaps, which is correct for a plugin with nothing built yet.

## Method

1. Read the V2 docs in full, and took the area list from what they say a plugin can add ([S1](#sources)).
2. Read the SDK's context types ([S3](#sources)), which added what the docs leave out.
3. Read the three hosts, for what happens at load, reload and failure ([S4, S5, S6](#sources)).
4. Compared each doc against the source, which gave [drift.md](../../plugin-dev/guide/drift.md).
5. Ran what the docs and source disagreed on ([results.md](results.md)).
6. Read real plugins ([S7](#sources)): they added install notes and support, and no new area of code.

The areas stopped changing after step 3. Steps 4 to 6 added parts only.

## How the areas were chosen

The first ten follow the code: A1 and A2 are the two surfaces, A3 is the package, A4 to A7 are the groups of the server context, A8 and A9 are how parts talk and remember, and A10 is the host. A11 to A16 surround the code: they come from packaging, the demonstrations, the security reading, and the owner's rule that source outranks docs.

## Sources

Every URL, and the commit, is in [RESEARCH_LOG.md](RESEARCH_LOG.md).

| Code | Source | Kind | How it was read | What it adds |
|---|---|---|---|---|
| S1 | [OpenCode V2 plugin docs](../../plugin-dev/upstream/services/www/src/docs/content/build/plugins/index.mdx) | Official docs | In full, against the source | Sets the parts, and names what each adds |
| S2 | [OpenCode plugin configuration docs](../../plugin-dev/upstream/services/www/src/docs/content/plugins.mdx) | Official docs | In full | Config entries, discovery, Desktop and terminal behaviour |
| S3 | [The plugin SDK, `packages/plugin/`](../../plugin-dev/upstream/packages/plugin/src/README.md) | Source code | In full for the Promise, TUI and GUI APIs | Every context member a plugin can touch |
| S4 | [The server host, `packages/core/src/plugin/`](../../plugin-dev/upstream/packages/core/src/plugin/supervisor.ts) | Source code | In full for loading and lifecycle; by pin for the rest | What really happens at load, reload and failure |
| S5 | [The terminal host, `packages/tui/src/plugin/`](../../plugin-dev/upstream/packages/tui/src/plugin/context.tsx) | Source code | In full | How a TUI part is found and run |
| S6 | [The Desktop hosts, `packages/desktop/src/main/plugin/` and `packages/app/src/runtime/plugin/`](../../plugin-dev/upstream/packages/desktop/src/main/plugin/host.ts) | Source code | In full for loading; by pin for the rest | How a GUI part is found and run |
| S7 | [Real plugins: Figma, Browser, Pairing](../../plugin-dev/upstream/packages/plugins/README.md) | Source code | In part | What shipped plugins actually contain |
| S8 | [This study's own runs on OpenCode CLI 2.2.1 and 2.2.5](../../studies/2026-11-03/results.md) | Our measurement | Run | What was observed, as against read |

## What the repository covers

| Area | The question it answers | Parts | Recorded | Gap |
|---|---|---|---|---|
| A1 Terminal UI | What a person sees in `opencode`, from a TUI part. | 5 | 0 | 5 |
| A2 OpenCode Desktop | What a person sees in Desktop, from a GUI part. | 8 | 0 | 8 |
| A3 Plugin shape | Which parts the plugin has, and how they fit together. Everything passes through this. | 5 | 1 | 4 |
| A4 Tools | What the model can call. | 5 | 0 | 5 |
| A5 Commands and session work | What a person triggers, and how results enter a session. | 4 | 0 | 4 |
| A6 Hooks and transforms | Changing what OpenCode does as it runs. | 6 | 0 | 6 |
| A7 What it contributes | Adding to OpenCode's own catalogs. | 5 | 0 | 5 |
| A8 RPC | How the parts and outside clients call the server part. | 4 | 0 | 4 |
| A9 State | What the plugin keeps, and where. | 4 | 0 | 4 |
| A10 OpenCode itself | What the plugin draws on: the release it runs under, and how that loads it. | 6 | 0 | 6 |
| A11 Compatibility | Which OpenCode this works on. | 5 | 1 | 4 |
| A12 Packaging and distribution | How it reaches a user. | 5 | 0 | 5 |
| A13 Demonstration | How anyone knows it works. | 7 | 3 | 4 |
| A14 Security and privacy | What the plugin can reach, and what it must not leak. | 4 | 0 | 4 |
| A15 Docs, support and legal | What a user reads, and what the owner must clear. | 4 | 2 | 2 |
| A16 Plugin knowledge | Keeping what this project knows true to upstream. | 4 | 4 | 0 |

The parts, with their status and Proposed priority:

**A1 Terminal UI.** What a person sees in `opencode`, from a TUI part.

| Part | Meaning | Status |
|---|---|---|
| A1.1 Commands and keybindings | Commands in the palette, as slash commands and on keys | Gap |
| A1.2 Routes and slots | Whole screens, and pieces placed in the home, session and sidebar layouts | Gap |
| A1.3 Dialogs, toasts and panels | Passing feedback, questions and session panels | Gap |
| A1.4 Markdown renderers and theme use | Custom code block rendering, and following the user's theme | Gap |
| A1.5 Terminal attention | Notifying the user, which is off until they enable it | Gap |

**A2 OpenCode Desktop.** What a person sees in Desktop, from a GUI part.

| Part | Meaning | Status |
|---|---|---|
| A2.1 Panels and tabs | Side panels, and tabs in the session view | Gap |
| A2.2 Commands and menu items | The palette, composer slash list, row menus and the title bar | Gap |
| A2.3 Settings pages | A page of the plugin's own under Settings | Gap |
| A2.4 Composer pills and notes | Controls and context in the prompt composer | Gap |
| A2.5 Toasts and attention | Passing feedback and notifications in windows | Gap |
| A2.6 Main process entry | Native work in Electron's main process, with full Node.js access | Gap |
| A2.7 Window to main calls | Typed calls between a window and the main entry (Ipc and Live) | Gap |
| A2.8 Translations | Text in the user's language, which cannot be loaded lazily here | Gap |

**A3 Plugin shape.** Which parts the plugin has, and how they fit together. Everything passes through this.

| Part | Meaning | Status |
|---|---|---|
| A3.1 Which parts it has | Server, TUI, GUI and RPC, chosen per feature | Gap, P1 |
| A3.2 Which surface each feature serves | Where a person sees each result, so none reaches nobody | Recorded |
| A3.3 Identity | The plugin's id, its package name, and how selectors use the id | Gap |
| A3.4 User options | Settings from the config entry. They reach a GUI part only as JSON, and never reach a TUI part from `opencode.json` | Gap, P6 |
| A3.5 Promise or Effect | Which server API the code is written against | Gap |

**A4 Tools.** What the model can call.

| Part | Meaning | Status |
|---|---|---|
| A4.1 Tool definitions | Name, description, input and output schemas | Gap, P2 |
| A4.2 Reachability under Code Mode | A tool is reached only through `execute` unless it sets `codemode: false` | Gap, P2 |
| A4.3 Tool results | What `execute` returns, and how the model and the transcript see it | Gap |
| A4.4 Tool permissions | Asking before an action, and the action name used to hide a tool | Gap |
| A4.5 Changing other tools | Editing, removing or redirecting a tool, and name collisions | Gap |

**A5 Commands and session work.** What a person triggers, and how results enter a session.

| Part | Meaning | Status |
|---|---|---|
| A5.1 Server slash commands | Listed on both surfaces. `execute` returns nothing | Gap, P3 |
| A5.2 Feedback into the session | `session.prompt`, which starts the model, or `session.synthetic` | Gap, P3 |
| A5.3 Reading and starting sessions | Listing, reading, creating and steering sessions | Gap |
| A5.4 Stateless generation | One model call with no session, which is experimental | Gap |

**A6 Hooks and transforms.** Changing what OpenCode does as it runs.

| Part | Meaning | Status |
|---|---|---|
| A6.1 Session hooks | Prompt, context, model request, retry and other points in a run | Gap |
| A6.2 Tool hooks | Before and after a tool runs | Gap |
| A6.3 Permission hooks | Deciding or watching permission requests | Gap |
| A6.4 Shell hooks | Changing the shell environment | Gap |
| A6.5 Events | Subscribing to what happens on the bus | Gap |
| A6.6 Transform safety | One throw disables the whole plugin | Gap, P4 |

**A7 What it contributes.** Adding to OpenCode's own catalogs.

| Part | Meaning | Status |
|---|---|---|
| A7.1 Agents | Agent definitions | Gap |
| A7.2 Skills and references | Skills and reference sources | Gap |
| A7.3 Providers and models | Model providers, models and their AI SDK hooks | Gap |
| A7.4 MCP servers and integrations | MCP servers, and connections with OAuth or keys | Gap |
| A7.5 Web search, VCS and worktrees | Other replaceable OpenCode services | Gap |

**A8 RPC.** How the parts and outside clients call the server part.

| Part | Meaning | Status |
|---|---|---|
| A8.1 The contract | Methods and events, always with `input`, `output` and `events` | Gap, P5 |
| A8.2 Errors | Declared errors, and the `rpc.` system errors callers can get | Gap |
| A8.3 Events to clients | Pushing changes to a TUI or GUI part | Gap |
| A8.4 Location | Which project a call runs against. From a GUI part with no location, it is the home folder | Gap |

**A9 State.** What the plugin keeps, and where.

| Part | Meaning | Status |
|---|---|---|
| A9.1 Server storage | `ctx.storage`, shared across locations for a plugin id | Gap |
| A9.2 TUI and GUI storage | Each surface's own stored state, which the others cannot read | Gap |
| A9.3 Surviving a restart | `setup` runs again on any reload, also for plugins that did not change | Gap, P4 |
| A9.4 Files and outside data | What the plugin stores outside OpenCode | Gap |

**A10 OpenCode itself.** What the plugin draws on: the release it runs under, and how that loads it.

| Part | Meaning | Status |
|---|---|---|
| A10.1 Finding the plugin | Config entries, discovered folders, and what is silently skipped | Gap |
| A10.2 Activation order | Who runs first, and duplicate ids | Gap |
| A10.3 Reload | What restarts when a file changes, including every plugin after it | Gap |
| A10.4 Failure | How a failed plugin shows, and how an older revision keeps running | Gap |
| A10.5 Cleanup | What `setup` must release, and in what order | Gap |
| A10.6 Managed policy | What an organization's policy can block | Gap |

**A11 Compatibility.** Which OpenCode this works on.

| Part | Meaning | Status |
|---|---|---|
| A11.1 The release it targets | The OpenCode version and the `@opencode/plugin` range | Recorded |
| A11.2 Desktop's own CLI | Desktop's bundled OpenCode updates apart from the CLI on PATH | Gap |
| A11.3 V1 users | Whether to support V1 from one package, and how to port | Gap |
| A11.4 Shared runtime modules | The host provides `effect` and the SDK; never bundle them | Gap |
| A11.5 Operating systems and builds | Windows paths, the Bun and Node builds, and a part's `os` limit | Gap |

**A12 Packaging and distribution.** How it reaches a user.

| Part | Meaning | Status |
|---|---|---|
| A12.1 Package layout | `exports`, `files` and what ships | Gap |
| A12.2 GUI bundle build | One CommonJS file through the official Vite preset, built before publishing | Gap |
| A12.3 Publishing | npm, or a Git URL as OpenCode's own plugins use | Gap, P8 |
| A12.4 Install instructions | A global config entry for a GUI, and `cli.json` for a remote server or TUI options | Gap, P8 |
| A12.5 Updates | The 24-hour check, pinned versions and what users do | Gap |

**A13 Demonstration.** How anyone knows it works.

| Part | Meaning | Status |
|---|---|---|
| A13.1 Isolated instance | A private OpenCode, so the owner's live one is never a test bench | Recorded |
| A13.2 Smoke test | The plugin's id, parts, commands and RPC, through the real API | Recorded |
| A13.3 Typecheck | Against the pinned SDK | Recorded |
| A13.4 A real model calling its tools | With a real provider, or a deterministic fake | Gap, P7 |
| A13.5 In a real Desktop window | The bundle running, its panels and commands visible | Gap, P7 |
| A13.6 In a real terminal UI | The TUI part drawn and used | Gap, P7 |
| A13.7 The installed package | A tarball or registry install, not the working folder | Gap, P7 |

**A14 Security and privacy.** What the plugin can reach, and what it must not leak.

| Part | Meaning | Status |
|---|---|---|
| A14.1 What a plugin can do | It runs with OpenCode's rights, and nothing read in the loader isolates it | Gap, P9 |
| A14.2 Secrets | Credential storage, and never placing a secret in options that reach windows | Gap, P9 |
| A14.3 Data sent to models | What the plugin adds to prompts and tool results | Gap |
| A14.4 Asking before acting | Permission rules for anything the plugin does outside OpenCode | Gap |

**A15 Docs, support and legal.** What a user reads, and what the owner must clear.

| Part | Meaning | Status |
|---|---|---|
| A15.1 User README | What it does, on which surface, how to install and turn off | Gap, P10 |
| A15.2 Compatibility statement | The releases it ran on, with what was not run | Gap, P10 |
| A15.3 Licenses | This plugin's license, and the flags on what it copies | Recorded |
| A15.4 The OpenCode name | Using it in a package name is not reviewed | Recorded |

**A16 Plugin knowledge.** Keeping what this project knows true to upstream.

| Part | Meaning | Status |
|---|---|---|
| A16.1 Source over docs | The rule, and the order of authority | Recorded |
| A16.2 The pinned snapshot | OpenCode's docs and source, copied at a commit | Recorded |
| A16.3 Noticing upstream change | `tools/sync_upstream.py --check` | Recorded |
| A16.4 Recorded drift | Where docs and source disagree, and what to do | Recorded |

## The gaps that matter most

Proposed, and our own reasoning except where a source is named. The main values are not set yet, so this ranks by what costs most to discover late.

| # | Gaps | Why |
|---|---|---|
| P1 | A3.1 | Which parts a plugin has decides everything else |
| P2 | A4.1, A4.2 | Tools are what a model reaches, and the Code Mode default hides a tool from direct use (`packages/core/src/tool.ts:262`) |
| P3 | A5.1, A5.2 | A command that gives no feedback looks broken, as `execute` returns nothing |
| P4 | A6.6, A9.3 | A throw disables a plugin, and `setup` re-runs on any reload ([results.md](results.md)) |
| P5 | A8.1 | The docs' RPC advice fails when followed ([results.md](results.md)) |
| P6 | A3.4 | Options do not reach every part alike ([drift.md](../../plugin-dev/guide/drift.md)) |
| P7 | A13.4 to A13.7 | The smoke test cannot show these. Each is `UNEXECUTED` in this template |
| P8 | A12.3, A12.4 | A GUI part in a project's config silently does not load |
| P9 | A14.1, A14.2 | A plugin holds OpenCode's rights, and options reach every window |
| P10 | A15.1, A15.2 | A user needs to know which surface and which release it works on |

## What this study does not settle

- What this plugin is, and so which of these parts it needs: the owner decides, in the first session.
- Any choice between options: none is put here. Each needs its own study ([Decisions rest on research](../../AGENTS.md#decisions-rest-on-research)).
- **Not reached:** the option precedence rules in `packages/ai`; OpenTUI's own source; Code Mode's runner; a real Desktop window, a real model and a real TUI, which are `UNEXECUTED`. [drift.md](../../plugin-dev/guide/drift.md#what-was-not-checked) lists the rest.
