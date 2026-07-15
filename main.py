# To run server, use command fastapi dev
# To see message in browser, visit http://localhost:8000/
# To see message in terminal, run command curl -i http://localhost:8000/
# To access a specific endpoint, add the endpoint to the end of the URL, e.g. http://localhost:8000/tasks

from fastapi import FastAPI, HTTPException

app = FastAPI()


in_memory = [{"id": 33, "title": "clean the house", "done": False},
             {"id": 50, "title": "cook dinner", "done": True},
             {"id": 89, "title": "do the laundry", "done": True}]

# Hello world endpoint from FastAPI documentation
"""@app.get("/")
async def root():
    return {"message": "Hello World"}
"""


# First real endpoint for stage 1 of the assignment
@app.get("/")
async def get_message():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
async def get_health():
    return {"status": "ok"}


# Stage 2 endpoint for the assignment
@app.get("/tasks")
async def get_tasks():
    return in_memory

@app.get("/tasks/{id}")
async def get_task(id: int):
    for task in in_memory:
        if task["id"] == id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {id} not found")
