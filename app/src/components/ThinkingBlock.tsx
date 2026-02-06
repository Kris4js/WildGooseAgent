import { useState } from "react";
import "./ThinkingBlock.css";

interface ThinkingBlockProps {
  content: string;
  isLoading?: boolean;
}

export function ThinkingBlock({ content, isLoading = false }: ThinkingBlockProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="thinking-bubble">
      <div className={`thinking-block ${isLoading ? "thinking-block--loading" : ""}`}>
        <div
          className="thinking-header"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <span className="thinking-icon">💭</span>
          <span className="thinking-label">
            {isLoading ? "思考中..." : "思考"}
          </span>
          <span className="thinking-toggle">{isExpanded ? "▼" : "▶"}</span>
        </div>
        {isExpanded && content && (
          <div className="thinking-content">{content}</div>
        )}
      </div>
    </div>
  );
}
