# Points d'entrée FastAPI
"""
Point d'entrée FastAPI

Initialise FastAPI, enregistre les gestionnaires d'exceptions et inclut les routers des deux groupes.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from .config import API_DESCRIPTION, API_TITLE, API_VERSION
from .database import DatabaseError, init_database
from .exceptions import (
    database_exception_handler,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from .routers import aavs, attempts, learners, statuts


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Initialisation de la base de données...")
    # on ne va pas init si on est en mode test
    if os.environ.get("DATABASE_PATH") != "test_platonAAV.db":
        init_database()
    yield
    print("🛑 Arrêt du serveur")


app = FastAPI(
    title=API_TITLE, description=API_DESCRIPTION, version=API_VERSION, lifespan=lifespan
)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(DatabaseError, database_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Inclusion des routers
app.include_router(aavs.router)
app.include_router(learners.router)
app.include_router(statuts.router)
app.include_router(attempts.router)


@app.get("/")
def root():
    return {
        "message": "Bienvenue sur l'API PlatonAAV",
        "documentation": "/docs",
        "version": API_VERSION,
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}
