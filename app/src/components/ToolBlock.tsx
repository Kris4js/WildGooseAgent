import { useState } from "react";
import type { ToolCall } from "../hooks/useChat";
import "./ToolBlock.css";

interface ToolBlockProps {
  toolCall: ToolCall;
}

export function ToolBlock({ toolCall }: ToolBlockProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const statusIcon =
    toolCall.status === "running"
      ? "⏳"
      : toolCall.status === "done"
        ? "✅"
        : "❌";

  return (
    <div className="tool-bubble">
      <div className={`tool-block tool-block--${toolCall.status}`}>
        <div className="tool-header" onClick={() => setIsExpanded(!isExpanded)}>
          <span className="tool-icon">🔧</span>
          <span className="tool-name">{toolCall.tool}</span>
          <span className="tool-status">{statusIcon}</span>
          {toolCall.duration_ms && (
            <span className="tool-duration">{toolCall.duration_ms}ms</span>
          )}
          <span className="tool-toggle">{isExpanded ? "▼" : "▶"}</span>
        </div>
        {isExpanded && (
          <div className="tool-content">
            <div className="tool-args">
              <strong>参数:</strong>
              <pre>{JSON.stringify(toolCall.args, null, 2)}</pre>
            </div>
            {toolCall.result && (
              <div className="tool-result">
                <strong>结果:</strong>
                <pre>{toolCall.result}</pre>
              </div>
            )}
            {toolCall.error && (
              <div className="tool-error">
                <strong>错误:</strong>
                <pre>{toolCall.error}</pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
