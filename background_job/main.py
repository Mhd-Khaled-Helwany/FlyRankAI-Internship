from fastapi import FastAPI
import logging
import datetime

import inngest
import inngest.fast_api

app = FastAPI()

inngest_client = inngest.Inngest(
    app_id="report-api",
    logger=logging.getLogger("uvicorn"),
)

@app.get("/health")
async def get_health():
    """Get the health of the API."""
    return {"status": "ok"}

@inngest_client.create_function(
    fn_id="say-hello",
    # Event that triggers this function
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello(ctx: inngest.Context) -> str:
    await ctx.step.sleep("sleep-5s", datetime.timedelta(seconds=5))
    ctx.logger.info(ctx.event)
    return "Hello from the background!"

inngest.fast_api.serve(app, inngest_client, [say_hello])
# terminal 1: INNGEST_DEV=1 ../.venv/bin/python -m uvicorn main:app --port 8000
# terminal 2: npx inngest-cli@latest dev -u http://localhost:8000/api/inngest
# browser: http://localhost:8288