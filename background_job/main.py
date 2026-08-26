from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import logging
import datetime
import inngest
import inngest.fast_api

class ReportRequest(BaseModel):
    topic: str = ""

app = FastAPI()

inngest_client = inngest.Inngest(
    app_id="report-api",
    logger=logging.getLogger("uvicorn"),
)

reports: dict[str, dict] = {}
next_id = 1

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

@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(event="report/requested"),
    retries=2,
)
async def make_report(ctx: inngest.Context) -> str:
    report_id = ctx.event.data["id"]
    topic = ctx.event.data["topic"]
    await ctx.step.sleep("do-the-slow-work", datetime.timedelta(seconds=8))

    def build(topic: str) -> str:
        if topic == "fail":
            raise ValueError("The report oven is broken!")
        return f"Generated report about '{topic}'"

    result = await ctx.step.run("build-report", build, topic)
    if report_id in reports:
        reports[report_id]["status"] = "done"
        reports[report_id]["result"] = result
    return result

@app.post("/reports", status_code=status.HTTP_202_ACCEPTED)
async def create_report(request: ReportRequest):
    """Accept a report request and hand the slow work to Inngest."""
    if not request.topic:
        raise HTTPException(status_code=400, detail="topic is required")

    global next_id
    report_id = str(next_id)
    next_id += 1
    reports[report_id] = {
        "id": report_id,
        "topic": request.topic,
        "status": "pending",
    }
    await inngest_client.send(
        inngest.Event(
            name="report/requested",
            data={"id": report_id, "topic": request.topic},
        )
    )
    return {"id": report_id, "status": "pending"}

@app.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Get the current state of a report."""
    if report_id not in reports:
        raise HTTPException(status_code=404, detail="Report not found")
    return reports[report_id]

inngest.fast_api.serve(app, inngest_client, [say_hello, make_report])
# terminal 1: INNGEST_DEV=1 ../.venv/bin/python -m uvicorn main:app --port 8000
# terminal 2: npx inngest-cli@latest dev -u http://localhost:8000/api/inngest
# browser: http://localhost:8288
