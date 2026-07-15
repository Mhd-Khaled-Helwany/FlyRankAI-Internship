from fastapi import FastAPI

app = FastAPI()

# Hello world endpoint from FastAPI documentation
# To run server, use command fastapi dev
# To see message in browser, visit http://localhost:8000
# To see message in terminal, run command curl -i http://localhost:8000/
@app.get("/")
async def root():
    return {"message": "Hello World"}