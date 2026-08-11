import json
from llm.prompts import get_enrich_system_prompt
from llm.schema import BookRecord

TEMPERATURE = 0.2

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
) -> str:
    """Calls the model and returns the raw text content of its reply.
    """
    messages = build_messages(record, broken_output, validation_error)
    response = client.chat.completions.create(
        model=model,
        temperature=TEMPERATURE,
        messages=messages,
    )
    return response.choices[0].message.content