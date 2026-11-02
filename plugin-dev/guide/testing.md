# Demonstrating a plugin

How to show a plugin really works, without touching your own OpenCode. This follows the repository's [build, demonstrate, deliver](../../AGENTS.md#how-work-gets-done): the point is evidence from the real entry point, not a test count.

## The rule: never test on the live setup

Your own OpenCode holds real sessions, and `opencode plugin add` changes the global config of the service Desktop uses, at once. Test in a private instance instead. It works because OpenCode reads every global path from the XDG variables (`packages/util/src/global-roots.ts:5`), on Windows too.

## The smoke test

```bash
python -I tools/smoke_plugin.py
```

It wipes `.dev/`, which git ignores, writes a private config that loads this folder, starts `opencode serve` on a free local port with a one-time password, checks the plugin through the server's real API, and stops the server. Set what it checks in [tools/smoke.json](../../tools/smoke.json).

| It checks | Through | Shows |
|---|---|---|
| The plugin is listed and `active` | `GET /api/plugin` | The server part loaded, and `setup` finished |
| Which parts were found | `features` on the same row | `exports` resolve as you meant |
| The GUI bundle is served, if built | `GET /api/plugin/gui` | Desktop could fetch it, not that a window runs it |
| Commands you name | `GET /api/command` | The command transform applied |
| RPC methods you name | `POST /api/rpc/{id}/{method}` | Your server code really runs, with no model and no account |

When the plugin fails, the row's `error` holds the stack, and `.dev/server.log` has the rest.

**What it does not cover:** a real model calling your tools, the TUI, Desktop windows, and the installed package. Say so in any report, and label those validations `UNEXECUTED` until they have run.

**Keep a way to reach your code without a model.** An RPC method is the cheapest: the starter's `ping` proves the server part runs, that `ctx.storage` works, and that its tool is registered.

**To test a question about OpenCode itself,** copy one of the [probes](../../studies/2026-11-03/README.md): each loads a throwaway plugin in a private instance, and prints what happened. That is how the **Observed** lines here were made, and [results.md](../../studies/2026-11-03/results.md) has their output.

## The API by hand

Against a server you started with `OPENCODE_PASSWORD` set, `opencode api --server <url> <operation>` calls any operation by its OpenAPI id (`packages/protocol/src/groups/plugin.ts:9`). Examples: `plugin.list`, `command.list`, `plugin.gui --param id=<id>`, `rpc.call`. **Observed:** without the password the CLI stops with "requires a password; set OPENCODE_PASSWORD".

## What to run for each part

| Part | Cheapest real demonstration | Status in this template |
|---|---|---|
| Server | `tools/smoke_plugin.py` | **Observed:** 5 of 5 pass on CLI 2.2.1 and 2.2.5, with the bundle built ([results](../../studies/2026-11-03/results.md)) |
| Tool execution | A session with a real model, or a deterministic fake provider ([working rule 3](../../AGENTS.md#working-rules)) | `UNEXECUTED` |
| TUI | `opencode --standalone` in the same XDG environment, and look | `UNEXECUTED`; the starter has no TUI part |
| GUI build | `npm run build:gui`, then check its `require` calls are all [provided modules](gui.md) | **Observed:** builds, and requires only `@opencode/plugin/gui` and `@opencode/plugin/rpc` |
| GUI in a window | Add the plugin to the global config of a Desktop you are willing to change, and run the command from the palette | `UNEXECUTED`: it changes a live setup, so it needs the owner's word |
| Published package | `npm pack`, install the tarball's contents in a clean folder, and point the smoke test's config at it | `UNEXECUTED` |

## Verifying a port from V1

The official list, restated from `services/www/src/docs/content/build/plugins/migrate-v1.mdx:364`: the id and source are in the plugin list; every hook, transform, tool, command and subscription has been exercised; cleanup works on reload or removal; options and stored state work in a clean project; and for a package, the installed copy passes.

## Typecheck

`npm run typecheck`. **Observed:** it catches a missing `events` key on an RPC definition, which the runtime reports only as a failed plugin or a line in the server log ([drift.md](drift.md)). It also flags a JSON Schema output, which types as `unknown`: cast it, or use a Standard Schema such as Zod, as [src/gui.tsx](../../src/gui.tsx) says.
