# Legal flags

License and terms flags on sources and candidates. Each goes to a legal review before the project ships ([AGENTS.md](AGENTS.md#working-rules) working rule 5). Add a new flag here when a source or dependency carries one, and say so even when a source is only read and not adopted.

- **OpenCode's docs and source are copied into this repository.** [plugin-dev/upstream/](plugin-dev/upstream/) is a verbatim copy of parts of [anomalyco/opencode](https://github.com/anomalyco/opencode), which is under the MIT license. The license goes with the copy, in [plugin-dev/upstream/LICENSE](plugin-dev/upstream/LICENSE), and must stay there: `tools/sync_upstream.py` copies it each time. Only what [plugin-dev/MANIFEST.json](plugin-dev/MANIFEST.json) lists is copied. Not reviewed: whether any file in the copy carries terms of its own beyond that license.
- **The OpenCode name.** Using it in a package name, as the docs' own `opencode-acme-plugin` example does, has not been reviewed against any trademark policy. Check before publishing.
