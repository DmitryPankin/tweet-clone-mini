import os

from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from .routers.tweets import router


def get_dist_dir():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "../dist")
    return dist_dir


app = FastAPI(
    title="Tweet-clone",
    description="Мини версия Tweet с минимальной функциональностью",
    version="1.0.0",
)

app.include_router(router)


@app.exception_handler(HTTPException)
async def http_exception_handler(exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "result": False,
            "error_type": "HTTPException",
            "error_message": exc.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "result": False,
            "error_type": "RequestValidationError",
            "error_message": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"result": False, "error_type": "Exception", "error_message": str(exc)},
    )
