from pydantic import BaseModel
from typing import List, Literal

class PromptVariations(BaseModel):
    developer: str
    designer: str
    copywriter: str

class ScreenDetail(BaseModel):
    screen_name: str
    complexity: Literal["Low", "Medium", "High"]
    notes: str
    prompts: PromptVariations

class PromptGenerationOutput(BaseModel):
    project_name: str
    screens: List[ScreenDetail]