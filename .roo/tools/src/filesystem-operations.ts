import { parametersSchema as z, defineCustomTool } from "@roo-code/types";
import * as fs from "fs";
import * as path from "path";

// Directory Creator Tool
export const filesystemDirectoryCreator = defineCustomTool({
  name: "filesystem_directory_creator",
  description: "Create a directory and ensure parent directories exist",
  parameters: z.object({
    dirPath: z.string().describe("Path to the directory to create"),
  }),
  async execute({ dirPath }) {
    try {
      if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
      }

      return JSON.stringify({
        success: true,
        dirPath,
        message: `Directory created: ${dirPath}`
      });
    } catch (error) {
      return `Error creating directory: ${error instanceof Error ? error.message : String(error)}`;
    }
  }
});

// Template Copier Tool
export const filesystemTemplateCopier = defineCustomTool({
  name: "filesystem_template_copier",
  description: "Copy a template file to a destination and optionally fill placeholders",
  parameters: z.object({
    templatePath: z.string().describe("Path to the template file"),
    destinationPath: z.string().describe("Path where to copy the template"),
    placeholders: z.record(z.string(), z.string()).optional().describe("Key-value pairs for placeholder replacement"),
  }),
  async execute({ templatePath, destinationPath, placeholders = {} }) {
    try {
      if (!fs.existsSync(templatePath)) {
        return `Error: Template file not found: ${templatePath}`;
      }

      // Ensure destination directory exists
      const destDir = path.dirname(destinationPath);
      if (!fs.existsSync(destDir)) {
        fs.mkdirSync(destDir, { recursive: true });
      }

      let content = fs.readFileSync(templatePath, 'utf-8');

      // Replace placeholders
      for (const [key, value] of Object.entries(placeholders)) {
        content = content.replace(new RegExp(`\\$\\{${key}\\}`, 'g'), String(value));
      }

      fs.writeFileSync(destinationPath, content, 'utf-8');

      return JSON.stringify({
        success: true,
        templatePath,
        destinationPath,
        placeholders: Object.keys(placeholders),
        message: `Template copied and processed: ${destinationPath}`
      });
    } catch (error) {
      return `Error copying template: ${error instanceof Error ? error.message : String(error)}`;
    }
  }
});

export default {
  filesystemDirectoryCreator,
  filesystemTemplateCopier
};