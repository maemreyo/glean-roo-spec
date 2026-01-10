# Feature Specification: Contextual AI Integration for Studio

**Feature Branch**: `007-contextual-ai-integration`
**Created**: 2026-01-10
**Status**: Draft
**Input**: User description: "Integrate AI features directly into Studio input fields with contextual AI toolbars, remove standalone AI box, add streaming translation, implement Undo/Redo with debounce optimization"

## Clarifications

### Session 2026-01-10

- **AI API Error Security** → Show user-friendly messages only (e.g., "AI service unavailable, please try again") without technical details
  - Impact: Security posture, UX clarity
  - Updated in: FR-009 (Error handling), Edge Cases section

- **AI Streaming Implementation** → Server-Sent Events (SSE) from Next.js API route
  - Impact: Technical architecture, API design
  - Updated in: Assumptions section, Dependencies section

- **Undo/Redo Scope** → Page session (persists across tab refreshes until tab is closed)
  - Impact: Data persistence, UX expectations
  - Updated in: FR-018 (session persistence), Assumptions section

- **AI Operation Timeout** → 10 seconds (fail fast)
  - Impact: Performance requirements, error handling UX
  - Updated in: Performance Requirements section, Edge Cases section

- **AI Button Placement** → Inline on right side of each field (always visible)
  - Impact: UI/UX design, component structure
  - Updated in: FR-025 (button positioning), UI/UX Requirements section

- **Streaming Speed** → 20-50ms per character (natural typing feel, ~1000-2000 characters/minute). This creates a "Stream Smoother" mechanism where incoming SSE chunks are buffered and rendered at a consistent rate for a buttery smooth feel.
  - Impact: Performance requirements, streaming architecture
  - Updated in: Performance Requirements section (FR-025 added), Acceptance Scenarios

- **Content Replacement Behavior** → AI operations replace existing content immediately (one-click workflow) without confirmation dialog. Users can undo if needed.
  - Impact: UI/UX workflow, undo/redo behavior
  - Updated in: AI Integration Requirements section, UI/UX Requirements section (FR-030 updated)

- **Translation Direction** → Bidirectional support (English ↔ Vietnamese) - users can translate either direction, not just English to Vietnamese.
  - Impact: Translation workflow, button placement logic
  - Updated in: AI Integration Requirements section (FR-003 updated)

- **Auto-save Timing** → Auto-save immediately after AI operation completes (ensures AI-generated content is saved), rather than waiting for the standard 500ms debounce timer used for manual edits.
  - Impact: Data persistence, auto-save behavior
  - Updated in: Data Management Requirements section

- **Undo History Snapshot** → AI operations create a history snapshot AFTER streaming completes (not before). A single undo removes the entire AI-generated content as one unit.
  - Impact: Undo/redo timing, history state management
  - Updated in: Undo/Redo Requirements section (FR-014 clarified)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Contextual AI Content Generation (Priority: P1)

A content creator is working in the Studio editor and needs AI assistance to generate or improve content. Instead of navigating to a separate AI section, they access AI features directly from each input field where they need help.

**Why this priority**: This is the core value proposition - making AI assistance seamlessly integrated into the workflow rather than a separate step. It directly addresses the UX friction identified in the current implementation.

**Independent Test**: Can be fully tested by clicking AI buttons on input fields and verifying content appears in the correct fields with streaming effects. Delivers immediate value by eliminating the two-step workflow (AI box → manual copy-paste).

**Acceptance Scenarios**:

