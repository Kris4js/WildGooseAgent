import { useState, useCallback, useEffect, useRef } from "react";

const SESSION_KEY_STORAGE = "wild-goose-session-key";

export interface ChatEvent {
  type:
    | "thinking"
    | "tool_start"
    | "tool_end"
    | "tool_error"
    | "tool_limit"
    | "answer_start"
    | "answer_chunk"
    | "done";
  message?: string;
  tool?: string;
  args?: Record<string, unknown>;
  result?: string;
  duration_ms?: number;
  error?: string;
  answer?: string;
  chunk?: string;
  iterations?: number;
  tool_calls?: { tool: string; args: Record<string, unknown> }[];
}

function toChunkText(chunk: unknown): string {
  if (typeof chunk === "string") return chunk;
  if (Array.isArray(chunk)) {
    return chunk
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "text" in item) {
          const text = (item as { text?: unknown }).text;
          return typeof text === "string" ? text : "";
        }
        return "";
      })
      .join("");
  }
  return "";
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  thinking?: string;
  toolCalls?: ToolCall[];
  isStreaming?: boolean;
  timestamp: number;
}

export interface ToolCall {
  id: string;
  tool: string;
  args: Record<string, unknown>;
  result?: string;
  error?: string;
  duration_ms?: number;
  status: "running" | "done" | "error";
}

interface SessionUiState {
  messages: Message[];
  isLoading: boolean;
  currentThinking: string | null;
  currentToolCalls: ToolCall[];
}

const API_BASE = "http://127.0.0.1:8000";

