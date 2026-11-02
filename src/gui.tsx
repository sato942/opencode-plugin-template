import { Command, Plugin } from "@opencode/plugin/gui"
import { Starter } from "./rpc.js"

// The GUI part: it runs in every OpenCode Desktop window, and only once built into dist/gui-experimental.cjs by
// `npm run build:gui`. It declares no id; the host gives it the server part's. plugin-dev/guide/gui.md has the rest.
export default Plugin.define({
  setup(ctx) {
    ctx.add(Command, {
      id: "ping",
      title: "Starter plugin: ping the server part",
      run: async () => {
        // A JSON Schema output is `unknown` to TypeScript; a Standard Schema such as Zod would infer this type.
        const result = (await ctx.client.rpc(Starter).ping({ name: "Desktop" })) as { text: string; calls: number }
        ctx.toast.show({ title: `${result.text} (call ${result.calls})` })
      },
    })
  },
})
