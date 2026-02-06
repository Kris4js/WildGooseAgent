"""Skills API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.skills import discover_skills, get_skill

router = APIRouter()


class SkillInfo(BaseModel):
    name: str
    description: str
    source: str


class SkillDetail(BaseModel):
    name: str
    description: str
    source: str
    instructions: str


@router.get("/skills", response_model=list[SkillInfo])
async def list_skills():
    """Get list of all available skills."""
    skills = discover_skills()
    return [
        SkillInfo(name=s.name, description=s.description, source=s.source.value)
        for s in skills
    ]


@router.get("/skills/{name}", response_model=SkillDetail)
async def get_skill_detail(name: str):
    """Get skill detail by name including full instructions."""
    skill = get_skill(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")

    return SkillDetail(
        name=skill.name,
        description=skill.description,
        source=skill.source.value,
        instructions=skill.instructions,
    )
