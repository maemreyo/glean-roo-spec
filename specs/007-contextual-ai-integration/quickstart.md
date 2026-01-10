# Quick Start: Contextual AI Integration

**Feature**: 007-contextual-ai-integration
**Branch**: `007-contextual-ai-integration`
**Prerequisites**: Feature 006 (Studio UI Premium) completed

---

## Installation

### New Dependencies

```bash
npm install zundo
```

### Existing Dependencies Used

- `zustand`: ^5.0.9 (already installed)
- `ai`: ^6.0.23 (already installed)
- `lucide-react`: ^0.562.0 (already installed)
- `sonner`: ^2.0.7 (already installed)

---

## Core Implementation Steps

### Step 1: Set Up zundo Middleware

Modify [`lib/stores/draft-store.ts`](../../lib/stores/draft-store.ts) to add undo/redo functionality:

```typescript
// lib/stores/draft-store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { temporal } from 'zundo';
import type { TopicData, Vocabulary } from '@/types/topic';
import { storageConfig } from '@/lib/stores/design/storage';

const defaultTopicData: TopicData = {
  title: '',
  heroImage: '',
  heroQuote: '',
  mainContentEn: '',
  mainContentVn: '',
  vocabList: [],
};

// Configure zundo middleware
const temporalConfig = {
  limit: 50, // Max 50 snapshots
  partialize: (state: DraftStore) => ({ topicData: state.topicData }),
  wrapTemporal: (storeInitializer) => {
    return persist(storeInitializer, {
      name: 'draft-undo-history',
      storage: {
        getItem: (name) => {
          const str = sessionStorage.getItem(name);
          return str ? JSON.parse(str) : null;
        },
        setItem: (name, value) => {
          sessionStorage.setItem(name, JSON.stringify(value));
        },
        removeItem: (name) => sessionStorage.removeItem(name),
      },
    });
  },
};

export const useDraftStore = create<DraftStore>()(
  persist(
    temporal(
      (set) => ({
        topicData: defaultTopicData,
        // ... existing actions
      }),
      temporalConfig
    ),
    {
      name: 'studio-card-draft',
      storage: storageConfig,
    }
  )
);

// Access undo/redo functions
export const useDraftUndo = () => useDraftStore.temporal.getState();

// Reactive hook for undo state
export const useDraftTemporalState = () => {
  return useDraftStore.temporal((state) => ({
    pastStates: state.pastStates,
    futureStates: state.futureStates,
    canUndo: state.pastStates.length > 0,
    canRedo: state.futureStates.length > 0,
  }));
};
```

---

### Step 2: Implement StreamSmoother Class

Create [`lib/ai/stream-smoother.ts`](../../lib/ai/stream-smoother.ts):

```typescript
// lib/ai/stream-smoother.ts
export interface StreamSmootherOptions {
  charsPerMinute?: number; // Default: 1500 = ~25ms per char
  onUpdate: (text: string) => void;
  onComplete: (finalText: string) => void;
}

export class StreamSmoother {
  private buffer: string[] = [];
  private currentText = '';
  private isProcessing = false;
  private rafId: number | null = null;
  private lastRenderTime = 0;
  private readonly msPerChar: number;
  private readonly onUpdate: (text: string) => void;
  private readonly onComplete: (finalText: string) => void;

  constructor(options: StreamSmootherOptions) {
    const charsPerMinute = options.charsPerMinute ?? 1500;
    this.msPerChar = 60000 / charsPerMinute;
    this.onUpdate = options.onUpdate;
    this.onComplete = options.onComplete;
  }

  addChunk(chunk: string): void {
    this.buffer.push(chunk);
    if (!this.isProcessing) {
      this.startProcessing();
    }
  }

  private startProcessing(): void {
    this.isProcessing = true;
    this.processNext();
  }

  private processNext = (): void => {
    if (this.buffer.length === 0) {
      this.isProcessing = false;
      this.onComplete(this.currentText);
      return;
    }

    const now = performance.now();
    const timeSinceLastRender = now - this.lastRenderTime;

    if (timeSinceLastRender >= this.msPerChar) {
      const nextChar = this.buffer.shift();
      if (nextChar) {
        this.currentText += nextChar;
        this.onUpdate(this.currentText);
        this.lastRenderTime = now;
      }
    }

    this.rafId = requestAnimationFrame(this.processNext);
  };

  stop(): void {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    this.isProcessing = false;
    this.buffer = [];
  }

  reset(): void {
    this.stop();
    this.currentText = '';
    this.lastRenderTime = 0;
  }
}
```

