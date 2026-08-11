import json
from llm.prompts import get_enrich_system_prompt
from llm.schema import BookRecord

TEMPERATURE = 0.2

def build_messages(record: BookRecord) -> list[dict]:
    """System prompt and user data are always two separate messages.
    """
    system_prompt = get_enrich_system_prompt()
    record_json = json.dumps(record.model_dump(mode="json"), ensure_ascii=False)
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": record_json},
    ]

def call_model(client, model: str, record: BookRecord) -> str:
    """Calls the model and returns the raw text content of its reply.
    """
    messages = build_messages(record)
    response = client.chat.completions.create(
        model=model,
        temperature=TEMPERATURE,
        messages=messages,
    )
    return response.choices[0].message.content