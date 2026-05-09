from fastapi import FastAPI

app = FastAPI(title="Validation Service")

@app.get("/")
def root():
    return {"message": "Validation Service Running"}