---

### Step 3: Create AI Toolbar Button Component

Create [`components/ai/AIFieldButton.tsx`](../../components/ai/AIFieldButton.tsx):

```typescript
// components/ai/AIFieldButton.tsx
'use client';

import { Button } from '@/components/ui/button';
import { Sparkles, PenLine, Languages, Loader2 } from 'lucide-react';

interface AIFieldButtonProps {
  operation: 'generate' | 'rewrite' | 'translate';
  isLoading?: boolean;
  disabled?: boolean;
  onClick: () => void;
}

const icons = {
  generate: Sparkles,
  rewrite: PenLine,
  translate: Languages,
};

export function AIFieldButton({
  operation,
  isLoading,
  disabled,
  onClick,
}: AIFieldButtonProps) {
  const Icon = icons[operation];

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={onClick}
      disabled={disabled || isLoading}
      className="ml-2"
      aria-label={operation === 'generate' ? 'Generate content' :
                  operation === 'rewrite' ? 'Rewrite content' :
                  'Translate content'}
    >
      {isLoading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <Icon className="h-4 w-4" />
      )}
    </Button>
  );
}
```

---

### Step 4: Implement SSE Client for Streaming

Create [`lib/ai/stream-client.ts`](../../lib/ai/stream-client.ts):

```typescript
// lib/ai/stream-client.ts
export interface StreamOptions {
  onChunk: (chunk: string) => void;
  onComplete: () => void;
  onError: (error: Error) => void;
}

export async function streamAI(
  endpoint: string,
  payload: object,
  options: StreamOptions
): Promise<void> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('Response body is not readable');
    }

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);

          if (data === '[DONE]') {
            options.onComplete();
            return;
          }

          try {
            const parsed = JSON.parse(data);
            if (parsed.chunk) {
              options.onChunk(parsed.chunk);
            }
          } catch (e) {
            console.error('Failed to parse SSE data:', data);
          }
        }
      }
    }
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      options.onError(new Error('timeout'));
    } else {
      options.onError(error as Error);
    }
  } finally {
    clearTimeout(timeoutId);
  }
}
```

---

### Step 5: Add Debounce Patterns

Use existing debounce utility from [`lib/stores/design/debounce-persist.ts`](../../lib/stores/design/debounce-persist.ts):

```typescript
// In component
import { debounce } from '@/lib/stores/design/debounce-persist';
import { useDraftStore } from '@/lib/stores/draft-store';

// 500ms debounce for state sync (FR-020)
const debouncedUpdate = debounce(
  (value: string) => {
    setMainContentEn(value);
    triggerAutoSave();
  },
  500
);

// 2000ms debounce for history snapshots (FR-012)
const debouncedSnapshot = debounce(() => {
  const store = useDraftStore.getState();
  store.setTopicData({ ...store.topicData });
}, 2000);

onChange={(e) => {
  debouncedUpdate(e.target.value);
  debouncedSnapshot();
}}
```

---

### Step 6: Implement BroadcastChannel for Cross-Tab Sync

Create [`lib/sync/draft-sync-channel.ts`](../../lib/sync/draft-sync-channel.ts):

```typescript
// lib/sync/draft-sync-channel.ts
export interface DraftSyncMessage {
  type: 'update' | 'conflict';
  timestamp: number;
  tabId: string;
  data?: any;
}

export class DraftSyncChannel {
  private channel: BroadcastChannel;
  private tabId: string;
  private listeners: Set<(message: DraftSyncMessage) => void> = new Set();

  constructor(channelName = 'draft-sync') {
    this.channel = new BroadcastChannel(channelName);
    this.tabId = crypto.randomUUID();

    this.channel.onmessage = (event) => {
      this.notifyListeners(event.data);
    };
  }

  private notifyListeners(message: DraftSyncMessage): void {
    if (message.tabId === this.tabId) return;
    this.listeners.forEach((listener) => listener(message));
  }

  broadcast(data: any): void {
    const message: DraftSyncMessage = {
      type: 'update',
      timestamp: Date.now(),
      tabId: this.tabId,
      data,
    };
    this.channel.postMessage(message);
  }

  subscribe(listener: (message: DraftSyncMessage) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  close(): void {
    this.channel.close();
  }
}
```

