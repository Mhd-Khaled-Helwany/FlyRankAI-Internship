import os
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
client = OpenAI(base_url=os.environ["OPENROUTER_URL"], api_key=os.environ["OPENROUTER_KEY"])
res = client.chat.completions.create(
 model=os.environ["LLM_MODEL"],
 messages=[{"role": "user", "content": "Reply with exactly the word: ready"}],
)
print(res.choices[0].message.content)