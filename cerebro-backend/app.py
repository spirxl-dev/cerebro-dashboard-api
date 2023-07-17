from fastapi import FastAPI
import uvicorn
from starlette.responses import RedirectResponse
from functions import pollEvie2ups, pollEvieEW


app = FastAPI()


@app.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url="/docs")


@app.get("/evie-2ups-status")
async def get2upsStatus():

    twoUps_status_data = pollEvie2ups()
    return twoUps_status_data


@app.get("/evie-ew-status")
async def getEwStatus():
    ew_status_data = pollEvieEW()
    return ew_status_data


if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)