---

## Code Examples

### Basic AI Button Usage

```typescript
// In Studio field component
import { AIFieldButton } from '@/components/ai/AIFieldButton';
import { useAIStream } from '@/hooks/useAIStream';

function ContentField() {
  const { streamAI, isStreaming } = useAIStream('mainContentEn');
  const topicData = useDraftStore((state) => state.topicData);

  const handleGenerate = () => {
    streamAI('generate-content');
  };

  const handleRewrite = () => {
    streamAI('rewrite-content', topicData.mainContentEn);
  };

  return (
    <div className="relative">
      <Textarea
        value={topicData.mainContentEn}
        readOnly={isStreaming}
        onChange={(e) => setMainContentEn(e.target.value)}
      />
      <div className="absolute right-2 top-2">
        {!topicData.mainContentEn ? (
          <AIFieldButton
            operation="generate"
            isLoading={isStreaming}
            onClick={handleGenerate}
          />
        ) : (
          <AIFieldButton
            operation="rewrite"
            isLoading={isStreaming}
            onClick={handleRewrite}
          />
        )}
      </div>
    </div>
  );
}
```

### StreamSmoother with Hook

```typescript
// hooks/useStreamSmoother.ts
import { useState, useCallback, useRef } from 'react';
import { StreamSmoother } from '@/lib/ai/stream-smoother';

export function useStreamSmoother(charsPerMinute = 1500) {
  const [text, setText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const smootherRef = useRef<StreamSmoother | null>(null);

  const startStreaming = useCallback(() => {
    smootherRef.current?.reset();
    smootherRef.current = new StreamSmoother({
      charsPerMinute,
      onUpdate: setText,
      onComplete: (finalText) => {
        setText(finalText);
        setIsStreaming(false);
      },
    });
    setIsStreaming(true);
  }, [charsPerMinute]);

  const addChunk = useCallback((chunk: string) => {
    smootherRef.current?.addChunk(chunk);
  }, []);

  const stopStreaming = useCallback(() => {
    smootherRef.current?.stop();
    setIsStreaming(false);
  }, []);

  return { text, isStreaming, startStreaming, addChunk, stopStreaming };
}
```

### Keyboard Shortcuts

```typescript
// components/studio/KeyboardShortcuts.tsx
'use client';

import { useEffect } from 'react';
import { useDraftUndo } from '@/lib/stores/draft-store';
import { toast } from 'sonner';

export function KeyboardShortcuts() {
  const { undo, redo, pastStates, futureStates } = useDraftUndo();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+Z or Cmd+Z for undo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        if (pastStates.length > 0) {
          undo();
          toast.info('Undo', { duration: 1000 });
        } else {
          toast.info('Nothing to undo', { duration: 1000 });
        }
      }

      // Ctrl+Y or Ctrl+Shift+Z for redo
      if (
        (e.ctrlKey || e.metaKey) &&
        (e.key === 'y' || (e.key === 'z' && e.shiftKey))
      ) {
        e.preventDefault();
        if (futureStates.length > 0) {
          redo();
          toast.info('Redo', { duration: 1000 });
        } else {
          toast.info('Nothing to redo', { duration: 1000 });
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [undo, redo, pastStates.length, futureStates.length]);

  return null;
}
```

---

## Testing Commands

### Run Unit Tests

```bash
npm test
```

### Run Linting

```bash
npm run lint
```

### Type Checking

```bash
npm run type-check
```

---

## Implementation Checklist

