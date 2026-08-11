import json
import logging
import random
import time
from typing import Tuple

from llm.prompts import get_enrich_system_prompt
from llm.schema import BookRecord

TEMPERATURE = 0.2
TIMEOUT = 30.0
MAX_RETRIES = 3 
BACKOFFS = [1.0, 2.0, 4.0]

logger = logging.getLogger("llm")
if not logger.handlers:
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def build_messages(
    record: BookRecord,
    broken_output: str | None = None,
    validation_error: str | None = None,
) -> list[dict]:
    """System prompt and user data are always two separate messages.
    """
    system_prompt = get_enrich_system_prompt()
    record_json = json.dumps(record.model_dump(mode="json"), ensure_ascii=False)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": record_json},
    ]
    if broken_output is not None and validation_error is not None:
        messages.append(
            {
                "role": "user",
                "content": (
                    "Your previous answer was rejected for this reason. "
                    "Return only corrected JSON matching the schema.\n\n"
                    f"Previous answer:\n{broken_output}\n\n"
                    f"Validation error:\n{validation_error}"
                ),
            }
        )
    return messages


def call_model(
    client,
    model: str,
    record: BookRecord,
    broken_output: str | None = None,
    validation_error: str | None = None,
    timeout: float = TIMEOUT,
    prompt_version: str = "enrich-v1",
) -> Tuple[str, dict]:
    """Calls the model and returns (raw_text, metadata).
    """
    messages = build_messages(record, broken_output, validation_error)

    attempt = 0
    last_exc: Exception | None = None
    while True:
        attempt += 1
        start = time.monotonic()
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=TEMPERATURE,
                messages=messages,
                timeout=timeout,
            )
            duration_ms = int((time.monotonic() - start) * 1000)

            usage_obj = getattr(response, "usage", None)
            usage_dict = {}
            if usage_obj is None:
                try:
                    usage_dict = response.get("usage", {})
                except Exception:
                    usage_dict = {}

            def _pick_token(uobj, keys):
                # try attribute access first
                if uobj is None:
                    return 0
                for k in keys:
                    # attribute on object
                    try:
                        val = getattr(uobj, k)
                        if val is not None:
                            return int(val)
                    except Exception:
                        pass
                    # key in dict
                    try:
                        if isinstance(uobj, dict) and k in uobj and uobj[k] is not None:
                            return int(uobj[k])
                    except Exception:
                        pass
                return 0

            prompt_tokens = _pick_token(usage_obj if usage_obj is not None else usage_dict, ["prompt_tokens", "input_tokens"]) 
            output_tokens = _pick_token(usage_obj if usage_obj is not None else usage_dict, ["completion_tokens", "output_tokens"]) 

            raw = response.choices[0].message.content

            log_line = {
                "prompt_version": prompt_version,
                "model": model,
                "input_tokens": int(prompt_tokens),
                "output_tokens": int(output_tokens),
                "duration_ms": duration_ms,
                "repair": broken_output is not None,
            }
            logger.info(json.dumps(log_line, ensure_ascii=False))

            meta = {
                "prompt_version": prompt_version,
                "model": model,
                "input_tokens": int(prompt_tokens),
                "output_tokens": int(output_tokens),
                "duration_ms": duration_ms,
                "attempt": attempt,
                "repair": broken_output is not None,
            }
            return raw, meta

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            last_exc = exc

            status_code = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
            headers = getattr(exc, "headers", {}) or getattr(exc, "response", {}).get("headers", {})

            is_timeout = isinstance(exc, TimeoutError) or "timeout" in str(exc).lower()

            if status_code in (400, 401, 403):
                raise

            if status_code == 429:
                retry_after = None
                try:
                    retry_after = int(headers.get("Retry-After")) if headers.get("Retry-After") else None
                except Exception:
                    retry_after = None
                if attempt > MAX_RETRIES:
                    raise
                wait = retry_after if retry_after is not None else BACKOFFS[min(attempt - 1, len(BACKOFFS) - 1)]
            elif is_timeout or (status_code and 500 <= int(status_code) < 600):
                if attempt > MAX_RETRIES:
                    raise TimeoutError(str(exc)) from exc if is_timeout else exc
                wait = BACKOFFS[min(attempt - 1, len(BACKOFFS) - 1)]
            else:
                raise

            jitter = random.random() * 0.5
            sleep_for = float(wait) + jitter
            time.sleep(sleep_for)