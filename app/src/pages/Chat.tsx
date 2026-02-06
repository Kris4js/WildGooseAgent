import { useState, useRef, useEffect } from "react";
import { useChat } from "../hooks/useChat";
import { MessageBubble } from "../components/MessageBubble";
import { ThinkingBlock } from "../components/ThinkingBlock";
import { SessionList } from "../components/SessionList";
import "./Chat.css";

export function Chat() {
  const [input, setInput] = useState("");
  const [showSessionList, setShowSessionList] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const {
    messages,
    isLoading,
    currentThinking,
    currentToolCalls,
    sendMessage,
    clearMessages,
    switchSession,
    sessionKey,
  } = useChat();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentThinking, currentToolCalls]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    sendMessage(input.trim());
    setInput("");
  };

  const handleNewSession = () => {
    clearMessages();
  };

  const handleSessionSelect = (newSessionKey: string) => {
    if (newSessionKey !== sessionKey) {
      switchSession(newSessionKey);
    }
  };

  const handleDeleteSession = (deletedKey: string) => {
    // If current session is deleted, create a new one
    if (deletedKey === sessionKey) {
      clearMessages();
    }
  };

  return (
    <div className="chat-page">
      <div className="chat-main">
        <div className="chat-messages">
          {messages.map((msg) => (
            <div key={msg.id}>
              {/* User message */}
              {msg.role === "user" && <MessageBubble message={msg} />}

              {/* Assistant: thinking + answer with inline tools */}
              {msg.role === "assistant" && (
                <>
                  {msg.thinking && (
                    <ThinkingBlock content={msg.thinking} isLoading={false} />
                  )}
                  <MessageBubble message={msg} />
                </>
              )}
            </div>
          ))}

          {/* Live streaming: thinking only (tools shown in message bubble) */}
          {isLoading && currentThinking && (
            <ThinkingBlock content={currentThinking} isLoading={true} />
          )}

          <div ref={messagesEndRef} />
        </div>

        <form className="chat-input-form" onSubmit={handleSubmit}>
          <input
            type="text"
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入消息..."
            disabled={isLoading}
          />
          <button type="submit" className="chat-submit" disabled={isLoading}>
            {isLoading ? "发送中..." : "发送"}
          </button>
        </form>
      </div>

      {showSessionList && (
        <SessionList
          currentSessionKey={sessionKey}
          onSessionSelect={handleSessionSelect}
          onNewSession={handleNewSession}
          onDeleteSession={handleDeleteSession}
        />
      )}

      <button
        className="toggle-sessions-btn"
        onClick={() => setShowSessionList(!showSessionList)}
        title={showSessionList ? "隐藏会话列表" : "显示会话列表"}
      >
        {showSessionList ? "›" : "‹"}
      </button>
    </div>
  );
}
