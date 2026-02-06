import ReactMarkdown from "react-markdown";
import type { SelectionState } from "../types";

interface ResourcesPreviewProps {
  selection: SelectionState;
}

export function ResourcesPreview({ selection }: ResourcesPreviewProps) {
  return (
    <div className="resources-preview">
      {selection.group && !selection.tool && !selection.skill && (
        <div className="preview-content">
          <h2>📁 {selection.group.name}</h2>
          <div className="preview-section">
            <h3>描述</h3>
            <ReactMarkdown>{selection.group.description}</ReactMarkdown>
          </div>
        </div>
      )}

      {selection.tool && (
        <div className="preview-content">
          <h2>🔧 {selection.tool.displayName}</h2>
          <div className="preview-section">
            <h3>描述</h3>
            <ReactMarkdown>{selection.tool.description}</ReactMarkdown>
          </div>
          {selection.tool.parameters && (
            <div className="preview-section">
              <h3>参数</h3>
              <pre>{JSON.stringify(selection.tool.parameters, null, 2)}</pre>
            </div>
          )}
        </div>
      )}

      {selection.skill && (
        <div className="preview-content">
          <h2>⚡ {selection.skill.name}</h2>
          <div className="preview-meta">
            来源: <span className="preview-source">{selection.skill.source}</span>
          </div>
          <div className="preview-section">
            <h3>描述</h3>
            <ReactMarkdown>{selection.skill.description}</ReactMarkdown>
          </div>
          <div className="preview-section">
            <h3>说明</h3>
            <div className="preview-instructions">
              <ReactMarkdown>{selection.skill.instructions}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}

      {!selection.tool && !selection.skill && !selection.group && (
        <div className="preview-empty">选择一个 Tool、Skill 或工具组查看详情</div>
      )}
    </div>
  );
}
