export interface ToolInfo {
  name: string;
  displayName: string;
  description: string;
}

export interface ToolGroupInfo {
  id: string;
  name: string;
  description: string;
  tools: ToolInfo[];
}

export interface GroupDetail {
  id: string;
  name: string;
  description: string;
}

export interface SkillInfo {
  name: string;
  description: string;
  source: string;
}

export interface ToolDetail {
  name: string;
  displayName: string;
  description: string;
  parameters: Record<string, unknown> | null;
}

export interface SkillDetail {
  name: string;
  description: string;
  source: string;
  instructions: string;
}

export type Tab = "tools" | "skills";

export interface SelectionState {
  tool: ToolDetail | null;
  skill: SkillDetail | null;
  group: GroupDetail | null;
}
