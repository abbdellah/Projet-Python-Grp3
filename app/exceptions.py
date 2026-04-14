"""
Gestionnaires d'exceptions de l'application
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from .database import DatabaseError

# ============================================
# GESTIONNAIRES D'EXCEPTIONS (fonctions simples)
# ============================================


async def http_exception_handler(
        request: Request, exc: StarletteHTTPException):
    """Gère les erreurs HTTP 404, 400, etc."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )


async def validation_exception_handler(
        request: Request, exc: RequestValidationError):
    """Gère les erreurs de validation Pydantic (422)."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Les données fournies sont invalides",
            "details": errors,
            "path": str(request.url)
        }
    )


async def database_exception_handler(request: Request, exc: DatabaseError):
    """Gère les erreurs de base de données."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "database_error",
            "message": "Une erreur est survenue lors de l'accès aux données",
            "details": {"error": str(exc)},
            "path": str(request.url)
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Attrape toutes les exceptions non gérées."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "Une erreur interne est survenue",
            "path": str(request.url)
        }
    )
