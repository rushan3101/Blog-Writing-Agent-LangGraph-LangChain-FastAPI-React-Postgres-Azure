from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.blogs import router
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.core.config import settings

app = FastAPI(
    title="Blog Writing Agent",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

Path("images").mkdir(
    exist_ok=True
)

app.mount(
    "/blogs/images",
    StaticFiles(directory="images"),
    name="images"
)

app.include_router(router)