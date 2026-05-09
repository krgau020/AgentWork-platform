from fastapi import FastAPI

app = FastAPI(title="AI Service")

@app.get("/")
def root():
    return {"message": "AI Service Running"}