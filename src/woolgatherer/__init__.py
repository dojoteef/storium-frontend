"""
Main entry point for woolgatherer. This is where we setup the app.
"""
from fastapi import FastAPI

from woolgatherer.routers import stories, suggestions


app = FastAPI()

app.include_router(stories.router, prefix="/stories", tags=["stories"])
app.include_router(suggestions.router, prefix="/suggestions", tags=["suggestions"])
