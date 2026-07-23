# To run server, use command fastapi dev
# To see message in browser, visit http://localhost:8000/
# To see message in terminal, run command curl -i http://localhost:8000/
# To access a specific endpoint, add the endpoint to the end of the URL, e.g. http://localhost:8000/tasks

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import sqlite3

class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: str
    done: bool

app = FastAPI()

# Stage 0: No dupelication of data and table is created once
conn = sqlite3.connect("tasks.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        done BOOLEAN NOT NULL
    )
""")

cursor.execute("SELECT COUNT(*) FROM tasks")
count = cursor.fetchone()[0]
if count == 0:
    cursor.executemany(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        [
            ("clean the house", False),
            ("cook dinner", True),
            ("do the laundry", True),
        ]
    )
conn.commit()
conn.close()

in_memory = [{"id": 1, "title": "clean the house", "done": False},
             {"id": 2, "title": "cook dinner", "done": True},
             {"id": 3, "title": "do the laundry", "done": True}]
next_id = 4

# Hello world endpoint from FastAPI documentation
"""@app.get("/")
async def root():
    return {"message": "Hello World"}
"""

@app.get("/")
async def get_message():
    """Get a message from the API."""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
async def get_health():
    """Get the health of the API."""
    return {"status": "ok"}

# Stage 1: make the server fetch data from the database
@app.get("/tasks")
async def get_tasks():
    """Get all tasks."""
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    rows = cursor.fetchall()
    conn.close()
    tasks = [{"id": row[0], "title": row[1], "done": bool(row[2])} for row in rows]
    return tasks

@app.get("/tasks/{id}")
async def get_task(id: int):
    """Get a task by ID."""
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "title": row[1], "done": bool(row[2])}
    raise HTTPException(status_code=404, detail=f"Task {id} not found")

# Stage 2: make the server create data in the database
@app.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(request: TaskCreate):
    """Create a new task."""
    if not request.title:
        raise HTTPException(status_code=400, detail="Title is required")
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (request.title, False))
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return {"id": task_id, "title": request.title, "done": False}

# Stage 3: make the server update and delete data in the database
@app.put("/tasks/{id}")
async def update_task(id: int, request: TaskUpdate):
    """Update a task by ID."""
    if not request.title:
        raise HTTPException(status_code=400, detail="Title is required")
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ?", (request.title, request.done, id))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    conn.close()
    return {"id": id, "title": request.title, "done": request.done}

@app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(id: int):
    """Delete a task by ID."""
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (id,))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    conn.close()
