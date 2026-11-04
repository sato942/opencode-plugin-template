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
| GUI in a window | The official workflow, in a Desktop you are willing to change: [Desktop windows](#desktop-windows) | `UNEXECUTED`: it changes a live setup, so it needs the owner's word |
| Published package | `npm pack`, install the tarball's contents in a clean folder, and point the smoke test's config at it | `UNEXECUTED` |

## Desktop windows

**The official workflow** (`services/www/src/docs/content/build/plugins/gui/index.mdx:214-230`): list the plugin's local directory in `plugins` in `opencode.json(c)`, run `vite build --watch`, and each rebuild reloads the GUI part in every window and in the main process. The server entry does not restart.

That config is the global config of the service Desktop uses, and Desktop lists GUI parts only from its own service ([gui.md](gui.md)). So the workflow changes a live setup. Run it where that is acceptable:

| Where | What keeps it apart | What to set first |
|---|---|---|
| A throwaway virtual machine, such as Windows Sandbox | Its own user, files and network, so its own service port | Install Desktop inside it and copy the plugin in |
| Another user account on the same computer | Its own home folder, app data and per-user install (inference: Desktop's paths and the service's XDG defaults are all per user) | The service port. It is fixed, and one computer has one of each port, so the second account's service fails while the first one runs. In that account, run `opencode service set port <free port>` before Desktop starts |
| Your own Desktop | Nothing | The owner's word. Remove the plugin from `plugins` afterwards |

Give each a model the plugin can call: a deterministic fake provider keeps the trial free and repeatable.

**The port, from source at the pin.** The managed service listens on a fixed port per channel: `0xC0DE` for `latest`, which Windows moves to `0x70DE`, 28894 (`packages/cli/src/services/service-config.ts:46-60`). A second service on that port stops with "Managed service port … is already in use" (`packages/cli/src/server-process.ts:181-182`). `opencode service set port <port>` stores the port in `<XDG_CONFIG_HOME>/opencode/service.json` (`service-config.ts:116-130`). **Observed** 5 Nov 2026, CLI 2.2.5: that file, `{"port": N}`, was the only one written.

**What does not keep it apart: a second copy of the installed Desktop.** Desktop has a test root, `OPENCODE_DESKTOP_TEST_ROOT`, which moves its user data, session data and XDG folders under one folder (`packages/desktop/src/main/lifecycle/configure.ts:66-86`). In an installed build that is not enough. **Observed** 5 Nov 2026, Desktop 2.2.5 on Windows 11:

1. Desktop deletes `XDG_STATE_HOME` after the test root sets it, unless a login shell defines it, and on Windows it reads no login shell (`packages/desktop/src/main/lifecycle/environment.ts:28-33`). The service registration then falls back to `~/.local/state/opencode/service.json`, so the copy found the same user's running service and connected to it, with that service's password. That service then opened the home folder as a location: it subscribed watchers and loaded its plugins there.
2. With the home folder moved as well (`USERPROFILE` and `HOME`), the copy started a service of its own, which stopped on the port above until a port was set for it.
3. With the port set, the window opened with no renderer process and stayed blank. The cause was not found.

Any such copy also meets two more things. An installed build always runs its updater, which checks at start and every 10 minutes and can download and stage an update (read from the installed 2.2.5 bundle). **Observed:** Chromium's `--proxy-server` pointed at a proxy that refuses outside hosts stopped the check with `net::ERR_TUNNEL_CONNECTION_FAILED`. And it registers itself as the `opencode://` handler (`environment.ts:46-47`). Desktop's isolated server mode, which avoids the shared service, exists only for an unpackaged Desktop run from OpenCode's source (`packages/desktop/script/dev.ts:19`, `packages/desktop/src/main/service/background-service.ts:42,46`). That is the workflow for working on OpenCode itself, not on a plugin.

**Stop only what you started.** On Windows, walk the process tree yourself. `taskkill /T` follows parent process ids, and Windows reuses ids, so a process whose parent exited long ago can count as the child of a new one (inference, not reproduced). `stop_tree` in [tools/smoke_plugin.py](../../tools/smoke_plugin.py) counts a child only if it started after its parent; copy it into any probe that stops a server. The dated probes in `studies/` still use `taskkill /T`.

## Verifying a port from V1

The official list, restated from `services/www/src/docs/content/build/plugins/migrate-v1.mdx:364`: the id and source are in the plugin list; every hook, transform, tool, command and subscription has been exercised; cleanup works on reload or removal; options and stored state work in a clean project; and for a package, the installed copy passes.

## Typecheck

`npm run typecheck`. **Observed:** it catches a missing `events` key on an RPC definition, which the runtime reports only as a failed plugin or a line in the server log ([drift.md](drift.md)). It also flags a JSON Schema output, which types as `unknown`: cast it, or use a Standard Schema such as Zod, as [src/gui.tsx](../../src/gui.tsx) says.
