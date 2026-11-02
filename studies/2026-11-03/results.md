# What was run on real OpenCode

**Date:** 3 November 2026, on Windows 11. **Versions:** OpenCode CLI 2.2.1 and 2.2.5, with `@opencode/plugin` 2.2.5 for types. **Environment:** each run used a private instance, with its own XDG folders, a one-time password and a free local port, and never touched anyone's real OpenCode.

These are this project's own functional runs, through the server's real API. They show what the server does. They do not show a Desktop window, a TUI session or a model.

## How to repeat them

```bash
python -I tools/smoke_plugin.py --opencode PATH
```

```bash
python -I studies/2026-11-03/probes/rpc_probe.py PATH
```

```bash
python -I studies/2026-11-03/probes/rpc_probe.py PATH --no-events
```

```bash
python -I studies/2026-11-03/probes/rpc_probe.py PATH --no-events --no-await
```

```bash
python -I studies/2026-11-03/probes/rebuild_probe.py PATH
```

## Results

Both versions gave the same results. The output below is from 2.2.5, with the port number removed.

### The starter, with its GUI bundle built

```text
OpenCode opencode v2.2.5, private server, config in .dev/
PASS  the plugin is listed: opencode-plugin-starter
PASS  its state is active
      parts found: gui, rpc, server
PASS  the server serves its GUI bundle: 756 bytes; whether a Desktop window runs it is not checked here
PASS  command starter-greet is listed
PASS  rpc ping: {"text": "pong smoke", "calls": 1, "tool": true}
5 of 5 checks passed. Not covered: a real model calling the tools, the TUI and Desktop.
```

On 2.2.1, before the bundle was built and with no `node_modules`, the same starter passed 4 of 4, with `parts found: rpc, server`. So `./gui-experimental` declared with no file is simply no GUI part, and the host provides `@opencode/plugin`.

Also on 3 November 2026: `npm run typecheck` exited 0 against SDK 2.2.5, and `npm run build:gui` wrote a 756-byte bundle whose only `require` calls are `@opencode/plugin/gui` and `@opencode/plugin/rpc`.

### An RPC contract leaving out `input` or `output`

The docs say this is allowed.

```text
OpenCode opencode v2.2.5 | events present | register awaited
plugin state: active
full      handler ran=True  HTTP 200 {"output": {"text": "ok"}}
noInput   handler ran=False  HTTP 500 {"_tag":"RpcInternalError","type":"rpc.internal","message":"RPC call failed"}
noOutput  handler ran=True  HTTP 500 {"_tag":"RpcInternalError","type":"rpc.internal","message":"RPC call failed"}
neither   handler ran=False  HTTP 500 {"_tag":"RpcInternalError","type":"rpc.internal","message":"RPC call failed"}
```

### A contract with no `events`

```text
OpenCode opencode v2.2.5 | events left out | register awaited
plugin state: failed TypeError: Object.entries requires that input parameter not be null or undefined
```

Not awaited, the failure is hidden. The plugin reads as `active`, and its methods behave as in the table above, but the server logs it:

```text
OpenCode opencode v2.2.5 | events left out | register not awaited
plugin state: active
server log: unhandled rejection: "TypeError: Object.entries requires that input parameter not be null or undefined" role=cli
```

### A GUI rebuild

The docs say the server entry does not restart. The second plugin is ordered after the first, and is unchanged.

```text
OpenCode opencode v2.2.5
after start:                 setup runs: plugin 1, later plugin 1
after only the bundle changed: setup runs: plugin 2, later plugin 2 | GUI revision changed: True
after the server file changed (control): setup runs: plugin 3, later plugin 3
```

## Not run

`UNEXECUTED`, with why:

- **The GUI bundle in a real Desktop window.** It needs a plugin in a real global config, and the live setup was left alone. An isolated second Desktop might do it; it has not been tried.
- **A real model calling `starter_greet`.** It needs a provider and an account.
- **A TUI part.** The starter has none, and a TUI needs a terminal to look at.
- **The published package path:** `npm pack`, `plugin add`, and an install from a registry or Git.
