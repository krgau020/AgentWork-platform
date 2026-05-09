from fastapi import FastAPI

app = FastAPI(title="Document Service")

@app.get("/")
def root():
    return {"message": "Document Service Running"}