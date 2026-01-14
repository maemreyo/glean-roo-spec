import { parametersSchema as z, defineCustomTool } from "@roo-code/types";

export default defineCustomTool({
  name: "branch_name_generator",
  description: "Generate a short branch name from feature description",
  parameters: z.object({
    featureDescription: z.string().describe("Feature description to generate name from"),
    customShortName: z.string().optional().describe("Custom short name if provided"),
  }),
  async execute({ featureDescription, customShortName }) {
    try {
      if (customShortName && customShortName.trim()) {
        // Use provided short name, just clean it up
        return cleanBranchName(customShortName.trim());
      }

      // Generate from description with smart filtering
      return generateBranchName(featureDescription);
    } catch (error) {
      return `Error generating branch name: ${error instanceof Error ? error.message : String(error)}`;
    }
  }
});

// Helper functions from Python feature_utils.py
function cleanBranchName(name: string): string {
  // Convert to lowercase, replace spaces and special chars with hyphens
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') // Remove leading/trailing hyphens
    .substring(0, 50); // Limit length
}

function generateBranchName(description: string): string {
  // Extract meaningful keywords from description
  const words = description
    .toLowerCase()
    .replace(/[^\w\s]/g, ' ') // Replace punctuation with spaces
    .split(/\s+/)
    .filter(word => word.length > 2) // Filter out short words
    .filter(word => !isStopWord(word)) // Filter stop words
    .slice(0, 4); // Limit to 4 words

  if (words.length === 0) {
    return 'feature'; // Fallback
  }

  // Try action-noun pattern first
  const actionNoun = findActionNounPattern(words);
  if (actionNoun) {
    return actionNoun;
  }

  // Join remaining words
  return words.join('-');
}

function isStopWord(word: string): boolean {
  const stopWords = new Set([
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'can', 'i', 'you', 'he', 'she',
    'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'this', 'that',
    'these', 'those', 'what', 'when', 'where', 'why', 'how', 'all', 'any',
    'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
    'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very'
  ]);
  return stopWords.has(word);
}

function findActionNounPattern(words: string[]): string | null {
  // Look for action-noun patterns
  const actions = ['add', 'create', 'implement', 'fix', 'update', 'remove', 'delete', 'build', 'setup', 'configure'];
  const nouns = ['user', 'auth', 'login', 'dashboard', 'api', 'database', 'component', 'page', 'system', 'feature'];

  for (let i = 0; i < words.length - 1; i++) {
    if (actions.includes(words[i]) && nouns.some(noun => words[i + 1].includes(noun) || noun.includes(words[i + 1]))) {
      return `${words[i]}-${words[i + 1]}`;
    }
  }

  // If no perfect match, try first action + first noun
  const action = words.find(w => actions.includes(w));
  const noun = words.find(w => nouns.some(n => w.includes(n) || n.includes(w)));

  if (action && noun) {
    return `${action}-${noun}`;
  }

  return null;
}