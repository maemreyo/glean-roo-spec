# Feature Specification: Story Builder Studio

**Feature Branch**: `013-story-builder-studio`  
**Created**: 2026-01-06  
**Status**: Draft  
**Input**: User description: "1 --design" - Idea #1 from brainstorm session specs-012-standalone-story-2026-01-06-0853.md

## Feature Description

Transform the manual URL encoding workflow into an intuitive, Instagram-style story creation experience. The Story Builder Studio provides a visual drag-and-drop interface at `/create-story` that allows users to build interactive stories without any technical knowledge. Users can visually assemble slides with rich content, see real-time previews, and generate shareable URLs with a single click.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visual Story Creation with Drag-and-Drop (Priority: P1)

A content creator wants to build an interactive story without writing code or manually encoding URLs. They visit `/create-story` and see an intuitive editor where they can add slides by clicking buttons, rearrange them by dragging, and edit content in place. As they make changes, a live mobile preview (9:16 aspect ratio) updates in real-time to show exactly what their story will look like.

**Why this priority**: This is the core value proposition - eliminating technical barriers to story creation. Without this, users must manually construct JSON and encode URLs, which is the primary pain point being solved.

**Independent Test**: Can be fully tested by creating a 3-slide story (text, image, teleprompter), reordering slides via drag-and-drop, editing slide content, and verifying the mobile preview updates correctly. Delivers a complete story creation workflow.

**Acceptance Scenarios**:

1. **Given** a user is on the Story Builder page, **When** they click the "Add Text Slide" button, **Then** a new text slide is added to the end of the slide list and appears in the mobile preview
2. **Given** a user has 3 slides in their story, **When** they drag slide 2 and drop it after slide 3, **Then** the slide order updates in both the editor and the preview
3. **Given** a user is editing a text slide, **When** they type in the content textarea, **Then** the mobile preview updates within 100ms to show the new text
4. **Given** a user has added 10 slides, **When** they click the "Add Image Slide" button, **Then** a new image slide is added and the slide counter shows "11 slides"
5. **Given** a user wants to remove a slide, **When** they click the delete button on a slide card, **Then** that slide is removed and the slide list reorders

---

### User Story 2 - One-Click URL Generation with Size Tracking (Priority: P2)

After building their story, a user needs to share it with others. They click the "Generate Shareable Link" button, which instantly encodes their story into a URL and copies it to their clipboard. The system shows the current URL size relative to the 32KB browser limit, warning them if they're approaching or exceeding it.

**Why this priority**: URL generation is essential for sharing, and size tracking prevents the critical failure of URLs exceeding browser limits. This builds on P1 by making the created story shareable.

**Independent Test**: Can be tested by creating a story, clicking "Generate Link", verifying the URL is copied to clipboard, and checking the size indicator accurately reflects URL length vs 32KB limit.

**Acceptance Scenarios**:

1. **Given** a user has built a story with 5 slides, **When** they click "Generate Shareable Link", **Then** the encoded URL is copied to clipboard and a success toast appears
2. **Given** a user's story URL is 25KB, **When** they view the URL size indicator, **Then** it shows "25KB / 32KB" with a yellow warning color
3. **Given** a user's story URL exceeds 32KB, **When** they attempt to generate a link, **Then** the system shows an error message: "Story too large - reduce slides or content to fit URL limit"
4. **Given** a user has just generated a URL, **When** they add more content that would exceed 32KB, **Then** the size indicator immediately turns red and shows "Warning: URL will exceed limit"
5. **Given** a user wants to share their story, **When** they paste the copied URL into a new browser tab, **Then** the story loads and displays correctly

---

### User Story 3 - Template Library for Quick Story Creation (Priority: P3)

A user wants to create a story but doesn't want to start from scratch. They browse the template library and select a "Sales Pitch" template, which pre-populates the editor with 5 slides (hook, problem, solution, social proof, call-to-action). They can then customize the content to match their needs.

**Why this priority**: Templates accelerate story creation and provide best-practice starting points. This enhances P1 by reducing time-to-value for users.

**Independent Test**: Can be tested by selecting a template, verifying it populates slides with pre-defined content, and confirming the user can edit those slides normally.

**Acceptance Scenarios**:

1. **Given** a user is on the Story Builder page, **When** they click the "Templates" button, **Then** a template library modal opens showing available templates
2. **Given** the template library is open, **When** they click "Use Template" on the "Sales Pitch" template, **Then** the modal closes and 5 pre-configured slides appear in the editor
3. **Given** a user has loaded a template, **When** they edit the content of any slide, **Then** their changes persist and the preview updates
4. **Given** a user has already built a custom story, **When** they select a template, **Then** the system asks "Replace current story? (Unsaved changes will be lost)"
5. **Given** a user selects the "Tutorial" template, **When** the template loads, **Then** it includes 4 slides: introduction, step 1, step 2, conclusion with teleprompter scripts

