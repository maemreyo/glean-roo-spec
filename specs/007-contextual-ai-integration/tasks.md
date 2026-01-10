# Tasks: Contextual AI Integration for Studio

**Feature**: 007-contextual-ai-integration
**Branch**: `007-contextual-ai-integration`
**Generated**: 2026-01-10
**Status**: Ready for Implementation

---

## Feature Summary

Integrate AI capabilities directly into Studio input fields with contextual toolbars, streaming responses, undo/redo functionality, and performance-optimized input handling. Remove standalone AI box and provide seamless one-click AI operations.

---

## Phase 1: Setup (Project Initialization)

### Dependencies & Configuration
- [ ] T001 [P] Install `zundo` npm package for undo/redo middleware
- [ ] T002 [P] Update `.roo/rules/specify-rules.md` to add TypeScript 5.3+ and React 18.2+ to Active Technologies (per spec clarification)

---

## Phase 2: Foundational (Blocking Prerequisites)

### Core Utilities
- [ ] T003 Create `lib/ai/stream-smoother.ts` - StreamSmoother class for 20-50ms character rendering
- [ ] T004 [P] Create `lib/ai/stream-client.ts` - SSE client with fetch/ReadableStream, 10s timeout
- [ ] T005 [P] Create `lib/ai/operations.ts` - AIOperation types, AI_OPERATIONS config with prompts
- [ ] T006 [P] Create `lib/ai/error-messages.ts` - User-friendly error messages (no technical details)

### State Management Infrastructure
- [ ] T007 Modify `lib/stores/draft-store.ts` - Integrate zundo middleware with temporal(), sessionStorage for history
- [ ] T008 [P] Create `lib/sync/draft-sync-channel.ts` - BroadcastChannel manager for cross-tab sync

### API Endpoint
- [ ] T009 Create `app/api/ai/stream/route.ts` - SSE streaming endpoint with AI SDK integration

### React Hooks
- [ ] T010 [P] Create `hooks/useStreamSmoother.ts` - React hook for StreamSmoother integration
- [ ] T011 [P] Create `hooks/useAIStream.ts` - React hook combining streaming, field updates, undo snapshots

---

## Phase 3: User Story 1 - Contextual AI Content Generation (P1)

### AI Toolbar Buttons
- [ ] T012 [US1] Create `components/ai/AIFieldButton.tsx` - Toolbar button component with Sparkles/PenLine/Languages icons
- [ ] T013 [US1] [P] Create `components/ai/MagicFillButton.tsx` - Generate button for empty fields (Sparkles icon)
- [ ] T014 [US1] [P] Create `components/ai/RewriteButton.tsx` - Rewrite button for filled fields (PenLine icon)
- [ ] T015 [US1] [P] Create `components/ai/TranslateButton.tsx` - Translate button with bidirectional EN↔VN support (Languages icon)

### Field Integration
- [ ] T016 [US1] Update `components/studio/GridField.tsx` - Add AI toolbar buttons inline on right side of fields
  - ⚠️ **CRITICAL**: Add `pr-20` or `pr-16` padding-right to Input/Textarea to prevent text from overlapping with absolutely positioned AI buttons on mobile. See research.md §16.1
- [ ] T017 [US1] [P] Integrate AI buttons with English content field (mainContentEn)
  - ⚠️ **CRITICAL**: Ensure sufficient padding-right on textarea to prevent text overlap with AI buttons. See research.md §16.1
- [ ] T018 [US1] [P] Integrate AI buttons with Vietnamese content field (mainContentVn)
  - ⚠️ **CRITICAL**: Ensure sufficient padding-right on textarea to prevent text overlap with AI buttons. See research.md §16.1
- [ ] T019 [US1] [P] Integrate sparkle suggestion buttons with Topic field (title)
- [ ] T020 [US1] [P] Integrate sparkle suggestion buttons with Quote field (heroQuote)

### Streaming Integration
- [ ] T021 [US1] Wire useAIStream hook to stream content into target fields
- [ ] T022 [US1] [P] Implement Magic Fill operation - generate content from scratch for empty fields
  - ⚠️ **CRITICAL**: Ensure field has sufficient padding-right for AI buttons. Use local state (useState) for immediate UI updates, then debounced store sync to prevent lag. See research.md §16.3
