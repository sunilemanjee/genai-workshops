import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import search_router
import os
from elasticapm.contrib.starlette import make_apm_client, ElasticAPM

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


apm = make_apm_client({
    'SERVICE_NAME': os.getenv('APM_SERVICE_NAME'),
    'API_KEY': os.getenv('APM_API_KEY'),
    'SERVER_URL': os.getenv('APM_SERVER_URL')
})


app = FastAPI()
# app.add_middleware(ElasticAPM, client=apm)


# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ElasticAPM, client=apm)

# Include the router
app.include_router(search_router.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}
