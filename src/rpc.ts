import { Rpc } from "@opencode/plugin/rpc"

// The contract the server part implements and the other parts and clients call. It imports no implementation, so a
// client can import it through the package's ./rpc export without loading the plugin.
export const Starter = Rpc.define({
  id: "opencode-plugin-starter",
  methods: {
    ping: {
      input: {
        type: "object",
        properties: { name: { type: "string" } },
        required: ["name"],
        additionalProperties: false,
      },
      output: {
        type: "object",
        properties: { text: { type: "string" }, calls: { type: "number" }, tool: { type: "boolean" } },
        required: ["text", "calls", "tool"],
        additionalProperties: false,
      },
    },
  },
  // Required even when empty: without it, `await ctx.rpc.register` throws and the plugin fails (plugin-dev/guide/drift.md).
  events: {},
})
