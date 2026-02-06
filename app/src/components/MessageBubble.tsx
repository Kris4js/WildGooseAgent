import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Message } from "../hooks/useChat";
import { InlineToolCall } from "./InlineToolCall";
import "./MessageBubble.css";

interface MessageBubbleProps {
  message: Message;
}

function formatTime(timestamp: number): string {
  const date = new Date(timestamp);
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();

  if (isToday) {
    // Show only time for today's messages
    return date.toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  } else {
    // Show date and time for older messages
    return date.toLocaleString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
}

export function MessageBubble({ message }: MessageBubbleProps) {
  return (
    <div className={`message-bubble message-bubble--${message.role}`}>
      <div className="message-content">
        {/* Show tool calls inline before the answer */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="message-tool-calls">
            {message.toolCalls.map((tc) => (
              <InlineToolCall key={tc.id} toolCall={tc} />
            ))}
          </div>
        )}

        {/* Show the message content (streaming or final) */}
        {message.role === "assistant" ? (
          <>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
            {message.isStreaming && !message.content && (
              <span className="streaming-indicator">正在生成回复...</span>
            )}
          </>
        ) : (
          message.content
        )}
      </div>
      <div className="message-timestamp">{formatTime(message.timestamp)}</div>
    </div>
  );
}
