# Task API

A minimal in-memory CRUD API for managing tasks, built with FastAPI. Each task has an `id`, a `title`, and a `done` status. The API validates input, enforces basic business rules, and returns proper HTTP status codes for success and error cases.

## Installation & Running

Install dependencies and start the development server with a single command:

```bash
pip install fastapi uvicorn && fastapi dev
```

By default, the server runs at `http://localhost:8000`.

## Endpoints

| Method | Path          | Description                    | Success Status |
|--------|---------------|---------------------------------|-----------------|
| GET    | `/`           | Get a message describing the API | 200            |
| GET    | `/health`     | Check that the server is alive  | 200             |
| GET    | `/tasks`      | Get all tasks                   | 200             |
| GET    | `/tasks/{id}` | Get a single task by ID         | 200             |
| POST   | `/tasks`      | Create a new task               | 201             |
| PUT    | `/tasks/{id}` | Update a task by ID             | 200             |
| DELETE | `/tasks/{id}` | Delete a task by ID             | 204             |

### Validation & error handling

- `POST /tasks` requires a non-empty `title`; missing or empty titles return `400`.
- `PUT /tasks/{id}` requires a non-empty `title` and a valid boolean `done`; invalid input returns `400`, and a non-boolean `done` value is rejected automatically by FastAPI's own request validation with `422`.
- Requesting, updating, or deleting a task ID that doesn't exist returns `404`.

## Example: creating a task

```bash
curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk"}'
```

Example response:

```
HTTP/1.1 201 Created
content-type: application/json

{"id":4,"title":"Buy milk","done":false}
```

## Interactive API docs (Swagger UI)

FastAPI automatically generates interactive documentation for every endpoint, available at:

```
http://localhost:8000/docs
```

This page lists all endpoints, their expected request bodies, and their possible responses, and lets you send test requests directly from the browser. Each endpoint's one-line docstring (e.g. `"Get all tasks."`) appears here as its description, making the page self-explanatory without needing to read the source code.

![Swagger UI screenshot](<img width="959" height="460" alt="Server" src="https://github.com/user-attachments/assets/bed5f893-5071-46c0-bb6d-11c9380faf76" />
)