const createEmptySessionState = (): SessionUiState => ({
  messages: [],
  isLoading: false,
  currentThinking: null,
  currentToolCalls: [],
});

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentThinking, setCurrentThinking] = useState<string | null>(null);
  const [currentToolCalls, setCurrentToolCalls] = useState<ToolCall[]>([]);
  const [sessionKey, setSessionKey] = useState<string>(() => {
    const stored = localStorage.getItem(SESSION_KEY_STORAGE);
    return stored || crypto.randomUUID();
  });

  const sessionStateRef = useRef<Record<string, SessionUiState>>({});
  const activeSessionRef = useRef(sessionKey);
  const streamControllersRef = useRef<Record<string, AbortController>>({});
  const historyLoadRef = useRef(0);

  const ensureSessionState = useCallback((key: string): SessionUiState => {
    if (!sessionStateRef.current[key]) {
      sessionStateRef.current[key] = createEmptySessionState();
    }
    return sessionStateRef.current[key];
  }, []);

  const syncVisibleState = useCallback(
    (key: string) => {
      const state = ensureSessionState(key);
      setMessages(state.messages);
      setIsLoading(state.isLoading);
      setCurrentThinking(state.currentThinking);
      setCurrentToolCalls(state.currentToolCalls);
    },
    [ensureSessionState]
  );

  const updateSessionState = useCallback(
    (key: string, updater: (prev: SessionUiState) => SessionUiState) => {
      const prev = ensureSessionState(key);
      const next = updater(prev);
      sessionStateRef.current[key] = next;
      if (activeSessionRef.current === key) {
        setMessages(next.messages);
        setIsLoading(next.isLoading);
        setCurrentThinking(next.currentThinking);
        setCurrentToolCalls(next.currentToolCalls);
      }
    },
    [ensureSessionState]
  );

  useEffect(() => {
    activeSessionRef.current = sessionKey;
    syncVisibleState(sessionKey);

    const controller = new AbortController();
    const loadId = ++historyLoadRef.current;

    const loadHistory = async () => {
      try {
        const response = await fetch(
          `${API_BASE}/api/sessions/${encodeURIComponent(sessionKey)}`,
          {
            cache: "no-store",
            signal: controller.signal,
          }
        );
        if (!response.ok) return;

        const data = await response.json();
        if (controller.signal.aborted || historyLoadRef.current !== loadId) {
          return;
        }

        const loadedMessages: Message[] = (data.messages || []).map((msg: any) => ({
          id: crypto.randomUUID(),
          role:
            msg.role === "assistant" || msg.role === "ai" || msg.role === "model"
              ? "assistant"
              : "user",
          content: msg.content,
          timestamp: msg.timestamp || Date.now(),
          toolCalls: msg.tool_calls?.map((tc: any) => ({
            id: tc.id || crypto.randomUUID(),
            tool: tc.tool,
            args: tc.args,
            result: tc.result,
            status: tc.result ? "done" : "running",
          })),
        }));

        updateSessionState(sessionKey, (prev) => {
          if (prev.isLoading || prev.messages.length > 0) {
            return prev;
          }
          return { ...prev, messages: loadedMessages };
        });
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          console.error("Failed to load session history:", error);
        }
      }
    };

    localStorage.setItem(SESSION_KEY_STORAGE, sessionKey);
    loadHistory();
    return () => controller.abort();
  }, [sessionKey, syncVisibleState, updateSessionState]);

  const sendMessage = useCallback(
    async (content: string) => {
      const requestSessionKey = sessionKey;
      const existingController = streamControllersRef.current[requestSessionKey];
      if (existingController) {
        existingController.abort();
      }

      const controller = new AbortController();
      streamControllersRef.current[requestSessionKey] = controller;

      const assistantMessageId = crypto.randomUUID();
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content,
        timestamp: Date.now(),
      };
      const emptyAssistantMessage: Message = {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        timestamp: Date.now(),
        isStreaming: true,
      };

      updateSessionState(requestSessionKey, (prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage, emptyAssistantMessage],
        isLoading: true,
        currentThinking: null,
        currentToolCalls: [],
      }));

      let localThinking: string | null = null;
      let localToolCalls: ToolCall[] = [];

      try {
        const response = await fetch(`${API_BASE}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: content, session_key: requestSessionKey }),
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let streamedContent = "";
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done || controller.signal.aborted) break;

          buffer += decoder.decode(value, { stream: true });
          buffer = buffer.replace(/\r\n/g, "\n");

          let separatorIndex = buffer.indexOf("\n\n");
          while (separatorIndex !== -1) {
            const rawEvent = buffer.slice(0, separatorIndex);
            buffer = buffer.slice(separatorIndex + 2);

            const dataLines = rawEvent
              .split("\n")
              .filter((line) => line.startsWith("data:"));
            if (dataLines.length === 0) {
              separatorIndex = buffer.indexOf("\n\n");
              continue;
            }

            const jsonStr = dataLines
              .map((line) => line.replace(/^data:\s?/, ""))
              .join("\n")
              .trim();
            if (!jsonStr) {
              separatorIndex = buffer.indexOf("\n\n");
              continue;
            }

            try {
              const event: ChatEvent = JSON.parse(jsonStr);
              if (controller.signal.aborted) break;

              switch (event.type) {
                case "thinking":
                  localThinking = event.message || "";
                  updateSessionState(requestSessionKey, (prev) => ({
                    ...prev,
                    currentThinking: localThinking,
                  }));
                  break;

                case "tool_start": {
                  const newToolCall: ToolCall = {
                    id: crypto.randomUUID(),
                    tool: event.tool || "",
                    args: event.args || {},
                    status: "running",
                  };
                  localToolCalls = [...localToolCalls, newToolCall];
                  updateSessionState(requestSessionKey, (prev) => ({
                    ...prev,
                    currentToolCalls: localToolCalls,
                  }));
                  break;
                }

                case "tool_end":
                  localToolCalls = localToolCalls.map((tc) =>
                    tc.tool === event.tool && tc.status === "running"
                      ? {
                          ...tc,
                          result: event.result,
                          duration_ms: event.duration_ms,
                          status: "done" as const,
                        }
                      : tc
                  );
                  updateSessionState(requestSessionKey, (prev) => ({
                    ...prev,
                    currentToolCalls: localToolCalls,
                    messages: prev.messages.map((m) =>
                      m.id === assistantMessageId
                        ? { ...m, toolCalls: [...localToolCalls] }
                        : m
                    ),
                  }));
                  break;

                case "tool_error":
                  localToolCalls = localToolCalls.map((tc) =>
                    tc.tool === event.tool && tc.status === "running"
                      ? { ...tc, error: event.error, status: "error" as const }
                      : tc
                  );
                  updateSessionState(requestSessionKey, (prev) => ({
                    ...prev,
                    currentToolCalls: localToolCalls,
                    messages: prev.messages.map((m) =>
                      m.id === assistantMessageId
                        ? { ...m, toolCalls: [...localToolCalls] }
                        : m
                    ),
                  }));
                  break;

                case "answer_start":
                  streamedContent = "";
                  updateSessionState(requestSessionKey, (prev) => ({
                    ...prev,
                    messages: prev.messages.map((m) =>
                      m.id === assistantMessageId
                        ? {
                            ...m,
                            thinking: localThinking || undefined,
                            toolCalls: [...localToolCalls],
                            isStreaming: true,
                          }
                        : m
                    ),
                  }));
                  break;

                case "answer_chunk":
                  {
                    const chunkText = toChunkText(event.chunk);
                    if (!chunkText) break;
                    streamedContent += chunkText;
                    updateSessionState(requestSessionKey, (prev) => ({
                      ...prev,
                      messages: prev.messages.map((m) =>
                        m.id === assistantMessageId
                          ? { ...m, content: streamedContent }
                          : m
                      ),
                    }));
                  }
                  break;

                case "done":
                  updateSessionState(requestSessionKey, (prev) => ({
                    ...prev,
                    messages: prev.messages.map((m) =>
                      m.id === assistantMessageId
                        ? {
                            ...m,
                            content: event.answer || "",
                            toolCalls: localToolCalls,
                            isStreaming: false,
                          }
                        : m
                    ),
                  }));
                  break;
              }
            } catch {
              console.error("Failed to parse SSE event:", jsonStr);
            }

            separatorIndex = buffer.indexOf("\n\n");
          }
        }
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          console.error("Chat error:", error);
          updateSessionState(requestSessionKey, (prev) => ({
            ...prev,
            messages: [
              ...prev.messages,
              {
                id: crypto.randomUUID(),
                role: "assistant",
                content: `Error: ${
                  error instanceof Error ? error.message : "Unknown error"
                }`,
                timestamp: Date.now(),
              },
            ],
          }));
        }
      } finally {
        if (streamControllersRef.current[requestSessionKey] === controller) {
          delete streamControllersRef.current[requestSessionKey];
        }
        updateSessionState(requestSessionKey, (prev) => ({
          ...prev,
          isLoading: false,
          currentThinking: null,
          currentToolCalls: [],
        }));
      }
    },
    [sessionKey, updateSessionState]
  );

  const clearMessages = useCallback(() => {
    const current = activeSessionRef.current;
    const controller = streamControllersRef.current[current];
    if (controller) {
      controller.abort();
      delete streamControllersRef.current[current];
    }
    sessionStateRef.current[current] = createEmptySessionState();

    const newSessionKey = crypto.randomUUID();
    ensureSessionState(newSessionKey);
    activeSessionRef.current = newSessionKey;
    syncVisibleState(newSessionKey);
    setSessionKey(newSessionKey);
    localStorage.setItem(SESSION_KEY_STORAGE, newSessionKey);
  }, [ensureSessionState, syncVisibleState]);

  const switchSession = useCallback(
    (newSessionKey: string) => {
      activeSessionRef.current = newSessionKey;
      ensureSessionState(newSessionKey);
      syncVisibleState(newSessionKey);
      setSessionKey(newSessionKey);
      localStorage.setItem(SESSION_KEY_STORAGE, newSessionKey);
    },
    [ensureSessionState, syncVisibleState]
  );

  return {
    messages,
    isLoading,
    currentThinking,
    currentToolCalls,
    sendMessage,
    clearMessages,
    switchSession,
    sessionKey,
  };
}
