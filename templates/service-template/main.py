from fastapi import FastAPI

app = FastAPI(title="TEMPLATE_NAME")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
