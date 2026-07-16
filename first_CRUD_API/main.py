# To run server, use command fastapi dev
# To see message in browser, visit http://localhost:8000/
# To see message in terminal, run command curl -i http://localhost:8000/
# To access a specific endpoint, add the endpoint to the end of the URL, e.g. http://localhost:8000/tasks

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: str
    done: bool

app = FastAPI()


in_memory = [{"id": 1, "title": "clean the house", "done": False},
             {"id": 2, "title": "cook dinner", "done": True},
             {"id": 3, "title": "do the laundry", "done": True}]
next_id = 4

# Hello world endpoint from FastAPI documentation
"""@app.get("/")
async def root():
    return {"message": "Hello World"}
"""


# First real endpoint for stage 1 of the assignment
@app.get("/")
async def get_message():
    """Get a message from the API."""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
async def get_health():
    """Get the health of the API."""
    return {"status": "ok"}


# Stage 2 endpoint for the assignment
@app.get("/tasks")
async def get_tasks():
    """Get all tasks."""
    return in_memory

@app.get("/tasks/{id}")
async def get_task(id: int):
    """Get a task by ID."""
    for task in in_memory:
        if task["id"] == id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {id} not found")

# Stage 3 endpoint for the assignment
# Example of a POST request using curl:
"""curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk","done":false}'"""
@app.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(request: TaskCreate):
    """Create a new task."""
    global next_id
    if not request.title:
        raise HTTPException(status_code=400, detail="Title is required")
    task = {"id": next_id, "title": request.title, "done": False}
    next_id += 1
    in_memory.append(task)
    return task

# Stage 4 endpoint for the assignment
# Example of a PUT request using curl:
"""curl -i -X PUT http://localhost:8000/tasks/3 \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy food","done":true}'
"""
@app.put("/tasks/{id}")
async def update_task(id: int, request: TaskUpdate):
    """Update a task by ID."""
    if not request.title:
        raise HTTPException(status_code=400, detail="Title is required")
    for task in in_memory:
        if task["id"] == id:
            task["title"] = request.title
            task["done"] = request.done
            return task
    raise HTTPException(status_code=404, detail=f"Task {id} not found")

# Example of a DELETE request using curl:
"""curl -i -X DELETE http://localhost:8000/tasks/3"""
@app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(id: int):
    """Delete a task by ID."""
    for task in in_memory:
        if task["id"] == id:
            in_memory.remove(task)
            return
    raise HTTPException(status_code=404, detail=f"Task {id} not found")