- [ ] T023 [US1] [P] Implement Rewrite operation - improve existing content with grammar fixes
  - ⚠️ **CRITICAL**: Ensure field has sufficient padding-right for AI buttons. Use local state (useState) for immediate UI updates, then debounced store sync to prevent lag. See research.md §16.3
- [ ] T024 [US1] [P] Implement Translate EN→VN operation - read English, stream Vietnamese
- [ ] T025 [US1] [P] Implement Translate VN→EN operation - read Vietnamese, stream English
- [ ] T026 [US1] [P] Implement Suggest Topic operation - generate title from English content
- [ ] T027 [US1] [P] Implement Suggest Quote operation - generate quote from English content

### Content Replacement Logic
- [ ] T028 [US1] Implement immediate content replacement without confirmation dialog (one-click workflow)
- [ ] T029 [US1] Add disable logic for translate buttons when source field is empty

---

## Phase 4: User Story 2 - Streaming AI Response with Visual Feedback (P1)

### Loading States
- [ ] T030 [US2] Add loading state (Loader2 spinner) to AI buttons during operations
- [ ] T031 [US2] [P] Implement loading skeleton or typing indicator for fields during streaming
- [ ] T032 [US2] [P] Add disabled state to AI buttons during active operations

### Field State Management
- [ ] T033 [US2] Implement read-only state for target fields during AI streaming
- [ ] T034 [US2] Add "AI is writing..." message or visual indicator for locked fields
- [ ] T035 [US2] Prevent concurrent AI operations on same field (queue or cancel previous)

### Completion & Error Handling
- [ ] T036 [US2] Add success toast notification on AI operation completion using Sonner
- [ ] T037 [US2] [P] Implement error toast with user-friendly messages (no technical details)
- [ ] T038 [US2] [P] Add retry button to error toasts
- [ ] T039 [US2] Implement field reversion to previous state on error/timeout

---

## Phase 5: User Story 3 - Undo/Redo with Smart History Management (P2)

### Keyboard Shortcuts
- [ ] T040 [US3] Create `components/studio/KeyboardShortcuts.tsx` - Global keyboard listener component
- [ ] T041 [US3] Implement Ctrl+Z / Cmd+Z for undo
- [ ] T042 [US3] [P] Implement Ctrl+Y / Ctrl+Shift+Z / Cmd+Shift+Z for redo

### History Snapshot Triggers
- [ ] T043 [US3] Implement 2-second debounce trigger for history snapshots during typing
- [ ] T044 [US3] [P] Implement field blur trigger for history snapshots
- [ ] T045 [US3] Create history snapshot AFTER AI streaming completes (entire content as one unit)

### History Management
- [ ] T046 [US3] Configure zundo limit to 50 snapshots maximum
- [ ] T047 [US3] Implement sessionStorage persistence for undo history (persists across refreshes)
- [ ] T048 [US3] Clear redo history when user makes new edit after undoing

### Undo Feedback
- [ ] T049 [US3] Add toast notification on undo ("Undo" with 1s duration)
- [ ] T050 [US3] [P] Add toast notification on redo ("Redo" with 1s duration)
- [ ] T051 [US3] [P] Show "Nothing to undo" toast when history is empty
- [ ] T052 [US3] [P] Show "Nothing to redo" toast when redo history is empty

---

## Phase 6: User Story 4 - Performance-Optimized Input Handling (P2)

### State Sync Debounce
- [ ] T054 [US4] Implement 500ms debounce for state synchronization (reuse existing debounce utility)
- [ ] T055 [US4] [P] Apply debounce to English content field (mainContentEn)
- [ ] T056 [US4] [P] Apply debounce to Vietnamese content field (mainContentVn)
- [ ] T057 [US4] [P] Apply debounce to Topic field (title)
- [ ] T058 [US4] [P] Apply debounce to Quote field (heroQuote)

### Preview Panel Optimization
- [ ] T059 [US4] Update preview panel to only refresh after 500ms debounce completes
- [ ] T060 [US4] Ensure preview does NOT update on every keystroke

### Auto-save Timing
- [ ] T061 [US4] Trigger auto-save immediately after AI operation completes (bypass 500ms debounce)
- [ ] T062 [US4] [P] Ensure auto-save respects standard 500ms debounce for manual edits

### Non-Blocking Operations
- [ ] T063 [US4] Verify user typing remains responsive during AI operations in other fields
- [ ] T064 [US4] [P] Test keystroke latency is <16ms (60fps) during rapid typing
  - ⚠️ **CRITICAL**: Test thoroughly on low-end devices. Use local state (useState) for immediate display (16ms latency target), then push to Store via debounce. Input should NOT be bound directly to Store to avoid lag with zundo middleware. See research.md §16.3

