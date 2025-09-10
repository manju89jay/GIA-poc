import base64
import io
import re
import zipfile
from typing import List
from fastapi import HTTPException

from models import FileOut

FILE_RE = re.compile(r"// FILE: ([^\n]+)\n```(c|cpp)\n(.*?)\n```", re.DOTALL)


def parse_llm_files(text: str) -> List[FileOut]:
    if re.fullmatch(r"\s*/\*.*?\*/\s*", text, re.DOTALL):
        raise HTTPException(status_code=409, detail=text.strip())
    text = text.strip()
    matches = list(FILE_RE.finditer(text))
    if len(matches) != 4 or FILE_RE.sub("", text).strip():
        raise HTTPException(status_code=422, detail="expected four file blocks")
    files = []
    has_versioned = has_conv_h = has_conv_cpp = has_converters = False
    for m in matches:
        name, lang, body = m.group(1).strip(), m.group(2), m.group(3)
        files.append(FileOut(name=name, language=lang, content=body))
        if name.endswith("_versioned.h"):
            has_versioned = True
        elif name.startswith("Converter_") and name.endswith(".h"):
            has_conv_h = True
        elif name.startswith("Converter_") and name.endswith(".cpp"):
            has_conv_cpp = True
        elif name == "converters.cpp":
            has_converters = True
    if not (has_versioned and has_conv_h and has_conv_cpp and has_converters):
        raise HTTPException(status_code=422, detail="missing expected files")
    return files


def zip_base64(files: List[FileOut]) -> str:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.writestr(f.name, f.content)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
