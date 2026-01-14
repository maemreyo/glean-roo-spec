import { parametersSchema as z, defineCustomTool } from "@roo-code/types";

export default defineCustomTool({
  name: "tool_template",
  description: "Template for creating new Roo Tools",
  parameters: z.object({
    exampleParam: z.string().describe("An example parameter"),
  }),
  async execute({ exampleParam }) {
    return `Template tool executed with: ${exampleParam}`;
  }
});