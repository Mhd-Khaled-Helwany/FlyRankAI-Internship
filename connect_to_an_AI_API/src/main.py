import json
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from openai import OpenAI
from pydantic import ValidationError
from llm.schema import EnrichRequest, EnrichmentOutput, Category
from llm.model_client import call_model

load_dotenv()

client = OpenAI(base_url=os.environ["OPENROUTER_URL"], api_key=os.environ["OPENROUTER_KEY"])
MODEL = os.environ["LLM_MODEL"]
PROMPT_VERSION = "enrich-v1"
QUARANTINE_LOG = Path(__file__).resolve().parents[1] / "logs" / "quarantine.jsonl"
app = FastAPI()


def validate_model_output(raw_output: str) -> EnrichmentOutput:
    """Parse and validate model output without accepting arbitrary text."""
    json.loads(raw_output)
    return EnrichmentOutput.model_validate_json(raw_output)


def quarantine_output(
    request: EnrichRequest,
    raw_output: str,
    error: str,
) -> None:
    entry = {
        "input": request.record.model_dump(mode="json"),
        "raw_model_output": raw_output,
        "error": error,
        "prompt_version": PROMPT_VERSION,
    }
    try:
        QUARANTINE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with QUARANTINE_LOG.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        # Quarantine logging must not turn a controlled 422 into a server crash.
        pass

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

    try:
        return validate_model_output(raw_output)
    except (json.JSONDecodeError, ValidationError) as first_error:
        first_error_text = str(first_error)

    try:
        retry_output = call_model(
            client,
            MODEL,
            request.record,
            broken_output=raw_output,
            validation_error=first_error_text,
        )
    except Exception as exc:
        quarantine_output(request, raw_output, str(exc))
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "invalid_model_output",
                "message": "The model did not return valid JSON matching the schema.",
            },
        )

    try:
        return validate_model_output(retry_output)
    except (json.JSONDecodeError, ValidationError) as second_error:
        quarantine_output(request, retry_output, str(second_error))
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "invalid_model_output",
                "message": "The model returned invalid output after one correction attempt.",
            },
        )