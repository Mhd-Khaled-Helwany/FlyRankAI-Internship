from fastapi import FastAPI

app = FastAPI()

# Hello world endpoint from FastAPI documentation
# To run server, use command fastapi dev
# To see message in browser, visit http://localhost:8000/
# To see message in terminal, run command curl -i http://localhost:8000/
"""@app.get("/")
async def root():
    return {"message": "Hello World"}
"""


# First real endpoint for stage 1 of the assignment
# To run server, use command fastapi dev
# To see message in browser, visit http://localhost:8000/
# To see message in terminal, run command curl -i http://localhost:8000/
# Add /health at the end of the URL to see the enpoint's status
@app.get("/")
async def get_message():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
async def get_health():
    return {"status": "ok"}