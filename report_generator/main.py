from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def get_health():
    """Get the health of the API."""
    return {"status": "ok"}