1. **Given** a user is on the Studio page with an empty English content field, **When** they click the "Magic Fill" button (Sparkles icon) in the field's toolbar, **Then** AI generates content directly in that field with a visible streaming effect, and the field shows a loading state during generation
2. **Given** a user has existing English content, **When** they click the "Rewrite/Fix Grammar" button (PenLine icon), **Then** AI rewrites the content while preserving their intent, streaming the result into the same field at 20-50ms per character
3. **Given** a user has English content and an empty Vietnamese field, **When** they click the "Auto Translate" button (Languages icon) on the Vietnamese field, **Then** the system reads the English content, translates it via AI, and streams the Vietnamese translation into the Vietnamese field
4. **Given** a user has Vietnamese content and an empty English field, **When** they click the "Auto Translate" button (Languages icon) on the English field, **Then** the system reads the Vietnamese content, translates it via AI, and streams the English translation into the English field
5. **Given** a user has content in the English field, **When** they click the sparkle icon button next to the Topic input, **Then** AI analyzes the content and suggests an appropriate topic/title, populating the Topic field
6. **Given** a user has content in the English field, **When** they click the sparkle icon button next to the Quote input, **Then** AI analyzes the content and suggests a relevant quote, populating the Quote field
7. **Given** a user triggers any AI operation on a field with existing content, **When** the operation completes, **Then** the new content replaces the old content immediately without confirmation, and the user can press Ctrl+Z to undo

---

### User Story 2 - Streaming AI Response with Visual Feedback (Priority: P1)

A user triggers an AI operation and needs to understand that the system is working and see the content being generated in real-time, providing a natural and responsive experience.

**Why this priority**: Critical UX requirement that prevents user confusion during AI operations. Without streaming and visual feedback, users may think the system is frozen or not responding.

**Independent Test**: Can be tested by triggering any AI operation and observing the visual loading indicators, streaming text effect, and field state changes. Delivers value by providing clear system status during async operations.

**Acceptance Scenarios**:

1. **Given** a user clicks an AI button, **When** the AI request is in progress, **Then** the target field shows a loading skeleton or typing indicator, and the button shows a loading/spinner state
2. **Given** AI is generating content in a field, **When** content streams in character by character, **Then** the field updates in real-time showing the content being written at 20-50ms per character, creating a smooth typing effect via a Stream Smoother buffer mechanism
3. **Given** AI is writing to a field, **When** the user tries to type in that same field, **Then** the field is read-only or shows a "AI is writing..." message, preventing concurrent edits
4. **Given** an AI operation completes successfully, **When** the streaming finishes, **Then** the loading indicators disappear, the field becomes editable again, and a subtle success animation or toast appears
5. **Given** an AI operation fails or times out, **When** the error occurs, **Then** the field returns to its previous state, an error message explains what went wrong, and the user can retry

---

### User Story 3 - Undo/Redo with Smart History Management (Priority: P2)

A user makes several edits to their content, triggers AI operations, and accidentally deletes an important paragraph. They need to restore their work without losing other recent changes.

**Why this priority**: Essential for an editor experience, but not blocking for MVP. Users can work around this with careful editing, but lack of undo causes significant frustration and data loss anxiety.

**Independent Test**: Can be tested by making a series of edits and AI operations, then pressing Ctrl+Z (or Cmd+Z) repeatedly to verify each step can be undone. Delivers value by preventing data loss and enabling experimentation.

**Acceptance Scenarios**:

1. **Given** a user has made 10 edits over 2 minutes, **When** they press Ctrl+Z, **Then** only the most recent meaningful change is undone (not every keystroke), and they can press repeatedly to step back through history
2. **Given** a user triggers an AI translation that generates 500 characters, **When** they press Ctrl+Z once, **Then** the entire AI-generated translation is removed as one unit, not character by character
3. **Given** a user types continuously for 30 seconds, **When** they stop typing and wait 2 seconds, **Then** a snapshot is created capturing the entire typing session as one history entry
4. **Given** a user switches focus from one field to another, **When** they blur the first field, **Then** a history snapshot is created for the state of that field
5. **Given** a user has undone 5 steps and wants to redo, **When** they press Ctrl+Y or Ctrl+Shift+Z, **Then** they can step forward through the undone changes
6. **Given** a user makes a new edit after undoing, **When** they continue working, **Then** the redo history is cleared and new history entries are created from this point

---

### User Story 4 - Performance-Optimized Input Handling (Priority: P2)

A user is typing rapidly in the English content field, and each keystroke should feel instant without lag or delay, even though the system is auto-saving and managing state in the background.

**Why this priority**: Performance is critical for user satisfaction, but the optimization strategy (debounce) can be implemented progressively. Users may notice slight lag initially but the feature remains functional.

