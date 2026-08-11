import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from openai import OpenAI
from llm.schema import EnrichRequest, EnrichmentOutput, Category
from llm.model_client import call_model

load_dotenv()

client = OpenAI(base_url=os.environ["OPENROUTER_URL"], api_key=os.environ["OPENROUTER_KEY"])
MODEL = os.environ["LLM_MODEL"]
app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first = errors[0]
    field_path = ".".join(str(part) for part in first["loc"] if part != "body")
 
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "validation_error",
            "field": field_path or "body",
            "message": first["msg"],
        },
    )

@app.post("/enrich")
async def enrich_book(request: EnrichRequest):
    """"Endpoint that provides the LLM with a book record from books.json"""
    if os.environ.get("LLM_STUB") == "1":
        return EnrichmentOutput(
            category=Category.OTHER,
            summary=None,
            quality_flags=[],
        )
    try:
        raw_output = call_model(client, MODEL, request.record)
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"error": "model_call_failed", "message": str(exc)},
        )
 
    return {"raw_output": raw_output}