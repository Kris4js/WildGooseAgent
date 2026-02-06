import type { SkillInfo, ToolGroupInfo, ToolInfo } from "./types";

export const shortText = (text: string, maxLen: number): string => {
  if (!text) return "";
  const trimmed = text.replace(/\s+/g, " ").trim();
  return trimmed.length > maxLen ? `${trimmed.slice(0, maxLen)}...` : trimmed;
};

export const totalToolCount = (groups: ToolGroupInfo[]): number =>
  groups.reduce((sum, group) => sum + group.tools.length, 0);

export const findActiveGroup = (
  groups: ToolGroupInfo[],
  activeGroupId: string | null
): ToolGroupInfo | null => {
  if (!groups.length) return null;
  return groups.find((group) => group.id === activeGroupId) ?? groups[0];
};

export const filterTools = (
  groups: ToolGroupInfo[],
  search: string,
  activeGroupId: string | null
): ToolInfo[] => {
  const normalized = search.trim().toLowerCase();
  if (!normalized) {
    const activeGroup = findActiveGroup(groups, activeGroupId);
    return activeGroup?.tools ?? [];
  }

  return groups.flatMap((group) =>
    group.tools.filter(
      (tool) =>
        tool.displayName.toLowerCase().includes(normalized) ||
        tool.description.toLowerCase().includes(normalized)
    )
  );
};

export const filterSkills = (skills: SkillInfo[], search: string): SkillInfo[] => {
  const normalized = search.trim().toLowerCase();
  if (!normalized) return skills;

  return skills.filter(
    (skill) =>
      skill.name.toLowerCase().includes(normalized) ||
      skill.description.toLowerCase().includes(normalized)
  );
};