---

### User Story 4 - Rich Content Types (Image, Poll, Chart, Teleprompter) (Priority: P4)

A user wants to create engaging stories beyond just text. They add an image slide with an uploaded photo, a poll slide to collect feedback, a chart slide to visualize data, and a teleprompter slide for script-assisted recording. Each content type has an appropriate editor interface.

**Why this priority**: Rich content types make stories more engaging and versatile. This extends P1 with advanced slide types.

**Independent Test**: Can be tested by creating one of each slide type, filling in their specific content fields, and verifying each renders correctly in the preview.

**Acceptance Scenarios**:

1. **Given** a user adds an image slide, **When** they upload a JPG file, **Then** the image appears in the slide preview and the file size is checked (<5MB)
2. **Given** a user adds a poll slide, **When** they enter 4 poll options, **Then** the preview shows all 4 options as tappable buttons
3. **Given** a user adds a chart slide, **When** they select "bar chart" and enter data values, **Then** the preview displays a bar chart with those values
4. **Given** a user adds a teleprompter slide, **When** they enter a 500-word script, **Then** the teleprompter script is saved and the preview shows a "Record" button
5. **Given** a user uploads an invalid file type (e.g., .exe), **When** they try to add it to an image slide, **Then** the system shows an error: "Please upload JPG, PNG, or WebP images only"

---

### User Story 5 - Auto-Save and Draft Management (Priority: P5)

A user is building a complex story over multiple sessions. The system automatically saves their work to localStorage every 30 seconds. If they close the browser and return later, they see a "Restore Draft?" prompt that loads their previous work.

**Why this priority**: Auto-save prevents data loss and enables multi-session story creation. This enhances all user stories with persistence.

**Independent Test**: Can be tested by creating a story, waiting 31 seconds, closing the tab, reopening `/create-story`, and confirming the draft restoration prompt appears with all content intact.

**Acceptance Scenarios**:

1. **Given** a user has been editing a story for 31 seconds, **When** they refresh the page, **Then** a "Restore Draft?" modal appears with "Last saved 30 seconds ago"
2. **Given** a user sees the draft restoration prompt, **When** they click "Restore", **Then** their previous story content loads into the editor
3. **Given** a user clicks "Discard Draft", **When** the action completes, **Then** the editor starts fresh and localStorage draft is cleared
4. **Given** a user's localStorage is full, **When** auto-save attempts to run, **Then** the system shows a warning: "Auto-save failed - storage full. Please clear browser data."
5. **Given** a user manually clicks "Save Draft", **When** the save completes, **Then** a success toast appears and the last saved timestamp updates

---

### Edge Cases

- What happens when a user tries to drag a slide to an invalid position (e.g., before the first slide)?
- How does the system handle browser clipboard API failures (e.g., user denies permission)?
- What happens when a user uploads an image that exceeds the 5MB file size limit?
- How does the drag-and-drop behave on mobile devices with touch screens?
- What happens when localStorage is unavailable (e.g., private browsing mode)?
- How does the system handle concurrent edits if multiple tabs have the same story open?
- What happens when a generated URL exceeds 32KB (e.g., user adds too many slides)?
- How does the preview handle very long text content that would overflow the slide?
- What happens when a user's network is slow and image uploads take too long?
- How does the system handle malformed template data from the template library?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a visual story editor interface at `/create-story` route
- **FR-002**: System MUST allow users to add slides of types: text, teleprompter, image, poll, and chart
- **FR-003**: System MUST support drag-and-drop reordering of slides in the story editor
- **FR-004**: System MUST provide real-time mobile preview (9:16 aspect ratio) alongside the editor
- **FR-005**: System MUST update the mobile preview within 100ms of any content change
- **FR-006**: System MUST generate shareable URLs using the existing `encodeStoryForUrl()` function from `lib/story/utils/urlEncoder.ts`
- **FR-007**: System MUST display current URL size relative to 32KB browser limit with visual indicators (green <20KB, yellow 20-30KB, red >30KB)
- **FR-008**: System MUST prevent URL generation if the encoded URL would exceed 32KB
- **FR-009**: System MUST provide a "Copy to Clipboard" button that copies the generated URL
- **FR-010**: System MUST show a success toast notification when URL is copied to clipboard
- **FR-011**: System MUST provide a template library with at least 3 pre-built templates: "Sales Pitch", "Tutorial", "Announcement"
- **FR-012**: System MUST validate image uploads to be JPG, PNG, or WebP format with maximum 5MB file size
- **FR-013**: System MUST auto-save story drafts to localStorage every 30 seconds
- **FR-014**: System MUST prompt users to restore previous drafts on page load if a draft exists
- **FR-015**: System MUST support slide deletion with confirmation for slides containing content
- **FR-016**: System MUST maintain slide order state during drag-and-drop operations
- **FR-017**: System MUST use shadcn/ui components for all UI elements
- **FR-018**: System MUST use Framer Motion for drag-and-drop animations
- **FR-019**: System MUST extend the existing `useStoryStore` from `lib/stores/useStoryStore.ts` for state management
- **FR-020**: System MUST support touch-based drag-and-drop on mobile devices

