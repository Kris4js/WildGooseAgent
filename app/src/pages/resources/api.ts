import type {
  SkillDetail,
  SkillInfo,
  ToolDetail,
  ToolGroupInfo,
} from "./types";

const API_BASE = "http://127.0.0.1:8000";

interface ToolsResponse {
  groups: ToolGroupInfo[];
}

export const fetchToolGroups = async (): Promise<ToolGroupInfo[]> => {
  const response = await fetch(`${API_BASE}/api/tools`);
  if (!response.ok) {
    throw new Error(`Failed to load tools: ${response.status}`);
  }
  const data = (await response.json()) as ToolsResponse;
  return data.groups ?? [];
};

export const fetchSkills = async (): Promise<SkillInfo[]> => {
  const response = await fetch(`${API_BASE}/api/skills`);
  if (!response.ok) {
    throw new Error(`Failed to load skills: ${response.status}`);
  }
  return (await response.json()) as SkillInfo[];
};

export const fetchToolDetail = async (name: string): Promise<ToolDetail> => {
  const response = await fetch(`${API_BASE}/api/tools/${name}`);
  if (!response.ok) {
    throw new Error(`Failed to load tool detail: ${response.status}`);
  }
  return (await response.json()) as ToolDetail;
};

export const fetchSkillDetail = async (name: string): Promise<SkillDetail> => {
  const response = await fetch(`${API_BASE}/api/skills/${name}`);
  if (!response.ok) {
    throw new Error(`Failed to load skill detail: ${response.status}`);
  }
  return (await response.json()) as SkillDetail;
};
