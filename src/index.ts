import { Plugin } from "@opencode/plugin"
import { Starter } from "./rpc.js"

// The server part. It runs in the OpenCode server, so it works under the terminal UI and under Desktop alike.
// tools/smoke_plugin.py loads it in an isolated OpenCode and checks each thing it registers.
export default Plugin.define({
  id: "opencode-plugin-starter",
  async setup(ctx) {
    await ctx.tool.transform((editor) => {
      editor.add({
        name: "starter_greet",
        description: "Greet someone by name. A starter tool: replace it with your own.",
        input: {
          type: "object",
          properties: { name: { type: "string" } },
          required: ["name"],
          additionalProperties: false,
        },
        // Without this, the model reaches the tool only through Code Mode's `execute` tool while Code Mode is on.
        options: { codemode: false },
        async execute(input) {
          return { content: `Hello ${(input as { name: string }).name}!` }
        },
      })
    })

    await ctx.command.transform((editor) => {
      editor.add({
        name: "starter-greet",
        description: "Ask the model to greet someone with the starter tool",
        execute: async (input) => {
          await ctx.session.prompt({
            ...input.prompt,
            sessionID: input.sessionID,
            text: `Use the starter_greet tool to greet ${input.prompt.text || "the user"}.`,
            delivery: input.delivery,
          })
        },
      })
    })

    await ctx.rpc.register(Starter, {
      ping: async (input) => {
        const calls = ((await ctx.storage.get("calls")) as number | undefined) ?? 0
        await ctx.storage.set("calls", calls + 1)
        const tools = await ctx.tool.list()
        return {
          text: `pong ${(input as { name: string }).name}`,
          calls: calls + 1,
          tool: tools.some((tool) => tool.id === "starter_greet"),
        }
      },
    })
  },
})
