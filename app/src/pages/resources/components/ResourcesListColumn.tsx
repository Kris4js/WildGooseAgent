import type { SkillInfo, Tab, ToolInfo } from "../types";

interface ResourcesListColumnProps {
  tab: Tab;
  search: string;
  toolCount: number;
  skillsCount: number;
  visibleTools: ToolInfo[];
  visibleSkills: SkillInfo[];
  selectedToolName: string | null;
  selectedSkillName: string | null;
  onToolSelect: (name: string) => void;
  onSkillSelect: (name: string) => void;
}

export function ResourcesListColumn({
  tab,
  search,
  toolCount,
  skillsCount,
  visibleTools,
  visibleSkills,
  selectedToolName,
  selectedSkillName,
  onToolSelect,
  onSkillSelect,
}: ResourcesListColumnProps) {
  return (
    <div className="resources-list-column">
      <div className="resources-list-header">
        {tab === "tools" ? (
          <>
            <div className="resources-list-title">{search ? "搜索结果" : "工具列表"}</div>
            <div className="resources-list-subtitle">
              {search ? `匹配 ${visibleTools.length} 个工具` : `共 ${toolCount} 个工具`}
            </div>
          </>
        ) : (
          <>
            <div className="resources-list-title">Skills</div>
            <div className="resources-list-subtitle">当前共 {skillsCount} 个技能</div>
          </>
        )}
      </div>

      <div className="resources-list">
        {tab === "tools" &&
          visibleTools.map((tool) => (
            <div
              key={tool.name}
              className={`resources-item ${selectedToolName === tool.name ? "active" : ""}`}
              onClick={() => onToolSelect(tool.name)}
            >
              <div className="resources-item-name">{tool.displayName}</div>
            </div>
          ))}

        {tab === "skills" &&
          visibleSkills.map((skill) => (
            <div
              key={skill.name}
              className={`resources-item ${selectedSkillName === skill.name ? "active" : ""}`}
              onClick={() => onSkillSelect(skill.name)}
            >
              <div className="resources-item-name">⚡ {skill.name}</div>
              <div className="resources-item-desc">{skill.description}</div>
              <div className="resources-item-source">{skill.source}</div>
            </div>
          ))}

        {tab === "tools" && visibleTools.length === 0 && (
          <div className="resources-list-empty">没有匹配的工具</div>
        )}
        {tab === "skills" && visibleSkills.length === 0 && (
          <div className="resources-list-empty">没有匹配的技能</div>
        )}
      </div>
    </div>
  );
}
