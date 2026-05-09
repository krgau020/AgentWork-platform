from fastapi import FastAPI

app = FastAPI(title="Gateway Service")

@app.get("/")
def root():
    return {"message": "Gateway Service Running"}