from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Service is running!"}

@app.get("/health")
def health_check():
    return JSONResponse(status_code=200, content={"status": "success", "message": "200 OK"})
