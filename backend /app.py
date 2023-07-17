from fastapi import FastAPI
import uvicorn
from starlette.responses import RedirectResponse
from functions import pollEvie2ups


app = FastAPI()


@app.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url="/docs")


@app.get("/evie-2ups-status")
async def get2upsStatus():
    data = pollEvie2ups()
    return data


if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)
