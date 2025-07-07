# main.py
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def _():
    return {"ok": True}
