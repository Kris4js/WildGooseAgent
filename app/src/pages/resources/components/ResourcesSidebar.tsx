import { shortText } from "../selectors";
import type { Tab, ToolGroupInfo } from "../types";

interface ResourcesSidebarProps {
  tab: Tab;
  search: string;
  onSearchChange: (value: string) => void;
  onTabChange: (tab: Tab) => void;
  toolGroups: ToolGroupInfo[];
  activeGroupId: string | null;
  onGroupSelect: (group: ToolGroupInfo) => void;
  toolCount: number;
  skillCount: number;
}

export function ResourcesSidebar({
  tab,
  search,
  onSearchChange,
  onTabChange,
  toolGroups,
  activeGroupId,
  onGroupSelect,
  toolCount,
  skillCount,
}: ResourcesSidebarProps) {
  return (
    <div className="resources-sidebar">
      <div className="resources-sidebar-top">
        <input
          type="text"
          className="resources-search"
          placeholder="搜索工具或技能..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
        />

        <div className="resources-tabs">
          <button
            className={`resources-tab ${tab === "tools" ? "active" : ""}`}
            onClick={() => onTabChange("tools")}
          >
            Tools ({toolCount})
          </button>
          <button
            className={`resources-tab ${tab === "skills" ? "active" : ""}`}
            onClick={() => onTabChange("skills")}
          >
            Skills ({skillCount})
          </button>
        </div>
      </div>

      <div className="resources-nav">
        {tab === "tools" &&
          toolGroups.map((group) => (
            <button
              key={group.id}
              className={`resources-nav-item ${
                activeGroupId === group.id ? "active" : ""
              }`}
              onClick={() => onGroupSelect(group)}
            >
              <div className="resources-nav-title">{group.name}</div>
              <div className="resources-nav-desc">
                {shortText(group.description, 80)}
              </div>
            </button>
          ))}

        {tab === "skills" && <div className="resources-nav-empty">技能列表</div>}
      </div>
    </div>
  );
}