**Independent Test**: Can be tested by typing rapidly in input fields and measuring response time. Delivers value by ensuring the editor feels responsive and professional.

**Acceptance Scenarios**:

1. **Given** a user is typing rapidly in a content field, **When** each keystroke occurs, **Then** the character appears instantly without perceptible delay (<16ms)
2. **Given** a user stops typing, **When** 500ms elapses without further keystrokes, **Then** the state is synchronized with the global store and auto-save is triggered
3. **Given** a user triggers an AI operation that completes successfully, **When** the streaming finishes, **Then** auto-save is triggered immediately without waiting for the debounce timer
4. **Given** a user makes 20 rapid edits, **When** they observe the preview panel, **Then** the preview updates only after they pause typing, not on every keystroke
5. **Given** a user is typing during an AI operation in another field, **When** they continue working, **Then** their typing remains responsive and is not blocked by the AI streaming

---

### User Story 5 - Manual Validation with Clear Error Messages (Priority: P3)

A user tries to publish a card with an invalid image URL or missing required fields, and needs to understand what's wrong and how to fix it without technical jargon.

**Why this priority**: Validation is important for data quality, but users can still create drafts without strict validation. This can be enforced at publish time rather than during editing.

**Independent Test**: Can be tested by entering invalid data and attempting to publish or save, verifying error messages appear and guide users to fix issues. Delivers value by preventing frustration from unclear errors.

**Acceptance Scenarios**:

