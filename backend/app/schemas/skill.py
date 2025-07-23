# app/schemas/skill.py
from pydantic import BaseModel
from typing import Optional

class SkillBase(BaseModel):
    name: str

class SkillCreate(SkillBase):
    pass

class SkillUpdate(SkillBase):
    pass

class Skill(SkillBase):
    id: int

    class Config:
        from_attributes = True