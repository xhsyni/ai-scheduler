from fastapi import FastAPI
from fastmcp import FastMCP
from routers import user

app = FastAPI()
mcp=FastMCP(app)

@app.get("/health")
def health_check():
    return {"message": "OK"}

@app.get("/")
def read_root():
    return {"message": "Hello World"}

app.include_router(user.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)