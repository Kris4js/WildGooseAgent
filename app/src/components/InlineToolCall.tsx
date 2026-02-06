import { useState } from "react";
import type { ToolCall } from "../hooks/useChat";
import "./InlineToolCall.css";

interface InlineToolCallProps {
  toolCall: ToolCall;
}

function formatToolName(tool: string): string {
  // Remove _tool suffix and convert to uppercase
  const name = tool.replace(/_tool$/, "");
  return name.toUpperCase();
}

export function InlineToolCall({ toolCall }: InlineToolCallProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="inline-tool-call">
      <button
        className="inline-tool-call-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="inline-tool-name">{formatToolName(toolCall.tool)}</span>
        <span className="inline-tool-toggle">{isExpanded ? "▼" : "▶"}</span>
      </button>

      {isExpanded && (
        <div className="inline-tool-details">
          <div className="inline-tool-section">
            <strong>参数:</strong>
            <pre>{JSON.stringify(toolCall.args, null, 2)}</pre>
          </div>

          {toolCall.result && (
            <div className="inline-tool-section">
              <strong>结果:</strong>
              <pre>{toolCall.result}</pre>
            </div>
          )}

          {toolCall.error && (
            <div className="inline-tool-section inline-tool-error">
              <strong>错误:</strong>
              <pre>{toolCall.error}</pre>
            </div>
          )}

          {toolCall.duration_ms && (
            <div className="inline-tool-duration">
              用时: {toolCall.duration_ms}ms
            </div>
          )}
        </div>
      )}
    </div>
  );
}