1. **Given** a user enters an invalid image URL (not https:// or not an image format), **When** they blur the field or attempt to publish, **Then** a clear error message appears explaining the valid URL format
2. **Given** a user leaves a required field empty, **When** they attempt to publish, **Then** the empty field is highlighted with a red border and a message indicates it's required
3. **Given** a user enters a title exceeding 100 characters, **When** they blur the field, **Then** a character counter shows they're over the limit and a warning appears
4. **Given** a user fixes all validation errors, **When** they attempt to publish again, **Then** the publish succeeds and all error indicators disappear

---

### Edge Cases

- What happens when the user clicks multiple AI buttons in rapid succession? Only one AI operation should run at a time per field, with subsequent clicks queuing or cancelling the previous operation
- What happens when a user triggers AI on a field with existing content? The content is replaced immediately without confirmation, and the user can undo with Ctrl+Z to restore the previous content
- What happens when AI streaming is interrupted (network error, timeout after 10 seconds, server error)? The partial content is discarded, the field reverts to its previous state, and a user-friendly error message (e.g., "AI service unavailable, please try again") offers retry without technical details
- What happens when the user triggers AI on Vietnamese field but English field is empty? The button is disabled or shows a tooltip indicating the source field must have content first
- What happens when undo history exceeds storage limits? Oldest history entries are removed to maintain a maximum of 50 snapshots per session
- What happens when the user tries to undo but history is empty? The undo action is ignored or a toast indicates "Nothing to undo"
- What happens when browser localStorage is full or unavailable? The system gracefully degrades by running in-memory only for the session
- What happens when the user has unsaved changes and tries to close the tab? A browser confirmation dialog appears warning about unsaved changes
- What happens when two browser tabs are open editing the same draft? Changes sync via BroadcastChannel API, with the last write winning and a conflict notification shown
- What happens when AI content exceeds field length limits? The streaming stops at the limit, a warning indicates content was truncated, and the user can edit to fit
- What happens when the user edits content while AI is streaming into a different field? Their editing is unaffected and the AI field remains read-only during streaming

## Requirements *(mandatory)*

### Functional Requirements

**AI Integration Requirements**

- **FR-001**: System MUST provide a contextual AI toolbar button ("Magic Fill" with Sparkles icon from lucide-react) for empty text fields that generates content directly in the field
- **FR-002**: System MUST provide a contextual AI toolbar button ("Rewrite/Fix Grammar" with PenLine icon from lucide-react) for filled text fields that improves existing content
- **FR-003**: System MUST provide an "Auto Translate" button (Languages icon from lucide-react) on content fields that supports bidirectional translation (English ↔ Vietnamese)
- **FR-004**: System MUST provide sparkle icon buttons (Sparkles icon from lucide-react) for Topic and Quote fields that generate suggestions based on English content
- **FR-005**: System MUST stream AI-generated content character-by-character into target fields with visible typing effect
- **FR-006**: System MUST lock target fields to read-only state during AI streaming operations
- **FR-007**: System MUST display loading indicators (skeleton, spinner, or typing animation) during AI operations
- **FR-008**: System MUST disable AI buttons when their dependencies are not met (e.g., translate button when English field is empty)
- **FR-009**: System MUST handle AI operation failures by reverting field state and displaying user-friendly error messages without technical details or stack traces (e.g., "AI service unavailable, please try again") with retry option
- **FR-010**: System MUST prevent concurrent AI operations on the same field (queue or cancel previous operation)

**Undo/Redo Requirements**

- **FR-011**: System MUST support keyboard shortcuts for undo (Ctrl+Z / Cmd+Z) and redo (Ctrl+Y / Ctrl+Shift+Z / Cmd+Shift+Z)
- **FR-012**: System MUST create history snapshots after user stops typing for 2 seconds (debounce mechanism)
- **FR-013**: System MUST create history snapshots when user blurs (leaves) a field
- **FR-014**: System MUST create history snapshots after AI streaming completes (snapshot is created when the entire AI-generated content is present, not before streaming starts)
- **FR-015**: System MUST treat entire AI-generated content as a single undoable unit (not character-by-character)
- **FR-016**: System MUST maintain a maximum of 50 history snapshots per session, removing oldest entries when limit exceeded
- **FR-017**: System MUST clear redo history when user makes a new edit after undoing
- **FR-018**: System MUST persist undo history using browser sessionStorage for page session (persists across tab refreshes, cleared on tab close)

**Performance Requirements**

- **FR-019**: System MUST render each keystroke in input fields within 16ms (60fps) without lag
- **FR-020**: System MUST debounce state synchronization by 500ms after user stops typing
- **FR-021**: System MUST update preview panel only after debounce, not on every keystroke
- **FR-022**: System MUST not block user input during AI operations in other fields
- **FR-023**: System MUST limit history snapshot creation to maximum once per 2 seconds during continuous typing
- **FR-024**: System MUST timeout AI operations after 10 seconds with user-friendly error message (fail fast)
- **FR-025**: System MUST stream AI-generated content at 20-50ms per character using a "Stream Smoother" mechanism that buffers incoming SSE chunks and renders them at a consistent rate for a natural typing feel (~1000-2000 characters/minute)

**UI/UX Requirements**

- **FR-026**: System MUST remove the standalone "AI Content Generation" box from the Studio page
- **FR-027**: System MUST position AI toolbar buttons inline on the right side of each input field, always visible
- **FR-028**: System MUST display empty state buttons for empty fields and filled state buttons for fields with content
- **FR-029**: System MUST show clear visual feedback for field states: editable, loading, read-only during AI, error
- **FR-030**: System MUST display toast notifications for AI operation completion, errors, and retry options
- **FR-031**: System MUST replace existing content immediately during AI operations without confirmation dialog (one-click workflow), with undo available to restore previous content
- **FR-032**: System MUST show character counters for fields with length limits (e.g., Title: 100 characters max)

**Validation Requirements**

- **FR-033**: System MUST validate image URLs to ensure they start with https:// and point to image formats (jpg, jpeg, png, gif, webp, svg)
- **FR-034**: System MUST validate required fields when user attempts to publish or save
- **FR-035**: System MUST display inline error messages below fields with validation errors
- **FR-036**: System MUST highlight fields with validation errors using visual indicators (red border, icon)
- **FR-037**: System MUST allow users to save drafts with validation errors, but prevent publishing until errors are fixed

**Data Management Requirements**

- **FR-038**: System MUST continue using existing Zustand store for state management (no React Hook Form)
- **FR-039**: System MUST integrate zundo middleware with Zustand for undo/redo functionality
- **FR-040**: System MUST maintain auto-save functionality with existing localStorage and Supabase sync, triggering auto-save immediately after AI operation completes (bypassing the standard 500ms debounce timer)
- **FR-041**: System MUST store undo history separately from draft data to avoid sync conflicts
- **FR-042**: System MUST support BroadcastChannel API for cross-tab sync of draft changes

### Key Entities

- **Draft Snapshot**: A point-in-time capture of the entire draft state (all field values) created at specific triggers (debounce, blur, AI completion) for undo/redo history. Attributes: timestamp, draft state, operation type (edit, ai-generate, translate)
- **AI Operation Request**: A request from the user to generate or improve content via AI. Attributes: operation type (generate, rewrite, translate, suggest), source field ID, target field ID, timestamp, status (pending, streaming, completed, failed)
- **Field State**: The current condition of an input field. Attributes: field ID, value, is read-only, is loading, validation errors, has unsaved changes
- **Validation Rule**: A rule that defines acceptable input for a field. Attributes: field ID, rule type (required, format, length), constraint value, error message

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can generate AI content in 1 click instead of 3+ clicks (navigate to AI box, select option, copy, paste), reducing the time to first AI-generated content by 60%
- **SC-002**: 95% of users report that AI features feel integrated into their workflow rather than being a separate tool (measured via post-release survey)
- **SC-003**: Input fields render keystrokes with <16ms latency during rapid typing (>5 keystrokes per second) on all supported devices
- **SC-004**: 90% of users successfully use Undo/Redo to recover from mistakes without needing to refresh the page or lose data
- **SC-005**: AI streaming starts within 500ms of button click and completes average operations (100 words) within 5 seconds
- **SC-006**: Zero data loss incidents reported due to accidental deletions (measured by support tickets for "lost content" over 30 days)
- **SC-007**: Preview panel updates only once after user stops typing, reducing render cycles by 80% compared to updating on every keystroke
- **SC-008**: Validation error messages are understood and resolved by users on first attempt 85% of the time (measured by error correction rate)
- **SC-009**: Browser tab remains responsive (60fps) during AI operations in background fields
- **SC-010**: Undo history memory footprint remains under 1MB for a typical 30-minute editing session with 50 snapshots

## Dependencies & Assumptions

### Dependencies

- **Phase 006 (Studio UI Premium)**: Must be completed as this builds on the Studio page structure and state management architecture
- **Existing AI API**: The current AI generation endpoint at `/api/generate` must support Server-Sent Events (SSE) for streaming responses
- **Zustand Store**: The existing `draft-store.ts` must be accessible and follow the documented structure
- **Supabase Drafts Table**: Existing drafts table with JSONB storage must support the current draft schema

### Assumptions

- AI API supports Server-Sent Events (SSE) for streaming responses from Next.js API route
- Users primarily work in a single browser tab, with multi-tab scenarios being edge cases
- AI operations must timeout after 10 seconds (fail fast)
- Users are familiar with standard undo/redo keyboard shortcuts (Ctrl+Z, Ctrl+Y)
- Browser localStorage has sufficient capacity for storing 50+ draft snapshots
- Network connectivity is generally reliable, with brief interruptions handled gracefully
- The target audience uses modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+) that support BroadcastChannel API
- Users will understand the difference between "Save Draft" (allows validation errors) and "Publish" (requires valid data)

## Out of Scope

The following items are explicitly out of scope for this feature:

- **Full Version History**: Undo/redo is page session using sessionStorage (persists across tab refreshes, cleared on tab close). Persistent version history like Google Docs is a future feature
- **AI Operation Customization**: Users cannot customize AI prompts, tone, or style in this phase. Future feature may add AI settings
- **Collaborative Editing**: Real-time multi-user editing with conflict resolution is not included
- **Offline Mode**: Application requires internet connectivity for AI operations. Offline queueing of AI requests is not supported
- **Voice Input**: Dictation or voice-to-text input is not included in this feature
- **AI Chat Interface**: Conversational AI where users can ask questions or refine results iteratively is not included
- **Mobile Touch Gestures**: Touch-specific UI patterns for mobile devices are not the primary focus, though responsive design is maintained
- **Advanced Validation**: Complex cross-field validation rules (e.g., "Topic must be related to keywords in content") are not included
- **AI Cost Management**: Usage tracking, quotas, or cost warnings for AI operations are not included
