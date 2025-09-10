from fastapi import FastAPI, HTTPException

from llm_backends import get_backend, LLMError
from models import GenerateRequest, GenerateResponse
from parser_validator import parse_llm_files, zip_base64
from prompt_text import SYSTEM_PROMPT, build_user_prompt

app = FastAPI()

MAX_HEADER_LEN = 100_000


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    if not req.root or not req.old_header or not req.new_header:
        raise HTTPException(status_code=400, detail="missing input")
    if len(req.old_header) > MAX_HEADER_LEN or len(req.new_header) > MAX_HEADER_LEN:
        raise HTTPException(status_code=400, detail="input too large")

    try:
        backend = get_backend(req.backend, req.model, req.temperature)
    except LLMError as e:
        raise HTTPException(status_code=424, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    system_prompt = SYSTEM_PROMPT
    user_prompt = build_user_prompt(req.root, req.old_header, req.new_header)
    try:
        text = backend.generate(system_prompt, user_prompt)
    except Exception as e:  # backend failure
        raise HTTPException(status_code=424, detail=str(e))

    try:
        files = parse_llm_files(text)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    zip_str = zip_base64(files) if req.return_zip else None
    return GenerateResponse(root=req.root, files=files, zip_base64=zip_str)
