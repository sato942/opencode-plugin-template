# Feature matrix

Every feature on every target. Update this file in the same change as any work that adds, changes or removes a feature on a target ([developer guide](AGENTS.md#working-rules), working rule 9).

## Marks

| Mark | Meaning |
|---|---|
| — | Not started |
| P | Prototype only; not accepted |
| ✓ | Done: the feature's validations pass on this target, with recorded evidence |
| ✗ | Not possible on this target; the note says why |
| n/a | The feature has no part on this target, once its design settles that |

- A cell becomes ✓ only when the validations in the feature's spec files that apply to that target pass, with recorded evidence.
- Reaching a service on another target is access, not parity: it never makes a cell ✓.
- Every mark other than "—" links its evidence or note.
- A new feature gets a row in the change that records it, starting with its ID as a link: `| [F001](features/F001-short-name.md) The feature's name | — | — | — |`

## Targets

A target is a surface a person uses the plugin on, at a named OpenCode release. The columns below are the two surfaces OpenCode has, plus what runs with no surface at all. _Which of them this plugin serves: not set yet, the owner says in the first session._ Delete a column the plugin does not serve, and add one for a further release it must work on.

- **Terminal UI** is `opencode`, with a server part and optionally a TUI part.
- **Desktop** is OpenCode Desktop, with a server part and optionally a GUI part. It never renders a TUI part.
- **Headless** is a client or script on the server's API, or a model's tool call in a run nobody watches. It has server and RPC parts only.

A smoke test run shows a server part loads and runs. It does not make a Terminal UI or Desktop cell ✓ ([testing.md](plugin-dev/guide/testing.md)).

## Features

| Feature | Terminal UI | Desktop | Headless |
|---|---|---|---|
