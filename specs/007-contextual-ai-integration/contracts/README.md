# API Contracts: Contextual AI Integration

**Feature**: 007-contextual-ai-integration
**Created**: 2026-01-10
**Status**: Phase 1 Planning

## Overview

This directory contains API contracts and interface definitions for the Contextual AI Integration feature. These contracts define the communication patterns between client components, server endpoints, and state management systems.

---

## Available Contracts

| Contract | Description |
|----------|-------------|
| [`ai-streaming-api.md`](ai-streaming-api.md) | Server-Sent Events (SSE) streaming API for AI content generation |
| [`draft-store-api.md`](draft-store-api.md) | Zustand store with zundo middleware for undo/redo functionality |

---

## Architecture Overview

```mermaid
flowchart LR
    subgraph Client
        BUTTON[AI Button]
        HOOK[useAIStream Hook]
        SMOOTHER[StreamSmoother]
    end

    subgraph API
        ROUTE[/api/ai/stream]
    end

    subgraph State
        STORE[DraftStore+zundo]
        HISTORY[sessionStorage]
    end

    BUTTON -->|trigger| HOOK
    HOOK -->|POST| ROUTE
    ROUTE -->|SSE chunks| HOOK
    HOOK -->|buffer| SMOOTHER
    SMOOTHER -->|20-50ms| STORE
    STORE -->|snapshots| HISTORY
```

---

## Key Design Decisions

### Server-Sent Events (SSE)
- **Protocol**: HTTP with `text/event-stream` content type
- **Direction**: Server-to-client streaming
- **Browser Support**: Native `EventSource` API or `fetch` with `ReadableStream`
- **Timeout**: 10-second hard limit with user-friendly error message

### zundo Middleware
- **Storage Key**: `draft-undo-history`
- **Storage Type**: `sessionStorage` (persists across refreshes, cleared on tab close)
- **Max Snapshots**: 50 entries
- **Partial State**: Only `topicData` is tracked (not design config)

### Stream Smoother
- **Target Speed**: 20-50ms per character (~1000-2000 chars/minute)
- **Mechanism**: `requestAnimationFrame` for 60fps rendering
- **Buffer**: Incoming SSE chunks are buffered and rendered at consistent rate

---

## Usage Patterns

### Triggering AI Operations

```typescript
// In component
const { streamAI } = useAIStream();

const handleGenerate = async () => {
  await streamAI({
    operation: 'generate-content',
    targetField: 'mainContentEn',
  });
};
```

### Streaming with Field Updates

```typescript
// StreamSmoother integration
const smoother = new StreamSmoother({
  charsPerMinute: 1500,
  onUpdate: (text) => setMainContentEn(text),
  onComplete: (finalText) => {
    // Trigger undo snapshot
    createSnapshot();
    // Trigger auto-save
    triggerAutoSave();
  },
});

// Add chunks from SSE
eventSource.onmessage = (event) => {
  const { chunk } = JSON.parse(event.data);
  smoother.addChunk(chunk);
};
```

### Undo/Redo with Keyboard

```typescript
// Keyboard shortcuts (handled at root level)
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
      e.preventDefault();
      undo(); // From zundo
    }
    if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
      e.preventDefault();
      redo(); // From zundo
    }
  };
  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [undo, redo]);
```

---

## Error Handling

All errors must be user-friendly without technical details:

| Error Type | User Message |
|------------|--------------|
| Timeout (10s) | "AI service is taking longer than expected. Please try again." |
| Network | "Unable to connect to AI service. Please check your connection." |
| Rate Limit | "Too many requests. Please wait a moment and try again." |
| API Key | "AI service configuration error. Please contact support." |
| Default | "AI service unavailable. Please try again." |

---

## Performance Requirements

| Metric | Target |
|--------|--------|
| Keystroke latency | <16ms (60fps) |
| State sync debounce | 500ms |
| History snapshot debounce | 2000ms (2s) |
| AI streaming speed | 20-50ms per character |
| AI operation timeout | 10 seconds |

---

## References

- **Specification**: [`../spec.md`](../spec.md)
- **Data Model**: [`../data-model.md`](../data-model.md)
- **Research**: [`../research.md`](../research.md)
- **Quick Start**: [`../quickstart.md`](../quickstart.md)
