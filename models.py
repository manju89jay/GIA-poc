from typing import List, Optional
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    root: str
    old_header: str
    new_header: str
    backend: str = "openai"
    model: str = "gpt-5"
    temperature: float = 0.0
    return_zip: bool = True


class FileOut(BaseModel):
    name: str
    language: str
    content: str


class GenerateResponse(BaseModel):
    root: str
    files: List[FileOut]
    zip_base64: Optional[str]
