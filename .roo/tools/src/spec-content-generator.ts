import { parametersSchema as z, defineCustomTool } from "@roo-code/types";

export default defineCustomTool({
  name: "spec_content_generator",
  description: "Generate basic specification content from a feature description",
  parameters: z.object({
    featureDescription: z.string().describe("Natural language feature description"),
    branchName: z.string().describe("Feature branch name"),
    templatePath: z.string().describe("Path to spec template"),
  }),
  async execute({ featureDescription, branchName, templatePath }) {
    try {
      // Read template
      const fs = require('fs');
      if (!fs.existsSync(templatePath)) {
        return `Error: Template not found: ${templatePath}`;
      }

      let content = fs.readFileSync(templatePath, 'utf-8');

      // Extract feature number and name
      const match = branchName.match(/^(\d{3})-(.+)$/);
      if (!match) {
        return `Error: Invalid branch name format: ${branchName}`;
      }

      const featureNum = match[1];
      const featureName = match[2].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

      // Basic content generation (simplified for production readiness)
      const placeholders = {
        FEATURE_NAME: featureName,
        FEATURE_NUMBER: featureNum,
        BRANCH_NAME: branchName,
        FEATURE_DESCRIPTION: featureDescription,
        CREATED_DATE: new Date().toISOString().split('T')[0],
      };

      // Replace placeholders
      for (const [key, value] of Object.entries(placeholders)) {
        content = content.replace(new RegExp(`\\$\\{${key}\\}`, 'g'), value);
      }

      // Generate basic sections based on description
      const userScenarios = generateUserScenarios(featureDescription);
      const requirements = generateRequirements(featureDescription);

      content = content.replace('${USER_SCENARIOS}', userScenarios);
      content = content.replace('${FUNCTIONAL_REQUIREMENTS}', requirements);

      return JSON.stringify({
        success: true,
        content,
        placeholders,
        message: `Spec content generated for ${branchName}`
      });
    } catch (error) {
      return `Error generating spec content: ${error instanceof Error ? error.message : String(error)}`;
    }
  }
});

// Helper functions for content generation
function generateUserScenarios(description: string): string {
  // Simple scenario generation - in production this would be more sophisticated
  return `## User Scenarios

### Primary User Flow
1. User accesses the ${description.toLowerCase()}
2. System processes the request
3. User receives expected outcome

### Edge Cases
- Error conditions
- Invalid inputs
- System constraints`;
}

function generateRequirements(description: string): string {
  // Simple requirements generation
  return `## Functional Requirements

### FR-001: Core Functionality
The system shall ${description.toLowerCase()}.

### FR-002: User Interface
The system shall provide appropriate user interface elements.

### FR-003: Error Handling
The system shall handle errors gracefully and provide meaningful feedback.

## Success Criteria

- Users can complete the primary workflow successfully
- System responds within acceptable performance limits
- Error messages are clear and actionable`;
}