---

## Phase 7: User Story 5 - Manual Validation with Clear Error Messages (P3)

### Validation Rules
- [ ] T065 [US5] Create `lib/validation/field-validator.ts` - Validation utility functions
- [ ] T066 [US5] [P] Implement image URL validation (https:// required, valid image formats)
- [ ] T067 [US5] [P] Implement required field validation for publish
- [ ] T068 [US5] [P] Implement character length validation for Title (100 max)

### Validation UI
- [ ] T069 [US5] Add inline error messages below fields with validation errors
- [ ] T070 [US5] [P] Add red border visual indicator for invalid fields
- [ ] T071 [US5] [P] Add character counter for Title field showing x/100

### Publish vs Save Draft
- [ ] T072 [US5] Allow saving drafts with validation errors
- [ ] T073 [US5] [P] Prevent publishing until all validation errors are fixed
- [ ] T074 [US5] [P] Clear error indicators when all validations pass

---

## Phase 8: Polish & Cross-Cutting Concerns

### UI Cleanup
- [ ] T075 Remove standalone "AI Content Generation" box from Studio page (FR-026)
- [ ] T076 [P] Verify AI button positioning is consistent across all fields (inline, right side)
- [ ] T077 [P] Test responsive design for AI buttons on mobile viewports

### Accessibility
- [ ] T078 Add ARIA labels to AI buttons for screen readers
- [ ] T079 [P] Ensure keyboard navigation works for all AI buttons (Tab, Enter, Space)
- [ ] T080 [P] Test color contrast for loading and error states

### Error Handling Edge Cases
- [ ] T081 Handle network interruption during streaming (show user-friendly message, revert field)
- [ ] T082 [P] Handle 10-second timeout with "AI service is taking longer than expected" message
- [ ] T083 [P] Handle rate limiting with "Too many requests, please wait" message
- [ ] T084 [P] Gracefully degrade when localStorage/sessionStorage is unavailable

### Cross-Tab Sync
- [ ] T085 Integrate BroadcastChannel with draft store to broadcast changes
- [ ] T086 [P] Subscribe to cross-tab updates and show conflict notification
- [ ] T087 [P] Implement last-write-wins semantics with timestamp comparison

### Performance Testing
- [ ] T088 Test streaming speed is 20-50ms per character (~1000-2000 chars/min)
- [ ] T089 [P] Verify memory footprint remains under 1MB for 50 snapshots
- [ ] T090 [P] Test on low-end devices to ensure 60fps during streaming

---

## Phase 9: Testing

### Unit Tests
- [ ] T091 [P] Create `lib/ai/__tests__/stream-smoother.test.ts` - Test StreamSmoother timing accuracy
- [ ] T092 [P] Create `lib/ai/__tests__/stream-client.test.ts` - Test SSE client with mock responses
- [ ] T093 [P] Create `hooks/__tests__/useAIStream.test.ts` - Test AI streaming hook
- [ ] T094 [P] Create `lib/stores/__tests__/draft-store-zundo.test.ts` - Test zundo integration

### Integration Tests
- [ ] T095 [P] Test undo/redo keyboard shortcuts trigger store updates
- [ ] T096 [P] Test debounce creates snapshots after 2 seconds of typing
- [ ] T097 [P] Test field blur creates history snapshot

### Component Tests
- [ ] T098 Create `components/ai/__tests__/AIFieldButton.test.tsx` - Test button states and interactions
- [ ] T099 [P] Test AI buttons disable when dependencies not met (translate with empty source)
- [ ] T100 [P] Test loading spinner shows during operations

### E2E Scenarios
- [ ] T101 User triggers Magic Fill and sees streaming effect in target field
- [ ] T102 [P] User triggers Translate EN→VN and Vietnamese content streams correctly
- [ ] T103 [P] User clicks Ctrl+Z and entire AI-generated content is removed as one unit
- [ ] T104 [P] Two tabs edit same draft and changes sync via BroadcastChannel

### Linting & Type Checking
- [ ] T105 Run `npm run lint` and fix all linting errors
- [ ] T106 Run TypeScript type checking and resolve all type errors

---

## Dependencies

### Critical Path (Must Complete First)
- T007 (zundo integration) must complete before T043-T052 (undo/redo implementation)
- T003 (StreamSmoother) must complete before T010 (useStreamSmoother hook)
- T009 (AI streaming API) must complete before T021-T027 (AI operation implementations)

### User Story Dependencies
- US1 tasks (T012-T029) must complete before US2 tasks (T030-T039) - streaming must work before visual feedback
- US3 tasks (T040-T052) can start in parallel with US1-US2 after T007 completes
- US4 tasks (T054-T064) require US1 completion for auto-save timing tests
- US5 tasks (T065-T074) are independent and can run in parallel with any user story

### Parallel Opportunities
- T004, T005, T006 can run in parallel (different utility files)
- T008 can run in parallel with T003-T006 (separate concern)
- T010, T011 can run in parallel with T012 (different layers)
- T017-T020 can run in parallel (different fields)
- T022-T027 can run in parallel (different AI operations)
- T031-T032 can run in parallel (different visual indicators)
- T037-T039 can run in parallel (different error scenarios)
- T042, T051-T052 can run in parallel (different keyboard shortcuts)
- T055-T058 can run in parallel (different fields)
- T066-T068 can run in parallel (different validation rules)
- T070-T071 can run in parallel (different UI elements)
- All unit tests (T091-T094) can run in parallel

---

## Implementation Strategy (MVP First)

### MVP Scope (P1 User Stories)
1. **Phase 1-2**: Setup and foundational infrastructure (T001-T011)
2. **Phase 3**: US1 - Core AI content generation (T012-T029)
3. **Phase 4**: US2 - Visual feedback during streaming (T030-T039)
4. **Phase 9**: Essential testing (T091-T098, T105-T106)

### Post-MVP Enhancements (P2-P3 User Stories)
5. **Phase 5**: US3 - Undo/redo with history management (T040-T052)
6. **Phase 6**: US4 - Performance optimization (T054-T064)
7. **Phase 7**: US5 - Manual validation (T065-T074)
8. **Phase 8**: Polish and cross-cutting concerns (T075-T090)
9. **Phase 9**: Complete testing suite (T099-T104)

---

## Task Summary

### Total Tasks: 106

### By User Story
- **Setup/Foundational**: 11 tasks (T001-T011)
- **US1 - Contextual AI Generation (P1)**: 18 tasks (T012-T029)
- **US2 - Visual Feedback (P1)**: 10 tasks (T030-T039)
- **US3 - Undo/Redo (P2)**: 13 tasks (T040-T052)
- **US4 - Performance (P2)**: 11 tasks (T054-T064)
- **US5 - Validation (P3)**: 10 tasks (T065-T074)
- **Polish & Cross-Cutting**: 16 tasks (T075-T090)
- **Testing**: 16 tasks (T091-T106)

### Parallel Execution Opportunities
- **High Parallelization**: 28 tasks marked with [P] can run independently
- **Medium Parallelization**: 15 tasks have partial parallelization opportunities
- **Critical Path**: 32 tasks must run sequentially due to dependencies

### Key Files Created/Modified

**New Files** (28):
- `lib/ai/stream-smoother.ts`
- `lib/ai/stream-client.ts`
- `lib/ai/operations.ts`
- `lib/ai/error-messages.ts`
- `lib/sync/draft-sync-channel.ts`
- `lib/validation/field-validator.ts`
- `app/api/ai/stream/route.ts`
- `hooks/useStreamSmoother.ts`
- `hooks/useAIStream.ts`
- `components/ai/AIFieldButton.tsx`
- `components/ai/MagicFillButton.tsx`
- `components/ai/RewriteButton.tsx`
- `components/ai/TranslateButton.tsx`
- `components/studio/KeyboardShortcuts.tsx`
- Test files (10)

**Modified Files** (3):
- `lib/stores/draft-store.ts` (zundo integration)
- `components/studio/GridField.tsx` (AI buttons)
- `.roo/rules/specify-rules.md` (tech stack update)

---

## References

- **Specification**: `specs/007-contextual-ai-integration/spec.md`
- **Research**: `specs/007-contextual-ai-integration/research.md`
- **Data Model**: `specs/007-contextual-ai-integration/data-model.md`
- **Quick Start**: `specs/007-contextual-ai-integration/quickstart.md`
- **API Contracts**: `specs/007-contextual-ai-integration/contracts/`

---

**Generated by**: Architect Mode
**Last Updated**: 2026-01-10