- [ ] Install `zundo` dependency
- [ ] Update [`lib/stores/draft-store.ts`](../../lib/stores/draft-store.ts) with zundo middleware
- [ ] Create [`lib/ai/stream-smoother.ts`](../../lib/ai/stream-smoother.ts) class
- [ ] Create [`lib/ai/stream-client.ts`](../../lib/ai/stream-client.ts) for SSE handling
- [ ] Create [`components/ai/AIFieldButton.tsx`](../../components/ai/AIFieldButton.tsx) component
- [ ] Create [`components/studio/KeyboardShortcuts.tsx`](../../components/studio/KeyboardShortcuts.tsx) component
- [ ] Create [`lib/sync/draft-sync-channel.ts`](../../lib/sync/draft-sync-channel.ts) for cross-tab sync
- [ ] Create [`hooks/useAIStream.ts`](../../hooks/useAIStream.ts) React hook
- [ ] Create [`hooks/useStreamSmoother.ts`](../../hooks/useStreamSmoother.ts) React hook
- [ ] Update [`app/studio/page.tsx`](../../app/studio/page.tsx) with AI buttons
- [ ] Update SSE route at [`app/api/ai/stream/route.ts`](../../app/api/ai/stream/route.ts)
- [ ] Add unit tests for new components
- [ ] Add integration tests for undo/redo
- [ ] Test streaming speed (20-50ms per character)
- [ ] Test keyboard shortcuts (Ctrl+Z, Ctrl+Y)
- [ ] Test cross-tab sync with BroadcastChannel

---

## Important Implementation Notes

This section contains critical technical feedback to prevent bugs during implementation.

### ⚠️ 1. Mobile UI - Prevent Text Overlap with AI Buttons

**Issue**: AI buttons placed "inline on the right side" could cause text to wrap under buttons or be hidden on mobile screens.

**Solution**: Ensure Input/Textarea has sufficient padding-right (`pr-20` or `pr-16`) to reserve space for absolutely positioned button groups.

```typescript
// Add padding to prevent text overlap
<Textarea className="pr-20" /> {/* 80px for button group */}

// Mobile-specific adjustment
<Textarea className="pr-16 md:pr-20" /> {/* 64px on mobile, 80px on desktop */}
```

**See**: [`research.md`](research.md) §16.1 for details.

---

### ⚠️ 2. BroadcastChannel - Prevent Infinite Loop

**Issue**: Infinite loop risk: Tab A sends → Tab B receives → Tab B updates store → Tab B broadcasts → Tab A receives...

**Solution**: Use `silent: true` flag or similar logic when receiving cross-tab updates to prevent re-broadcasting.

```typescript
// When receiving cross-tab update, update store without broadcasting
syncChannel.subscribe((message) => {
  if (message.type === 'update' && message.data) {
    useDraftStore.setState({ topicData: message.data }, true); // silent flag
  }
});

// In persist middleware - only broadcast if not from sync
onRehydrateStorage: () => (state) => {
  state.subscribe((newState, oldState) => {
    if (oldState?._syncSource) return; // Skip broadcast from external updates
    syncChannel.broadcast(newState.topicData);
  });
}
```

**See**: [`research.md`](research.md) §16.2 for details.

---

### ⚠️ 3. Performance - Use Local State for Immediate UI Updates

**Issue**: Using debounce 500ms with direct Store binding could cause lag, especially with zundo middleware.

**Solution**: Use local state (React `useState`) for immediate display (<16ms latency), then push to Store via debounce.

```typescript
function ContentField() {
  const [localValue, setLocalValue] = useState(''); // Immediate UI
  const storeValue = useDraftStore((s) => s.topicData.mainContentEn);
  
  useEffect(() => {
    setLocalValue(storeValue); // Sync store -> local on mount/external changes
  }, [storeValue]);

  const handleChange = (value: string) => {
    setLocalValue(value); // Immediate UI update (~16ms)
    debouncedUpdate(value); // Debounced store sync (500ms)
  };

  return <Textarea value={localValue} onChange={(e) => handleChange(e.target.value)} />;
}
```

**Performance Target**: Input latency <16ms (60fps). Test thoroughly on low-end devices.

**See**: [`research.md`](research.md) §16.3 for details.

---

## References

- **Specification**: [`spec.md`](spec.md)
- **Data Model**: [`data-model.md`](data-model.md)
- **Research**: [`research.md`](research.md)
- **API Contracts**: [`contracts/README.md`](contracts/README.md)
- **Existing Store**: [`lib/stores/draft-store.ts`](../../lib/stores/draft-store.ts)