### Key Entities

- **Story**: A collection of slides with metadata (title, description, created date, last modified)
- **Slide**: An individual story component with type (text, teleprompter, image, poll, chart), order position, and type-specific content
- **Template**: A pre-configured story structure with slides and placeholder content that users can customize
- **Draft**: Auto-saved story state stored in localStorage with timestamp and content hash
- **URLSizeTracker**: Real-time calculator that monitors encoded URL length against 32KB limit

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a 5-slide story with mixed content types in under 3 minutes
- **SC-002**: 95% of users successfully generate a shareable URL on their first attempt
- **SC-003**: Mobile preview updates within 100ms for all content changes
- **SC-004**: URL size indicator accurately predicts final URL length within 5% margin
- **SC-005**: Zero data loss occurs due to missing auto-save (100% draft recovery rate)
- **SC-006**: 90% of users rate the drag-and-drop interface as "intuitive" or "very intuitive" in user testing
- **SC-007**: Template selection reduces story creation time by 50% compared to starting from scratch
- **SC-008**: System handles 50+ slides without performance degradation (drag-and-drop remains smooth)

## Assumptions

1. Users have modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+) that support drag-and-drop API
2. Users have JavaScript enabled in their browsers
3. localStorage is available (not in private browsing mode for draft storage)
4. The existing `encodeStoryForUrl()` function in `lib/story/utils/urlEncoder.ts` works correctly for story encoding
5. The existing `useStoryStore` in `lib/stores/useStoryStore.ts` can be extended without breaking changes
6. Users have basic familiarity with drag-and-drop interfaces (similar to other web tools)
7. shadcn/ui and Framer Motion are already installed in the project
8. Image uploads are client-side only (no server-side storage required for MVP)
9. The 32KB URL limit is based on browser URL length limitations
10. Template data is stored as JSON files in the project (no database required)

## Out of Scope

- User authentication or accounts (anonymous story creation)
- Backend storage or database integration
- Story analytics or view tracking
- Social media sharing integrations (e.g., direct Facebook/Twitter sharing)
- Video slide type (images only for MVP)
- Real-time collaboration between multiple users
- Story versioning or history
- Export to PDF or other formats
- Advanced image editing (crop, filters, etc.)
- Custom template creation by users
- Story search or discovery
- Monetization or premium features

## Dependencies

### Existing Code
- `lib/story/utils/urlEncoder.ts` - encodeStoryForUrl() function
- `lib/stores/useStoryStore.ts` - Zustand store for story state
- `lib/story/types.ts` - TypeScript type definitions for stories
- `components/story/StoryViewer.tsx` - Existing story viewer component (may be reused for preview)

### External Libraries (to be added if not present)
- `@dnd-kit/core` and `@dnd-kit/sortable` - Drag-and-drop functionality
- `framer-motion` - Animations (may already be installed per project guidelines)
- `react-dropzone` - File upload handling

### UI Components
- shadcn/ui: Button, Card, Input, Textarea, Select, Dialog, Toast, Slider
- Existing project components may be reused where applicable

## Technical Notes

- The story builder will be a client-side only feature (Next.js client component)
- State management will use Zustand via the extended `useStoryStore`
- Drag-and-drop will use @dnd-kit for better accessibility and mobile support than react-beautiful-dnd
- The mobile preview will reuse rendering logic from the existing story viewer to ensure consistency
- Template data will be stored as JSON in `lib/templates/` directory
- Auto-save will use a debounce pattern to avoid excessive localStorage writes
- Image uploads will be converted to base64 for URL encoding (consider size implications)
- The 32KB URL limit will be calculated based on LZString compression ratio from existing encoder

## Open Questions

(Resolved - no open questions based on brainstorm content)
