import { useCallback, useEffect, useMemo, useState } from "react";
import "./Resources.css";
import {
  fetchSkillDetail,
  fetchSkills,
  fetchToolDetail,
  fetchToolGroups,
} from "./resources/api";
import {
  filterSkills,
  filterTools,
  totalToolCount,
} from "./resources/selectors";
import { ResourcesListColumn } from "./resources/components/ResourcesListColumn";
import { ResourcesPreview } from "./resources/components/ResourcesPreview";
import { ResourcesSidebar } from "./resources/components/ResourcesSidebar";
import type {
  GroupDetail,
  SelectionState,
  SkillInfo,
  Tab,
  ToolGroupInfo,
} from "./resources/types";

export function Resources() {
  const [tab, setTab] = useState<Tab>("tools");
  const [toolGroups, setToolGroups] = useState<ToolGroupInfo[]>([]);
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [activeGroupId, setActiveGroupId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [selection, setSelection] = useState<SelectionState>({
    tool: null,
    skill: null,
    group: null,
  });

  const setGroupSelection = useCallback((group: GroupDetail) => {
    setSelection({ tool: null, skill: null, group });
  }, []);

  const setToolSelection = useCallback((tool: SelectionState["tool"]) => {
    setSelection({ tool, skill: null, group: null });
  }, []);

  const setSkillSelection = useCallback((skill: SelectionState["skill"]) => {
    setSelection({ tool: null, skill, group: null });
  }, []);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const [groups, skillList] = await Promise.all([
          fetchToolGroups(),
          fetchSkills(),
        ]);
        if (cancelled) return;

        setToolGroups(groups);
        setSkills(skillList);

        if (groups.length > 0) {
          const first = groups[0];
          setActiveGroupId(first.id);
          setGroupSelection({
            id: first.id,
            name: first.name,
            description: first.description,
          });
        }
      } catch (error) {
        console.error(error);
      }
    };

    load();

    return () => {
      cancelled = true;
    };
  }, [setGroupSelection]);

  useEffect(() => {
    if (tab === "skills") {
      setSelection((prev) => ({ ...prev, tool: null, group: null }));
      setActiveGroupId(null);
      return;
    }

    setSelection((prev) => ({ ...prev, skill: null }));

    if (!activeGroupId && toolGroups.length > 0) {
      const first = toolGroups[0];
      setActiveGroupId(first.id);
      setGroupSelection({
        id: first.id,
        name: first.name,
        description: first.description,
      });
    }
  }, [tab, activeGroupId, setGroupSelection, toolGroups]);

  const visibleTools = useMemo(
    () => filterTools(toolGroups, search, activeGroupId),
    [toolGroups, search, activeGroupId]
  );
  const visibleSkills = useMemo(
    () => filterSkills(skills, search),
    [skills, search]
  );
  const toolCount = useMemo(() => totalToolCount(toolGroups), [toolGroups]);

  const handleSelectGroup = useCallback(
    (group: ToolGroupInfo) => {
      setActiveGroupId(group.id);
      setGroupSelection({
        id: group.id,
        name: group.name,
        description: group.description,
      });
    },
    [setGroupSelection]
  );

  const handleSelectTool = useCallback(
    async (name: string) => {
      try {
        const tool = await fetchToolDetail(name);
        setToolSelection(tool);
      } catch (error) {
        console.error(error);
      }
    },
    [setToolSelection]
  );

  const handleSelectSkill = useCallback(
    async (name: string) => {
      try {
        const skill = await fetchSkillDetail(name);
        setSkillSelection(skill);
      } catch (error) {
        console.error(error);
      }
    },
    [setSkillSelection]
  );

  return (
    <div className="resources-page">
      <ResourcesSidebar
        tab={tab}
        search={search}
        onSearchChange={setSearch}
        onTabChange={setTab}
        toolGroups={toolGroups}
        activeGroupId={activeGroupId}
        onGroupSelect={handleSelectGroup}
        toolCount={toolCount}
        skillCount={skills.length}
      />

      <ResourcesListColumn
        tab={tab}
        search={search}
        toolCount={toolCount}
        skillsCount={skills.length}
        visibleTools={visibleTools}
        visibleSkills={visibleSkills}
        selectedToolName={selection.tool?.name ?? null}
        selectedSkillName={selection.skill?.name ?? null}
        onToolSelect={handleSelectTool}
        onSkillSelect={handleSelectSkill}
      />

      <ResourcesPreview selection={selection} />
    </div>
  );
}
