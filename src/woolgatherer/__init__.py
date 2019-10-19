"""
Main entry point for woolgatherer. This is where we setup the app.
"""
from fastapi import FastAPI

from woolgatherer.routers import stories, suggestions
from woolgatherer.db.session import open_connection_pool, close_connection_pool


app = FastAPI()

app.include_router(stories.router, prefix="/stories", tags=["stories"])
app.include_router(suggestions.router, prefix="/suggestions", tags=["suggestions"])

app.add_event_handler("startup", open_connection_pool)
app.add_event_handler("shutdown", close_connection_pool)
