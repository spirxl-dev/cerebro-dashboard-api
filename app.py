from fastapi import FastAPI
import uvicorn
from starlette.responses import RedirectResponse
from functions import pollEvie2ups

# Create an instance of fastAPI class
app = FastAPI()

# Redirects default page on open to OpenAPI UI
@app.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url='/docs')




# Endpoint for evie 2ups. Copy and paste job for the other bots so leaving those out for now
@app.get("/evie-2ups-status")
async def get2upsStatus():
    
    # Call pollEvie2ups and assign it to variable data
    data = pollEvie2ups()

    # When endpoint is requested, it will return a json object which the frontend can parse
    return data


if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)